import logging
import smtplib
import ssl
from email.message import EmailMessage
from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD and settings.SMTP_FROM)


def send_email(to_email: str, subject: str, text: str) -> None:
    if not _smtp_configured():
        logger.warning("SMTP is not configured; skipping email to %s", to_email)
        return

    message = EmailMessage()
    from_name = settings.SMTP_FROM_NAME.strip() if settings.SMTP_FROM_NAME else "DocuBot"
    message["From"] = f"{from_name} <{settings.SMTP_FROM}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text)

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        if settings.SMTP_USE_TLS:
            server.starttls(context=context)
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)
