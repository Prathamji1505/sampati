from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

WORKSPACE_ID = 'local-demo'


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = 'workspaces'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    name: Mapped[str] = mapped_column(String(100), default='Demo workspace', server_default='Demo workspace', nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false', nullable=False)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Membership(Base):
    __tablename__ = 'memberships'
    __table_args__ = (CheckConstraint("role IN ('owner', 'editor', 'viewer')"),)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id', ondelete='CASCADE'), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)


class UserSession(Base):
    __tablename__ = 'user_sessions'
    __table_args__ = (ForeignKeyConstraint(['user_id', 'workspace_id'], ['memberships.user_id', 'memberships.workspace_id'], ondelete='CASCADE'),)
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LoginThrottle(Base):
    __tablename__ = 'login_throttles'
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ImportBatch(Base):
    __tablename__ = 'import_batches'
    __table_args__ = (UniqueConstraint('workspace_id', 'fingerprint'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    actor: Mapped[str] = mapped_column(String(120), default='Local demo user', nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unchanged_count: Mapped[int] = mapped_column(Integer, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)


class Aircraft(Base):
    __tablename__ = 'aircraft'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'aircraft_id'),
        CheckConstraint("reported_status IN ('available', 'unavailable', 'unknown')"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    aircraft_id: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    reported_status: Mapped[str] = mapped_column(String(20), nullable=False)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_timestamp_raw: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_import_id: Mapped[str] = mapped_column(ForeignKey('import_batches.id'), nullable=False)


class AircraftChange(Base):
    __tablename__ = 'aircraft_changes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    import_id: Mapped[str] = mapped_column(ForeignKey('import_batches.id'), nullable=False)
    aircraft_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict] = mapped_column(JSON, nullable=False)


class RecoveryCode(Base):
    __tablename__ = 'recovery_codes'
    code_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Invitation(Base):
    __tablename__ = 'invitations'
    __table_args__ = (CheckConstraint("role IN ('editor', 'viewer')"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    target_user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    issuer_id: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class DataSource(Base):
    __tablename__ = 'data_sources'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey('users.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IncomingDataset(Base):
    __tablename__ = 'incoming_datasets'
    __table_args__ = (CheckConstraint("state IN ('pending', 'accepted', 'rejected')"), Index('ix_incoming_workspace_state', 'workspace_id', 'state'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey('data_sources.id'), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    rows: Mapped[list] = mapped_column(JSON, nullable=False)
    state: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    import_id: Mapped[str | None] = mapped_column(ForeignKey('import_batches.id'), nullable=True)


class ReliefRequest(Base):
    __tablename__ = 'relief_requests'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'reference_key'),
        UniqueConstraint('workspace_id', 'submission_key'),
        UniqueConstraint('workspace_id', 'id'),
        ForeignKeyConstraint(['workspace_id', 'incident_id'], ['incidents.workspace_id', 'incidents.id']),
        CheckConstraint("status IN ('draft', 'submitted', 'reviewed', 'cancelled')"),
        CheckConstraint("category IN ('food', 'water', 'medicine', 'shelter', 'other')"),
        CheckConstraint("unit IN ('items', 'boxes', 'kits', 'litres', 'kilograms', 'packs')"),
        CheckConstraint('quantity > 0 AND quantity <= 1000000000'),
        CheckConstraint('version >= 1'),
        Index('ix_relief_workspace_updated', 'workspace_id', 'updated_at'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    reference: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_key: Mapped[str] = mapped_column(String(64), nullable=False)
    incident_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    incident_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submission_key: Mapped[str] = mapped_column(String(36), nullable=False)
    create_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    requesting_organisation: Mapped[str] = mapped_column(String(120), nullable=False)
    locality: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    item_name: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    needed_by: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    needed_by_raw: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default='')
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='draft')
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_actor: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReliefRequestEvent(Base):
    __tablename__ = 'relief_request_events'
    __table_args__ = (
        ForeignKeyConstraint(['workspace_id', 'request_id'], ['relief_requests.workspace_id', 'relief_requests.id'], ondelete='CASCADE'),
        UniqueConstraint('request_id', 'version'),
        CheckConstraint("action IN ('created', 'edited', 'status_changed')"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict] = mapped_column(JSON, nullable=False)


class Incident(Base):
    __tablename__ = 'incidents'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'id'),
        UniqueConstraint('workspace_id', 'reference_key'),
        CheckConstraint("status IN ('pending', 'reviewed', 'dismissed')"),
        CheckConstraint('version >= 1'),
        Index('ix_incident_workspace_received', 'workspace_id', 'received_at'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    reference_key: Mapped[str] = mapped_column(String(64), nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    assessment: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_actor: Mapped[str] = mapped_column(String(120), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IncidentEvent(Base):
    __tablename__ = 'incident_events'
    __table_args__ = (
        ForeignKeyConstraint(['workspace_id', 'incident_id'], ['incidents.workspace_id', 'incidents.id'], ondelete='CASCADE'),
        UniqueConstraint('incident_id', 'version'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    before_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    after_status: Mapped[str] = mapped_column(String(20), nullable=False)


class InventoryItem(Base):
    __tablename__ = 'inventory_items'
    __table_args__ = (UniqueConstraint('workspace_id', 'id'), UniqueConstraint('workspace_id', 'code_key'),
        CheckConstraint("category IN ('food','water','medicine','shelter','other')"),
        CheckConstraint("unit IN ('items','boxes','kits','litres','kilograms','packs')"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    code_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    created_actor: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StorageLocation(Base):
    __tablename__ = 'storage_locations'
    __table_args__ = (UniqueConstraint('workspace_id', 'id'), UniqueConstraint('workspace_id', 'code_key'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    code_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    locality: Mapped[str] = mapped_column(String(160), nullable=False)
    created_actor: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StockPosition(Base):
    __tablename__ = 'stock_positions'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'id'), UniqueConstraint('workspace_id', 'item_id', 'location_id'),
        ForeignKeyConstraint(['workspace_id','item_id'], ['inventory_items.workspace_id','inventory_items.id']),
        ForeignKeyConstraint(['workspace_id','location_id'], ['storage_locations.workspace_id','storage_locations.id']),
        CheckConstraint('on_hand >= 0 AND on_hand <= 1000000000 AND reserved >= 0 AND reserved <= on_hand'),
        CheckConstraint('version >= 0'), Index('ix_stock_workspace_updated','workspace_id','updated_at'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    item_id: Mapped[str] = mapped_column(String(36), nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), nullable=False)
    on_hand: Mapped[Decimal] = mapped_column(Numeric(15,3), nullable=False)
    reserved: Mapped[Decimal] = mapped_column(Numeric(15,3), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StockRecord(Base):
    __tablename__ = 'stock_records'
    __table_args__ = (
        UniqueConstraint('workspace_id','position_id','id'), UniqueConstraint('workspace_id','reference_key'),
        UniqueConstraint('workspace_id','submission_key'), UniqueConstraint('position_id','sequence'),
        ForeignKeyConstraint(['workspace_id','position_id'], ['stock_positions.workspace_id','stock_positions.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['workspace_id','position_id','parent_id'], ['stock_records.workspace_id','stock_records.position_id','stock_records.id']),
        ForeignKeyConstraint(['workspace_id','request_id'], ['relief_requests.workspace_id','relief_requests.id']),
        CheckConstraint("kind IN ('receipt','reserve','release','issue','return','report','adjustment_in','adjustment_out')"),
        CheckConstraint("quantity <= 1000000000 AND ((kind = 'report' AND quantity >= 0) OR quantity > 0)"),
        CheckConstraint("(kind IN ('release','issue','return')) = (parent_id IS NOT NULL)"),
        CheckConstraint("(kind IN ('reserve','release','issue','return')) = (request_id IS NOT NULL)"),
        CheckConstraint('sequence >= 1'))
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    position_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    reference: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_key: Mapped[str] = mapped_column(String(64), nullable=False)
    submission_key: Mapped[str] = mapped_column(String(36), nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15,3), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    observed_at_raw: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    after: Mapped[dict] = mapped_column(JSON, nullable=False)
