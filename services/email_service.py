import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.logger import app_logger

class EmailAlertService:
    @staticmethod
    def send_alert(subject: str, body: str):
        """Dispatches an email alert to the security/governance team."""
        recipient = os.getenv("GRC_ALERT_EMAIL", "compliance-alerts@enterprise.com")
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASS", "")

        app_logger.info(f"EmailService: Attempting to dispatch alert to {recipient}...")

        # Fallback to simulation mode to avoid blocking or throwing when credentials are empty
        if not smtp_user or not smtp_pass:
            app_logger.warning(
                f"[SIMULATED ALERT] Destination: {recipient}\n"
                f"Subject: {subject}\n"
                f"Body:\n{body}\n"
                "----------------------------------------"
            )
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, recipient, msg.as_string())
            server.close()
            
            app_logger.info("EmailService: Alert email successfully delivered via SMTP.")
            return True
        except Exception as e:
            app_logger.error(f"EmailService: Failed to deliver SMTP alert: {e}")
            return False

email_service = EmailAlertService()
