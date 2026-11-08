"""Relief file intake, source policy and provenance-linked draft automation."""
from alembic import op
import sqlalchemy as sa

revision='008'
down_revision='007'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('data_sources',sa.Column('purpose',sa.String(20),nullable=False,server_default='aircraft'))
    op.add_column('data_sources',sa.Column('automation_mode',sa.String(20),nullable=False,server_default='review'))
    op.add_column('data_sources',sa.Column('policy_version',sa.Integer,nullable=False,server_default='1'))
    op.create_unique_constraint('uq_data_source_workspace_id','data_sources',['workspace_id','id'])
    for name,rule in [('purpose',"purpose IN ('aircraft','relief')"),('mode',"automation_mode IN ('review','new_drafts')"),('scope',"purpose = 'relief' OR automation_mode = 'review'"),('version','policy_version >= 1')]:
        op.create_check_constraint('ck_data_source_'+name,'data_sources',rule)
    op.create_table('automation_source_events',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace_id',sa.String(64),nullable=False),sa.Column('source_id',sa.String(36),nullable=False),
        sa.Column('version',sa.Integer,nullable=False),sa.Column('action',sa.String(24),nullable=False),
        sa.Column('actor_id',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL'),nullable=True),sa.Column('actor',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('reason',sa.String(500),nullable=False),sa.Column('before',sa.JSON,nullable=True),sa.Column('after',sa.JSON,nullable=False),
        sa.ForeignKeyConstraint(['workspace_id','source_id'],['data_sources.workspace_id','data_sources.id'],ondelete='CASCADE'),sa.UniqueConstraint('source_id','version'))
    op.create_table('automation_receipts',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace_id',sa.String(64),nullable=False),sa.Column('source_id',sa.String(36),nullable=False),
        sa.Column('fingerprint',sa.String(64),nullable=False),sa.Column('filename',sa.String(200),nullable=False),sa.Column('raw_text',sa.Text,nullable=False),
        sa.Column('report_reference',sa.String(64),nullable=True),sa.Column('observed_at',sa.DateTime(timezone=True),nullable=True),sa.Column('observed_at_raw',sa.String(64),nullable=True),
        sa.Column('rows',sa.JSON,nullable=False),sa.Column('errors',sa.JSON,nullable=False),sa.Column('state',sa.String(20),nullable=False),sa.Column('version',sa.Integer,nullable=False),
        sa.Column('source_policy_version',sa.Integer,nullable=False),sa.Column('source_policy_mode',sa.String(20),nullable=False),
        sa.Column('received_actor_id',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL'),nullable=True),sa.Column('received_actor',sa.String(120),nullable=False),
        sa.Column('received_at',sa.DateTime(timezone=True),nullable=False),sa.Column('reviewed_at',sa.DateTime(timezone=True),nullable=True),
        sa.Column('automatic',sa.Boolean,nullable=False),sa.Column('results',sa.JSON,nullable=False),
        sa.UniqueConstraint('workspace_id','id'),sa.UniqueConstraint('source_id','fingerprint'),
        sa.ForeignKeyConstraint(['workspace_id','source_id'],['data_sources.workspace_id','data_sources.id']),sa.CheckConstraint("state IN ('pending','blocked','applied','dismissed')"),sa.CheckConstraint('version >= 1'))
    op.create_index('ix_automation_workspace_received','automation_receipts',['workspace_id','received_at'])
    op.create_table('automation_receipt_events',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace_id',sa.String(64),nullable=False),sa.Column('receipt_id',sa.String(36),nullable=False),
        sa.Column('version',sa.Integer,nullable=False),sa.Column('action',sa.String(24),nullable=False),
        sa.Column('actor_id',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL'),nullable=True),sa.Column('actor',sa.String(120),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('reason',sa.String(500),nullable=False),sa.Column('after',sa.JSON,nullable=False),
        sa.ForeignKeyConstraint(['workspace_id','receipt_id'],['automation_receipts.workspace_id','automation_receipts.id'],ondelete='CASCADE'),sa.UniqueConstraint('receipt_id','version'))
    op.add_column('relief_requests',sa.Column('intake_id',sa.String(36),nullable=True))
    op.create_foreign_key('fk_relief_intake_workspace','relief_requests','automation_receipts',['workspace_id','intake_id'],['workspace_id','id'])


def downgrade():
    op.drop_constraint('fk_relief_intake_workspace','relief_requests',type_='foreignkey')
    op.drop_column('relief_requests','intake_id')
    op.drop_table('automation_receipt_events');op.drop_index('ix_automation_workspace_received',table_name='automation_receipts');op.drop_table('automation_receipts');op.drop_table('automation_source_events')
    for name in ('version','scope','mode','purpose'):op.drop_constraint('ck_data_source_'+name,'data_sources',type_='check')
    op.drop_constraint('uq_data_source_workspace_id','data_sources',type_='unique')
    for column in ('policy_version','automation_mode','purpose'):op.drop_column('data_sources',column)
