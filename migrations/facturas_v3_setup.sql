-- ============================================================
-- Facturas v3: configuración por cliente (ruta de descarga + plantilla de correo)
-- Ejecutar después de facturas_v2_setup.sql
-- ============================================================

ALTER TABLE FacturaClientes ADD
    ruta_descarga  VARCHAR(500) NULL,
    email_asunto   VARCHAR(300) NULL,
    email_cuerpo   VARCHAR(MAX) NULL;
