"""Envío de facturas por correo usando Outlook (win32com), con cuerpo HTML.

Requiere que Outlook esté instalado y haya una cuenta configurada.
La sesión activa de Outlook se utiliza como remitente.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ResultadoEnvio:
    ok: bool
    mensaje: str
    error: str = ""


def _normalizar_destinatarios(raw: str) -> list[str]:
    if not raw:
        return []
    partes: list[str] = []
    for trozo in raw.replace("\n", ";").replace(",", ";").split(";"):
        v = trozo.strip()
        if v:
            partes.append(v)
    vistos = set()
    out: list[str] = []
    for p in partes:
        k = p.lower()
        if k not in vistos:
            vistos.add(k)
            out.append(p)
    return out


# ---------- Estilos de la tabla (estilo Word/Outlook con Rubik Light) ----------
_TABLE_STYLE = (
    "border-collapse:collapse;margin:8pt 0;"
    "font-family:'Rubik Light',Arial,sans-serif;"
)
_TH_STYLE = (
    "border:1pt solid black;padding:6pt 8pt;text-align:center;"
    "font-family:'Rubik Light',Arial,sans-serif;font-size:14pt;"
    "color:black;font-weight:bold;background:#FFFFFF;"
)
_TD_BASE = (
    "border:1pt solid black;padding:4pt 8pt;"
    "font-family:'Rubik Light',Arial,sans-serif;font-size:14pt;"
    "color:black;background:#FFFFFF;"
)


def _esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def _td(value, *, align: str = "left") -> str:
    return f'<td style="{_TD_BASE}text-align:{align};">{_esc(value)}</td>'


def construir_tabla_html(
    mes: str,
    convenio: str,
    referencia: str,
    numero_factura: str,
    linea: str,
    total: Optional[float],
    fecha_limite: Optional[str],
) -> str:
    """Construye la tabla HTML estilizada con los datos de la factura.
    Reproduce el formato del correo de referencia (Rubik Light 14pt, bordes 1pt)."""
    headers = ["MES", "Convenio", "Referencia", "Factura", "Línea",
               "Total a pagar", "Fecha límite de pago"]
    total_txt = f"$ {total:,.2f}" if total is not None else "—"
    th_cells = "".join(f'<th style="{_TH_STYLE}">{_esc(h)}</th>' for h in headers)
    td_cells = "".join([
        _td(mes or "—"),
        _td(convenio or "—", align="right"),
        _td(referencia or "—"),
        _td(numero_factura or "—"),
        _td(linea or "—"),
        _td(total_txt),
        _td(fecha_limite or "—", align="right"),
    ])
    return (
        f'<table cellspacing="0" cellpadding="0" style="{_TABLE_STYLE}">'
        f'<thead><tr>{th_cells}</tr></thead>'
        f'<tbody><tr>{td_cells}</tr></tbody>'
        f'</table>'
    )


# ---------- Firma corporativa (replica de email.txt) ----------
FIRMA_DEFAULT = (
    '<p style="margin:0;font-family:Rubik,Arial,sans-serif;font-size:12pt;'
    '"><b>Jesus Alexis Tenorio Hernández</b></p>'
    '<p style="margin:0;font-family:Rubik,Arial,sans-serif;font-size:12pt;'
    'color:#7F7F7F;">Systems Analyst</p>'
    '<p style="margin:6pt 0 0 0;font-family:Rubik,Arial,sans-serif;font-size:8pt;">'
    'Av. Industrial sección 1 #39</p>'
    '<p style="margin:0;font-family:Rubik,Arial,sans-serif;font-size:8pt;">'
    'San Luis Teolocholco, Tlaxcala. 90850</p>'
    '<p style="margin:6pt 0 0 0;font-family:Rubik,Arial,sans-serif;font-size:10pt;">'
    '<a href="http://www.taurus.com.mx/" '
    'style="color:#0563C1;text-decoration:none;"><b>www.taurus.com.mx</b></a></p>'
    '<p style="margin:0;font-family:Rubik,Arial,sans-serif;font-size:10pt;">'
    '<a href="https://www.group-taurus.com/en/work-with-us/" '
    'style="color:#0563C1;text-decoration:none;">Work with us</a> '
    'and connect with us on '
    '<a href="https://es-la.facebook.com/taurusmexico/" '
    'style="color:#0563C1;text-decoration:none;">Facebook TaurusMéxico</a></p>'
    '<p style="margin:10pt 0 0 0;font-family:Rubik,Arial,sans-serif;font-size:8pt;'
    'color:#7F7F7F;"><i>This email is confidential and may be privileged. '
    'If you have received it in error, please notify us immediately and then delete it. '
    'Please do not copy it, disclose its contents or use it for any purpose.</i></p>'
)


class FacturasEmailService:
    """Envío de correos HTML con adjuntos PDF/XML mediante Outlook (COM)."""

    PLANTILLA_ASUNTO_DEFAULT = "Factura Telcel — {cliente} — {mes} {anio}"
    PLANTILLA_CUERPO_DEFAULT = (
        '<p style="font-family:\'Rubik Light\',Arial,sans-serif;font-size:11pt;">'
        'Hola, te comparto la factura y complemento de pago de la línea Telcel correspondiente.'
        '</p>'
        '{tabla_factura}'
        '<p style="font-family:\'Rubik Light\',Arial,sans-serif;font-size:11pt;">'
        'Quedo al pendiente.</p>'
        '<p style="font-family:\'Rubik Light\',Arial,sans-serif;font-size:11pt;">'
        'Saludos,</p>'
        '{firma}'
    )

    PLACEHOLDERS = [
        "cliente", "cuenta", "linea", "mes", "anio",
        "total", "fecha_corte", "fecha_limite", "convenio", "referencia",
        "numero_factura", "tabla_factura", "firma",
    ]

    def enviar(
        self,
        destinatarios: str,
        asunto: str,
        cuerpo_html: str,
        adjuntos: list[Path],
    ) -> ResultadoEnvio:
        emails = _normalizar_destinatarios(destinatarios)
        if not emails:
            return ResultadoEnvio(False, "Sin destinatarios.", error="Lista de destinatarios vacía.")

        adjuntos_validos = [p for p in adjuntos if p and Path(p).exists()]
        if not adjuntos_validos and adjuntos:
            return ResultadoEnvio(
                False,
                "No se encontraron los archivos adjuntos.",
                error=f"Rutas inexistentes: {[str(a) for a in adjuntos]}",
            )

        try:
            import pythoncom  # type: ignore
            import win32com.client  # type: ignore
        except ImportError:
            return ResultadoEnvio(
                False,
                "pywin32 no está instalado. Instálalo con: pip install pywin32.",
                error="ImportError: win32com.client",
            )

        pythoncom.CoInitialize()
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)  # 0 = olMailItem
            mail.To = "; ".join(emails)
            mail.Subject = asunto
            mail.HTMLBody = cuerpo_html
            for adj in adjuntos_validos:
                mail.Attachments.Add(str(Path(adj).resolve()))
            mail.Send()
            return ResultadoEnvio(True, f"Enviado a {len(emails)} destinatario(s).")
        except Exception as exc:
            return ResultadoEnvio(
                False,
                f"Error al enviar por Outlook: {exc}",
                error=str(exc),
            )
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def construir_mensaje_telcel(
        self,
        cliente: str,
        cuenta: str,
        linea: str,
        mes: str,
        anio: int,
        total: Optional[float],
        fecha_limite: Optional[str],
        convenio: str,
        referencia: str,
        fecha_corte: Optional[str] = None,
        numero_factura: str = "",
        plantilla_asunto: str = "",
        plantilla_cuerpo: str = "",
    ) -> tuple[str, str]:
        """
        Genera (asunto, cuerpoHTML) usando la plantilla del cliente o el default.

        Reemplaza placeholders en ambas plantillas:
            {cliente} {cuenta} {linea} {mes} {anio} {total}
            {fecha_corte} {fecha_limite} {convenio} {referencia}
            {numero_factura} {tabla_factura} {firma}
        """
        tabla = construir_tabla_html(
            mes=mes, convenio=convenio, referencia=referencia,
            numero_factura=numero_factura, linea=linea,
            total=total, fecha_limite=fecha_limite,
        )
        ctx = {
            "cliente": cliente or "",
            "cuenta": cuenta or "",
            "linea": linea or "—",
            "mes": mes or "",
            "anio": str(anio) if anio else "",
            "total": f"${total:,.2f} MN" if total is not None else "—",
            "fecha_corte": fecha_corte or "—",
            "fecha_limite": fecha_limite or "—",
            "convenio": convenio or "—",
            "referencia": referencia or "—",
            "numero_factura": numero_factura or "—",
            "tabla_factura": tabla,
            "firma": FIRMA_DEFAULT,
        }
        asunto_tpl = (plantilla_asunto or self.PLANTILLA_ASUNTO_DEFAULT).strip()
        cuerpo_tpl = plantilla_cuerpo or self.PLANTILLA_CUERPO_DEFAULT

        # Asunto en texto plano (sin tabla ni firma)
        asunto_ctx = {k: v for k, v in ctx.items() if k not in ("tabla_factura", "firma")}
        asunto = self._aplicar(asunto_tpl, asunto_ctx)

        # Cuerpo: si la plantilla está en texto plano, la convertimos a HTML
        # respetando saltos de línea.
        cuerpo_html = cuerpo_tpl
        if "<" not in cuerpo_html and ">" not in cuerpo_html:
            cuerpo_html = "<p>" + cuerpo_html.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"
        cuerpo_html = self._aplicar(cuerpo_html, ctx)

        # Fallbacks si el usuario olvidó incluir los placeholders
        if "{tabla_factura}" not in cuerpo_tpl and tabla not in cuerpo_html:
            cuerpo_html += tabla
        if "{firma}" not in cuerpo_tpl and FIRMA_DEFAULT not in cuerpo_html:
            cuerpo_html += FIRMA_DEFAULT

        return asunto, cuerpo_html

    @staticmethod
    def _aplicar(plantilla: str, ctx: dict) -> str:
        out = plantilla
        for k, v in ctx.items():
            out = out.replace("{" + k + "}", str(v))
        return out
