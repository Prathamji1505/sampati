"""Add accounts, membership-verified sessions and named workspaces without moving demo records."""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('workspaces', sa.Column('name', sa.String(100), server_default='Demo workspace', nullable=False))
    op.add_column('workspaces', sa.Column('is_demo', sa.Boolean, server_default=sa.false(), nullable=False))
    op.execute("UPDATE workspaces SET is_demo = true WHERE id = 'local-demo'")
    op.create_table('users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(32), nullable=False, unique=True),
        sa.Column('display_name', sa.String(80), nullable=False),
        sa.Column('password_hash', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('memberships',
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('workspace_id', sa.String(64), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'editor', 'viewer')"))
    op.create_table('user_sessions',
        sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('workspace_id', sa.String(64), nullable=False),
        sa.Column('csrf_token', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id', 'workspace_id'], ['memberships.user_id', 'memberships.workspace_id'], ondelete='CASCADE'))
    op.create_table('login_throttles',
        sa.Column('key_hash', sa.String(64), primary_key=True),
        sa.Column('attempts', sa.Integer, nullable=False),
        sa.Column('window_started_at', sa.DateTime(timezone=True), nullable=False))
    op.add_column('import_batches', sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True))


def downgrade():
    op.drop_column('import_batches', 'actor_id')
    op.drop_table('login_throttles')
    op.drop_table('user_sessions')
    op.drop_table('memberships')
    op.drop_table('users')
    op.drop_column('workspaces', 'is_demo')
    op.drop_column('workspaces', 'name')
