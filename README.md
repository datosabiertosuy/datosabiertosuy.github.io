# 🤖 Asistente de Metadatos con IA — Catálogo de Datos Abiertos Uruguay

Herramienta web para analizar y mejorar automáticamente los metadatos de conjuntos de datos publicados en el [Catálogo de Datos Abiertos de Uruguay](https://catalogodatos.gub.uy), utilizando Inteligencia Artificial (Claude de Anthropic) e integrándose con la API de CKAN.

---

## 📋 Descripción

Esta aplicación es una página web autocontenida (`index.html`) que replica el *look & feel* del Catálogo de Datos Abiertos uruguayo y permite a los administradores de datos:

- Obtener los metadatos de un conjunto de datos directamente desde la API de CKAN
- Visualizar sugerencias de mejora generadas por IA para título, descripción y etiquetas
- Aplicar esos cambios directamente sobre el catálogo con un solo clic
- Analizar y mejorar las descripciones de los recursos (archivos) asociados al dataset
- Analizar archivos de metadatos en formato JSON (archivos que comienzan con `Metadatos`) y generar una versión mejorada descargable
- Inspeccionar todas las llamadas HTTP a la API CKAN mediante un panel de debug integrado

---

## ✨ Funcionalidades

### Tab 1 — Metadatos del Dataset
- Muestra el **título**, **descripción** y **etiquetas** actuales del conjunto de datos
- Genera sugerencias de mejora para cada campo usando IA (Claude)
- Las sugerencias se muestran en color violeta diferenciado del valor actual
- Botón individual por campo para **aplicar el cambio** directamente en el catálogo vía `package_patch`

### Tab 2 — Recursos
- Lista todos los recursos (archivos) asociados al dataset
- Cada recurso se identifica por su **ID único (UUID)**, no por posición
- Genera sugerencias de mejora para la descripción de cada recurso
- Botón individual por recurso para **aplicar el cambio** vía `resource_patch`

### Tab 3 — Metadatos JSON
- Detecta automáticamente archivos cuyo nombre comienza con `Metadatos` y tienen formato `JSON`
- Analiza el contenido del archivo junto con los recursos de datos relacionados
- Genera una versión mejorada del JSON con:
  - Mejores descripciones de columnas/campos en español
  - Tipos de dato inferidos
  - Ejemplos de valores plausibles
- Permite **descargar el JSON mejorado**
- Si no existe ningún archivo de metadatos JSON, muestra un mensaje claro indicándolo

### 🔍 Panel de Debug
- Toggle para activar/desactivar el modo debug en cualquier momento
- Se activa automáticamente al hacer la primera llamada al catálogo
- Muestra un log en tiempo real de cada llamada a la API CKAN con:
  - Timestamp exacto
  - Método HTTP (`GET` / `POST`) con código de color
  - Endpoint y URL completa llamada
  - Estado de la respuesta (HTTP status, OK/Error)
  - Tiempo de respuesta en milisegundos
- Cada entrada es **expandible** para ver:
  - URL completa
  - Headers enviados (la API Key se enmascara automáticamente)
  - Body de la request (en POST)
  - Respuesta JSON completa del servidor
- Filtros por estado: Todas / Solo OK / Solo Error
- Botón para **copiar el log** completo al portapapeles
- Diagnóstico específico para errores `Failed to fetch` (CORS, conectividad, etc.)

---

## 🚀 Instalación y uso

### Requisitos
- Python 3.8 o superior
- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- Acceso a internet (para comunicarse con la API del catálogo y la API de Claude)
- Una **clave de API de CKAN** con permisos de escritura sobre los datasets que querés editar

### Por qué se necesita el proxy

La aplicación llama directamente a la API de CKAN desde el browser. Los navegadores modernos bloquean este tipo de peticiones cross-origin por la política CORS, generando el error `Failed to fetch`. El proxy Python resuelve esto actuando como intermediario: recibe las peticiones del browser, las reenvía al catálogo, y agrega el header `Access-Control-Allow-Origin: *` en la respuesta.

```
Browser  ──→  proxy.py (:8080)  ──→  test.catalogodatos.gub.uy
         ←──  + CORS headers   ←──
```

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/ckan-metadata-assistant.git
cd ckan-metadata-assistant

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Iniciar el proxy
python proxy.py
```

### Uso

1. Iniciá el proxy: `python proxy.py`
2. Abrí **http://127.0.0.1:8080** en tu navegador
3. Ingresá tu **clave de API CKAN** y hacé clic en "Guardar"
4. Ingresá el **ID del conjunto de datos** (UUID o nombre-slug) y hacé clic en "Analizar"
5. Revisá las sugerencias generadas en cada tab y aplicá los cambios que considerés pertinentes

### Opciones del proxy

```bash
# Puerto por defecto (8080)
python proxy.py

# Puerto personalizado
python proxy.py --port 3000

# Escuchar en todas las interfaces (acceso desde la red local)
python proxy.py --host 0.0.0.0 --port 8080

# Apuntar a otro catálogo CKAN
python proxy.py --ckan https://catalogodatos.gub.uy

# Ver todas las opciones
python proxy.py --help
```

### ¿Dónde encuentro mi API Key de CKAN?

1. Iniciá sesión en el [Catálogo de Datos Abiertos](https://catalogodatos.gub.uy)
2. Hacé clic en tu nombre de usuario (esquina superior derecha)
3. En tu perfil, buscá la sección **"Clave API"** o **"API Key"**
4. Copiá la clave y pegala en el campo correspondiente de la aplicación

### ¿Cómo obtengo el ID del dataset?

Podés usar cualquiera de estos dos formatos:

| Formato | Ejemplo |
|--------|---------|
| **Nombre-slug** (aparece en la URL del dataset) | `encuestas-de-hogares` |
| **UUID** (identificador único) | `a3f1b2c4-1234-5678-abcd-ef0123456789` |

El UUID lo encontrás en la página del dataset → pestaña **"Información adicional"** → campo `Identificador`.

---

## 🏗 Arquitectura

```
index.html
├── CSS embebido (sin dependencias externas críticas)
│   ├── Replica fiel del design system del catálogo uruguayo
│   └── Estilos propios de la aplicación y panel de debug
├── HTML
│   ├── Header idéntico al catálogo (estructura BEM)
│   ├── Breadcrumb
│   ├── Sección de configuración (API Key + ID dataset)
│   ├── Panel de Debug (toggle + log de llamadas)
│   ├── Tabs: Metadatos / Recursos / JSON
│   └── Footer idéntico al catálogo
└── JavaScript (vanilla, sin frameworks)
    ├── ckanFetch()     — wrapper de fetch con logging automático
    ├── ckanGet/Post()  — llamadas GET y POST a la API CKAN
    ├── claude()        — llamadas a la API de Anthropic
    ├── renderMeta()    — Tab 1: metadatos del dataset
    ├── renderResources() — Tab 2: recursos del dataset
    ├── renderJsonTab() — Tab 3: análisis de archivos JSON
    └── Debug Engine    — log, filtros, expand/collapse, copy
```

### APIs utilizadas

| API | Endpoints usados | Propósito |
|-----|-----------------|-----------|
| **CKAN** (`/api/3/action/`) | `package_show` | Obtener metadatos del dataset |
| **CKAN** | `package_patch` | Actualizar título, descripción, etiquetas |
| **CKAN** | `resource_patch` | Actualizar descripción de recursos |
| **Anthropic** (`/v1/messages`) | `claude-sonnet-4-20250514` | Generar sugerencias de mejora con IA |

---

## ⚠️ CORS y el proxy

El proxy Python incluido resuelve automáticamente las restricciones CORS agregando el header `Access-Control-Allow-Origin: *` en todas las respuestas de la API CKAN. Mientras uses la aplicación a través del proxy (`http://127.0.0.1:8080`), no deberías tener problemas.

Si aun así recibís el error `Failed to fetch`, el **panel de debug** (toggle en la interfaz) mostrará el detalle exacto:

- La URL completa que se intentó llamar
- El código de error HTTP
- Las causas más probables: proxy no iniciado, puerto incorrecto, sin conectividad con el catálogo

Si necesitás acceder desde otra máquina de la red, iniciá el proxy con:
```bash
python proxy.py --host 0.0.0.0
```
Y accedé desde `http://<IP-del-servidor>:8080`.

---

## 🔒 Seguridad

- La **clave de API** se almacena únicamente en memoria de sesión (variable JavaScript) y **nunca se persiste** en localStorage, cookies ni se envía a ningún servidor que no sea el propio catálogo CKAN
- En el panel de debug, la API Key se **enmascara automáticamente** como `●●●●●●●●` en los headers mostrados
- La aplicación no tiene backend propio — toda la comunicación es directa entre el navegador y las APIs de CKAN y Anthropic

---

## 🛠 Personalización

### Apuntar a otro catálogo CKAN

Desde la línea de comandos del proxy:
```bash
python proxy.py --ckan https://catalogodatos.gub.uy
```

O editando la constante en `index.html` (solo si no usás el proxy):
```javascript
const CKAN_BASE = 'http://127.0.0.1:8080';  // con proxy local
const CKAN_BASE = '';                         // URL relativa (default, proxy en mismo host)
```

### Cambiar el entorno (test → producción)

```bash
# Test
python proxy.py --ckan https://test.catalogodatos.gub.uy

# Producción
python proxy.py --ckan https://catalogodatos.gub.uy
```

### Cambiar el modelo de IA

En `index.html`:
```javascript
const CLAUDE_MDL = 'claude-sonnet-4-20250514'; // Podés cambiar por otro modelo de Anthropic
```

---

## 📁 Estructura del repositorio

```
.
├── index.html          # Aplicación web (autocontenida, servida por el proxy)
├── proxy.py            # Proxy inverso Python — resuelve CORS
├── requirements.txt    # Dependencias Python (solo 'requests')
└── README.md           # Este archivo
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Hacé un fork del repositorio
2. Creá una rama para tu feature (`git checkout -b feature/mi-mejora`)
3. Commiteá tus cambios (`git commit -m 'Agrego mi mejora'`)
4. Pusheá la rama (`git push origin feature/mi-mejora`)
5. Abrí un Pull Request

---

## 📄 Licencia

Este proyecto es de uso interno para la gestión del Catálogo de Datos Abiertos de Uruguay. Consultar con [AGESIC](https://www.gub.uy/agencia-gobierno-electronico-sociedad-informacion-conocimiento/) para condiciones de uso y distribución.

---

## 🔗 Links relacionados

- [Catálogo de Datos Abiertos — Producción](https://catalogodatos.gub.uy)
- [Catálogo de Datos Abiertos — Test](https://test.catalogodatos.gub.uy)
- [Documentación API CKAN](https://docs.ckan.org/en/latest/api/index.html)
- [Anthropic API](https://docs.anthropic.com)
- [AGESIC — Agencia de Gobierno Electrónico](https://www.gub.uy/agencia-gobierno-electronico-sociedad-informacion-conocimiento/)

---

*Desarrollado como herramienta de apoyo a la gestión de metadatos del Catálogo Nacional de Datos Abiertos de Uruguay.*
