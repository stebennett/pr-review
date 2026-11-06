"""Email service for sending notifications via SMTP2GO.

This module provides functions for sending PR notification emails.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pr_review_scheduler.config import get_settings

logger = logging.getLogger(__name__)


def send_notification_email(
    to_address: str,
    subject: str,
    body: str,
) -> bool:
    """Send a notification email via SMTP2GO.

    Args:
        to_address: Recipient email address.
        subject: Email subject line.
        body: Email body content.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    settings = get_settings()

    logger.info("Sending email to %s: %s", to_address, subject)

    try:
        # Create MIME message
        msg = MIMEMultipart()
        msg["From"] = settings.email_from_address
        msg["To"] = to_address
        msg["Subject"] = subject

        # Attach body as plain text
        msg.attach(MIMEText(body, "plain"))

        # Connect to SMTP server and send
        with smtplib.SMTP(settings.smtp2go_host, settings.smtp2go_port) as server:
            server.starttls()
            server.login(settings.smtp2go_username, settings.smtp2go_password)
            server.sendmail(
                settings.email_from_address,
                to_address,
                msg.as_string(),
            )

        logger.info("Email sent successfully to %s", to_address)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_address, str(e))
        return False


def format_pr_summary_email(
    repositories: dict[str, int],
    application_url: str,
) -> tuple[str, str]:
    """Format a PR summary notification email.

    Args:
        repositories: Dictionary mapping repo names to PR counts.
        application_url: Base URL of the application.

    Returns:
        Tuple of (subject, body) for the email.
    """
    subject = "[PR-Review] Open Pull Requests Summary"

    body_lines = [
        "You have open pull requests that need attention.",
        "",
        "Repository Summary:",
    ]

    for repo_name, pr_count in repositories.items():
        body_lines.append(f"- {repo_name}: {pr_count} open PR{'s' if pr_count != 1 else ''}")

    body_lines.extend(
        [
            "",
            f"View details: {application_url}/",
            "",
            "---",
            "This is an automated message from PR-Review.",
            f"To manage your notification settings, visit {application_url}/settings",
        ]
    )

    return subject, "\n".join(body_lines)
