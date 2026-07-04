import smtplib
from email.message import EmailMessage

from app.config import settings


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    if not settings.smtp_host:
        raise RuntimeError("SMTP is not configured")

    from_email = settings.smtp_from_email or settings.smtp_username

    message = EmailMessage()
    message["Subject"] = "Reset your Spendly password"
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(
        "We received a request to reset your Spendly password.\n\n"
        f"Reset it here (this link expires in {settings.password_reset_token_expire_minutes} minutes):\n"
        f"{reset_link}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
