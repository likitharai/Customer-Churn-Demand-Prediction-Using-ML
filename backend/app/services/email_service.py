import os
import smtplib
import ssl
from email.message import EmailMessage


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def send_invitation_email(recipient: str, organization: str, role: str, invitation_url: str) -> dict:
    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip() or username
    if not host or not sender:
        return {"status": "not_configured", "detail": "SMTP is not configured"}

    port = int(os.getenv("SMTP_PORT", "587"))
    use_tls = _truthy(os.getenv("SMTP_USE_TLS", "true"))
    use_ssl = _truthy(os.getenv("SMTP_USE_SSL", "false"))
    message = EmailMessage()
    message["Subject"] = f"Join {organization} on RetainIQ"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"You have been invited to {organization} as {role}.\n\n"
        f"Create your employee account using this one-time link:\n{invitation_url}\n\n"
        "This link expires in 7 days. If you did not expect this invitation, ignore this email."
    )
    message.add_alternative(
        f"<h2>Join {organization} on RetainIQ</h2>"
        f"<p>You have been invited as <strong>{role}</strong>.</p>"
        f"<p><a href=\"{invitation_url}\">Accept employee invitation</a></p>"
        "<p>This one-time link expires in 7 days.</p>",
        subtype="html",
    )

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=15, context=ssl.create_default_context()) as server:
                if username:
                    server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                server.ehlo()
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                if username:
                    server.login(username, password)
                server.send_message(message)
        return {"status": "sent", "detail": f"Invitation sent to {recipient}"}
    except Exception as exc:
        return {"status": "failed", "detail": f"Email delivery failed: {exc}"}
