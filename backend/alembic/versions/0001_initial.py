"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-17

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_RSS_FEEDS = [
    "https://www.theflightdeal.com/feed/",
    "https://www.secretflying.com/feed/",
    "https://www.fly4free.com/flight-deals/feed/",
]


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("location_label", sa.String(120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("units", sa.String(16), nullable=False),
        sa.Column("email_to", sa.String(255), nullable=True),
        sa.Column("digest_hour", sa.Integer(), nullable=False),
        sa.Column("digest_minute", sa.Integer(), nullable=False),
        sa.Column("digest_enabled", sa.Boolean(), nullable=False),
        sa.Column("rss_feeds", postgresql.JSONB(), nullable=False),
        sa.Column("deal_keywords", postgresql.JSONB(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "watchlist_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(16), nullable=False, unique=True),
        sa.Column("shares", sa.Float(), nullable=True),
        sa.Column("cost_basis", sa.Float(), nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_watchlist_item_symbol", "watchlist_item", ["symbol"])

    priority = postgresql.ENUM("low", "medium", "high", name="priority")
    priority.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "todo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "priority",
            postgresql.ENUM("low", "medium", "high", name="priority", create_type=False),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_todo_done", "todo", ["done"])

    op.create_table(
        "cache_entry",
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "digest_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sent_for_date", sa.Date(), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("trigger", sa.String(16), nullable=False, server_default="scheduled"),
        sa.Column("status", sa.String(32), nullable=False, server_default="sent"),
        sa.Column("detail", sa.Text(), nullable=True),
    )
    op.create_index("ix_digest_log_sent_for_date", "digest_log", ["sent_for_date"])

    settings = sa.table(
        "settings",
        sa.column("id", sa.Integer),
        sa.column("location_label", sa.String),
        sa.column("latitude", sa.Float),
        sa.column("longitude", sa.Float),
        sa.column("timezone", sa.String),
        sa.column("units", sa.String),
        sa.column("digest_hour", sa.Integer),
        sa.column("digest_minute", sa.Integer),
        sa.column("digest_enabled", sa.Boolean),
        sa.column("rss_feeds", postgresql.JSONB()),
        sa.column("deal_keywords", postgresql.JSONB()),
    )
    op.bulk_insert(
        settings,
        [
            {
                "id": 1,
                "location_label": "San Francisco, US",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "timezone": "America/Los_Angeles",
                "units": "imperial",
                "digest_hour": 7,
                "digest_minute": 0,
                "digest_enabled": True,
                "rss_feeds": DEFAULT_RSS_FEEDS,
                "deal_keywords": [],
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("digest_log")
    op.drop_table("cache_entry")
    op.drop_table("todo")
    op.drop_table("watchlist_item")
    op.drop_table("settings")
    postgresql.ENUM(name="priority").drop(op.get_bind(), checkfirst=True)
