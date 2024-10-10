import models_sqlalchemy as model
from sqlalchemy import update, func, desc

def get_admins(session):
    return session.query(model.UserDetail).join(model.UserConfig).filter(model.UserConfig.user_level >= 10).all()

def get_all_users(session):
    return session.query(model.UserDetail).all()

def get_all_active_partner(session):
    return session.query(model.Partner).filter(model.Partner.active == True).all()


def get_all_products(session):
    return session.query(model.Product).all()


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