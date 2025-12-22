"""Email service for sending notifications via SMTP2GO.

This module provides functions for sending PR notification emails.
"""

import logging

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
    _settings = get_settings()  # noqa: F841 - Used in Task 6.4 implementation

    logger.info("Sending email to %s: %s", to_address, subject)

    # TODO: Implement in Task 6.4
    # Use smtplib to send email via SMTP2GO:
    # - _settings.smtp2go_host
    # - _settings.smtp2go_port
    # - _settings.smtp2go_username
    # - _settings.smtp2go_password
    # - _settings.email_from_address

    return True


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
