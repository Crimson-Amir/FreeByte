import logging
import sys, os, json
import traceback

import utilities_reFactore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from virtual_number import onlinesim_api
from utilities_reFactore import FindText
from crud import crud, vn_crud
from database_sqlalchemy import SessionLocal

file_path = 'virtual_number/numbers_notification.json'

def modify_json(key_to_add=None, value_to_add=None, key_to_remove=None):
    if not os.path.exists(file_path):
        data = {}
    else:
        with open(file_path, "r") as f:
            data = json.load(f)

    if key_to_remove:
        data.pop(key_to_remove, None)
    elif key_to_add and value_to_add is not None:
        data[key_to_add] = value_to_add

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def read_json():
    if not os.path.exists(file_path):
        data = {}
    else:
        with open(file_path, "r") as f:
            data = json.load(f)
    return data

class VNotification:
    def __init__(self):
        self.queue = {}
        self.refresh_json()

    def refresh_json(self):
        self.queue = read_json()

    async def vn_timer(self, context):
        if self.queue:

            get_all_number = await onlinesim_api.onlinesim.get_state(message_to_code=1, msg_list=1)
            if not isinstance(get_all_number, list):
                get_all_number = [{'tzid': None}]

            ft_instance = FindText(None, None)
            modified_queue = self.queue.copy()

            for tzid, values in self.queue.items():
                try:
                    get_number = [number for number in get_all_number if number['tzid'] == int(tzid)]
                    with SessionLocal() as session:
                        with session.begin():
                            get_vn = vn_crud.get_virtual_number_by_tzid(session, int(tzid))

                            if not get_number:
                                if get_vn.status == 'hold':
                                    vn_crud.update_virtual_number_record(session, vn_id=get_vn.virtual_number_id, status='canceled')
                                    financial = crud.update_financial_report_status(
                                        session=session, financial_id=values.get('financial_id'),
                                        new_status='refund',
                                        operation='recive', authority=values.get('financial_id')
                                    )
                                    vn_crud.add_credit_to_wallet(session, financial)
                                    msg = await ft_instance.find_from_database(financial.chat_id, 'vn_refund_money_timer')
                                    msg = msg.format(get_vn.number, f"{financial.amount:,}")
                                    await context.bot.send_message(chat_id=financial.chat_id, text=msg)

                                modified_queue.pop(tzid)
                                continue

                            response = get_number[0]['response']

                            if response == 'TZ_NUM_WAIT':
                                continue

                            elif response == 'TZ_NUM_ANSWER':
                                answer_count = len(get_number[0]['msg'])

                                if answer_count > values.get('recived_code_count', 1):
                                    msg = await ft_instance.find_from_database(values.get('chat_id'), 'vn_recived_code_timer')
                                    msg = msg.format(f"<code>{get_vn.number}</code>", f"<code>{get_number[0]['msg'][-1]['msg']}</code>")
                                    await context.bot.send_message(chat_id=values.get('chat_id'), text=msg, parse_mode='html')

                                    if values.get('recived_code_count', 0) == 0:
                                        vn_crud.update_virtual_number_record(session, vn_id=get_vn.virtual_number_id, status='answer')
                                        crud.update_financial_report_status(
                                            session=session, financial_id=values.get('financial_id'),
                                            new_status='paid', authority=values.get('financial_id')
                                        )
                                    modified_queue[tzid]['recived_code_count'] = values.get('recived_code_count', 1) + 1

                except Exception as e:
                    logging.error(f'error in vn timer:\n{e}')
                    tb = traceback.format_exc()
                    msg = ('Error in Virtual Number Timer!'
                           f'\n\nTZID: {tzid}'
                           f'\n\nValue: {values}'
                           f'\n\nError Type: {type(e)}'
                           f'\nError Reason:\n{str(e)}'
                           f'\n\nTB: \n{tb}')
                    await utilities_reFactore.report_to_admin('error', 'vn_timer', msg)

            with open(file_path, "w") as f:
                json.dump(modified_queue, f, indent=4)

            self.queue = modified_queue

vn_notification_instance = VNotification()