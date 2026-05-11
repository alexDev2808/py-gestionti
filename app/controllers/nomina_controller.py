"""Controlador de envío de nómina."""

from __future__ import annotations

from typing import Optional

from app.config.settings import settings
from app.dto.Areas.areas_nomina_config_update_dto import AreasNominaConfigUpdateDTO
from app.dto.Areas.areas_response_dto import AreasResponseDTO
from app.repositories.personal_repository import PersonalRepository
from app.services.areas_service import AreasService
from app.services.historial_nomina_service import HistorialNominaService
from app.services.nomina_service import NominaItem, NominaService


class NominaController:

    def __init__(
        self,
        areas_service: Optional[AreasService] = None,
        nomina_service: Optional[NominaService] = None,
        historial_service: Optional[HistorialNominaService] = None,
        personal_repo: Optional[PersonalRepository] = None,
    ):
        self._areas_service = areas_service or AreasService()
        self._nomina_service = nomina_service or NominaService()
        self._historial_service = historial_service or HistorialNominaService()
        self._personal_repo = personal_repo or PersonalRepository()

    # ------------------------------------------------------------------ #
    # Áreas                                                               #
    # ------------------------------------------------------------------ #

    def cargar_areas(self) -> list[AreasResponseDTO]:
        ok, _, data = self._areas_service.listar_areas()
        if not ok:
            return []
        return list(data or [])

    def guardar_config_area(
        self,
        id_area: int,
        rfc: str,
        correo_remitente: str,
        ruta_cfdi: str,
        prefijo_carpeta: str,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        firma_html: str = "",
        logo_path: str = "",
        logo_width: int = 240,
        nombre_legal: str = "",
    ) -> tuple[bool, str]:
        dto = AreasNominaConfigUpdateDTO(
            id_area=id_area,
            rfc=rfc.strip(),
            correo_remitente=correo_remitente.strip(),
            ruta_cfdi=ruta_cfdi.strip(),
            prefijo_carpeta=prefijo_carpeta.strip(),
            nombre_legal=(nombre_legal or "").strip(),
        )
        ok, msg, _ = self._areas_service.actualizar_nomina_config(dto)
        if not ok:
            return False, msg

        if tenant_id or client_id or client_secret:
            settings.set_nomina_credentials(id_area, tenant_id.strip(), client_id.strip(), client_secret.strip())

        settings.set_nomina_firma(id_area, firma_html or "")
        settings.set_nomina_logo(id_area, (logo_path or "").strip())
        settings.set_nomina_logo_width(id_area, logo_width)

        return True, "Configuración guardada."

    def get_credenciales(self, id_area: int) -> dict:
        return settings.get_nomina_credentials(id_area)

    def get_firma_area(self, id_area: int) -> str:
        return settings.get_nomina_firma(id_area)

    def get_logo_area(self, id_area: int) -> str:
        return settings.get_nomina_logo(id_area)

    def get_logo_width_area(self, id_area: int) -> int:
        return settings.get_nomina_logo_width(id_area)

    def get_plantilla(self) -> dict:
        return settings.get_nomina_plantilla()

    def guardar_plantilla(self, plantilla: dict) -> None:
        settings.set_nomina_plantilla(plantilla)

    # ------------------------------------------------------------------ #
    # Escaneo de carpeta                                                   #
    # ------------------------------------------------------------------ #

    def escanear(self, area: AreasResponseDTO, anio: int, num_semana: int) -> list[NominaItem]:
        """
        Lee la carpeta de CFDIs, empareja archivos con empleados de la BD
        y devuelve la lista de NominaItem con su estado.
        """
        if not area.ruta_cfdi or not area.prefijo_carpeta:
            raise ValueError("El área no tiene configurada la ruta de CFDIs.")

        carpeta = self._nomina_service.construir_ruta(
            area.ruta_cfdi, area.prefijo_carpeta, anio, num_semana
        )
        pares = self._nomina_service.scan_carpeta(carpeta)

        es_logym = "logym" in area.nombre.lower()
        items: list[NominaItem] = []
        for pdf_path, xml_path, num_empleado in pares:
            # Logym: 141 → 0141L  |  MBancor: 141 → 141
            num_empleado_db = f"0{num_empleado}L" if es_logym else num_empleado
            personal = self._personal_repo.get_by_num_empleado(num_empleado_db)
            if not personal:
                items.append(NominaItem(
                    num_empleado=num_empleado_db,
                    nombre_empleado="(no encontrado en BD)",
                    correo="",
                    pdf_path=str(pdf_path),
                    xml_path=str(xml_path) if xml_path else "",
                    pdf_nombre=pdf_path.name,
                    xml_nombre=xml_path.name if xml_path else "",
                    anio=anio,
                    num_semana=num_semana,
                    estado="sin_empleado",
                ))
                continue

            nombre = f"{personal.nombres} {personal.apellido_paterno} {personal.apellido_materno}".strip()
            correo_envio = personal.correo_nomina or ""

            if not xml_path:
                estado = "sin_xml"
            elif not correo_envio:
                estado = "sin_correo"
            else:
                estado = "listo"

            items.append(NominaItem(
                num_empleado=num_empleado_db,
                nombre_empleado=nombre,
                correo=correo_envio,
                pdf_path=str(pdf_path),
                xml_path=str(xml_path) if xml_path else "",
                pdf_nombre=pdf_path.name,
                xml_nombre=xml_path.name if xml_path else "",
                anio=anio,
                num_semana=num_semana,
                estado=estado,
            ))

        # Sin correo primero, luego listos, después errores
        _orden = {"sin_correo": 0, "listo": 1, "sin_xml": 2, "sin_empleado": 3}
        items.sort(key=lambda i: _orden.get(i.estado, 9))
        return items

    # ------------------------------------------------------------------ #
    # Edición de correo del empleado                                       #
    # ------------------------------------------------------------------ #

    def actualizar_correo_empleado(self, num_empleado: str, nuevo_correo: str) -> tuple[bool, str]:
        """Actualiza el correo de nómina (correo_nomina) del empleado en la BD."""
        correo = (nuevo_correo or "").strip()
        if not correo:
            return False, "El correo no puede estar vacío."
        if "@" not in correo or "." not in correo.split("@")[-1]:
            return False, "Formato de correo inválido."
        try:
            ok = self._personal_repo.update_correo_nomina(num_empleado, correo)
            if not ok:
                return False, "No se encontró el empleado."
            return True, "Correo actualizado."
        except Exception as exc:
            return False, str(exc)

    # ------------------------------------------------------------------ #
    # Envío                                                                #
    # ------------------------------------------------------------------ #

    def enviar_item(
        self,
        area: AreasResponseDTO,
        item: NominaItem,
    ) -> tuple[bool, str]:
        """Envía un CFDI y registra el resultado en el historial."""
        creds = self.get_credenciales(area.id_area)
        plantilla = settings.get_nomina_plantilla()

        fecha_inicio, fecha_fin = self._nomina_service.calcular_periodo(item.anio, item.num_semana)
        # Razón social fiscal viene de Areas.nombre_legal (e.g. "Manufacturas Bancor S.A. de C.V.").
        # Si no está configurado, cae al nombre corto como fallback.
        razon_social = (area.nombre_legal or "").strip() or area.nombre

        subject_tpl = plantilla.get("subject", "CFDI Nómina Semana {num_semana} - {num_empleado} {nombre_empleado}")
        try:
            subject = subject_tpl.format(
                num_semana=item.num_semana,
                num_empleado=item.num_empleado,
                nombre_empleado=item.nombre_empleado,
                rfc=area.rfc or "",
                razon_social=razon_social,
            )
        except (KeyError, ValueError):
            subject = subject_tpl

        from pathlib import Path as _P
        logo_path = settings.get_nomina_logo(area.id_area)
        tiene_logo = bool(logo_path) and _P(logo_path).exists()
        logo_width = settings.get_nomina_logo_width(area.id_area)

        body, content_type = self._nomina_service.formatear_cuerpo(
            rfc=area.rfc or "",
            razon_social=razon_social,
            num_empleado=item.num_empleado,
            nombre_empleado=item.nombre_empleado,
            num_semana=item.num_semana,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            plantilla=plantilla,
            firma_html=settings.get_nomina_firma(area.id_area),
            tiene_logo=tiene_logo,
            logo_width=logo_width,
        )

        try:
            self._nomina_service.enviar_cfdi(
                tenant_id=creds.get("tenant_id", ""),
                client_id=creds.get("client_id", ""),
                client_secret=creds.get("client_secret", ""),
                remitente=area.correo_remitente or "",
                destinatario=item.correo,
                subject=subject,
                body=body,
                pdf_path=item.pdf_path,
                xml_path=item.xml_path,
                content_type=content_type,
                logo_path=logo_path if tiene_logo else "",
            )
            self._historial_service.registrar(
                num_semana=item.num_semana,
                anio=item.anio,
                razon_social=area.nombre,
                num_empleado=item.num_empleado,
                nombre_empleado=item.nombre_empleado,
                nombre_pdf=item.pdf_nombre,
                nombre_xml=item.xml_nombre,
                estatus="Enviado",
            )
            return True, "Enviado"
        except Exception as exc:
            error_msg = str(exc)
            self._historial_service.registrar(
                num_semana=item.num_semana,
                anio=item.anio,
                razon_social=area.nombre,
                num_empleado=item.num_empleado,
                nombre_empleado=item.nombre_empleado,
                nombre_pdf=item.pdf_nombre,
                nombre_xml=item.xml_nombre,
                estatus="Error",
                error_detalle=error_msg[:500],
            )
            return False, error_msg
