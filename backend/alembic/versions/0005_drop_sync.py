"""Remove sync_state (WooCommerce integrations removed; only user data remains).

Revision ID: 0005_drop_sync
Revises: 0004_profile_notes
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_drop_sync"
down_revision = "0004_profile_notes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "sync_state" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("sync_state")


def downgrade() -> None:
    if "sync_state" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "sync_state",
            sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
            sa.Column("last_sync_at", sa.DateTime(), nullable=True),
            sa.Column("mode", sa.String(20), nullable=False, server_default="demo"),
            sa.Column("customers_synced", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("orders_synced", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("message", sa.String(500), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
