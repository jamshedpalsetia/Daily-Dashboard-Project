from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

log = logging.getLogger(__name__)


def send_email(to: str, subject: str, html: str, text: str) -> None:
    cfg = get_settings()
    if not cfg.smtp_configured:
        raise RuntimeError("SMTP is not configured; set SMTP_HOST and SMTP_FROM in .env")
    if not to:
        raise RuntimeError("no recipient configured; set it in dashboard settings")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = cfg.smtp_from
    message["To"] = to
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    if cfg.smtp_port == 465:
        with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=30) as server:
            if cfg.smtp_user:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as server:
            server.ehlo()
            if cfg.smtp_starttls:
                server.starttls()
                server.ehlo()
            if cfg.smtp_user:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.send_message(message)

    log.info("digest email sent to %s", to)
