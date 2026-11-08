"""Immutable flood assessments, human review and optional relief-request linkage."""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('incidents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id'), nullable=False),
        sa.Column('reference_key', sa.String(64), nullable=False),
        sa.Column('digest', sa.String(64), nullable=False),
        sa.Column('assessment', sa.JSON, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_actor', sa.String(120), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('workspace_id', 'id'),
        sa.UniqueConstraint('workspace_id', 'reference_key'),
        sa.CheckConstraint("status IN ('pending', 'reviewed', 'dismissed')"),
        sa.CheckConstraint('version >= 1'))
    op.create_index('ix_incident_workspace_received', 'incidents', ['workspace_id', 'received_at'])
    op.create_table('incident_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workspace_id', sa.String(64), nullable=False),
        sa.Column('incident_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('before_status', sa.String(20), nullable=True),
        sa.Column('after_status', sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id', 'incident_id'], ['incidents.workspace_id', 'incidents.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('incident_id', 'version'))
    op.add_column('relief_requests', sa.Column('incident_id', sa.String(36), nullable=True))
    op.add_column('relief_requests', sa.Column('incident_reference', sa.String(64), nullable=True))
    op.create_foreign_key('fk_relief_incident_workspace', 'relief_requests', 'incidents', ['workspace_id', 'incident_id'], ['workspace_id', 'id'])


def downgrade():
    op.drop_constraint('fk_relief_incident_workspace', 'relief_requests', type_='foreignkey')
    op.drop_column('relief_requests', 'incident_reference')
    op.drop_column('relief_requests', 'incident_id')
    op.drop_table('incident_events')
    op.drop_index('ix_incident_workspace_received', table_name='incidents')
    op.drop_table('incidents')
