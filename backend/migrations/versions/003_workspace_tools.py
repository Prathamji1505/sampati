"""Add local recovery, invitations, scoped sources and reviewable incoming datasets."""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('recovery_codes',
        sa.Column('code_hash', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table('invitations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('target_user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('issuer_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked', sa.Boolean, nullable=False),
        sa.CheckConstraint("role IN ('editor', 'viewer')"))
    op.create_table('data_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('token_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('enabled', sa.Boolean, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_received_at', sa.DateTime(timezone=True), nullable=True))
    op.create_table('incoming_datasets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('source_id', sa.String(36), sa.ForeignKey('data_sources.id'), nullable=False),
        sa.Column('fingerprint', sa.String(64), nullable=False),
        sa.Column('filename', sa.String(200), nullable=False),
        sa.Column('rows', sa.JSON, nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewer_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('import_id', sa.String(36), sa.ForeignKey('import_batches.id'), nullable=True),
        sa.CheckConstraint("state IN ('pending', 'accepted', 'rejected')"))
    op.create_index('ix_incoming_workspace_state', 'incoming_datasets', ['workspace_id', 'state'])


def downgrade():
    op.drop_index('ix_incoming_workspace_state', table_name='incoming_datasets')
    for name in ('incoming_datasets', 'data_sources', 'invitations', 'recovery_codes'):
        op.drop_table(name)
