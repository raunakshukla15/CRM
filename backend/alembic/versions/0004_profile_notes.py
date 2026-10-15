"""Rename customers.notes -> profile_notes (0003 used a colliding name).

Revision ID: 0004_profile_notes
Revises: 0003_auth
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_profile_notes"
down_revision = "0003_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("customers")}
    if "notes" in cols and "profile_notes" not in cols:
        # Raw SQL: portable column rename for a TEXT column on MySQL.
        op.execute("ALTER TABLE customers CHANGE `notes` `profile_notes` TEXT NULL")
    elif "profile_notes" not in cols:
        op.add_column("customers", sa.Column("profile_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("customers")}
    if "profile_notes" in cols and "notes" not in cols:
        op.execute("ALTER TABLE customers CHANGE `profile_notes` `notes` TEXT NULL")
