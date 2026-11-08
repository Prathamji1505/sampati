"""Add independently versioned civilian relief requests and their audit trail."""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('relief_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('reference', sa.String(64), nullable=False),
        sa.Column('reference_key', sa.String(64), nullable=False),
        sa.Column('submission_key', sa.String(36), nullable=False),
        sa.Column('create_digest', sa.String(64), nullable=False),
        sa.Column('requesting_organisation', sa.String(120), nullable=False),
        sa.Column('locality', sa.String(160), nullable=False),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('item_name', sa.String(160), nullable=False),
        sa.Column('quantity', sa.Numeric(15, 3), nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('needed_by', sa.DateTime(timezone=True), nullable=False),
        sa.Column('needed_by_raw', sa.String(64), nullable=False),
        sa.Column('source_name', sa.String(120), nullable=False),
        sa.Column('note', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_actor', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'reference_key'),
        sa.UniqueConstraint('workspace_id', 'submission_key'),
        sa.UniqueConstraint('workspace_id', 'id'),
        sa.CheckConstraint("status IN ('draft', 'submitted', 'reviewed', 'cancelled')"),
        sa.CheckConstraint("category IN ('food', 'water', 'medicine', 'shelter', 'other')"),
        sa.CheckConstraint("unit IN ('items', 'boxes', 'kits', 'litres', 'kilograms', 'packs')"),
        sa.CheckConstraint('quantity > 0 AND quantity <= 1000000000'),
        sa.CheckConstraint('version >= 1'))
    op.create_index('ix_relief_workspace_updated', 'relief_requests', ['workspace_id', 'updated_at'])
    op.create_table('relief_request_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), nullable=False),
        sa.Column('request_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('before', sa.JSON, nullable=True),
        sa.Column('after', sa.JSON, nullable=False),
        sa.ForeignKeyConstraint(['workspace_id', 'request_id'], ['relief_requests.workspace_id', 'relief_requests.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('request_id', 'version'),
        sa.CheckConstraint("action IN ('created', 'edited', 'status_changed')"))


def downgrade():
    op.drop_table('relief_request_events')
    op.drop_index('ix_relief_workspace_updated', table_name='relief_requests')
    op.drop_table('relief_requests')
