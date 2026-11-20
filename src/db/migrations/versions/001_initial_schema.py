"""Initial schema: instructors, events, event_dates, allocations, availabilities

Revision ID: 001
Revises:
Create Date: 2026-11-19 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. instructors (no FK dependencies)
    op.create_table(
        "instructors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("lead", "primary", "secondary", name="roleenum"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # 2. events (no FK dependencies)
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("min_primary_instructors", sa.Integer(), nullable=False),
        sa.Column("min_secondary_instructors", sa.Integer(), nullable=False),
        sa.Column("max_students", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column(
            "catalog_status",
            sa.Enum("active", "archived", name="catalogstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. event_dates (depends on events, instructors)
    op.create_table(
        "event_dates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("lead_instructor_id", sa.Integer(), nullable=True),
        sa.Column("registered_students", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["lead_instructor_id"], ["instructors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. allocations (depends on event_dates, instructors)
    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_date_id", sa.Integer(), nullable=False),
        sa.Column("instructor_id", sa.Integer(), nullable=False),
        sa.Column(
            "shift_duration",
            sa.Enum("HALF_DAY", "FULL_DAY", name="shiftduration"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("lead", "primary", "secondary", name="roleenum"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["event_date_id"], ["event_dates.id"]),
        sa.ForeignKeyConstraint(["instructor_id"], ["instructors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_date_id",
            "instructor_id",
            name="uq_allocation_event_date_instructor",
        ),
    )

    # 5. availabilities (depends on instructors)
    op.create_table(
        "availabilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instructor_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["instructor_id"], ["instructors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("availabilities")
    op.drop_table("allocations")
    op.drop_table("event_dates")
    op.drop_table("events")
    op.drop_table("instructors")
    # Drop custom enum types
    op.execute("DROP TYPE IF EXISTS shiftduration")
    op.execute("DROP TYPE IF EXISTS catalogstatus")
    op.execute("DROP TYPE IF EXISTS roleenum")
