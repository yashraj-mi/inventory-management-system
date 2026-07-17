"""
Email service for asynchronous notifications.

Configures SMTP via fastapi-mail and dispatches transactional emails such as
registration reviews, approvals, and credential generation to users.
"""

from pathlib import Path
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import get_settings

settings = get_settings()


class EmailService:
    """
    Service responsible for dispatching transactional emails asynchronously.

    Uses `fastapi-mail` to configure SMTP connections and send templated HTML emails.
    """

    def __init__(self):
        """
        Initialize EmailService with connection configurations.

        Sets up the SMTP connection parameters using environment variables and
        initializes the FastMail instance with the templating directory.
        """
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email",
        )
        self.fastmail = FastMail(self.config)

    def send_pending_review_email(
        self, background_tasks: BackgroundTasks, recipient: str, org_name: str
    ):
        """
        Send an email acknowledging receipt of an organization registration request.

        This delegates the actual sending to a FastAPI background task.

        Args:
            background_tasks: FastAPI background task manager to run sending asynchronously.
            recipient: Email address of the organization contact.
            org_name: Name of the registered organization.
        """
        message = MessageSchema(
            subject=f"Registration Received - {org_name}",
            recipients=[recipient],
            template_body={"org_name": org_name},
            subtype=MessageType.html,
        )
        background_tasks.add_task(
            self.fastmail.send_message,
            message,
            template_name="organization_request.html",
        )

    def send_approval_email(
        self, background_tasks: BackgroundTasks, recipient: str, org_name: str
    ):
        """
        Send an email notifying that the organization registration was approved.

        This delegates the actual sending to a FastAPI background task.

        Args:
            background_tasks: FastAPI background task manager.
            recipient: Email address of the organization contact.
            org_name: Name of the approved organization.
        """
        message = MessageSchema(
            subject=f"Welcome to the Platform! Organization Approved: {org_name}",
            recipients=[recipient],
            template_body={"org_name": org_name},
            subtype=MessageType.html,
        )
        background_tasks.add_task(
            self.fastmail.send_message,
            message,
            template_name="organization_approval.html",
        )

    def send_credentials_email(
        self,
        background_tasks: BackgroundTasks,
        recipient: str,
        first_name: str,
        org_name: str,
        temp_password: str,
    ):
        """
        Send an email with temporary login credentials for a new organization admin.

        This delegates the actual sending to a FastAPI background task.

        Args:
            background_tasks: FastAPI background task manager.
            recipient: Email address of the new admin user.
            first_name: First name of the admin user.
            org_name: Name of the organization.
            temp_password: The automatically generated temporary password.
        """
        message = MessageSchema(
            subject="Action Required: Setup Your Admin Profile Account",
            recipients=[recipient],
            template_body={
                "first_name": first_name,
                "org_name": org_name,
                "email": recipient,
                "temporary_password": temp_password,
            },
            subtype=MessageType.html,
        )
        background_tasks.add_task(
            self.fastmail.send_message, message, template_name="send_credentials.html"
        )


email_service = EmailService()
