"""SQLAlchemy ORM models for v1: User, Account, Transaction.

v2 adds AuditLog, JitAccessGrant. v3 adds IdempotencyKey, ScaChallenge, Consent, Notification.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    JSON,
    Date,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator, CHAR

from minibank.db.base import Base


class IsoDate(TypeDecorator):
    """Date column that also accepts ISO-8601 date strings ("YYYY-MM-DD")."""

    impl = Date
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise TypeError(f"IsoDate expects date or ISO string, got {type(value).__name__}")


class GUID(TypeDecorator):
    """Platform-independent GUID — uses CHAR(36) on SQLite, native UUID on Postgres."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return str(value) if dialect.name != "postgresql" else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class Role(str, enum.Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    ADMIN = "admin"
    SUPERVISOR = "supervisor"


class Currency(str, enum.Enum):
    PLN = "PLN"
    EUR = "EUR"
    USD = "USD"


class AccountStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class AltIdType(str, enum.Enum):
    PASSPORT = "passport"
    RESIDENCE_CARD = "residence_card"
    UKR_STATUS = "ukr_status"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_DUAL_APPROVAL = "requires_dual_approval"


class TransactionCategory(str, enum.Enum):
    SPOZYWCZE = "SPOZYWCZE"
    RESTAURACJE = "RESTAURACJE"
    TRANSPORT = "TRANSPORT"
    TELEKOM = "TELEKOM"
    RACHUNKI = "RACHUNKI"
    ROZRYWKA = "ROZRYWKA"
    PRZELEW_WLASNY = "PRZELEW_WLASNY"
    WPLYWY = "WPLYWY"
    INNE = "INNE"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role, name="role"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pesel: Mapped[str | None] = mapped_column(String(11), nullable=True)
    alt_id_type: Mapped[AltIdType | None] = mapped_column(SqlEnum(AltIdType, name="alt_id_type"), nullable=True)
    alt_id_value: Mapped[str | None] = mapped_column(String(32), nullable=True)
    citizenship: Mapped[str] = mapped_column(String(2), default="PL", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=_utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_step_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    accounts: Mapped[list[Account]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    holder_iban: Mapped[str] = mapped_column(String(40), nullable=False)
    balance: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(SqlEnum(Currency, name="currency"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default=AccountStatus.OPEN.value, nullable=False)
    overdraft_limit: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), default=Decimal("0"), nullable=False)
    opened_on: Mapped[date] = mapped_column(IsoDate, nullable=False)
    closed_on: Mapped[date | None] = mapped_column(IsoDate, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=_utcnow)

    owner: Mapped[User] = relationship(back_populates="accounts")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    source_account_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("accounts.id"), nullable=False, index=True)
    dest_account_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("accounts.id"), nullable=True)
    dest_iban: Mapped[str | None] = mapped_column(String(40), nullable=True)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(SqlEnum(Currency, name="currency"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(140), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=TransactionStatus.PENDING.value, nullable=False)
    initiated_by_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requires_dual_approval: Mapped[bool] = mapped_column(default=False, nullable=False, server_default="0")
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    recipient_name: Mapped[str] = mapped_column(String(140), nullable=False)
    category: Mapped[TransactionCategory] = mapped_column(
        SqlEnum(TransactionCategory, name="transaction_category"),
        default=TransactionCategory.INNE,
        server_default=TransactionCategory.INNE.value,
        nullable=False,
    )


class AuditLogEntry(Base):
    """One append-only audit-log row. Mutation is prevented by a DB trigger
    (set up in the Alembic migration in Task 2).
    """
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    row_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class JitAccessGrant(Base):
    """Break-glass JIT access grant by an agent to a customer's data.

    Lifecycle: created (granted_at set) → expires (expires_at < now) OR revoked
    (revoked_at set). Middleware `require_active_grant` checks both — except
    BUG-06 forgets the expires_at half.
    """
    __tablename__ = "jit_access_grants"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agent_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    customer_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    ticket_id: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IdempotencyKey(Base):
    """Stripe-style idempotency cache. TTL handled by cleanup job (not in v3)."""
    __tablename__ = "idempotency_keys"

    key: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class ScaChallenge(Base):
    """PSD2 dynamic-linking challenge.

    BUG-08 in services/sca_service.py:verify — does not check that
    request.amount == linked_amount and request.dest_iban == linked_dest_iban.
    """
    __tablename__ = "sca_challenges"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    linked_amount: Mapped[Decimal] = mapped_column(DECIMAL(18, 2), nullable=False)
    linked_dest_iban: Mapped[str] = mapped_column(String(40), nullable=False)
    pending_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Notification(Base):
    """In-app pull-based notification queue. Mock SMS gateway dumps here + stdout."""
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsentScope(str, enum.Enum):
    READ = "read"
    READ_WRITE = "read_write"


class ConsentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Consent(Base):
    """Customer's consent for an agent's specific scope, with expiry."""
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    customer_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    agent_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    scope: Mapped[ConsentScope] = mapped_column(SqlEnum(ConsentScope, name="consent_scope"), nullable=False)
    status: Mapped[ConsentStatus] = mapped_column(SqlEnum(ConsentStatus, name="consent_status"),
                                                  default=ConsentStatus.PENDING, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
