"""Source-backed shipment review, partial delivery, return and correction history."""
from alembic import op
import sqlalchemy as sa

revision='007'
down_revision='006'
branch_labels=None
depends_on=None


def upgrade():
    op.create_table('shipments',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace_id',sa.String(64),sa.ForeignKey('workspaces.id'),nullable=False),
        sa.Column('reference',sa.String(64),nullable=False),sa.Column('reference_key',sa.String(64),nullable=False),
        sa.Column('submission_key',sa.String(36),nullable=False),sa.Column('create_digest',sa.String(64),nullable=False),
        sa.Column('position_id',sa.String(36),nullable=False),sa.Column('issue_id',sa.String(36),nullable=False),sa.Column('request_id',sa.String(36),nullable=False),
        sa.Column('quantity',sa.Numeric(15,3),nullable=False),sa.Column('delivered',sa.Numeric(15,3),nullable=False),sa.Column('returned',sa.Numeric(15,3),nullable=False),
        sa.Column('receiving_organisation',sa.String(120),nullable=False),sa.Column('destination',sa.String(160),nullable=False),sa.Column('note',sa.Text,nullable=False),
        sa.Column('status',sa.String(24),nullable=False),sa.Column('approved_at',sa.DateTime(timezone=True),nullable=True),sa.Column('dispatched_at',sa.DateTime(timezone=True),nullable=True),
        sa.Column('version',sa.Integer,nullable=False),sa.Column('created_by',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL'),nullable=True),
        sa.Column('created_actor',sa.String(120),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('workspace_id','id'),sa.UniqueConstraint('workspace_id','reference_key'),sa.UniqueConstraint('workspace_id','submission_key'),
        sa.ForeignKeyConstraint(['workspace_id','position_id','issue_id'],['stock_records.workspace_id','stock_records.position_id','stock_records.id']),
        sa.ForeignKeyConstraint(['workspace_id','request_id'],['relief_requests.workspace_id','relief_requests.id']),
        sa.CheckConstraint("status IN ('draft','approved','in_transit','partially_delivered','delivered','closed','cancelled')"),
        sa.CheckConstraint('quantity > 0 AND quantity <= 1000000000 AND delivered >= 0 AND returned >= 0 AND delivered + returned <= quantity'),sa.CheckConstraint('version >= 1'))
    op.create_index('ix_shipment_workspace_updated','shipments',['workspace_id','updated_at'])
    op.create_table('shipment_events',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace_id',sa.String(64),nullable=False),sa.Column('shipment_id',sa.String(36),nullable=False),
        sa.Column('version',sa.Integer,nullable=False),sa.Column('kind',sa.String(24),nullable=False),
        sa.Column('reference',sa.String(64),nullable=True),sa.Column('reference_key',sa.String(64),nullable=True),sa.Column('submission_key',sa.String(36),nullable=True),sa.Column('digest',sa.String(64),nullable=True),
        sa.Column('quantity',sa.Numeric(15,3),nullable=True),sa.Column('parent_event_id',sa.String(36),nullable=True),sa.Column('parent_reference',sa.String(64),nullable=True),
        sa.Column('stock_position_id',sa.String(36),nullable=True),sa.Column('stock_record_id',sa.String(36),nullable=True),sa.Column('stock_reference',sa.String(64),nullable=True),
        sa.Column('source_name',sa.String(120),nullable=False),sa.Column('observed_at',sa.DateTime(timezone=True),nullable=False),sa.Column('observed_at_raw',sa.String(64),nullable=False),
        sa.Column('received_at',sa.DateTime(timezone=True),nullable=False),sa.Column('actor_id',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL'),nullable=True),
        sa.Column('actor',sa.String(120),nullable=False),sa.Column('reason',sa.String(500),nullable=False),sa.Column('after',sa.JSON,nullable=False),
        sa.UniqueConstraint('workspace_id','shipment_id','id'),sa.UniqueConstraint('shipment_id','version'),sa.UniqueConstraint('workspace_id','reference_key'),sa.UniqueConstraint('workspace_id','submission_key'),
        sa.ForeignKeyConstraint(['workspace_id','shipment_id'],['shipments.workspace_id','shipments.id'],ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id','shipment_id','parent_event_id'],['shipment_events.workspace_id','shipment_events.shipment_id','shipment_events.id']),
        sa.ForeignKeyConstraint(['workspace_id','stock_position_id','stock_record_id'],['stock_records.workspace_id','stock_records.position_id','stock_records.id']),
        sa.CheckConstraint("kind IN ('created','approved','dispatched','delivery','return','cancelled','delivery_correction')"),
        sa.CheckConstraint("(kind = 'delivery_correction') = (parent_event_id IS NOT NULL)"),sa.CheckConstraint("(kind = 'return') = (stock_record_id IS NOT NULL)"))


def downgrade():
    op.drop_table('shipment_events')
    op.drop_index('ix_shipment_workspace_updated',table_name='shipments')
    op.drop_table('shipments')
