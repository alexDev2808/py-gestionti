# GestionTI - Sistema de Gestión Integral

Aplicación de escritorio para gestionar áreas, departamentos, personal, cargos, puestos y responsabilidades. Desarrollada con **Flet** (UI) y **SQL Server** (Base de datos).

## 📋 Requisitos Previos

- **Python 3.10 o superior**
- **SQL Server 2019 o posterior** (con driver ODBC instalado)
- **pip** (gestor de paquetes de Python)

### Verificar versión de Python

```bash
python --version
```

## 🚀 Instalación y Ejecución

### 1. Clonar o descargar el proyecto

```bash
cd gestionti
```

### 2. Crear entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la base de datos

La aplicación requiere conexión a SQL Server. Existen 3 formas de configurar las credenciales (en orden de prioridad):

#### Opción A: Archivo de configuración persistente (RECOMENDADO para producción)

1. Crear directorio de configuración:
```bash
mkdir %APPDATA%\GestionTI
```

2. Crear archivo `%APPDATA%\GestionTI\config.json`:
```json
{
  "DB_SERVER": "localhost",
  "DB_NAME": "GestionTI",
  "DB_USER": "sa",
  "DB_PASSWORD": "TuContraseña123",
  "DB_DRIVER": "ODBC Driver 17 for SQL Server",
  "DB_ENCRYPT": "yes",
  "DB_TRUST_SERVER_CERTIFICATE": "yes",
  "DB_CONNECTION_TIMEOUT": "30"
}
```

#### Opción B: Variables de entorno o archivo `.env` (RECOMENDADO para desarrollo)

Crear archivo `.env` en la raíz del proyecto:
```env
DB_SERVER=localhost
DB_NAME=GestionTI
DB_USER=sa
DB_PASSWORD=TuContraseña123
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_ENCRYPT=yes
DB_TRUST_SERVER_CERTIFICATE=yes
DB_CONNECTION_TIMEOUT=30
```

#### Opción C: Valores por defecto

Si no configura nada, la aplicación usa valores por defecto (localhost/GestionTI/sa).

### 5. Verificar conexión a la base de datos (Opcional)

```bash
python -c "from app.config.database import test_connection; success, msg = test_connection(); print(msg)"
```

### 6. Ejecutar la aplicación

```bash
python main.py
```

La aplicación se abrirá en una ventana de escritorio.

## 🔐 Credenciales de Acceso

Al iniciar la aplicación, debe ingresar sus credenciales de usuario. Estas se validan contra la base de datos configurada.

## 📁 Estructura del Proyecto

```
gestionti/
├── app/
│   ├── assets/              # Recursos (imágenes, iconos, etc.)
│   ├── components/          # Componentes reutilizables de la UI
│   ├── config/              # Configuración (BD, tema, settings)
│   ├── controllers/         # Lógica de controladores
│   ├── dto/                 # Objetos de transferencia de datos
│   ├── models/              # Modelos de datos
│   ├── navigation/          # Sistema de enrutamiento
│   ├── repositories/        # Acceso a datos
│   ├── services/            # Servicios de negocio
│   ├── utils/               # Utilidades
│   └── views/               # Vistas de la interfaz
├── tests/                   # Pruebas unitarias
├── main.py                  # Punto de entrada
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## 🛠️ Dependencias Principales

- **flet 0.84.0** - Framework de interfaz de usuario
- **pyodbc 5.3.0** - Conexión a SQL Server
- **python-dotenv 1.2.2** - Gestión de variables de entorno
- **httpx 0.28.1** - Cliente HTTP

## ⚙️ Variables de Configuración

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `DB_SERVER` | Servidor SQL Server | `localhost` |
| `DB_NAME` | Nombre de la base de datos | `GestionTI` |
| `DB_USER` | Usuario de SQL Server | `sa` |
| `DB_PASSWORD` | Contraseña de SQL Server | (sin defecto) |
| `DB_DRIVER` | Driver ODBC a usar | `ODBC Driver 17 for SQL Server` |
| `DB_ENCRYPT` | Encriptación de conexión | `yes` |
| `DB_TRUST_SERVER_CERTIFICATE` | Confiar en certificado auto-firmado | `yes` |
| `DB_CONNECTION_TIMEOUT` | Timeout de conexión (segundos) | `30` |

## 🧪 Ejecutar Pruebas

```bash
python -m pytest tests/
```

## 🔧 Troubleshooting

### Error: "pyodbc.OperationalError: ('08001', '[08001]...)"

**Problema**: No puede conectar a SQL Server.

**Soluciones**:
1. Verificar que SQL Server está ejecutándose
2. Verificar las credenciales en `.env` o `config.json`
3. Verificar que el driver ODBC está instalado: `odbcad32.exe`
4. Probar la conexión: `python -c "from app.config.database import test_connection; print(test_connection())"`

### Error: "ModuleNotFoundError: No module named 'flet'"

**Problema**: Dependencias no instaladas.

**Solución**:
```bash
pip install -r requirements.txt
```

### Error: "No module named 'pyodbc'"

**Problema**: pyodbc no está instalado.

**Solución**:
```bash
pip install pyodbc
```

### La aplicación se cierra después del login

**Problema**: Posible error en la base de datos o permisos insuficientes.

**Solución**: Verificar los logs de la aplicación y permisos del usuario en la base de datos.

## 📝 Notas Importantes

- La aplicación requiere **conexión activa** a la base de datos para funcionar
- El sistema incluye **auditoría de acciones** que se registra en la base de datos
- Hay un sistema de **permisos por rol** que controla el acceso a diferentes secciones
- El **monitoreo de conexión** alerta al usuario si se pierde la conexión a la BD

## 🤝 Soporte

Para reportar problemas o sugerencias, contacte al equipo de desarrollo.

---

**Última actualización**: Abril 2026