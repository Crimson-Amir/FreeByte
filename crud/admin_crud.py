import models_sqlalchemy as model
from sqlalchemy import update, func, desc
from typing import List, Optional

def get_admins(session):
    return session.query(model.UserDetail).join(model.UserConfig).filter(model.UserConfig.user_level >= 10).all()

def get_all_users(session):
    return session.query(model.UserDetail).all()

def get_all_active_partner(session):
    return session.query(model.Partner).filter(model.Partner.active == True).all()


def get_all_products(session):
    return session.query(model.Product).all()


def get_all_purchase(session):
    return session.query(model.Purchase).all()


def get_product(session, product_id):
    return session.query(model.Product).filter(model.Product.product_id == product_id).first()

def get_user_by_id(session, user_id: int):
    return session.query(model.UserDetail).filter(model.UserDetail.user_id == user_id).first()

def add_product(session, active, product_name, main_server_id):
    user = model.Product(
        active=active,
        product_name=product_name,
        main_server_id=main_server_id
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    return user

def add_mainserver(session, active, server_ip, server_protocol, server_port, server_username, server_password):
    server = model.MainServer(
        active=active,
        server_ip=server_ip,
        server_protocol=server_protocol,
        server_port=server_port,
        server_username=server_username,
        server_password=server_password
    )
    session.add(server)
    session.flush()
    session.refresh(server)
    return server

def update_user_by_id(session, chat_id: int, **kwargs):
    stmt = (
        update(model.UserDetail)
        .where(model.UserDetail.chat_id == chat_id)
        .values(
            **kwargs
        )
    )
    session.execute(stmt)

def add_partner(session, active, chat_id, **kwargs):
    partner = model.Partner(
        active=active,
        chat_id=chat_id,
        **kwargs
    )
    session.add(partner)
    session.flush()
    session.refresh(partner)
    return partner


def update_product(session, product_id: int, **kwargs):
    stmt = (
        update(model.Product)
        .where(model.Product.product_id == product_id)
        .values(
            **kwargs
        )
    )
    session.execute(stmt)


def create_vote_campaign(session, question: str, options: List[str], created_by_chat_id: Optional[int] = None):
    campaign = model.AdminVoteCampaign(
        question=question,
        options=options,
        created_by_chat_id=created_by_chat_id,
        active=True,
    )
    session.add(campaign)
    session.flush()
    session.refresh(campaign)
    return campaign


def add_vote_poll_message(session, campaign_id: int, poll_id: str, chat_id: int):
    poll_message = model.AdminVotePollMessage(
        campaign_id=campaign_id,
        poll_id=poll_id,
        chat_id=chat_id,
    )
    session.add(poll_message)
    session.flush()
    session.refresh(poll_message)
    return poll_message


def get_vote_poll_message_by_poll_id(session, poll_id: str):
    return session.query(model.AdminVotePollMessage).filter(model.AdminVotePollMessage.poll_id == poll_id).first()


def upsert_vote_answer(
    session,
    campaign_id: int,
    poll_id: str,
    chat_id: int,
    telegram_user_id: Optional[int],
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    option_ids: List[int],
):
    existing = session.query(model.AdminVoteAnswer).filter(
        model.AdminVoteAnswer.campaign_id == campaign_id,
        model.AdminVoteAnswer.chat_id == chat_id,
    ).first()

    if existing:
        existing.poll_id = poll_id
        existing.telegram_user_id = telegram_user_id
        existing.username = username
        existing.first_name = first_name
        existing.last_name = last_name
        existing.option_ids = option_ids
        return existing

    answer = model.AdminVoteAnswer(
        campaign_id=campaign_id,
        poll_id=poll_id,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        option_ids=option_ids,
    )
    session.add(answer)
    session.flush()
    session.refresh(answer)
    return answer


def get_vote_campaign(session, campaign_id: int):
    return session.query(model.AdminVoteCampaign).filter(model.AdminVoteCampaign.campaign_id == campaign_id).first()


def get_last_vote_campaign(session):
    return session.query(model.AdminVoteCampaign).order_by(desc(model.AdminVoteCampaign.campaign_id)).first()


def get_vote_answers(session, campaign_id: int):
    return session.query(model.AdminVoteAnswer).filter(model.AdminVoteAnswer.campaign_id == campaign_id).all()