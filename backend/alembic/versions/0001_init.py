"""init

Revision ID: 0001
Revises: 
Create Date: 2026-09-30 17:38:57.777224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table('equipment',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('rooms',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('location', sa.Text(), nullable=True),
    sa.Column('capacity', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.CheckConstraint('capacity > 0', name='ck_rooms_capacity'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('full_name', sa.Text(), nullable=False),
    sa.Column('email', sa.Text(), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('role', sa.Enum('employee', 'admin', name='user_role'), server_default='employee', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('failed_attempts', sa.Integer(), server_default='0', nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(full_name) BETWEEN 1 AND 200', name='ck_users_full_name'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('users_email_uq', 'users', [sa.literal_column('lower(email)')], unique=True)
    op.create_table('bookings',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('room_id', sa.BigInteger(), nullable=False),
    sa.Column('organizer_id', sa.BigInteger(), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('attendees', sa.Integer(), nullable=False),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('active', 'cancelled', name='booking_status'), server_default='active', nullable=False),
    sa.Column('cancelled_by', sa.BigInteger(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    postgresql.ExcludeConstraint((sa.column('room_id'), '='), (sa.text("tstzrange(start_at, end_at, '[)')"), '&&'), where=sa.text("status = 'active'"), using='gist', name='bookings_no_overlap'),
    sa.CheckConstraint("end_at - start_at BETWEEN interval '15 minutes' AND interval '8 hours'", name='ck_bookings_duration'),
    sa.CheckConstraint('attendees >= 1', name='ck_bookings_attendees'),
    sa.CheckConstraint('extract(epoch FROM start_at)::bigint % 900 = 0 AND extract(epoch FROM end_at)::bigint % 900 = 0', name='ck_bookings_aligned'),
    sa.CheckConstraint('length(title) BETWEEN 1 AND 200', name='ck_bookings_title'),
    sa.CheckConstraint('start_at < end_at', name='ck_bookings_order'),
    sa.ForeignKeyConstraint(['cancelled_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('bookings_organizer_idx', 'bookings', ['organizer_id', sa.literal_column('start_at DESC')], unique=False)
    op.create_index('bookings_start_idx', 'bookings', ['start_at'], unique=False, postgresql_where=sa.text("status = 'active'"))
    op.create_table('refresh_tokens',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('room_equipment',
    sa.Column('room_id', sa.BigInteger(), nullable=False),
    sa.Column('equipment_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('room_id', 'equipment_id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('type', sa.Enum('reminder', 'changed', 'cancelled', name='notification_type'), nullable=False),
    sa.Column('booking_id', sa.BigInteger(), nullable=True),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('dedupe_key', sa.Text(), nullable=True),
    sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dedupe_key')
    )
    op.create_index('notifications_user_idx', 'notifications', ['user_id', sa.literal_column('created_at DESC')], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('notifications_user_idx', table_name='notifications')
    op.drop_table('notifications')
    op.drop_table('room_equipment')
    op.drop_table('refresh_tokens')
    op.drop_index('bookings_start_idx', table_name='bookings', postgresql_where=sa.text("status = 'active'"))
    op.drop_index('bookings_organizer_idx', table_name='bookings')
    op.drop_table('bookings')
    op.drop_index('users_email_uq', table_name='users')
    op.drop_table('users')
    op.drop_table('rooms')
    op.drop_table('equipment')
    for name in ("notification_type", "booking_status", "user_role"):
        op.execute(f"DROP TYPE {name}")
