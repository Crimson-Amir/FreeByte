import traceback

import requests, json
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
import utilities_reFactore
from crud import crud, vn_crud
from WebApp import WebAppUtilities
from database_sqlalchemy import SessionLocal
from WebApp.WebAppDialogue import transaction
from virtual_number import vn_utilities, vn_notification

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get('/')
async def send_telegram_notification():
    return {'status': 'ok'}

@app.get('/zarinpal_receive_payment_result/')
async def receive_payment_result(Authority: str, Status: str, request: Request):
    """Handles the Zarinpal payment result webhook."""
    with SessionLocal() as session:
        session.begin()
        financial = crud.get_financial_report_by_authority(session, Authority)
        WebAppUtilities.connect_to_server_instance.refresh_token()

        if Status != 'OK' or not financial:
            dialogues = transaction.get('fa')
            return templates.TemplateResponse(
                request=request,
                name='fail_pay.html',
                context={'translation': dialogues, 'error_code': 400}
            )

        try:
            dialogues = transaction.get(financial.owner.language, transaction.get('fa'))
            response_json = WebAppUtilities.verify_payment_zarinpal(Authority, financial.amount)
            payment_code = response_json.get('data', {}).get('code', 101)

        except Exception as e:
            await WebAppUtilities.report_unhandled_error(e, 'ZarinPalWebApp', Authority, financial)
            return templates.TemplateResponse(
                request=request,
                name='fail_pay.html',
                context={'translation': dialogues, 'error_code': 405}
            )

        if payment_code == 100 and financial.payment_status not in ['paid', 'refund']:

            ref_id = response_json.get('data').get('ref_id')
            message = dialogues.get('successful_pay', '').format(ref_id)
            await utilities_reFactore.report_to_user('success', financial.chat_id, message)

            try:
                await WebAppUtilities.handle_successful_payment(session, financial, Authority, 'ZarinPalWebApp')
                session.commit()
            except Exception as e:
                session.rollback()
                await WebAppUtilities.handle_failed_payment(session, financial, e, dialogues, Authority, 'ZarinPalWebApp')
                return templates.TemplateResponse(
                    request=request,
                    name='error_and_refund_credit_to_wallet.html',
                    context={'translation': dialogues, 'amount': financial.amount}
                )
            else:
                return templates.TemplateResponse(
                    request=request,
                    name='success_pay.html',
                    context={'ref_id': ref_id}
                )

        else:
            error_code = response_json.get('data', {}).get('code', 404)
            error_code = response_json.get('errors', {}).get('code', 404) if error_code == 404 else error_code
            return templates.TemplateResponse(
                request=request,
                name='fail_pay.html',
                context={'translation': dialogues, 'error_code': error_code}
            )

@app.post('/cryptomus_receive_payment_result/')
async def crypto_receive_payment_result(data: WebAppUtilities.CryptomusPaymentWebhook):
    """Handles incoming webhook for Cryptomus payment result."""
    with SessionLocal() as session:
        session.begin()
        WebAppUtilities.connect_to_server_instance.refresh_token()
        financial = crud.get_financial_report_by_authority(session, data.order_id)

        if not financial or data.status not in ['paid', 'paid_over'] or financial.payment_status in ['paid', 'refund']:
            return

        dialogues = transaction.get(financial.owner.language, transaction.get('fa'))
        response = await WebAppUtilities.verify_cryptomus_payment(data.order_id, None, financial)

        if response:
            ref_id = response.get('result', {}).get('uuid')
            message = dialogues.get('successful_pay', '').format(ref_id)
            await utilities_reFactore.report_to_user('success', financial.chat_id, message)

            try:
                await WebAppUtilities.handle_successful_payment(session, financial, data.order_id, 'CryptomusWebApp')
                session.commit()
            except Exception as e:
                session.rollback()
                await WebAppUtilities.handle_failed_payment(session, financial, e, dialogues, data.order_id, 'CryptomusWebApp')

@app.post('/send_telegram_notification/')
async def send_telegram_notification(
        chat_id: int = Form(...),
        text: str = Form(...),
        message_thread_id: int = Form(...),
        bot_token: str = Form(...)
):
    telegram_bot_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(telegram_bot_url, data={'chat_id': chat_id, 'text': text, 'message_thread_id': message_thread_id}, timeout=5)


@app.get("/onlinesim")
async def onlinesim_receive_sms(request: Request):
    query_params = request.query_params
    data = {key: value for key, value in query_params.items()}
    tzid = data.get('operation_id')
    with SessionLocal() as session:
        session.begin()
        virtual_number = vn_crud.get_virtual_number_by_tzid(session, int(tzid))
        try:
            json_data = vn_notification.read_json()

            message = (
                f'{data.get("number")}:'
                f'\n\nMessage:\n{data.get("message")}'
                f'\n\nCode: <code>{data.get("code")}</code>'
                f'\n\nTime Left: {vn_utilities.seconds_to_minutes(int(data.get("time_left", 0)))} min'
            )
            await utilities_reFactore.report_to_user('success', virtual_number.chat_id, message)

            vn_json = json_data.get(tzid, {})
            print(vn_json)

            if vn_json:
                modified_queue = json_data.copy()
                financial_id = vn_json.get('financial_id')
                print('yes', str(financial_id))
                modified_queue[tzid]['recived_code_count'] = vn_json.get('recived_code_count', 1) + 1
                print(modified_queue)
                with open(vn_notification.file_path, "w") as f:
                    json.dump(modified_queue, f, indent=4)
                vn_notification.vn_notification_instance.refresh_json()

            else:
                financial = vn_crud.get_financial_by_vn_id(session, virtual_number.virtual_number_id)
                financial_id = financial.financial_id
                print('no', str(financial_id))

            if financial_id:
                vn_utilities.set_virtual_number_answer(
                    session, virtual_number.virtual_number_id, financial_id
                )
            else:
                vn_crud.update_virtual_number_record(session, vn_id=virtual_number.virtual_number_id, status='answer')

            await vn_utilities.report_recive_code(virtual_number)

            session.commit()
            return {"status": "success"}
        except Exception as e:
            session.rollback()
            tb = traceback.format_exc()
            msg = (
                f'tzid: {tzid}'
                f'\n\ndata: {data}'
                f'\n\nError Type: {type(e)}'
                f'\nError Reason: {str(e)}'
                f'\n\nTB:\n{tb}'
            )
            await utilities_reFactore.report_to_admin('error', 'onlinesim_receive_sms', msg, virtual_number.owner)