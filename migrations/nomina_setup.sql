-- Agregar campos de nómina a la tabla Areas
ALTER TABLE Areas ADD
    rfc              VARCHAR(20)  NULL,
    correo_remitente VARCHAR(150) NULL,
    ruta_cfdi        VARCHAR(500) NULL,
    prefijo_carpeta  VARCHAR(5)   NULL;

-- Tabla de historial de envíos de nómina
CREATE TABLE HistorialNomina (
    id               INT           IDENTITY(1,1) PRIMARY KEY,
    num_semana       INT           NOT NULL,
    anio             INT           NOT NULL,
    razon_social     VARCHAR(100)  NOT NULL,
    num_empleado     VARCHAR(20)   NOT NULL,
    nombre_empleado  VARCHAR(200)  NOT NULL,
    nombre_pdf       VARCHAR(300)  NOT NULL,
    nombre_xml       VARCHAR(300)  NOT NULL,
    fecha_hora_envio DATETIME      NOT NULL,
    estatus          VARCHAR(20)   NOT NULL,  -- 'Enviado' | 'Error' | 'Sin correo'
    error_detalle    VARCHAR(500)  NULL
);
