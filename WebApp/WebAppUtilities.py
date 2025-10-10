import requests, utilities_reFactore, setting, logging, traceback
from crud import crud
from vpn_service import buy_and_upgrade_service
from WebApp.WebAppDialogue import transaction
from pydantic import BaseModel
from API import cryptomusAPI
from vpn_service import panel_api
from datetime import datetime, timedelta

class ConnectToServer:
    last_update = None
    def refresh_token(self):
        now = datetime.now()
        if self.last_update:
            if self.last_update < now:
                panel_api.marzban_api.refresh_connection()
                self.last_update = now + timedelta(hours=12)
        else:
            panel_api.marzban_api.refresh_connection()
            self.last_update = now + timedelta(hours=12)

connect_to_server_instance = ConnectToServer()

async def handle_inviter_referral(session, financial):
    if financial.owner.invited_by and not financial.owner.config.first_purchase_refreal_for_inviter:
        try:
            with session.begin_nested():
                ft_instance = utilities_reFactore.FindText(None, None)
                referral_amount = int((financial.amount * setting.REFERRAL_PERCENT) / 100)
                finacial_report = crud.create_financial_report(
                    session, 'recive',
                    chat_id=financial.owner.invited_by,
                    amount=referral_amount,
                    action='first_purchase_referral',
                    service_id=financial.financial_id,
                    payment_status='not paid',
                    payment_getway='wallet',
                    currency='IRT',
                )
                crud.add_credit_to_wallet(session, finacial_report)
                text = await ft_instance.find_from_database(financial.owner.invited_by, 'recive_money_for_referral')
                text = text.format(setting.REFERRAL_PERCENT, f"{referral_amount:,}")
                crud.update_user_config(session, chat_id=financial.chat_id, first_purchase_refreal_for_inviter=True)
                await utilities_reFactore.report_to_user('success', financial.owner.invited_by, text)
                admin_msg = (f"\nUser Get Refferal"
                             f"\nInviter ChatID: {financial.owner.invited_by}"
                             f"\nService ID: {financial.id_holder}"
                             f"\nService Amount: {financial.amount:,} IRT"
                             f"\nRefferal Amount: {referral_amount:,} IRT ({setting.REFERRAL_PERCENT}%)"
                             )

                await utilities_reFactore.report_to_admin('info', financial.owner.invited_by, admin_msg, financial.owner)
        except Exception as e:
            msg = (f"Error Type: {type(e)}"
                   f"\nError Str: {str(e)}")
            await utilities_reFactore.report_to_admin('error', "handle_inviter_referral", msg)
            logging.error(f'error to add referral to inviter wallet:\n{e}')

async def increase_wallet_balance(financial, context, session):
    dialogues = transaction.get(financial.owner.language, transaction.get('fa'))
    crud.add_credit_to_wallet(session, financial)
    text = dialogues.get('amount_added_to_wallet_successfully')
    text = text.format(f"{financial.amount:,}")
    await context.bot.send_message(text=text, chat_id=financial.chat_id)

def refund(session, financial_db):
    crud.add_credit_to_wallet(session, financial_db, 'refund')
    session.commit()

class PaymentError(Exception):
    pass

def verify_payment_zarinpal(authority: str, amount: int):
    """Verifies payment with Zarinpal API."""
    url = 'https://payment.zarinpal.com/pg/v4/payment/verify.json'
    json_payload = {
        'merchant_id': setting.zarinpal_merchant_id,
        'amount': amount,
        'authority': authority
    }

    response = requests.post(url=url, json=json_payload)

    if not response.json():
        raise PaymentError(f"Invalid response from Zarinpal: {response}")

    return response.json()


async def handle_successful_payment(session, financial, authority, payment_getway):
    """Processes the successful payment."""
    context = utilities_reFactore.FakeContext()

    extra_data = ""
    if financial.action == 'buy_vpn_service':
        service = await buy_and_upgrade_service.create_service_for_user(context, session, financial.id_holder)
        extra_data = f"Service Traffic: {service.traffic}GB\nService Period: {service.period} Day\nService Username: {service.username}"

    if financial.action == 'upgrade_vpn_service':
        purchase, upgrade_traffic, upgrade_period = await buy_and_upgrade_service.upgrade_service_for_user(context, session, financial.id_holder)
        extra_data = (f"\nService Username: {purchase.username}"
                      f"\nUpgrade Traffic: {upgrade_traffic}GB"
                      f"\nUpgrade Period: {upgrade_period} Day")

    elif financial.action == 'increase_wallet_balance':
        await increase_wallet_balance(financial, context, session)

    await handle_inviter_referral(session, financial)
    await handle_successful_report(financial, extra_data, authority, payment_getway)
    crud.update_financial_report_status(session, financial.financial_id, 'paid')

async def handle_failed_payment(session, financial, exception, dialogues, authority, payment_getway):
    """Handles payment failure and refunds if necessary."""
    refund(session, financial)
    error_msg = log_error(
        'Amount refunded to user wallet! Payment was not successful!', exception, authority
    )
    message = dialogues.get('operation_failed_user').format(f"{financial.amount:,}")

    await utilities_reFactore.report_to_admin('error', payment_getway, error_msg, financial.owner)
    await utilities_reFactore.report_to_user('warning', financial.chat_id, message)

async def handle_successful_report(financial, extra_data, authority, payment_getway):
    """Reports successful payment."""
    msg = (
        f'Action: {financial.action.replace("_", " ")}\n'
        f'Authority: {authority}\n'
        f'Amount: {financial.amount:,}\n'
        f'Service ID: {financial.id_holder}\n'
        f'{extra_data}'
    )
    await utilities_reFactore.report_to_admin('purchase', payment_getway, msg, financial.owner)

def log_error(msg, exception, order_id):
    """Logs error details."""
    logging.error(f'{msg} {exception}')
    tb = traceback.format_exc()
    error = (
        f'{msg}\n\n'
        f'Error Type: {type(exception)}\n'
        f'Authority: {order_id}\n'
        f'Error Reason: {exception}\n'
        f'Traceback: \n{tb}'
    )
    return error

async def report_unhandled_error(exception, section, authority, financial):
    """Reports unhandled errors to the admin."""
    error_msg = log_error('Unhandled error occurred | User does not know payment status', exception, authority)
    await utilities_reFactore.report_to_admin(
        'emergency_error', section, error_msg, financial.owner
    )

class CryptomusPaymentWebhook(BaseModel):
    type: str
    uuid: str
    order_id: str
    amount: str
    payment_amount_usd: str
    is_final: bool
    status: str
    sign: str
    additional_data: str

async def verify_cryptomus_payment(order_id: str, uuid_: str | None, financial):
    """Verifies payment status using the Cryptomus API."""
    try:

        invoice_check = await cryptomusAPI.InvoiceInfo(
            setting.cryptomus_api_key, setting.cryptomus_merchant_id
        ).execute(order_id, uuid_)

        if invoice_check:
            payment_status = invoice_check.get('result', {}).get('payment_status')
            if payment_status in ('paid', 'paid_over'):
                return invoice_check

    except Exception as e:
        await report_unhandled_error(e, 'CryptomusWebApp', order_id, financial)
