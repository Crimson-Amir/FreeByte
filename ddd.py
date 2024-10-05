from database_sqlalchemy import SessionLocal
import models_sqlalchemy as model

with SessionLocal() as session:
    all_user = session.query(model.UserDetail).all()
    for user in all_user:
        config = model.UserConfig(chat_id=user.chat_id)
        session.add(config)