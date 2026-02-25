"""
FastAPI Email Sender

SMTP 邮件发送 + Jinja2 模板渲染。

使用方式：
    from fastapi_email_sender.email import send_email, render_email_template, EmailData, SmtpConfig

    config = SmtpConfig(
        host="smtp.example.com",
        port=587,
        tls=True,
        user="user@example.com",
        password="secret",
        from_email="noreply@example.com",
        from_name="My App",
    )

    html = render_email_template(
        template_name="welcome.html",
        context={"username": "Alice"},
        templates_dir="/path/to/templates",
    )

    send_email(
        email_to="alice@example.com",
        subject="Welcome!",
        html_content=html,
        smtp_config=config,
    )
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import emails  # type: ignore
from jinja2 import Template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SmtpConfig:
    """SMTP 服务器配置。"""
    host: str
    port: int = 587
    user: str | None = None
    password: str | None = None
    tls: bool = True
    ssl: bool = False
    from_email: str = ""
    from_name: str = ""


@dataclass
class EmailData:
    """邮件数据。"""
    html_content: str
    subject: str


def render_email_template(
    *,
    template_name: str,
    context: dict[str, Any],
    templates_dir: str | Path,
) -> str:
    """
    渲染 Jinja2 邮件模板。

    Args:
        template_name: 模板文件名（相对于 templates_dir）
        context: 模板变量
        templates_dir: 模板目录路径
    """
    template_str = (Path(templates_dir) / template_name).read_text()
    return Template(template_str).render(context)


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
    smtp_config: SmtpConfig,
) -> None:
    """
    通过 SMTP 发送邮件。

    Args:
        email_to: 收件人邮箱
        subject: 邮件主题
        html_content: HTML 邮件内容
        smtp_config: SMTP 配置
    """
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(smtp_config.from_name, smtp_config.from_email),
    )
    smtp_options: dict[str, Any] = {
        "host": smtp_config.host,
        "port": smtp_config.port,
    }
    if smtp_config.tls:
        smtp_options["tls"] = True
    elif smtp_config.ssl:
        smtp_options["ssl"] = True
    if smtp_config.user:
        smtp_options["user"] = smtp_config.user
    if smtp_config.password:
        smtp_options["password"] = smtp_config.password

    response = message.send(to=email_to, smtp=smtp_options)
    logger.info(f"send email result: {response}")
