from database_sqlalchemy import Base
from sqlalchemy import Integer, String, Column, Boolean, ForeignKey, DateTime, BigInteger, ARRAY, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class UserDetail(Base):
    __tablename__ = 'user_detail'

    user_id = Column(Integer, primary_key=True)
    active = Column(Boolean, default=True)
    email = Column(String, unique=True, default=None)
    phone_number = Column(String, unique=True, default=None)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    language = Column(String, default='fa')
    wallet = Column(Integer, default=0)
    invited_by = Column(BigInteger, ForeignKey('user_detail.chat_id'))
    register_date = Column(DateTime, default=datetime.now())
    financial_reports = relationship("FinancialReport", back_populates="owner", cascade="all, delete-orphan")
    services = relationship("Purchase", back_populates="owner", cascade="all, delete-orphan")
    virtual_numbers = relationship("VirtualNumber", back_populates="owner", cascade="all, delete-orphan")
    config = relationship("UserConfig", back_populates="owner", cascade="all, delete-orphan", uselist=False)
    partner = relationship("Partner", back_populates="owner", cascade="all, delete-orphan", uselist=False)


class UserConfig(Base):
    __tablename__ = 'user_config'
    config_id = Column(Integer, primary_key=True)
    user_level = Column(Integer, default=1)
    user_status = Column(String, default='active')
    traffic_notification_percent = Column(Integer, default=85)
    period_notification_day = Column(Integer, default=3)
    get_vpn_free_service = Column(Boolean, default=False)
    chat_id = Column(BigInteger, ForeignKey('user_detail.chat_id'), unique=True)
    first_purchase_refreal_for_inviter = Column(Boolean, default=False)
    webapp_password = Column(String)
    owner = relationship("UserDetail", back_populates="config")

class Partner(Base):
    __tablename__ = 'partner'
    partner_id = Column(Integer, primary_key=True)
    active = Column(Boolean, default=True)
    vpn_price_per_gigabyte_irt = Column(Integer, nullable=False)
    vpn_price_per_period_time_irt = Column(Integer, nullable=False)
    chat_id = Column(BigInteger, ForeignKey('user_detail.chat_id'), unique=True)
    owner = relationship("UserDetail", back_populates="partner")

class FinancialReport(Base):
    __tablename__ = 'financial_report'

    financial_id = Column(Integer, primary_key=True)
    operation = Column(String, default='spend')

    amount = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    id_holder = Column(Integer)

    payment_getway = Column(String)
    authority = Column(String)
    currency = Column(String)
    url_callback = Column(String)
    additional_data = Column(String)
    payment_status = Column(String)

    register_date = Column(DateTime, default=datetime.now())

    chat_id = Column(BigInteger, ForeignKey('user_detail.chat_id'))
    owner = relationship("UserDetail", back_populates="financial_reports")


class MainServer(Base):
    __tablename__ = 'main_server'
    server_id = Column(Integer, primary_key=True)
    active = Column(Boolean)
    server_ip = Column(String)
    server_protocol = Column(String)
    server_port = Column(Integer)
    server_username = Column(String)
    server_password = Column(String)
    products = relationship("Product", back_populates="main_server")

class Product(Base):
    __tablename__ = 'product'

    product_id = Column(Integer, primary_key=True)
    active = Column(Boolean)
    product_name = Column(String)
    register_date = Column(DateTime, default=datetime.now())
    purchase = relationship("Purchase", back_populates="product")

    main_server_id = Column(Integer, ForeignKey('main_server.server_id'))
    main_server = relationship("MainServer", back_populates="products")

class Purchase(Base):
    __tablename__ = 'purchase'

    purchase_id = Column(Integer, primary_key=True)
    username = Column(String)
    active = Column(Boolean)
    status = Column(String)
    traffic = Column(Integer)
    period = Column(Integer)
    day_notification_status = Column(Boolean, default=False)
    traffic_notification_status = Column(Boolean, default=False)
    service_uuid = Column(String)
    subscription_url = Column(String)

    upgrade_traffic = Column(Integer, default=0)
    upgrade_period = Column(Integer, default=0)

    product_id = Column(Integer, ForeignKey('product.product_id'))
    product = relationship("Product", back_populates="purchase")
    chat_id = Column(BigInteger, ForeignKey('user_detail.chat_id'))
    owner = relationship("UserDetail", back_populates="services")

    expired_at = Column(DateTime)
    register_date = Column(DateTime, default=datetime.now())


class VirtualNumber(Base):
    __tablename__ = 'virtual_number'

    virtual_number_id = Column(Integer, primary_key=True)

    status = Column(String)
    tzid = Column(Integer)
    service_name = Column(String)
    country_code = Column(Integer)
    number = Column(String)
    recived_code = Column(String)

    chat_id = Column(BigInteger, ForeignKey('user_detail.chat_id'))
    owner = relationship("UserDetail", back_populates="virtual_numbers")
    register_date = Column(DateTime, default=datetime.now())


class Statistics(Base):
    __tablename__ = 'statistics'

    statistics_id = Column(Integer, primary_key=True)
    traffic_usage = Column(String)
    register_date = Column(DateTime, default=datetime.now())


class LastUsage(Base):
    __tablename__ = 'last_usage'

    last_usage_id = Column(Integer, primary_key=True)
    last_usage = Column(JSON)
    register_date = Column(DateTime, default=datetime.now())
