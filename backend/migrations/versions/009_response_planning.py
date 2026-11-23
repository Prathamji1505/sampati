"""Civilian warning intake, aircraft support evidence and reviewable workflows."""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'
branch_labels = depends_on = None


def upgrade():
    op.drop_constraint('ck_data_source_purpose', 'data_sources', type_='check')
    op.create_check_constraint('ck_data_source_purpose', 'data_sources', "purpose IN ('aircraft','relief','response')")
    op.create_table('response_signals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('identity_key', sa.String(64), nullable=False), sa.Column('digest', sa.String(64), nullable=False),
        sa.Column('payload', sa.JSON, nullable=False), sa.Column('state', sa.String(20), nullable=False),
        sa.Column('version', sa.Integer, nullable=False), sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'id'), sa.UniqueConstraint('workspace_id', 'identity_key'),
        sa.CheckConstraint("state IN ('unreviewed','verified','dismissed')"), sa.CheckConstraint('version >= 1'))
    op.create_index('ix_response_signal_workspace_received', 'response_signals', ['workspace_id', 'received_at'])
    op.create_table('aircraft_support_reports',
        sa.Column('workspace_id', sa.String(64), primary_key=True), sa.Column('aircraft_id', sa.String(64), primary_key=True),
        sa.Column('payload', sa.JSON, nullable=False), sa.Column('version', sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(['workspace_id', 'aircraft_id'], ['aircraft.workspace_id', 'aircraft.aircraft_id']),
        sa.CheckConstraint('version >= 1'))
    op.create_table('response_plans',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('signal_id', sa.String(36), nullable=False), sa.Column('submission_key', sa.String(36), nullable=False),
        sa.Column('input_digest', sa.String(64), nullable=False), sa.Column('inputs', sa.JSON, nullable=False),
        sa.Column('snapshot', sa.JSON, nullable=False), sa.Column('state', sa.String(20), nullable=False),
        sa.Column('version', sa.Integer, nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'submission_key'),
        sa.ForeignKeyConstraint(['workspace_id', 'signal_id'], ['response_signals.workspace_id', 'response_signals.id']),
        sa.CheckConstraint("state IN ('draft','reviewed')"), sa.CheckConstraint('version >= 1'))
    op.create_index('ix_response_plan_workspace_created', 'response_plans', ['workspace_id', 'created_at'])
    op.create_table('response_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('entity_kind', sa.String(20), nullable=False), sa.Column('entity_id', sa.String(64), nullable=False),
        sa.Column('version', sa.Integer, nullable=False), sa.Column('actor', sa.String(120), nullable=False),
        sa.Column('action', sa.String(32), nullable=False), sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('after', sa.JSON, nullable=False),
        sa.UniqueConstraint('workspace_id', 'entity_kind', 'entity_id', 'version'),
        sa.CheckConstraint("entity_kind IN ('signal','aircraft','plan','source')"))
    op.create_index('ix_response_event_entity', 'response_events', ['workspace_id', 'entity_kind', 'entity_id'])


def downgrade():
    # Deactivating a connector preserves its evidence rather than discarding it.
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM data_sources WHERE purpose = 'response'")):
        raise RuntimeError('Response sources exist. Keep migration 009 to preserve their scope and evidence.')
    op.drop_index('ix_response_event_entity', table_name='response_events')
    op.drop_table('response_events')
    op.drop_index('ix_response_plan_workspace_created', table_name='response_plans')
    op.drop_table('response_plans')
    op.drop_table('aircraft_support_reports')
    op.drop_index('ix_response_signal_workspace_received', table_name='response_signals')
    op.drop_table('response_signals')
    op.drop_constraint('ck_data_source_purpose', 'data_sources', type_='check')
    op.create_check_constraint('ck_data_source_purpose', 'data_sources', "purpose IN ('aircraft','relief')")
