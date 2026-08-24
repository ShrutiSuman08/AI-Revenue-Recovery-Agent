from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship

from .connection import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(
        String,
        primary_key=True
    )

    name = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        nullable=False
    )

    payments = relationship(
        "Payment",
        back_populates="customer"
    )


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(
        String,
        primary_key=True
    )

    customer_id = Column(
        String,
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    status = Column(
        String,
        nullable=False
    )

    failure_reason = Column(
        String,
        nullable=True
    )

    payment_method = Column(
        String,
        nullable=False
    )

    attempt_count = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        nullable=False
    )

    customer = relationship(
        "Customer",
        back_populates="payments"
    )


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    case_id = Column(
         Integer, 
         primary_key=True,  
         autoincrement=True
     )

    payment_id = Column(
        String,
        ForeignKey("payments.payment_id"),
        nullable=False
    )

    risk_level = Column(
        String,
        nullable=False
    )

    diagnosis = Column(
        String,
        nullable=True
    )

    recommended_action = Column(
        String,
        nullable=False
    )

    confidence = Column(
        Float,
        nullable=True
    )

    status = Column(
        String,
        nullable=False
    )

    payment = relationship(
        "Payment"
    )
    attempts = relationship(
        "RecoveryAttempt",
        back_populates="case"
    )


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    attempt_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    case_id = Column(
        Integer,
        ForeignKey("recovery_cases.case_id"),
        nullable=False
    )

    action = Column(
        String,
        nullable=False
    )

    result = Column(
        String,
        nullable=False
    )

    amount_recovered = Column(
        Float,
        default=0.0
    )

    timestamp = Column(
        DateTime,
        nullable=False
    )

    case = relationship(
    "RecoveryCase",
    back_populates="attempts"
)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    case_id = Column(
        Integer,
        ForeignKey("recovery_cases.case_id"),
        nullable=True
    )

    event = Column(
        String,
        nullable=False
    )

    reason = Column(
        Text,
        nullable=True
    )

    action = Column(
        String,
        nullable=True
    )

    result = Column(
        String,
        nullable=True
    )

    timestamp = Column(
        DateTime,
        nullable=False
    )
