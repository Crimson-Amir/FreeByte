import sys, os, pytz
from datetime import datetime
from sqlalchemy import update, delete, or_
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import models_sqlalchemy as model

def get_purchase(session, purchase_id):
    return session.query(model.Purchase).filter_by(purchase_id=purchase_id).first()

def get_purchase_with_chat_id(session, purchase_id, chat_id):
    return session.query(model.Purchase).filter(
        model.Purchase.purchase_id==purchase_id,
        model.Purchase.chat_id==chat_id
    ).first()

def get_all_inactive_purchase(session):
    return session.query(model.Purchase).filter(
        or_(
            model.Purchase.status == 'limited',
            model.Purchase.status == 'expired'
            )
    ).all()


def get_purchase_by_chat_id(session, chat_id):
    return session.query(model.Purchase).filter(
        model.Purchase.chat_id == chat_id,
        model.Purchase.subscription_url.isnot(None)
    ).all()

def get_first_purchase_by_chat_id(session, chat_id):
    return session.query(model.Purchase).filter(
        model.Purchase.chat_id==chat_id,
        model.Purchase.subscription_url.isnot(None)
    ).first()

def get_purchase_bu_username(session, username):
    return session.query(model.Purchase).filter_by(username=username).first()


def update_purchase(session, purchase_id:int, **kwargs):
    stmt = (
        update(model.Purchase)
        .where(model.Purchase.purchase_id == purchase_id)
        .values(
            active=True,
            **kwargs
        ).returning(model.Purchase)
    )
    result = session.execute(stmt)
    updated_purchase_id = result.scalar()
    return updated_purchase_id

def remove_purchase(session, purchase_id:int, chat_id):
    stmt = (
        delete(model.Purchase)
        .where(model.Purchase.purchase_id == purchase_id, model.Purchase.chat_id == chat_id)
        .returning(model.Purchase)
    )
    result = session.execute(stmt)
    purchase = result.scalar()
    return purchase

def get_all_main_servers(session):
    with session.begin():
        return session.query(model.MainServer).where(model.MainServer.active==True).all()

def get_all_product(session):
    return session.query(model.Product).where(model.Product.active==True).all()

def get_users_last_usage(session):
    return session.query(model.LastUsage).order_by(model.LastUsage.last_usage_id.desc()).first()


def create_new_last_usage(session, last_usage_dict):
    last_usage = model.LastUsage(
        last_usage=last_usage_dict,
        register_date=datetime.now(pytz.timezone('Asia/Tehran')),
    )
    session.add(last_usage)

def create_new_statistics(session, statistics_usage_traffic):
    statistics = model.Statistics(
        traffic_usage=statistics_usage_traffic,
        register_date=datetime.now(pytz.timezone('Asia/Tehran')),
    )
    session.add(statistics)

def get_specific_time_statistics(session, date):
    return session.query(model.Statistics).filter(model.Statistics.register_date > date).all()
