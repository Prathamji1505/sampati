"""Civilian supply catalog, storage, balances and append-only stock ledger."""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    for table, name_length, extra in [
        ('inventory_items',160,[sa.Column('category',sa.String(20),nullable=False),sa.Column('unit',sa.String(20),nullable=False)]),
        ('storage_locations',120,[sa.Column('locality',sa.String(160),nullable=False)]),
    ]:
        op.create_table(table,
            sa.Column('id',sa.String(36),primary_key=True),
            sa.Column('workspace_id',sa.String(64),sa.ForeignKey('workspaces.id'),nullable=False),
            sa.Column('code',sa.String(64),nullable=False),sa.Column('code_key',sa.String(64),nullable=False),
            sa.Column('name',sa.String(name_length),nullable=False),*extra,
            sa.Column('created_actor',sa.String(120),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
            sa.UniqueConstraint('workspace_id','id'),sa.UniqueConstraint('workspace_id','code_key'))
    op.create_check_constraint('ck_inventory_category','inventory_items',"category IN ('food','water','medicine','shelter','other')")
    op.create_check_constraint('ck_inventory_unit','inventory_items',"unit IN ('items','boxes','kits','litres','kilograms','packs')")
    op.create_table('stock_positions',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace_id',sa.String(64),sa.ForeignKey('workspaces.id'),nullable=False),
        sa.Column('item_id',sa.String(36),nullable=False),sa.Column('location_id',sa.String(36),nullable=False),
        sa.Column('on_hand',sa.Numeric(15,3),nullable=False),sa.Column('reserved',sa.Numeric(15,3),nullable=False),
        sa.Column('version',sa.Integer,nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('workspace_id','id'),sa.UniqueConstraint('workspace_id','item_id','location_id'),
        sa.ForeignKeyConstraint(['workspace_id','item_id'],['inventory_items.workspace_id','inventory_items.id']),
        sa.ForeignKeyConstraint(['workspace_id','location_id'],['storage_locations.workspace_id','storage_locations.id']),
        sa.CheckConstraint('on_hand >= 0 AND on_hand <= 1000000000 AND reserved >= 0 AND reserved <= on_hand'),sa.CheckConstraint('version >= 0'))
    op.create_index('ix_stock_workspace_updated','stock_positions',['workspace_id','updated_at'])
    op.create_table('stock_records',
        sa.Column('id',sa.String(36),primary_key=True),sa.Column('workspace_id',sa.String(64),nullable=False),
        sa.Column('position_id',sa.String(36),nullable=False),sa.Column('sequence',sa.Integer,nullable=False),
        sa.Column('reference',sa.String(64),nullable=False),sa.Column('reference_key',sa.String(64),nullable=False),
        sa.Column('submission_key',sa.String(36),nullable=False),sa.Column('digest',sa.String(64),nullable=False),
        sa.Column('kind',sa.String(20),nullable=False),sa.Column('quantity',sa.Numeric(15,3),nullable=False),
        sa.Column('parent_id',sa.String(36),nullable=True),sa.Column('request_id',sa.String(36),nullable=True),
        sa.Column('parent_reference',sa.String(64),nullable=True),
        sa.Column('request_reference',sa.String(64),nullable=True),sa.Column('source_name',sa.String(120),nullable=False),
        sa.Column('observed_at',sa.DateTime(timezone=True),nullable=False),sa.Column('observed_at_raw',sa.String(64),nullable=False),
        sa.Column('received_at',sa.DateTime(timezone=True),nullable=False),
        sa.Column('actor_id',sa.String(36),sa.ForeignKey('users.id',ondelete='SET NULL'),nullable=True),
        sa.Column('actor',sa.String(120),nullable=False),sa.Column('reason',sa.String(500),nullable=False),sa.Column('after',sa.JSON,nullable=False),
        sa.UniqueConstraint('workspace_id','position_id','id'),sa.UniqueConstraint('workspace_id','reference_key'),
        sa.UniqueConstraint('workspace_id','submission_key'),sa.UniqueConstraint('position_id','sequence'),
        sa.ForeignKeyConstraint(['workspace_id','position_id'],['stock_positions.workspace_id','stock_positions.id'],ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id','position_id','parent_id'],['stock_records.workspace_id','stock_records.position_id','stock_records.id']),
        sa.ForeignKeyConstraint(['workspace_id','request_id'],['relief_requests.workspace_id','relief_requests.id']),
        sa.CheckConstraint("kind IN ('receipt','reserve','release','issue','return','report','adjustment_in','adjustment_out')"),
        sa.CheckConstraint("quantity <= 1000000000 AND ((kind = 'report' AND quantity >= 0) OR quantity > 0)"),
        sa.CheckConstraint("(kind IN ('release','issue','return')) = (parent_id IS NOT NULL)"),
        sa.CheckConstraint("(kind IN ('reserve','release','issue','return')) = (request_id IS NOT NULL)"),sa.CheckConstraint('sequence >= 1'))


def downgrade():
    op.drop_table('stock_records')
    op.drop_index('ix_stock_workspace_updated',table_name='stock_positions')
    op.drop_table('stock_positions')
    op.drop_table('storage_locations')
    op.drop_table('inventory_items')
