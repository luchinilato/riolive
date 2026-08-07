"""Alertas ao desenvolvedor por e-mail (canal da v1; Telegram fica pra v2).

Sem SMTP configurado (dev), o alerta é apenas logado. O cooldown por fonte é
responsabilidade do chamador (ControleSaude.tentar_iniciar_cooldown).
"""

import logging
import smtplib
from email.message import EmailMessage

from riolive.config import config

logger = logging.getLogger(__name__)


def enviar_alerta(assunto: str, corpo: str) -> None:
    cfg = config()
    if not cfg.smtp_host or not cfg.alerta_email_destino:
        logger.warning("ALERTA (e-mail não configurado): %s — %s", assunto, corpo)
        return
    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = cfg.smtp_usuario or cfg.alerta_email_destino
    mensagem["To"] = cfg.alerta_email_destino
    mensagem.set_content(corpo)
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_porta, timeout=15) as smtp:
        smtp.starttls()
        if cfg.smtp_usuario:
            smtp.login(cfg.smtp_usuario, cfg.smtp_senha.get_secret_value())
        smtp.send_message(mensagem)
    logger.info("Alerta enviado: %s", assunto)


def alertar_transicao(
    slug: str, estado_anterior: str | None, estado_novo: str, classe: str | None, detalhe: str
) -> None:
    if estado_novo == "online":
        assunto = f"[riolive] {slug} recuperada"
    else:
        assunto = f"[riolive] {slug}: {estado_novo}" + (f" ({classe})" if classe else "")
    corpo = (
        f"Fonte: {slug}\n"
        f"Transição: {estado_anterior or 'desconhecido'} → {estado_novo}\n"
        f"Classe de falha: {classe or '-'}\n"
        f"Detalhe: {detalhe}\n"
    )
    enviar_alerta(assunto, corpo)
