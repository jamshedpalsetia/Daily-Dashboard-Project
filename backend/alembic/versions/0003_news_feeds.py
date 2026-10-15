"""add news feed settings

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-25

"""
import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TOP_FEEDS = ["https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"]
BUSINESS_FEEDS = [
    "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"
]


def upgrade() -> None:
    for column, default in (
        ("news_top_feeds", TOP_FEEDS),
        ("news_business_feeds", BUSINESS_FEEDS),
    ):
        op.add_column(
            "settings",
            sa.Column(
                column,
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text(f"'{json.dumps(default)}'::jsonb"),
            ),
        )


def downgrade() -> None:
    op.drop_column("settings", "news_business_feeds")
    op.drop_column("settings", "news_top_feeds")
