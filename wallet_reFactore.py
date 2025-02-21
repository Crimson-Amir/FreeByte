import json, uuid, setting
from WebApp import WebAppUtilities
import logging
from crud import crud
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database_sqlalchemy import SessionLocal
from utilities_reFactore import FindText, message_token, handle_error, human_readable, report_to_user, report_to_admin, find_user
from vpn_service import vpn_utilities
from API import zarinPalAPI, cryptomusAPI, convert_irt_to_usd
from WebApp.WebAppDialogue import transaction
import utilities_reFactore


async def wallet_page(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    ft_instance = FindText(update, context)

    try:
        with SessionLocal() as session:
            get_user = crud.get_user(session, chat_id)
            get_financial_reports = crud.get_financial_reports(session, chat_id, 0, 5, True)

            last_transaction = await ft_instance.find_text('no_transaction_yet')
            lasts_report = ''

            if get_financial_reports:
                last_transaction = human_readable(f'{get_financial_reports[0].register_date}', await ft_instance.find_user_language())
                lasts_report = await ft_instance.find_text('recent_transactions')
                for report in get_financial_reports:
                    lasts_report += f"\n{await ft_instance.find_text('receive_money') if report.operation in ['recive', 'refund'] else await ft_instance.find_text('spend_money')} {report.amount:,} {await ft_instance.find_text('irt')} - {human_readable(report.register_date, await ft_instance.find_user_language())}"

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('refresh'), callback_data='wallet_page'),
                 InlineKeyboardButton(await ft_instance.find_keyboard('increase_balance'), callback_data='buy_credit_volume')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('financial_transactions'), callback_data='financial_transactions_wallet_1')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]]

            text = (
                f"<b>{await ft_instance.find_text('wallet_page_title')}</b>"
                f"\n\n{await ft_instance.find_text('wallet_balance_key')} {get_user.wallet:,} {await ft_instance.find_text('irt')}"
                f"\n{await ft_instance.find_text('last_transaction')} {last_transaction}"
                f"\n\n{lasts_report}"
            )

            if query:
                return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

    except Exception as e:
        logging.error(f'error in wallet page: {e}')
        if "specified new message content and reply markup are exactly the same" in str(e):
            return await query.answer()
        return await query.answer(await ft_instance.find_text('error_message'))


async def financial_transactions_wallet(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    page = int(query.data.split('_')[-1])
    items_per_page = 10
    ft_instance = FindText(update, context)

    try:
        with SessionLocal() as session:
            total_reports = crud.get_total_financial_reports(session, chat_id)
            total_pages = (total_reports + items_per_page - 1) // items_per_page

            offset = (page - 1) * items_per_page
            get_financial_reports = crud.get_financial_reports(session, chat_id, offset, items_per_page)

            if get_financial_reports:
                lasts_report = await ft_instance.find_text('recent_transactions') + '\n'

                for report in get_financial_reports:
                    payment_status = {
                        'not paid': await ft_instance.find_text('not_paid'),
                        'paid': await ft_instance.find_text('paid'),
                        'refund': await ft_instance.find_text('refund'),
                        'hold': await ft_instance.find_text('hold'),
                    }
                    payment_action = {
                        'upgrade_vpn_service': await ft_instance.find_text('upgrade_vpn_service_action'),
                        'buy_vpn_service': await ft_instance.find_text('buy_vpn_service_action'),
                        'increase_wallet_balance': await ft_instance.find_text('increase_wallet_balance_action'),
                        'remove_vpn_service': await ft_instance.find_text('remove_vpn_sevice_and_recive_payback'),
                        'increase_balance_by_admin': await ft_instance.find_text('increase_balance_by_admin'),
                        'reduction_balance_by_admin': await ft_instance.find_text('reduction_balance_by_admin'),
                        'first_purchase_referral': await ft_instance.find_text('first_purchase_referral'),
                        'buy_vn_number_for_sms': await ft_instance.find_text('buy_vn_number_for_sms'),

                    }
                    payment_gateway = {
                        'zarinpal': await ft_instance.find_text('zarinpal_label'),
                        'cryptomus': await ft_instance.find_text('cryptomus_label'),
                        'wallet': await ft_instance.find_keyboard('pay_with_wallet_balance'),
                    }
                    lasts_report += f"\n\n{await ft_instance.find_text('receive_money') if report.operation in ['recive', 'refund'] else await ft_instance.find_text('spend_money')} <code>{report.amount:,}</code> {await ft_instance.find_text('irt')} | "
                    lasts_report += f"{report.register_date.date()}"
                    lasts_report += f"\n{payment_status.get(report.payment_status, '')} | {payment_action.get(report.action, '')} {report.id_holder}"
                    lasts_report += f"\n{await ft_instance.find_text('payment_authority')} <code>{report.authority[-8:] if report.authority else '-'}</code> | {payment_gateway.get(report.payment_getway, '')}"
            else:
                lasts_report = await ft_instance.find_text('no_transaction_yet')

            keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('refresh'), callback_data='financial_transactions_wallet_1')],]

            if page > 1:
                keyboard.append([InlineKeyboardButton(f'{await ft_instance.find_keyboard("previous")}', callback_data=f'financial_transactions_wallet_{page - 1}')])
            if page < total_pages:
                keyboard.append([InlineKeyboardButton(f'{await ft_instance.find_keyboard("next")}', callback_data=f'financial_transactions_wallet_{page + 1}')])

            keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='wallet_page')])

            text_ = f"\n\n{lasts_report}"
            await query.edit_message_text(text=text_, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

    except Exception as e:
        logging.error(f'error in wallet page: {e}')
        if "specified new message content and reply markup are exactly the same" in str(e):
            return await query.answer()
        return await query.answer(await ft_instance.find_text('error_message'))


async def buy_credit_volume(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    chat_id = update.effective_chat.id
    in_new_message = query.data.replace('buy_credit_volume', '') == '__in_new_message'

    try:
        text = await ft_instance.find_text('add_credit_to_wallet_title')

        keyboard = [
            [InlineKeyboardButton(f"25,000 {await ft_instance.find_text('irt')}", callback_data="create_invoice__increase_wallet_balance__25000"),
             InlineKeyboardButton(f"50,000 {await ft_instance.find_text('irt')}", callback_data="create_invoice__increase_wallet_balance__50000")],
            [InlineKeyboardButton(f"75,000 {await ft_instance.find_text('irt')}", callback_data="create_invoice__increase_wallet_balance__75000"),
             InlineKeyboardButton(f"100,000 {await ft_instance.find_text('irt')}", callback_data="create_invoice__increase_wallet_balance__100000")],
            [InlineKeyboardButton(f"200,000 {await ft_instance.find_text('irt')}", callback_data="create_invoice__increase_wallet_balance__200000"),
             InlineKeyboardButton(f"500,000 {await ft_instance.find_text('irt')}", callback_data="create_invoice__increase_wallet_balance__500000")],
            [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='wallet_page')]
        ]

        if in_new_message:
            return await context.bot.send_message(chat_id=chat_id ,text=text, parse_mode='markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        await query.edit_message_text(text=text, parse_mode='markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logging.error(f'error in buy credit volume: {e}')
        return await query.answer(await ft_instance.find_text('error_message'))


@handle_error.handle_functions_error
@message_token.check_token
async def create_invoice(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    ft_instance = FindText(update, context)
    pay_by_wallet_satatus = True
    service_id = None
    action, *extra_data = query.data.replace('create_invoice__', '').split('__')

    with SessionLocal() as session:
        with session.begin():

            if action == "increase_wallet_balance":
                pay_by_wallet_satatus = False
                amount = int(extra_data[0])
                operation = 'recive'
                back_button_callback = 'buy_credit_volume'
                invoice_extra_data = await ft_instance.find_text('charge_wallet')

            elif action == "buy_vpn_service":
                period, traffic, product_id = extra_data
                amount = await vpn_utilities.calculate_price(traffic, period, chat_id, session)
                back_button_callback= f'vpn_set_period_traffic__30_40_{product_id}'
                operation = 'spend'
                invoice_extra_data = (f"{await ft_instance.find_text('buy_vpn_service')}"
                                      f"\n{await ft_instance.find_text('traffic')} {traffic} {await ft_instance.find_keyboard('gb_lable')}"
                                      f"\n{await ft_instance.find_text('period')} {period} {await ft_instance.find_keyboard('day_lable')}")

                purchase = crud.create_purchase(session, product_id, chat_id, traffic, period)
                service_id = purchase.purchase_id

            elif action == "upgrade_vpn_service":
                upgrade_period, upgrade_traffic, purchase_id = extra_data
                amount = await vpn_utilities.calculate_price(upgrade_traffic, upgrade_period, chat_id, session)
                back_button_callback, operation = f'vpn_upgrade_service__{upgrade_period}__{upgrade_traffic}__{purchase_id}', 'spend'
                format_title = await ft_instance.find_text('upgrade_vpn_service')
                format_title = format_title.format(purchase_id)
                invoice_extra_data = (f"{format_title}"
                                      f"\n{await ft_instance.find_text('traffic')} {upgrade_traffic} {await ft_instance.find_keyboard('gb_lable')}"
                                      f"\n{await ft_instance.find_text('period')} {upgrade_period} {await ft_instance.find_keyboard('day_lable')}")

                service_id = crud.update_purchase(session, purchase_id, upgrade_traffic, upgrade_period)

            finacial_report = crud.create_financial_report(session, operation, chat_id, amount, action, service_id, 'not paid')

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('iran_payment_gateway'), callback_data=f"pay_by_zarinpal__{action}__{finacial_report.financial_id}")],
                [InlineKeyboardButton(await ft_instance.find_keyboard('pay_with_wallet_balance'), callback_data=f"pay_by_wallet__{action}__{finacial_report.financial_id}")
                 if pay_by_wallet_satatus and finacial_report.owner.wallet >= amount else [],
                 InlineKeyboardButton(await ft_instance.find_keyboard('cryptomus_payment_gateway'), callback_data=f"pay_by_cryptomus__{action}__{finacial_report.financial_id}")],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=back_button_callback)],
            ]
            keyboard = [list(filter(None, row)) for row in keyboard]

            get_user = await find_user(session, chat_id)
            price_text = await ft_instance.find_text('price_with_discount') \
                if get_user.user_level > 1 and pay_by_wallet_satatus else await ft_instance.find_text('price')
            price_text = price_text.format(vpn_utilities.DiscountPerLevel.descount.get(get_user.user_level, 1))

            text = (f"<b>{await ft_instance.find_text('invoice_title')}</b>"
                    f"\n\n<b>{await ft_instance.find_text('wallet_credit_label')} {finacial_report.owner.wallet:,} {await ft_instance.find_text('irt')}</b>"
                    f"\n\n{await ft_instance.find_text('invoice_extra_data')}\n{invoice_extra_data}"
                    f"\n\n<b>{price_text} {amount:,} {await ft_instance.find_text('irt')}</b>"
                    f"\n\n{await ft_instance.find_text('payment_option_title')}")

            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def pay_by_zarinpal(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    action, financial_id = query.data.replace('pay_by_zarinpal__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            get_financial = crud.get_financial_report_by_id(session, financial_id)

            instance = zarinPalAPI.SendInformation(setting.zarinpal_merchant_id)

            create_zarinpal_invoice = await instance.execute(
                merchant_id=setting.zarinpal_merchant_id,
                amount=get_financial.amount,
                currency='IRT',
                description=action.replace('vpn', 'vps'),
                callback_url=setting.zarinpal_url_callback,
                metadata={"mobile": str(get_financial.owner.phone_number), "email": get_financial.owner.email}
            )

            if not create_zarinpal_invoice:
                return await query.answer(await ft_instance.find_text('fail_to_create_payment_gateway'), show_alert=True)

            crud.update_financial_report(
                session, get_financial.financial_id,
                payment_getway='zarinpal',
                authority=create_zarinpal_invoice.authority,
                currency=create_zarinpal_invoice.currency,
                url_callback=create_zarinpal_invoice.url_callback,
            )

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('login_to_payment_gateway'), url=f'https://payment.zarinpal.com/pg/StartPay/{create_zarinpal_invoice.authority}')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('manual_check_zarinpal_payment'), callback_data=f'manual_check_zarinpal_payment__{financial_id}')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data="start_in_new_message")]
            ]

            text = (
                f"<b>{await ft_instance.find_text('payment_gateway_title')}</b>"
                f"\n{await ft_instance.find_text('zarinpal_payment_gateway_body')}"
                f"\n\n{await ft_instance.find_text('payment_gateway_label')} {await ft_instance.find_text('zarinpal_label')}"
                f"\n{await ft_instance.find_text('price')} {get_financial.amount:,} {await ft_instance.find_text('irt')}"
                f"\n\n<b>{await ft_instance.find_text('payment_gateway_tail')}</b>"
                f"\n\n<b>{await ft_instance.find_text('manual_check_text')}</b>"
            )

            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def pay_by_cryptomus(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    action, financial_id = query.data.replace('pay_by_cryptomus__', '').split('__')
    order_id = uuid.uuid4().hex

    with SessionLocal() as session:
        with session.begin():
            get_financial = crud.get_financial_report_by_id(session, financial_id)
            amount = convert_irt_to_usd.convert_irt_to_usd(get_financial.amount)

            instance = cryptomusAPI.CreateInvoice(setting.cryptomus_api_key, setting.cryptomus_merchant_id)
            create_cryptomus_invoice = await instance.execute(
                amount=str(amount),
                order_id=order_id,
                lifetime=3600,
                currency='USD',
                url_callback=setting.cryptomus_url_callback
            )

            if not create_cryptomus_invoice:
                return await query.answer(await ft_instance.find_text('fail_to_create_payment_getway'), show_alert=True)

            invoice_link = create_cryptomus_invoice.get('result', {}).get('url')
            if not invoice_link:
                return await query.answer(await ft_instance.find_text('fail_to_create_payment_getway'), show_alert=True)

            crud.update_financial_report(
                session, get_financial.financial_id,
                payment_getway='cryptomus',
                authority=order_id,
                currency='USD',
                url_callback=setting.zarinpal_url_callback,
                additional_data=json.dumps({'amount_in_usd': amount})
            )

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('login_to_payment_gateway'), url=invoice_link)],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data="start_in_new_message")]
            ]

            text = (
                f"<b>{await ft_instance.find_text('payment_gateway_title')}</b>"
                f"\n{await ft_instance.find_text('cryptomus_payment_gateway_body')}"
                f"\n\n{await ft_instance.find_text('payment_gateway_label')} {await ft_instance.find_text('cryptomus_label')}"
                f"\n{await ft_instance.find_text('price')} {amount:,} {await ft_instance.find_text('usd')}"
                f"\n\n<b>{await ft_instance.find_text('payment_gateway_tail')}</b>"
            )

            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

@handle_error.handle_functions_error
@message_token.check_token
async def pay_by_wallet(update, context):
    query = update.callback_query
    action, financial_id = query.data.replace('pay_by_wallet__', '').split('__')
    ft_instance = FindText(update, context)

    with SessionLocal() as session:
        session.begin()
        financial = crud.get_financial_report_by_id(session, financial_id)
        dialogues = transaction.get(financial.owner.language, transaction.get('fa'))

        if financial.amount > financial.owner.wallet:
            return await query.answer(await ft_instance.find_text('not_enough_credit'), show_alert=True)

        if not financial or financial.payment_status in ['paid', 'refund']:
            return await query.answer(await ft_instance.find_text('invoice_already_paid'))

        try:
            crud.update_financial_report(
                session, financial.financial_id,
                payment_getway='wallet',
                authority=financial.financial_id,
                currency='IRT',
                url_callback=None
            )
            crud.less_from_wallet(session, financial)
            await WebAppUtilities.handle_successful_payment(session, financial, financial_id, 'WalletPayment')
            session.commit()

        except Exception as e:
            session.rollback()
            error_msg = WebAppUtilities.log_error(
                'Amount refunded to user wallet! Payment was not successful!', e, financial_id
            )
            message = dialogues.get('operation_failed_user').format(f"{financial.amount:,}")

            await report_to_admin('error', 'WalletPayment', error_msg, financial.owner)
            await report_to_user('warning', financial.chat_id, message)


    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data="start")]]
    return await query.edit_message_text(
        await ft_instance.find_text('invoice_paid_by_wallet_message'),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@handle_error.handle_functions_error
async def manual_check_zarinpal(update, context):
    query = update.callback_query
    financial_id = query.data.replace('manual_check_zarinpal_payment__', '')
    ft_instance = FindText(update, context)

    with SessionLocal() as session:
        session.begin()
        financial = crud.get_financial_report_by_id(session, financial_id)
        dialogues = transaction.get(financial.owner.language, transaction.get('fa'))

        try:
            response_json = WebAppUtilities.verify_payment_zarinpal(financial.authority, financial.amount)
            payment_code = response_json.get('data', {}).get('code', 101)

        except Exception as e:
            await WebAppUtilities.report_unhandled_error(e, 'Manual CHeck ZarinPal Payment', financial.authority, financial)
            return await query.answer(await ft_instance.find_text('error_in_zarinpal'), show_alert=True)

        if payment_code == 100 and financial.payment_status not in ['paid', 'refund']:

            ref_id = response_json.get('data').get('ref_id')
            message = dialogues.get('successful_pay', '').format(ref_id)
            await utilities_reFactore.report_to_user('success', financial.chat_id, message)

            try:
                await WebAppUtilities.handle_successful_payment(session, financial, financial.authority, 'ZarinPalWebApp')
                session.commit()
            except Exception as e:
                session.rollback()
                await WebAppUtilities.handle_failed_payment(session, financial, e, dialogues, financial.authority, 'ZarinPalWebApp')
                message = dialogues.get('operation_failed_user').format(f"{financial.amount:,}")
                return await query.answer(message, show_alert=True)

            else:
                message = dialogues.get('successful_pay').format(f"{ref_id}")
                return await query.answer(message, show_alert=True)

        else:
            error_code = response_json.get('data', {}).get('code', 404)
            error_code = response_json.get('errors', {}).get('code', 404) if error_code == 404 else error_code
            message = f"{dialogues.get(error_code, 'no error!')}"
            if error_code == 101:
                keyboard = [
                    [InlineKeyboardButton(await ft_instance.find_keyboard('login_to_payment_gateway'), url=f'https://payment.zarinpal.com/pg/StartPay/{financial_id}')],
                    [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data="start_in_new_message")]
                ]
                await query.edit_message_reply_markup(reply_markup=keyboard)
            return await query.answer(message, show_alert=True)