"""Create the local workspace, aircraft register, imports and change history."""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('workspaces', sa.Column('id', sa.String(64), primary_key=True), sa.Column('revision', sa.Integer, nullable=False))
    op.create_table('import_batches',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('fingerprint', sa.String(64), nullable=False),
        sa.Column('filename', sa.String(200), nullable=False),
        sa.Column('actor', sa.String(120), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('row_count', sa.Integer, nullable=False),
        sa.Column('new_count', sa.Integer, nullable=False),
        sa.Column('updated_count', sa.Integer, nullable=False),
        sa.Column('unchanged_count', sa.Integer, nullable=False),
        sa.Column('revision', sa.Integer, nullable=False),
        sa.UniqueConstraint('workspace_id', 'fingerprint'))
    op.create_table('aircraft',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('aircraft_id', sa.String(64), nullable=False),
        sa.Column('display_name', sa.String(120), nullable=False),
        sa.Column('reported_status', sa.String(20), nullable=False),
        sa.Column('source_updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_timestamp_raw', sa.String(64), nullable=False),
        sa.Column('source_name', sa.String(120), nullable=False),
        sa.Column('note', sa.Text, nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_import_id', sa.String(36), sa.ForeignKey('import_batches.id'), nullable=False),
        sa.UniqueConstraint('workspace_id', 'aircraft_id'),
        sa.CheckConstraint("reported_status IN ('available', 'unavailable', 'unknown')"))
    op.create_table('aircraft_changes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('import_id', sa.String(36), sa.ForeignKey('import_batches.id'), nullable=False),
        sa.Column('aircraft_id', sa.String(64), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('before', sa.JSON, nullable=True),
        sa.Column('after', sa.JSON, nullable=False))
    op.execute("INSERT INTO workspaces (id, revision) VALUES ('local-demo', 0)")


def downgrade():
    op.drop_table('aircraft_changes')
    op.drop_table('aircraft')
    op.drop_table('import_batches')
    op.drop_table('workspaces')
