"""Add type column to records

Revision ID: 62f053f169f9
Revises: 85dc32ea9532
Create Date: 2025-07-21 20:18:45.114036
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '62f053f169f9'
down_revision = '85dc32ea9532'
branch_labels = None
depends_on = None


def upgrade():
    # ✅ Create the ENUM type first
    type_enum = postgresql.ENUM('Red-Flag', 'Intervention', name='type_enum')
    type_enum.create(op.get_bind())

    # Now apply changes
    with op.batch_alter_table('records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.Enum('Red-Flag', 'Intervention', name='type_enum'), nullable=False))
        batch_op.alter_column('title',
               existing_type=postgresql.ENUM('Red-Flag', 'Intervention', name='title_enum'),
               type_=sa.String(length=100),
               existing_nullable=False)
        batch_op.drop_constraint(batch_op.f('fk_records_created_by_users'), type_='foreignkey')
        batch_op.drop_column('category')
        batch_op.drop_column('created_by')


def downgrade():
    # ✅ Drop the ENUM type safely after reversing
    with op.batch_alter_table('records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('category', sa.VARCHAR(length=100), autoincrement=False, nullable=False))
        batch_op.create_foreign_key(batch_op.f('fk_records_created_by_users'), 'users', ['created_by'], ['id'])
        batch_op.alter_column('title',
               existing_type=sa.String(length=100),
               type_=postgresql.ENUM('Red-Flag', 'Intervention', name='title_enum'),
               existing_nullable=False)
        batch_op.drop_column('type')

    # Drop the ENUM type after removing the column
    type_enum = postgresql.ENUM('Red-Flag', 'Intervention', name='type_enum')
    type_enum.drop(op.get_bind())
