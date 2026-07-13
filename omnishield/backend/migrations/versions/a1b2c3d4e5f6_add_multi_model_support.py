"""add_multi_model_support

Revision ID: a1b2c3d4e5f6
Revises: 6e11f0856190
Create Date: 2026-07-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6e11f0856190'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns for multi-model support
    op.add_column('moderation_logs', sa.Column('model_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('moderation_logs', sa.Column('model_versions', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('moderation_logs', sa.Column('face_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('moderation_logs', sa.Column('detected_text', sa.String(length=1000), nullable=True))
    op.add_column('moderation_logs', sa.Column('contains_profanity', sa.String(length=10), nullable=True))
    
    # Increase reason column length to accommodate multi-model reasons
    op.alter_column('moderation_logs', 'reason',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=512),
                    existing_nullable=True)


def downgrade() -> None:
    # Remove added columns
    op.drop_column('moderation_logs', 'contains_profanity')
    op.drop_column('moderation_logs', 'detected_text')
    op.drop_column('moderation_logs', 'face_count')
    op.drop_column('moderation_logs', 'model_versions')
    op.drop_column('moderation_logs', 'model_results')
    
    # Revert reason column length
    op.alter_column('moderation_logs', 'reason',
                    existing_type=sa.String(length=512),
                    type_=sa.String(length=255),
                    existing_nullable=True)
