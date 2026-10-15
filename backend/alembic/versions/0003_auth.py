"""Auth + ownership: users, sessions, password_resets, activity_logs,
order_status_history, owner_id columns, customer/interaction enrichment.

Revision ID: 0003_auth
Revises: 0002_workflows
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_auth"
down_revision = "0002_workflows"
branch_labels = None
depends_on = None


def _tables() -> set:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set:
    if table not in _tables():
        return set()
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _add_owner(table: str) -> None:
    if "owner_id" not in _columns(table):
        op.add_column(table, sa.Column("owner_id", sa.BigInteger(), nullable=True))
        op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])
        op.create_foreign_key(
            f"fk_{table}_owner_id", table, "users", ["owner_id"], ["id"], ondelete="CASCADE"
        )


def upgrade() -> None:
    if "users" not in _tables():
        op.create_table(
            "users",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("full_name", sa.String(255), nullable=False),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_users_email", "users", ["email"])

    if "sessions" not in _tables():
        op.create_table(
            "sessions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("last_activity_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("ip_address", sa.String(64), nullable=True),
            sa.Column("user_agent", sa.String(500), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"])
        op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
        op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])

    if "password_resets" not in _tables():
        op.create_table(
            "password_resets",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index("ix_password_resets_user_id", "password_resets", ["user_id"])
        op.create_index("ix_password_resets_token_hash", "password_resets", ["token_hash"])

    if "activity_logs" not in _tables():
        op.create_table(
            "activity_logs",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=True),
            sa.Column("action", sa.String(100), nullable=False),
            sa.Column("entity_type", sa.String(50), nullable=True),
            sa.Column("entity_id", sa.BigInteger(), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(64), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
        op.create_index("ix_activity_logs_action", "activity_logs", ["action"])
        op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])
        op.create_index(
            "ix_activity_user_action", "activity_logs", ["user_id", "action"]
        )

    if "order_status_history" not in _tables():
        op.create_table(
            "order_status_history",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("order_id", sa.BigInteger(), nullable=False),
            sa.Column("old_status", sa.String(50), nullable=True),
            sa.Column("new_status", sa.String(50), nullable=False),
            sa.Column("changed_by_user_id", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["changed_by_user_id"], ["users.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_order_status_history_order_id", "order_status_history", ["order_id"]
        )

    for table in (
        "customers",
        "orders",
        "interactions",
        "followups",
        "customer_notes",
        "communication_logs",
    ):
        if table in _tables():
            _add_owner(table)

    customer_cols = _columns("customers")
    if "customers" in _tables() and "company" not in customer_cols:
        op.add_column("customers", sa.Column("company", sa.String(255), nullable=True))
    if "customers" in _tables() and "profile_notes" not in _columns("customers"):
        op.add_column("customers", sa.Column("profile_notes", sa.Text(), nullable=True))

    interaction_cols = _columns("interactions")
    if "interactions" in _tables():
        if "subject" not in interaction_cols:
            op.add_column("interactions", sa.Column("subject", sa.String(255), nullable=True))
        if "status" not in interaction_cols:
            op.add_column(
                "interactions",
                sa.Column("status", sa.String(50), nullable=False, server_default="logged"),
            )
        if "scheduled_at" not in interaction_cols:
            op.add_column("interactions", sa.Column("scheduled_at", sa.DateTime(), nullable=True))
        if "completed_at" not in interaction_cols:
            op.add_column("interactions", sa.Column("completed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    for table in (
        "communication_logs",
        "customer_notes",
        "followups",
        "interactions",
        "orders",
        "customers",
    ):
        try:
            op.drop_constraint(f"fk_{table}_owner_id", table, type_="foreignkey")
        except Exception:
            pass
        try:
            op.drop_index(f"ix_{table}_owner_id", table_name=table)
        except Exception:
            pass
        for col in ("owner_id",):
            try:
                op.drop_column(table, col)
            except Exception:
                pass
    try:
        op.drop_table("order_status_history")
    except Exception:
        pass
    try:
        op.drop_table("activity_logs")
    except Exception:
        pass
    try:
        op.drop_table("password_resets")
    except Exception:
        pass
    try:
        op.drop_table("sessions")
    except Exception:
        pass
    try:
        op.drop_table("users")
    except Exception:
        pass
