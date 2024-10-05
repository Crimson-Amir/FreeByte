import models_sqlalchemy as model
from sqlalchemy import update, func, desc

def get_admins(session):
    return session.query(model.UserDetail).join(model.UserConfig).filter(model.UserConfig.user_level >= 10).all()

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

