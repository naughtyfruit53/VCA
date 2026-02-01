"""Add users table for authentication

Revision ID: 51176981435e
Revises: 
Create Date: 2026-02-01 02:23:50.178322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '51176981435e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create UserRole enum type
    user_role_enum = postgresql.ENUM('owner', 'admin', 'member', name='userrole', create_type=True)
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('supabase_user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', user_role_enum, nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create indexes
    op.create_index('idx_user_supabase_user_id', 'users', ['supabase_user_id'])
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_tenant_id', 'users', ['tenant_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_tenant_id', 'users')
    op.drop_index('idx_user_email', 'users')
    op.drop_index('idx_user_supabase_user_id', 'users')
    
    # Drop users table
    op.drop_table('users')
    
    # Drop UserRole enum type
    user_role_enum = postgresql.ENUM('owner', 'admin', 'member', name='userrole')
    user_role_enum.drop(op.get_bind(), checkfirst=True)
