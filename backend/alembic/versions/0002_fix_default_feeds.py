"""replace dead default RSS feeds

Secret Flying's /feed/ now 301s to its homepage and Fly4Free moved its feed off
/flight-deals/, so the originally seeded URLs return no entries. Only rows still
holding the old defaults are touched, so a customised feed list is preserved.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-17

"""
import json

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

OLD_FEEDS = [
    "https://www.theflightdeal.com/feed/",
    "https://www.secretflying.com/feed/",
    "https://www.fly4free.com/flight-deals/feed/",
]

NEW_FEEDS = [
    "https://www.theflightdeal.com/feed/",
    "https://www.fly4free.com/feed/",
    "https://feeds.feedburner.com/SecretFlying",
]

UPDATE = sa.text(
    "UPDATE settings SET rss_feeds = CAST(:new AS jsonb) "
    "WHERE rss_feeds = CAST(:old AS jsonb)"
)


def _swap(from_feeds: list[str], to_feeds: list[str]) -> None:
    op.get_bind().execute(
        UPDATE, {"new": json.dumps(to_feeds), "old": json.dumps(from_feeds)}
    )


def upgrade() -> None:
    _swap(OLD_FEEDS, NEW_FEEDS)


def downgrade() -> None:
    _swap(NEW_FEEDS, OLD_FEEDS)
