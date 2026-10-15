"""Initial schema: customers, orders, communication_logs, customer_notes

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("woocommerce_customer_id", sa.BigInteger(), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("billing_address", sa.JSON(), nullable=True),
        sa.Column("shipping_address", sa.JSON(), nullable=True),
        sa.Column("total_spend", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("lifetime_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "customer_status",
            sa.Enum("Lead", "Active", "VIP", "Churned", name="customerstatus"),
            nullable=False,
            server_default="Lead",
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("woocommerce_customer_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_status", "customers", ["customer_status"])
    op.create_index("ix_customers_total_spend", "customers", ["total_spend"])

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("woocommerce_order_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("order_total", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("line_items", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("woocommerce_order_id"),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_status", "orders", ["status"])

    op.create_table(
        "communication_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("message_type", sa.String(100), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("SENT", "FAILED", name="communicationstatus"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_communication_logs_customer_id", "communication_logs", ["customer_id"]
    )

    op.create_table(
        "customer_notes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=False, server_default="admin"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_customer_notes_customer_id", "customer_notes", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_customer_notes_customer_id", table_name="customer_notes")
    op.drop_table("customer_notes")
    op.drop_index("ix_communication_logs_customer_id", table_name="communication_logs")
    op.drop_table("communication_logs")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_customers_total_spend", table_name="customers")
    op.drop_index("ix_customers_status", table_name="customers")
    op.drop_index("ix_customers_email", table_name="customers")
    op.drop_table("customers")
    op.execute("DROP TYPE IF EXISTS customerstatus")
    op.execute("DROP TYPE IF EXISTS communicationstatus")
