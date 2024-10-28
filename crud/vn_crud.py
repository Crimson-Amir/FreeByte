import logging
from database_sqlalchemy import SessionLocal
import models_sqlalchemy as model
from sqlalchemy import delete, update, and_
from sqlalchemy.orm import joinedload

def create_virtual_number_record(session, chat_id, service_name, country_code, tzid, number, status='hold'):
    virtual_number = model.VirtualNumber(
        status=status,
        tzid=tzid,
        service_name=service_name,
        country_code=country_code,
        chat_id=chat_id,
        number=number
    )

    session.add(virtual_number)
    session.flush()
    return virtual_number

def update_virtual_number_record(session, vn_id, **kwargs):
    stmt = (
        update(model.VirtualNumber)
        .where(model.VirtualNumber.virtual_number_id == vn_id)
        .values(
            **kwargs
        ).returning(model.VirtualNumber)
    )
    result = session.execute(stmt)
    vn_ = result.scalar()
    return vn_

def less_credit_from_wallet(session, financial_db):
    user_id: int = financial_db.owner.chat_id

    stmt = (
        update(model.UserDetail)
        .where(model.UserDetail.chat_id == user_id)
        .values(
            wallet=model.UserDetail.wallet - financial_db.amount
        )
    )
    session.execute(stmt)


def add_credit_to_wallet(session, financial_db):
    user_id: int = financial_db.owner.chat_id

    stmt = (
        update(model.UserDetail)
        .where(model.UserDetail.chat_id == user_id)
        .values(
            wallet=model.UserDetail.wallet + financial_db.amount
        )
    )
    session.execute(stmt)


def delete_virtual_number_record(session, vn_id, chat_id):
    stmt = (
        delete(model.VirtualNumber).where(
            model.VirtualNumber.virtual_number_id==vn_id,
            model.VirtualNumber.chat_id==chat_id,
            ).returning(model.VirtualNumber)
    )
    result = session.execute(stmt)
    vn_ = result.scalar()
    return vn_


def get_virtual_number_by_tzid(session, tzid):
    vn_ = session.query(model.VirtualNumber).where(
        model.VirtualNumber.tzid == tzid,
        ).first()
    return vn_


def get_financial_by_vn_id(session, vn_id):
    financial = session.query(model.FinancialReport).where(
        and_(
            model.FinancialReport.id_holder == vn_id,
            model.FinancialReport.action == 'buy_vn_number_for_sms'
            )
    ).first()
    return financial