-- ============================================================
-- Facturas v2: campos específicos de Telcel + destinatarios por cliente
-- Ejecutar después de facturas_setup.sql
-- ============================================================

-- 1. Nuevos campos en Facturas
ALTER TABLE Facturas ADD
    fecha_corte        DATETIME      NULL,
    cuenta             VARCHAR(50)   NULL,
    linea              VARCHAR(30)   NULL,
    fecha_limite_pago  DATETIME      NULL,
    convenio           VARCHAR(50)   NULL,
    referencia_pago    VARCHAR(100)  NULL,
    mes                VARCHAR(20)   NULL,
    anio               INT           NULL,
    destinatarios      VARCHAR(MAX)  NULL,
    error_envio        VARCHAR(500)  NULL;

CREATE INDEX IX_Facturas_Cuenta ON Facturas(cuenta);
CREATE INDEX IX_Facturas_Anio_Mes ON Facturas(anio, mes);

-- 2. Lista de destinatarios fijos por cliente (LOGYM, MANUFACTURAS BANCOR, etc.)
ALTER TABLE FacturaClientes ADD
    correos_destino VARCHAR(MAX) NULL;
