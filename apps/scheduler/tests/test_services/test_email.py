"""Tests for the email service."""

from unittest.mock import MagicMock, patch

from pr_review_scheduler.services.email import (
    format_pr_summary_email,
    send_notification_email,
)


class TestFormatPrSummaryEmail:
    """Tests for format_pr_summary_email function."""

    def test_format_pr_summary_email_multiple_repos(self):
        """Verify email formatting with multiple repositories."""
        repositories = {
            "myorg/frontend": 3,
            "myorg/backend": 2,
            "myorg/docs": 1,
        }
        application_url = "https://pr-review.example.com"

        subject, body = format_pr_summary_email(repositories, application_url)

        # Check subject
        assert subject == "[PR-Review] Open Pull Requests Summary"

        # Check body contains expected content
        assert "You have open pull requests that need attention." in body
        assert "Repository Summary:" in body
        assert "- myorg/frontend: 3 open PRs" in body
        assert "- myorg/backend: 2 open PRs" in body
        assert "- myorg/docs: 1 open PR" in body  # Singular for 1 PR
        assert f"View details: {application_url}/" in body
        assert "This is an automated message from PR-Review." in body
        assert f"visit {application_url}/settings" in body

    def test_format_pr_summary_email_single_pr(self):
        """Verify singular 'PR' not 'PRs' for single PR count."""
        repositories = {
            "myorg/repo": 1,
        }
        application_url = "http://localhost:5173"

        subject, body = format_pr_summary_email(repositories, application_url)

        # Should use "PR" (singular) not "PRs"
        assert "- myorg/repo: 1 open PR" in body
        assert "- myorg/repo: 1 open PRs" not in body

    def test_format_pr_summary_email_multiple_prs(self):
        """Verify plural 'PRs' for multiple PR counts."""
        repositories = {
            "myorg/repo": 5,
        }
        application_url = "http://localhost:5173"

        subject, body = format_pr_summary_email(repositories, application_url)

        # Should use "PRs" (plural) for counts > 1
        assert "- myorg/repo: 5 open PRs" in body


class TestSendNotificationEmail:
    """Tests for send_notification_email function."""

    def test_send_notification_email_success(self):
        """Verify successful email sending via SMTP."""
        with patch(
            "pr_review_scheduler.services.email.get_settings"
        ) as mock_get_settings, patch(
            "pr_review_scheduler.services.email.smtplib.SMTP"
        ) as mock_smtp:
            # Configure mock settings
            mock_settings = MagicMock()
            mock_settings.smtp2go_host = "mail.smtp2go.com"
            mock_settings.smtp2go_port = 587
            mock_settings.smtp2go_username = "test-user"
            mock_settings.smtp2go_password = "test-password"
            mock_settings.email_from_address = "noreply@example.com"
            mock_get_settings.return_value = mock_settings

            # Configure mock SMTP server
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Call function
            result = send_notification_email(
                to_address="recipient@example.com",
                subject="Test Subject",
                body="Test body content",
            )

            # Verify result
            assert result is True

            # Verify SMTP connection
            mock_smtp.assert_called_once_with(
                mock_settings.smtp2go_host, mock_settings.smtp2go_port
            )

            # Verify TLS and login
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(
                mock_settings.smtp2go_username, mock_settings.smtp2go_password
            )

            # Verify sendmail was called
            mock_server.sendmail.assert_called_once()
            call_args = mock_server.sendmail.call_args
            assert call_args[0][0] == mock_settings.email_from_address
            assert call_args[0][1] == "recipient@example.com"
            # Message should contain subject and body
            msg_string = call_args[0][2]
            assert "Test Subject" in msg_string
            assert "Test body content" in msg_string

    def test_send_notification_email_smtp_error(self):
        """Verify returns False on SMTP error."""
        with patch(
            "pr_review_scheduler.services.email.get_settings"
        ) as mock_get_settings, patch(
            "pr_review_scheduler.services.email.smtplib.SMTP"
        ) as mock_smtp:
            # Configure mock settings
            mock_settings = MagicMock()
            mock_settings.smtp2go_host = "mail.smtp2go.com"
            mock_settings.smtp2go_port = 587
            mock_settings.smtp2go_username = "test-user"
            mock_settings.smtp2go_password = "test-password"
            mock_settings.email_from_address = "noreply@example.com"
            mock_get_settings.return_value = mock_settings

            # Configure mock SMTP to raise exception
            mock_smtp.return_value.__enter__.side_effect = Exception(
                "SMTP connection failed"
            )

            # Call function
            result = send_notification_email(
                to_address="recipient@example.com",
                subject="Test Subject",
                body="Test body content",
            )

            # Verify result is False on error
            assert result is False

    def test_send_notification_email_login_error(self):
        """Verify returns False on login failure."""
        with patch(
            "pr_review_scheduler.services.email.get_settings"
        ) as mock_get_settings, patch(
            "pr_review_scheduler.services.email.smtplib.SMTP"
        ) as mock_smtp:
            # Configure mock settings
            mock_settings = MagicMock()
            mock_settings.smtp2go_host = "mail.smtp2go.com"
            mock_settings.smtp2go_port = 587
            mock_settings.smtp2go_username = "test-user"
            mock_settings.smtp2go_password = "wrong-password"
            mock_settings.email_from_address = "noreply@example.com"
            mock_get_settings.return_value = mock_settings

            # Configure mock SMTP server to fail on login
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_server.login.side_effect = Exception("Authentication failed")

            # Call function
            result = send_notification_email(
                to_address="recipient@example.com",
                subject="Test Subject",
                body="Test body content",
            )

            # Verify result is False on error
            assert result is False

    def test_send_notification_email_sendmail_error(self):
        """Verify returns False on sendmail failure."""
        with patch(
            "pr_review_scheduler.services.email.get_settings"
        ) as mock_get_settings, patch(
            "pr_review_scheduler.services.email.smtplib.SMTP"
        ) as mock_smtp:
            # Configure mock settings
            mock_settings = MagicMock()
            mock_settings.smtp2go_host = "mail.smtp2go.com"
            mock_settings.smtp2go_port = 587
            mock_settings.smtp2go_username = "test-user"
            mock_settings.smtp2go_password = "test-password"
            mock_settings.email_from_address = "noreply@example.com"
            mock_get_settings.return_value = mock_settings

            # Configure mock SMTP server to fail on sendmail
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            mock_server.sendmail.side_effect = Exception("Failed to send email")

            # Call function
            result = send_notification_email(
                to_address="recipient@example.com",
                subject="Test Subject",
                body="Test body content",
            )

            # Verify result is False on error
            assert result is False
