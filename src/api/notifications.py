"""
Notification service — pluggable email backend.

In dev/test (NOTIFY_BACKEND=log, the default) all messages are written to
the Python logger so they're visible in test output without any SMTP config.

In production set:
  NOTIFY_BACKEND=smtp
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, NOTIFY_FROM_EMAIL

The public surface is a single async function:
  await send_notification(to, subject, body)

Callers (routers) fire-and-forget via asyncio.create_task so the HTTP
response is never blocked waiting for the mailer.
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)

_BACKEND = os.getenv("NOTIFY_BACKEND", "log").lower()
_SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USER = os.getenv("SMTP_USER", "")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
_FROM_EMAIL = os.getenv("NOTIFY_FROM_EMAIL", "noreply@instructor-system.local")


def _send_ses(to: str, subject: str, body: str) -> None:
    import boto3
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
    client = boto3.client("ses", region_name=region, endpoint_url=endpoint_url)
    client.send_email(
        Source=_FROM_EMAIL,
        Destination={"ToAddresses": [to]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": body}},
        },
    )


def _send_smtp(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = _FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as s:
        if _SMTP_USER:
            s.starttls()
            s.login(_SMTP_USER, _SMTP_PASSWORD)
        s.send_message(msg)


def send_notification(to: str, subject: str, body: str) -> None:
    """
    Send an email notification synchronously.
    Call via a background thread from async endpoints so the HTTP
    response is not blocked.
    """
    if _BACKEND == "ses":
        try:
            _send_ses(to, subject, body)
            logger.info("Email sent via SES to %s: %s", to, subject)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send SES email to %s: %s", to, exc)
    elif _BACKEND == "smtp":
        try:
            _send_smtp(to, subject, body)
            logger.info("Email sent to %s: %s", to, subject)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email to %s: %s", to, exc)
    else:
        # log backend (dev/test default)
        logger.info("[NOTIFY] to=%s subject=%r\n%s", to, subject, body)


# ---------------------------------------------------------------------------
# High-level notification helpers
# ---------------------------------------------------------------------------

def notify_allocation_created(
    instructor_email: str,
    instructor_name: str,
    event_title: str,
    event_date_str: str,
    role: str,
) -> None:
    send_notification(
        to=instructor_email,
        subject=f"You have been allocated to {event_title}",
        body=(
            f"Hi {instructor_name},\n\n"
            f"You have been assigned as {role} instructor for:\n"
            f"  Event: {event_title}\n"
            f"  Date:  {event_date_str}\n\n"
            "Please log in to review your upcoming schedule.\n\n"
            "— Instructor Reservation System"
        ),
    )


def notify_allocation_removed(
    instructor_email: str,
    instructor_name: str,
    event_title: str,
    event_date_str: str,
) -> None:
    send_notification(
        to=instructor_email,
        subject=f"Your allocation to {event_title} has been removed",
        body=(
            f"Hi {instructor_name},\n\n"
            f"Your allocation for the following event has been removed:\n"
            f"  Event: {event_title}\n"
            f"  Date:  {event_date_str}\n\n"
            "Please log in if you have questions.\n\n"
            "— Instructor Reservation System"
        ),
    )


def notify_event_date_cancelled(
    instructor_email: str,
    instructor_name: str,
    event_title: str,
    event_date_str: str,
) -> None:
    send_notification(
        to=instructor_email,
        subject=f"Event date cancelled: {event_title}",
        body=(
            f"Hi {instructor_name},\n\n"
            f"The following event date has been cancelled:\n"
            f"  Event: {event_title}\n"
            f"  Date:  {event_date_str}\n\n"
            "Your time has been freed in the system.\n\n"
            "— Instructor Reservation System"
        ),
    )
