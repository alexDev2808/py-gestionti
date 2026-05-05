"""Servicio de nómina: parseo de archivos CFDI, cálculo de períodos y envío por Graph API."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional


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

    def formatear_cuerpo(
        self,
        rfc: str,
        razon_social: str,
        num_empleado: str,
        nombre_empleado: str,
        num_semana: int,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> str:
        fi = fecha_inicio.strftime("%d/%m/%Y")
        ff = fecha_fin.strftime("%d/%m/%Y")
        return (
            "Saludos cordiales\n"
            "Servicio de entrega de CFDI de recibos electrónicos, emitido y enviado por:\n"
            f"RFC: {rfc}\n"
            f"Razón Social: {razon_social}\n"
            "Datos CFDI del recibo electrónico:\n"
            f"Nombre empleado: {num_empleado} - {nombre_empleado}\n"
            f"Período: {num_semana} Semanal del {fi} al {ff} -\n"
            "Se adjunta el archivo del CFDI correspondiente."
        )

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
                "body": {"contentType": "Text", "content": body},
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
