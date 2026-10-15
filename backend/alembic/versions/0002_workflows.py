"""Second CRM migration: interactions, followups, sync_state + order status columns.

Revision ID: 0002_workflows
Revises: 0001_initial
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_workflows"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent: the first attempt partially applied (MySQL DDL is
    # non-transactional), so only add/create what is actually missing.
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    order_cols = set()
    if "orders" in existing_tables:
        order_cols = {c["name"] for c in inspector.get_columns("orders")}
    if "payment_status" not in order_cols:
        op.add_column(
            "orders",
            sa.Column("payment_status", sa.String(50), nullable=False, server_default="pending"),
        )
    if "fulfillment_status" not in order_cols:
        op.add_column(
            "orders",
            sa.Column(
                "fulfillment_status", sa.String(50), nullable=False,
                server_default="unfulfilled",
            ),
        )

    if "interactions" not in existing_tables:
        op.create_table(
            "interactions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("customer_id", sa.BigInteger(), nullable=False),
            sa.Column("interaction_type", sa.String(50), nullable=False, server_default="note"),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("outcome", sa.String(100), nullable=True),
            sa.Column("created_by", sa.String(100), nullable=False, server_default="admin"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_interactions_customer_id", "interactions", ["customer_id"])

    if "followups" not in set(sa.inspect(op.get_bind()).get_table_names()):
        op.create_table(
            "followups",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("customer_id", sa.BigInteger(), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("due_date", sa.DateTime(), nullable=False),
            sa.Column(
                "status",
                sa.Enum("pending", "completed", "cancelled", name="followupstatus"),
                nullable=False,
                server_default="pending",
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by", sa.String(100), nullable=False, server_default="admin"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_followups_customer_id", "followups", ["customer_id"])
        op.create_index("ix_followups_due_date", "followups", ["due_date"])

    if "sync_state" not in set(sa.inspect(op.get_bind()).get_table_names()):
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


def downgrade() -> None:
    op.drop_table("sync_state")
    op.drop_index("ix_followups_due_date", table_name="followups")
    op.drop_index("ix_followups_customer_id", table_name="followups")
    op.drop_table("followups")
    op.execute("DROP TYPE IF EXISTS followupstatus")
    op.drop_index("ix_interactions_customer_id", table_name="interactions")
    op.drop_table("interactions")
    op.drop_column("orders", "fulfillment_status")
    op.drop_column("orders", "payment_status")
