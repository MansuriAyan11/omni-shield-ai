"""add_video_moderation_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-08 09:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_moderation_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=True),
        sa.Column("risk_level", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("recommended_action", sa.String(length=50), nullable=True),
        sa.Column("reason", sa.String(length=512), nullable=True),
        sa.Column("frames_sampled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frames_flagged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frame_interval_seconds", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_video_moderation_logs_user_id", "video_moderation_logs", ["user_id"])
    op.create_index("ix_video_moderation_logs_status", "video_moderation_logs", ["status"])
    op.create_index("ix_video_moderation_logs_created_at", "video_moderation_logs", ["created_at"])

    op.create_table(
        "video_frame_flags",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("video_log_id", sa.UUID(), nullable=False),
        sa.Column("timestamp_seconds", sa.Float(), nullable=False),
        sa.Column("frame_index", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("decision", sa.String(length=50), nullable=False),
        sa.Column("detected_labels", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["video_log_id"], ["video_moderation_logs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_video_frame_flags_video_log_id", "video_frame_flags", ["video_log_id"])


def downgrade() -> None:
    op.drop_index("ix_video_frame_flags_video_log_id", table_name="video_frame_flags")
    op.drop_table("video_frame_flags")
    op.drop_index("ix_video_moderation_logs_created_at", table_name="video_moderation_logs")
    op.drop_index("ix_video_moderation_logs_status", table_name="video_moderation_logs")
    op.drop_index("ix_video_moderation_logs_user_id", table_name="video_moderation_logs")
    op.drop_table("video_moderation_logs")
