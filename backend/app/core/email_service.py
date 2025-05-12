import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, PackageLoader, select_autoescape
from app.core.config import settings
import ssl

env = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

async def send_email(
    email_to: str,
    subject: str,
    template_name: str,
    template_data: dict
) -> None:
    message = MIMEMultipart()
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = email_to
    message["Subject"] = subject

    # Render the email template
    template = env.get_template(f"{template_name}.html")
    html_content = template.render(**template_data)
    
    # Attach the HTML content
    message.attach(MIMEText(html_content, "html"))

    # Create SSL context
    ssl_context = ssl.create_default_context()
    
    # Send the email
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=False,  # Don't use direct TLS
            tls_context=ssl_context,
            start_tls=True  # Use STARTTLS for Gmail
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send email: {str(e)}")
        raise 
