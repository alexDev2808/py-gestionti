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

## Dependencias Principales

| Paquete | Uso |
|---------|-----|
| `flet 0.84.0` | Framework de interfaz de usuario |
| `pyodbc` | Conexión a SQL Server |
| `msal` | Autenticación OAuth2 con Microsoft Graph API |
| `requests` | Envío de correos vía Graph API |
| `python-dotenv` | Variables de entorno en desarrollo |

## Troubleshooting

**`pyodbc.OperationalError: 08001`** — SQL Server no responde. Verificar que el servicio está activo y las credenciales en `.env` o `config.json`.

**`AADSTS7000216` al enviar nómina** — Client Secret vacío. Abrir ⚙ en la vista de nómina y reingresar el Client Secret.

**`ErrorAccessDenied` (403) al enviar nómina** — El permiso `Mail.Send` no tiene admin consent en el tenant. Ir a Entra ID → App registrations → API permissions → Grant admin consent.

**`ErrorInvalidUser` (404) al enviar nómina** — El correo remitente no existe o no tiene licencia en el tenant configurado.
