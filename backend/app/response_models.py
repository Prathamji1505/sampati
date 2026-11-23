"""Organisation-scoped evidence and immutable civilian response-plan snapshots."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class ResponseSignal(Base):
    __tablename__ = 'response_signals'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'id'), UniqueConstraint('workspace_id', 'identity_key'),
        CheckConstraint("state IN ('unreviewed','verified','dismissed')"), CheckConstraint('version >= 1'),
        Index('ix_response_signal_workspace_received', 'workspace_id', 'received_at'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    identity_key: Mapped[str] = mapped_column(String(64), nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AircraftSupport(Base):
    __tablename__ = 'aircraft_support_reports'
    __table_args__ = (
        ForeignKeyConstraint(['workspace_id', 'aircraft_id'], ['aircraft.workspace_id', 'aircraft.aircraft_id']),
        CheckConstraint('version >= 1'),
    )
    workspace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    aircraft_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)


class ResponsePlan(Base):
    __tablename__ = 'response_plans'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'submission_key'),
        ForeignKeyConstraint(['workspace_id', 'signal_id'], ['response_signals.workspace_id', 'response_signals.id']),
        CheckConstraint("state IN ('draft','reviewed')"), CheckConstraint('version >= 1'),
        Index('ix_response_plan_workspace_created', 'workspace_id', 'created_at'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    signal_id: Mapped[str] = mapped_column(String(36), nullable=False)
    submission_key: Mapped[str] = mapped_column(String(36), nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResponseEvent(Base):
    __tablename__ = 'response_events'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'entity_kind', 'entity_id', 'version'),
        CheckConstraint("entity_kind IN ('signal','aircraft','plan','source')"),
        Index('ix_response_event_entity', 'workspace_id', 'entity_kind', 'entity_id'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey('workspaces.id'), nullable=False)
    entity_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    after: Mapped[dict] = mapped_column(JSON, nullable=False)
