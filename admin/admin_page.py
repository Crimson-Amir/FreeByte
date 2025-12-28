import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from crud import crud, admin_crud
from database_sqlalchemy import SessionLocal
from vpn_service import vpn_utilities
from admin import partner
from virtual_number import onlinesim_api
import asyncio


def _parse_send_vote_text(raw_text: str):
    text = raw_text.strip()
    if text.startswith('/send_vote'):
        text = text[len('/send_vote'):].strip()

    if not text:
        return None, None

    if '|' in text:
        question_part, options_part = text.split('|', 1)
        question = question_part.strip()
        options = [o.strip() for o in options_part.split(',') if o.strip()]
        return question or 'Vote', options

    options = [o.strip() for o in text.split(',') if o.strip()]
    return 'Vote', options


@admin_access
async def send_vote(update, context):
    user_detail = update.effective_chat
    question, options = _parse_send_vote_text(update.message.text if update.message else '')

    if not options or len(options) < 2:
        return await context.bot.send_message(
            chat_id=user_detail.id,
            text='- usage: /send_vote option1, option2, ...\n(or) /send_vote Question | option1, option2, ...'
        )

    if len(options) > 10:
        return await context.bot.send_message(chat_id=user_detail.id, text='- maximum 10 options allowed.')

    try:
        with SessionLocal() as session:
            with session.begin():
                campaign = admin_crud.create_vote_campaign(session, question=question, options=options, created_by_chat_id=user_detail.id)
                campaign_id = campaign.campaign_id

        await context.bot.send_message(chat_id=user_detail.id, text='+ vote campaign created. id: %s' % campaign_id)

        with SessionLocal() as session:
            all_user = admin_crud.get_all_users(session)

        users = set([81532053])
        sent = 0
        failed = 0

        for user in all_user:
            # if user.chat_id != 6450325872:
            #     continue
            if user.chat_id in users:
                continue

            try:
                users.add(user.chat_id)
                msg = await context.bot.send_poll(
                    chat_id=user.chat_id,
                    question=question,
                    options=options,
                    is_anonymous=False,
                    allows_multiple_answers=True,
                )

                with SessionLocal() as session:
                    with session.begin():
                        admin_crud.add_vote_poll_message(
                            session,
                            campaign_id=campaign_id,
                            poll_id=msg.poll.id,
                            chat_id=user.chat_id,
                        )

                sent += 1
                await asyncio.sleep(3)
            except Exception:
                failed += 1
                await asyncio.sleep(3)

        await context.bot.send_message(
            chat_id=user_detail.id,
            text=f'+ vote sent. campaign_id={campaign_id}\nSent: {sent}\nFailed: {failed}'
        )

    except Exception as e:
        await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to send vote.\n{str(e)}')


async def handle_vote_poll_answer(update, context):
    poll_answer = update.poll_answer
    if not poll_answer:
        return

    try:
        with SessionLocal() as session:
            with session.begin():
                poll_message = admin_crud.get_vote_poll_message_by_poll_id(session, poll_answer.poll_id)
                if not poll_message:
                    return

                user = poll_answer.user
                admin_crud.upsert_vote_answer(
                    session,
                    campaign_id=poll_message.campaign_id,
                    poll_id=poll_answer.poll_id,
                    chat_id=poll_message.chat_id,
                    telegram_user_id=user.id if user else None,
                    username=getattr(user, 'username', None) if user else None,
                    first_name=getattr(user, 'first_name', None) if user else None,
                    last_name=getattr(user, 'last_name', None) if user else None,
                    option_ids=list(poll_answer.option_ids or []),
                )
    except Exception:
        return


@admin_access
async def vote_results(update, context):
    user_detail = update.effective_chat

    try:
        requested = context.args[0] if context.args else None
        with SessionLocal() as session:
            if requested and requested.isdigit():
                campaign = admin_crud.get_vote_campaign(session, int(requested))
            else:
                campaign = admin_crud.get_last_vote_campaign(session)

            if not campaign:
                return await context.bot.send_message(chat_id=user_detail.id, text='- no vote campaign found.')

            answers = admin_crud.get_vote_answers(session, campaign.campaign_id)

        options = campaign.options or []
        counts = [0 for _ in options]

        lines = []
        for ans in answers:
            for opt_id in (ans.option_ids or []):
                if isinstance(opt_id, int) and 0 <= opt_id < len(counts):
                    counts[opt_id] += 1

            display = ans.username or ans.first_name or str(ans.chat_id)
            if ans.option_ids:
                selected = ', '.join(options[i] for i in ans.option_ids if isinstance(i, int) and 0 <= i < len(options))
            else:
                selected = '(no vote)'
            lines.append(f'- {display}: {selected}')

        summary = '\n'.join([f'- {options[i]}: {counts[i]}' for i in range(len(options))])
        details = '\n'.join(lines) if lines else '- (no votes yet)'

        text = (
            f'<b>Vote Results</b>\n'
            f'Campaign ID: <code>{campaign.campaign_id}</code>\n'
            f'Question: {campaign.question}\n\n'
            f'<b>Counts</b>\n{summary}\n\n'
            f'<b>People</b>\n{details}'
        )

        await context.bot.send_message(chat_id=user_detail.id, text=text, parse_mode='html')
    except Exception as e:
        await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to load results.\n{str(e)}')


@admin_access
async def admin_page(update, context):
    user_detail = update.effective_chat

    keyboard = [
        [InlineKeyboardButton('System', callback_data=f"admin_system__1"),
         InlineKeyboardButton('Virtual Number', callback_data=f"admin_virtual_number")],
        [InlineKeyboardButton('VPN Section', callback_data=f"admin_vpn"),
         InlineKeyboardButton('Manage Users', callback_data=f"admin_manage_users__1")]
    ]
    text = '<b>Select Section who you want manage:</b>'

    if update.callback_query:
        return await update.callback_query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

@vpn_utilities.handle_functions_error
@admin_access
async def virtual_number_admin(update, context):
    query = update.callback_query
    get_balance = await onlinesim_api.onlinesim.get_balance()

    text = (f'Currnet Balance: ${get_balance.get("balance")}'
            f'\nZBalance: ${get_balance.get("zbalance")}')

    keyboard = [[InlineKeyboardButton('Back', callback_data='admin_page')]]

    return await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@admin_access
async def add_credit_for_user(update, context):
    user_detail = update.effective_chat
    ft_instance = FindText(None, None)
    try:
        with SessionLocal() as session:
            with session.begin():

                amount, user_chat_id = context.args

                finacial_report = crud.create_financial_report(
                    session, 'recive',
                    chat_id=user_chat_id,
                    amount=int(amount),
                    action='increase_balance_by_admin',
                    service_id=None,
                    payment_status='not paid',
                    payment_getway='wallet',
                    currency='IRT',
                )

                crud.add_credit_to_wallet(session, finacial_report)
                text = await ft_instance.find_from_database(user_chat_id, 'amount_added_to_wallet_successfully')
                text = text.format(f"{int(amount):,}")

                await context.bot.send_message(chat_id=user_chat_id, text=text)
                await context.bot.send_message(chat_id=user_detail.id, text=f'+ successfully Add {int(amount):,} IRT to user wallet.')

    except Exception as e:
        await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to add credit to user wallet.\n{str(e)}')


@admin_access
async def add_partner(update, context):
    user_detail = update.effective_chat
    try:
        with SessionLocal() as session:
            with session.begin():
                chat_id, price_per_traffic, price_per_period = context.args

                admin_crud.add_partner(
                    session, True,
                    chat_id,
                    vpn_price_per_gigabyte_irt=price_per_traffic,
                    vpn_price_per_period_time_irt=price_per_period
                )
                partner.partners.refresh_partner()
                await context.bot.send_message(chat_id=user_detail.id, text=f'+ successfully Add Partner.')

    except Exception as e:
        await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to add Partner.\n{str(e)}')


@admin_access
async def say_to_users(update, context):
    user_detail = update.effective_chat
    message = update.message.reply_to_message.text

    with SessionLocal() as session:
        all_user = admin_crud.get_all_purchase(session)
        users = set()
        for user in all_user:
            if user.chat_id in users:
                continue
            try:
                users.add(user.chat_id)
                await context.bot.send_message(
                    chat_id=user.chat_id,
                    text=message,
                    parse_mode='html'
                )
                await asyncio.sleep(1)
            except Exception as e:
                await context.bot.send_message(
                    chat_id=user_detail.id,
                    text=f'- failed to send message.\n{str(e)}'
                )
                await asyncio.sleep(1)


@admin_access
async def say_to_everyone(update, context):
    user_detail = update.effective_chat
    message = update.message.reply_to_message.text

    with SessionLocal() as session:
        all_user = admin_crud.get_all_users(session)
        users:set = {81532053}
        for user in all_user:
            if user in users: continue
            try:
                users.add(user.chat_id)
                await context.bot.send_message(chat_id=user.chat_id, text=message, parse_mode='html')
                await asyncio.sleep(3)
            except Exception as e:
                await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to send message.\n{str(e)}')
                await asyncio.sleep(3)