-- ============================================================
-- Módulo Facturas: catálogos jerárquicos y registro de facturas
-- ============================================================

-- 1. Filiales (México, Tlaxcala)
CREATE TABLE Filiales (
    id_filial   INT IDENTITY(1,1) PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    creado_en   DATETIME NOT NULL DEFAULT GETDATE()
);

-- 2. Proveedores de facturación (Telcel, Alestra, Megacable, AT&T)
CREATE TABLE FacturaProveedores (
    id_factprov INT IDENTITY(1,1) PRIMARY KEY,
    id_filial   INT NOT NULL,
    nombre      VARCHAR(150) NOT NULL,
    creado_en   DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_FactProv_Filial FOREIGN KEY (id_filial)
        REFERENCES Filiales(id_filial) ON DELETE CASCADE,
    CONSTRAINT UK_FactProv_Filial_Nombre UNIQUE (id_filial, nombre)
);

-- 3. Clientes / subcuentas (LOGYM, MANUFACTURAS BANCOR)
CREATE TABLE FacturaClientes (
    id_factcli  INT IDENTITY(1,1) PRIMARY KEY,
    id_factprov INT NOT NULL,
    nombre      VARCHAR(150) NOT NULL,
    creado_en   DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_FactCli_FactProv FOREIGN KEY (id_factprov)
        REFERENCES FacturaProveedores(id_factprov) ON DELETE CASCADE,
    CONSTRAINT UK_FactCli_Prov_Nombre UNIQUE (id_factprov, nombre)
);

-- 4. Facturas
CREATE TABLE Facturas (
    id_factura      INT IDENTITY(1,1) PRIMARY KEY,
    id_factprov     INT NOT NULL,
    id_factcli      INT NULL,
    periodo         VARCHAR(7)   NOT NULL,            -- 'YYYY-MM'
    numero_factura  VARCHAR(100) NULL,
    monto           DECIMAL(18,2) NULL,
    ruta_pdf        VARCHAR(500) NULL,
    ruta_xml        VARCHAR(500) NULL,
    fecha_descarga  DATETIME     NULL,
    fecha_envio     DATETIME     NULL,
    destinatario    VARCHAR(200) NULL,
    estado          VARCHAR(20)  NOT NULL DEFAULT 'pendiente',  -- pendiente | descargada | enviada
    notas           VARCHAR(500) NULL,
    creado_por      VARCHAR(50)  NULL,
    creado_en       DATETIME     NOT NULL DEFAULT GETDATE(),
    actualizado_en  DATETIME     NULL,
    CONSTRAINT FK_Factura_FactProv FOREIGN KEY (id_factprov)
        REFERENCES FacturaProveedores(id_factprov),
    CONSTRAINT FK_Factura_FactCli FOREIGN KEY (id_factcli)
        REFERENCES FacturaClientes(id_factcli)
);

CREATE INDEX IX_Facturas_Periodo  ON Facturas(periodo);
CREATE INDEX IX_Facturas_FactProv ON Facturas(id_factprov);
CREATE INDEX IX_Facturas_FactCli  ON Facturas(id_factcli);
CREATE INDEX IX_Facturas_Estado   ON Facturas(estado);

-- ============================================================
-- Seeds iniciales
-- ============================================================
INSERT INTO Filiales (nombre) VALUES ('M.BANCOR'), ('TAURUS');

INSERT INTO FacturaProveedores (id_filial, nombre)
SELECT id_filial, 'Alestra' FROM Filiales WHERE nombre = 'M.BANCOR' UNION ALL
SELECT id_filial, 'AT&T'    FROM Filiales WHERE nombre = 'M.BANCOR' UNION ALL
SELECT id_filial, 'Telcel'  FROM Filiales WHERE nombre = 'M.BANCOR' UNION ALL
SELECT id_filial, 'Telcel'  FROM Filiales WHERE nombre = 'TAURUS';

INSERT INTO FacturaClientes (id_factprov, nombre)
SELECT p.id_factprov, 'Tlaxcala'
FROM FacturaProveedores p
JOIN Filiales f ON p.id_filial = f.id_filial
WHERE f.nombre = 'M.BANCOR' AND p.nombre = 'Telcel'
UNION ALL
SELECT p.id_factprov, 'México'
FROM FacturaProveedores p
JOIN Filiales f ON p.id_filial = f.id_filial
WHERE f.nombre = 'TAURUS' AND p.nombre = 'Telcel';
