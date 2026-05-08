# GestionTI - Sistema de Gestión Integral

Aplicación de escritorio para gestionar áreas, departamentos, personal, cargos, puestos, responsabilidades y envío de recibos de nómina (CFDI). Desarrollada con **Flet** (UI) y **SQL Server** (Base de datos).

## Requisitos Previos

- **Python 3.10 o superior**
- **SQL Server 2019 o posterior** con ODBC Driver 18 instalado
- **Windows 10/11** (el cifrado de credenciales usa Windows DPAPI)

## Instalación y Ejecución

### 1. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar la base de datos

Copia `.env.example` a `.env` y completa los valores:

```bash
copy .env.example .env
```

```env
DB_SERVER=localhost
DB_NAME=DBTAUMEX
DB_USER=sa
DB_PASSWORD=tu_contraseña
DB_DRIVER=ODBC Driver 18 for SQL Server
```

Al ejecutar la aplicación por primera vez aparece el asistente de configuración de BD.

### 3. Ejecutar

```bash
python main.py
```

## Estructura del Proyecto

```
gestionti/
├── app/
│   ├── components/          # Componentes reutilizables de la UI
│   ├── config/              # Configuración (BD, tema, settings)
│   ├── controllers/         # Lógica de controladores
│   ├── dto/                 # Objetos de transferencia de datos
│   ├── models/              # Modelos de datos
│   ├── repositories/        # Acceso a datos (SQL Server)
│   ├── services/            # Servicios de negocio
│   └── views/               # Vistas de la interfaz
├── migrations/              # Scripts SQL de migración
├── scripts/                 # Utilidades de diagnóstico (PDFs, etc.)
├── main.py                  # Punto de entrada
├── requirements.txt         # Dependencias
└── .env.example             # Plantilla de variables de entorno
```

## Módulo de Nómina (CFDI)

Permite enviar recibos electrónicos de nómina (PDF + XML) por correo usando **Microsoft Graph API**.

### Configuración por Razón Social

Cada razón social (MBancor / Logym) requiere un registro de aplicación en Azure/Entra ID con:

- `Mail.Send` como permiso de tipo **Application** (no Delegated)
- Admin consent otorgado en el tenant correspondiente

Los datos se configuran desde la vista **Envío de Nómina → ⚙**:

| Campo | Descripción |
|-------|-------------|
| RFC | RFC de la empresa emisora |
| Correo remitente | Buzón desde el que se envía (debe existir en el tenant) |
| Ruta base CFDI | Carpeta raíz donde se almacenan los archivos, ej. `D:\nominas\MBancor` |
| Prefijo carpeta | Prefijo de la carpeta semanal, ej. `MB` o `LG` |
| Tenant ID | ID del tenant de Azure AD |
| Client ID | ID de la aplicación registrada |
| Client Secret | Secreto de la aplicación (se cifra con DPAPI al guardar) |

### Plantilla del correo

El botón ✉ abre el editor de plantilla donde se puede personalizar el asunto y cada línea del cuerpo del correo. Admite las siguientes variables que se resuelven por empleado en el momento del envío:

| Variable | Valor |
|----------|-------|
| `{rfc}` | RFC de la empresa emisora |
| `{razon_social}` | Nombre del área/razón social |
| `{num_empleado}` | Número de empleado |
| `{nombre_empleado}` | Nombre completo del empleado |
| `{num_semana}` | Número de semana |
| `{fecha_inicio}` | Fecha de inicio del período (dd/mm/aaaa) |
| `{fecha_fin}` | Fecha de fin del período (dd/mm/aaaa) |

La plantilla se guarda en `%APPDATA%\GestionTI\config.json` y persiste entre sesiones.

### Flujo de envío

1. Colocar el archivo ZIP con los CFDI en `[ruta_base]\[año]\`
2. En la app: seleccionar razón social, año y semana → **Escanear**
3. El sistema detecta el ZIP, crea la carpeta `[prefijo][semana]`, extrae los PDF/XML y mueve el ZIP a `[año]\Archivos_zip\`
4. Se muestra la tabla de empleados con estado de correo registrado
5. Clic en **Enviar todos** — el resultado queda registrado en el historial

### Nomenclatura de archivos

```
RE_[num_razon]_Semanal_[año]_[semana]_[num_empleado]_[extra].pdf
RE_[num_razon]_Semanal_[año]_[semana]_[num_empleado]_[extra].xml
```

### Seguridad de credenciales

Las credenciales de Graph API (Client Secret) se cifran con **Windows DPAPI** antes de almacenarse en `%APPDATA%\GestionTI\config.json`. Solo el usuario de Windows que las guardó puede descifrarlas.

## Módulo de Facturas

Importa y administra facturas de servicios (Telcel, Alestra) desde archivos ZIP o carpetas con PDFs/XMLs. Extrae automáticamente los campos clave del PDF, mueve los archivos a una ruta estructurada por año/mes y registra cada factura en BD.

### Proveedores soportados

| Proveedor | Campos extraídos del PDF | Numeración interna |
|-----------|-------------------------|-------------------|
| **Telcel** | No. de Cuenta, Teléfono (línea), Fecha de Corte, Total, Fecha límite, Convenio BBVA, Referencia BBVA | `numero_factura = LC-{cuenta}` |
| **Alestra** | No. de factura, Número de cliente, Número de cuenta, Fecha de expedición, Fecha límite de pago, Saldo a pagar | `numero_factura = FAB...` (extraído del PDF) |

La extracción se hace con `pdfplumber` aplicando estrategias en cascada (tabular por posición de columna → regex inline → búsqueda línea-por-línea), lo que tolera las distintas formas en que pdfplumber serializa cada PDF.

### Flujo de importación

1. En el árbol seleccionar **Filial → Proveedor → Cliente**.
2. Botón **Importar** → elegir un ZIP (o carpeta con PDFs/XMLs) y el mes/año.
3. Cada PDF se parsea, se renombra como `FACTURA_{cuenta}.pdf` (en el caso del ZIP) y se guarda en `[ruta_descarga]\{año}\{mes}`. Si hay XML pareado se renombra a `CFDI_{cuenta}.xml`.
4. Al final aparece un resumen tipo *"X importadas · Y complementos archivados · Z con error"*.

### Complementos de pago (solo Alestra)

Los archivos cuyo nombre empieza con `CP` (ej. `CPRBM1169478.pdf`) se reconocen como **complementos de pago** y se archivan en la misma carpeta destino sin extraer campos ni crear registro en BD. Su XML pareado por nombre exacto también se mueve junto al PDF.

### Layout de columnas según proveedor

La tabla muestra columnas distintas según el proveedor en scope:

- **Telcel**: ID · Fecha Corte · Mes · Año · **Cuenta · Línea** · Total · F. Límite · **Convenio · Referencia** · Descarga · Destinatarios · Estatus
- **Alestra**: ID · Fecha Corte · Mes · Año · **No. de factura · Número de cliente · Número de cuenta** · Total · F. Límite · Descarga · Destinatarios · Estatus

Sin proveedor seleccionado (raíz / filial / "Todas las facturas") se aplica el layout de Telcel por defecto.

### Diagnóstico de extracción

Si un PDF no extrae los campos esperados, el script `scripts/diagnose_factura_pdf.py` imprime el texto crudo que `pdfplumber` produce para ese archivo:

```bash
python scripts\diagnose_factura_pdf.py "C:\ruta\al\factura.pdf"
```

Útil para ver el orden real (tabular vs. label-then-value) y ajustar regex/estrategias del extractor sin tocar otros proveedores.

## Dependencias Principales

| Paquete | Uso |
|---------|-----|
| `flet 0.84.0` | Framework de interfaz de usuario |
| `pyodbc` | Conexión a SQL Server |
| `msal` | Autenticación OAuth2 con Microsoft Graph API |
| `requests` | Envío de correos vía Graph API |
| `pdfplumber` | Extracción de campos desde PDFs de facturas |
| `openpyxl` | Lectura/escritura de archivos Excel |
| `python-dotenv` | Variables de entorno en desarrollo |

## Troubleshooting

**`pyodbc.OperationalError: 08001`** — SQL Server no responde. Verificar que el servicio está activo y las credenciales en `.env` o `config.json`.

**`AADSTS7000216` al enviar nómina** — Client Secret vacío. Abrir ⚙ en la vista de nómina y reingresar el Client Secret.

**`ErrorAccessDenied` (403) al enviar nómina** — El permiso `Mail.Send` no tiene admin consent en el tenant. Ir a Entra ID → App registrations → API permissions → Grant admin consent.

**`ErrorInvalidUser` (404) al enviar nómina** — El correo remitente no existe o no tiene licencia en el tenant configurado.

**`No se pudo extraer 'No. de Cuenta'` al importar factura** — El PDF tiene un layout distinto al esperado. Correr `python scripts\diagnose_factura_pdf.py "ruta\al\pdf"` para ver el texto crudo y compartirlo, así se ajustan los patrones del extractor del proveedor afectado.

**`pdfplumber no está instalado`** — Falta la dependencia. Ejecutar `pip install -r requirements.txt` (incluye `pdfplumber`).
