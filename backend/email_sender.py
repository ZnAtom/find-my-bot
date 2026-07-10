import os
import logging
from email.message import EmailMessage
import aiosmtplib

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1") == "1"

async def send_match_email(to_email: str, item_name: str, contact_person: str, matched_items: list):
    if not to_email:
        logging.warning("No email address provided, skipping email.")
        return

    subject = f"【校园寻物】好消息！您的物品 '{item_name}' 疑似有了匹配结果"
    
    body = f"亲爱的 {contact_person}:\n\n"
    body += f"系统为您发布的物品 '{item_name}' 找到了 {len(matched_items)} 个潜在匹配！\n"
    body += "请尽快登录系统查看详细信息并确认匹配结果。\n\n"
    body += "祝好！\n校园失物招领小助手"

    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        # Fallback if no SMTP configuration is found
        logging.info(f"[SIMULATED EMAIL] To: {to_email} | Subject: {subject} | Body: {body}")
        return

    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            use_tls=SMTP_USE_TLS
        )
        logging.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
