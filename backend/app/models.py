from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="staff")  # 'admin' or 'staff'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    accounts = relationship("Account", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ebay_username = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="accounts")
    csv_data = relationship("CSVData", back_populates="account")


class CSVData(Base):
    __tablename__ = "csv_data"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    data_type = Column(String, nullable=False, index=True)  # 'order' or 'listing'
    csv_row = Column(JSON, nullable=False)
    item_id = Column(String, index=True)  # order_number or item_number
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="csv_data")
    order_status = relationship("OrderStatus", back_populates="csv_data", uselist=False)


class OrderStatus(Base):
    __tablename__ = "order_status"

    id = Column(Integer, primary_key=True, index=True)
    csv_data_id = Column(Integer, ForeignKey("csv_data.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, shipped, completed
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    csv_data = relationship("CSVData", back_populates="order_status")
    updated_by_user = relationship("User")