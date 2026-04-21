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
- Navegador web moderno (Chrome, Firefox, Edge, Safari)
- Acceso a internet (para comunicarse con la API del catálogo y la API de Claude)
- Una **clave de API de CKAN** con permisos de escritura sobre los datasets que querés editar
- La aplicación debe ser servida desde un dominio que tenga acceso al catálogo (para evitar restricciones CORS)

### Uso rápido

1. Descargá o cloná este repositorio
2. Abrí `index.html` en tu navegador (o deployalo en un servidor web)
3. Ingresá tu **clave de API CKAN** en el campo correspondiente y hacé clic en "Guardar"
4. Ingresá el **ID del conjunto de datos** (UUID o nombre-slug) y hacé clic en "Analizar"
5. Revisá las sugerencias generadas en cada tab y aplicá los cambios que considerés pertinentes

```
# Clonar el repositorio
git clone https://github.com/tu-usuario/ckan-metadata-assistant.git

# Abrir en el navegador (sin servidor)
open index.html

# O servir con cualquier servidor HTTP simple
npx serve .
python3 -m http.server 8080
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

## ⚠️ Consideraciones CORS

La API de CKAN puede rechazar peticiones desde ciertos orígenes por restricciones de CORS. Si recibís el error `Failed to fetch`, el panel de debug mostrará las causas probables:

- La aplicación se está abriendo como archivo local (`file://`) — servila desde un servidor HTTP
- El servidor del catálogo no permite el origen desde el que estás haciendo la petición
- Sin conectividad con el servidor del catálogo

**Solución recomendada**: deployar la aplicación en el mismo dominio del catálogo o en un dominio que esté en la lista de orígenes permitidos por la configuración CORS del servidor CKAN.

---

## 🔒 Seguridad

- La **clave de API** se almacena únicamente en memoria de sesión (variable JavaScript) y **nunca se persiste** en localStorage, cookies ni se envía a ningún servidor que no sea el propio catálogo CKAN
- En el panel de debug, la API Key se **enmascara automáticamente** como `●●●●●●●●` en los headers mostrados
- La aplicación no tiene backend propio — toda la comunicación es directa entre el navegador y las APIs de CKAN y Anthropic

---

## 🛠 Personalización

### Apuntar a otro catálogo CKAN

Editá la constante al inicio del bloque `<script>`:

```javascript
const CKAN_BASE = 'https://mi-otro-catalogo.gub.uy';
```

### Cambiar el entorno (test → producción)

```javascript
// Ambiente de test
const CKAN_BASE = 'https://test.catalogodatos.gub.uy';

// Producción
const CKAN_BASE = 'https://catalogodatos.gub.uy';
```

### Cambiar el modelo de IA

```javascript
const CLAUDE_MDL = 'claude-sonnet-4-20250514'; // Podés cambiar por otro modelo de Anthropic
```

---

## 📁 Estructura del repositorio

```
.
├── index.html          # Aplicación completa (autocontenida)
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
