"""align_video_moderation_fields

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-08 10:00:00.000000

"""
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility when renaming columns.
    with op.batch_alter_table("video_moderation_logs") as batch_op:
        batch_op.alter_column("duration_seconds", new_column_name="total_duration")
        batch_op.alter_column("decision", new_column_name="overall_status")

    with op.batch_alter_table("video_frame_flags") as batch_op:
        batch_op.alter_column("category", new_column_name="flag_category")


def downgrade() -> None:
    with op.batch_alter_table("video_frame_flags") as batch_op:
        batch_op.alter_column("flag_category", new_column_name="category")

    with op.batch_alter_table("video_moderation_logs") as batch_op:
        batch_op.alter_column("overall_status", new_column_name="decision")
        batch_op.alter_column("total_duration", new_column_name="duration_seconds")
