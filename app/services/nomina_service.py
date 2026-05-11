"""Servicio de nómina: parseo de archivos CFDI, cálculo de períodos y envío por Graph API."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

_VAR_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


@dataclass
class NominaItem:
    """Representa un CFDI a enviar con los datos del empleado."""
    num_empleado: str
    nombre_empleado: str
    correo: str
    pdf_path: str
    xml_path: str
    pdf_nombre: str
    xml_nombre: str
    anio: int
    num_semana: int
    # 'listo' | 'sin_correo' | 'sin_xml' | 'sin_empleado'
    estado: str = "listo"


class NominaService:
    """Lógica de negocio para el envío de CFDIs de nómina."""

    # ------------------------------------------------------------------ #
    # Parseo de nombres de archivo                                        #
    # ------------------------------------------------------------------ #

    def parse_cfdi_filename(self, filename: str) -> Optional[dict]:
        """
        Extrae metadatos del nombre RE_[num_razon]_Semanal_[año]_[semana]_[empleado]_*.

        Retorna dict con num_razon, anio, num_semana, num_empleado  o  None si no coincide.
        """
        stem = Path(filename).stem
        parts = stem.split("_")
        if len(parts) < 6 or parts[0].upper() != "RE" or parts[2].lower() != "semanal":
            return None
        try:
            return {
                "num_razon": parts[1],
                "anio": int(parts[3]),
                "num_semana": int(parts[4]),
                "num_empleado": parts[5],
            }
        except (ValueError, IndexError):
            return None

    # ------------------------------------------------------------------ #
    # Cálculo de período                                                   #
    # ------------------------------------------------------------------ #

    def calcular_periodo(self, anio: int, num_semana: int) -> tuple[date, date]:
        """
        Calcula las fechas de inicio (viernes) y fin (jueves) de la semana indicada.

        La semana 1 comienza el viernes más reciente en o antes del 1 de enero del año dado.
        """
        jan1 = date(anio, 1, 1)
        # weekday(): Mon=0 … Fri=4 … Sun=6
        days_since_friday = (jan1.weekday() - 4) % 7
        week1_start = jan1 - timedelta(days=days_since_friday)
        start = week1_start + timedelta(weeks=num_semana - 1)
        end = start + timedelta(days=6)
        return start, end

    # ------------------------------------------------------------------ #
    # Escaneo de carpeta                                                   #
    # ------------------------------------------------------------------ #

    def construir_ruta(self, ruta_cfdi: str, prefijo_carpeta: str, anio: int, num_semana: int) -> Path:
        """Construye la ruta completa de la carpeta de CFDIs."""
        return Path(ruta_cfdi) / str(anio) / f"{prefijo_carpeta}{num_semana}"

    def scan_carpeta(self, carpeta: Path) -> list[tuple[Path, Optional[Path], str]]:
        """
        Lista los pares (pdf, xml, num_empleado) encontrados en la carpeta.

        Retorna lista de (pdf_path, xml_path_o_None, num_empleado).
        """
        if not carpeta.exists():
            raise FileNotFoundError(f"La carpeta no existe: {carpeta}")

        # Busca todos los PDF y filtra por nombre usando parse_cfdi_filename
        resultados = []
        for pdf in sorted(carpeta.iterdir()):
            if pdf.suffix.lower() != ".pdf":
                continue
            meta = self.parse_cfdi_filename(pdf.name)
            if not meta:
                continue
            xml = pdf.with_suffix(".xml")
            if not xml.exists():
                # Intentar con mayúsculas
                xml_upper = pdf.with_suffix(".XML")
                xml = xml_upper if xml_upper.exists() else None
            resultados.append((pdf, xml, meta["num_empleado"]))
        return resultados

    def mover_zip(self, zip_path: Path, carpeta_destino: Path) -> None:
        """Mueve el ZIP a carpeta_destino (la crea si no existe)."""
        import shutil
        carpeta_destino.mkdir(parents=True, exist_ok=True)
        shutil.move(str(zip_path), str(carpeta_destino / zip_path.name))

    def extraer_zip(self, zip_path: Path, destino: Path) -> int:
        """
        Extrae solo los archivos PDF y XML del ZIP directamente en destino,
        ignorando la estructura de subcarpetas interna.

        Retorna el número de archivos extraídos.
        """
        import zipfile
        destino.mkdir(parents=True, exist_ok=True)
        count = 0
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                suffix = Path(info.filename).suffix.lower()
                if suffix not in (".pdf", ".xml"):
                    continue
                # Extraer con el nombre del archivo solamente, sin subcarpetas
                info.filename = Path(info.filename).name
                zf.extract(info, destino)
                count += 1
        return count

    # ------------------------------------------------------------------ #
    # Plantilla de correo                                                  #
    # ------------------------------------------------------------------ #

    # Fuente Rubik (con fallback a Arial para clientes que no la cargan, p.ej. Outlook desktop).
    _FONT_FAMILY = "'Rubik','Rubik Light',Arial,sans-serif"
    _PARRAFO_STYLE = (
        f"margin:0 0 8pt 0;font-family:{_FONT_FAMILY};font-size:11pt;color:#0F172A;"
    )

    def _envolver_html(self, contenido_html: str) -> str:
        """Envuelve el contenido HTML con <head> que precarga Rubik desde Google Fonts."""
        return (
            "<!DOCTYPE html><html><head>"
            '<meta charset="UTF-8">'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;600;700&display=swap" rel="stylesheet">'
            "<style>"
            f"body,p,div,td,th,span,strong{{font-family:{self._FONT_FAMILY};}}"
            "</style>"
            "</head>"
            f'<body style="font-family:{self._FONT_FAMILY};color:#0F172A;">'
            f'<div style="font-family:{self._FONT_FAMILY};">'
            f"{contenido_html}"
            "</div></body></html>"
        )

    def formatear_cuerpo(
        self,
        rfc: str,
        razon_social: str,
        num_empleado: str,
        nombre_empleado: str,
        num_semana: int,
        fecha_inicio: date,
        fecha_fin: date,
        plantilla: dict | None = None,
    ) -> tuple[str, str]:
        """Retorna (body, content_type). Siempre HTML con tipografía Rubik."""
        import html as _html

        fi = fecha_inicio.strftime("%d/%m/%Y")
        ff = fecha_fin.strftime("%d/%m/%Y")
        variables = {
            "rfc": rfc,
            "razon_social": razon_social,
            "num_empleado": num_empleado,
            "nombre_empleado": nombre_empleado,
            "num_semana": num_semana,
            "fecha_inicio": fi,
            "fecha_fin": ff,
        }

        if not plantilla or not plantilla.get("lineas"):
            lineas_default = [
                "Saludos cordiales",
                "Servicio de entrega de CFDI de recibos electrónicos, emitido y enviado por:",
                f"RFC: {rfc}",
                f"Razón Social: {razon_social}",
                "Datos CFDI del recibo electrónico:",
                f"Nombre empleado: {num_empleado} - {nombre_empleado}",
                f"Período: {num_semana} Semanal del {fi} al {ff} -",
                "Se adjunta el archivo del CFDI correspondiente.",
            ]
            parts = [
                f'<p style="{self._PARRAFO_STYLE}">{_html.escape(t)}</p>'
                for t in lineas_default
            ]
            return self._envolver_html("".join(parts)), "HTML"

        parts: list[str] = []
        for linea in plantilla["lineas"]:
            if not linea.get("visible", True):
                continue
            bold_vars = linea.get("bold_variables", True)
            html_linea = self._render_linea(
                linea.get("texto", ""), variables, bold_vars=bold_vars,
            )
            if linea.get("bold", False):
                parts.append(f'<p style="{self._PARRAFO_STYLE}"><strong>{html_linea}</strong></p>')
            else:
                parts.append(f'<p style="{self._PARRAFO_STYLE}">{html_linea}</p>')

        return self._envolver_html("".join(parts)), "HTML"

    def _render_linea(self, template: str, variables: dict, *, bold_vars: bool) -> str:
        """Devuelve el HTML de una línea sustituyendo variables.

        Si bold_vars es True, cada {variable} se envuelve en <strong>; el texto
        estático se escapa sin formato.
        """
        import html as _html

        out: list[str] = []
        last_end = 0
        for m in _VAR_PATTERN.finditer(template):
            estatico = template[last_end:m.start()]
            if estatico:
                out.append(_html.escape(estatico))
            nombre = m.group(1)
            if nombre in variables:
                valor = _html.escape(str(variables[nombre]))
                out.append(f"<strong>{valor}</strong>" if bold_vars else valor)
            else:
                out.append(_html.escape(m.group(0)))
            last_end = m.end()
        if last_end < len(template):
            out.append(_html.escape(template[last_end:]))
        return "".join(out)

    # ------------------------------------------------------------------ #
    # Envío por Microsoft Graph API                                        #
    # ------------------------------------------------------------------ #

    def enviar_cfdi(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        remitente: str,
        destinatario: str,
        subject: str,
        body: str,
        pdf_path: str,
        xml_path: str,
        content_type: str = "Text",
    ) -> None:
        """
        Envía el correo con los archivos CFDI adjuntos usando Microsoft Graph API.

        Lanza RuntimeError si el envío falla.
        """
        import msal
        import requests

        if not tenant_id or not client_id or not client_secret:
            raise RuntimeError(
                "Credenciales de Graph API incompletas. "
                "Abre ⚙ y completa Tenant ID, Client ID y Client Secret."
            )

        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )
        result = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError(
                result.get("error_description", "No se pudo obtener el token de Graph API")
            )

        attachments = []
        for path in [pdf_path, xml_path]:
            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            attachments.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": Path(path).name,
                "contentBytes": content,
            })

        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": content_type, "content": body},
                "toRecipients": [{"emailAddress": {"address": destinatario}}],
                "attachments": attachments,
            }
        }
        headers = {
            "Authorization": f"Bearer {result['access_token']}",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{remitente}/sendMail",
            headers=headers,
            json=payload,
            timeout=60,
        )
        if r.status_code != 202:
            raise RuntimeError(f"Error {r.status_code}: {r.text}")
