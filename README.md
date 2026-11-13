# Georreferenciación para la acción

**Observatorio IETS · Colombia · Prototipo local 1.0.0 · 30 de octubre de 2026**

Geoportal y herramienta de trabajo territorial para la continuidad de la atención de enfermedades crónicas no transmisibles (ECNT). Lee **la misma carpeta de microplanificación**, conserva su estructura original de archivos sin alterarla y permite documentar evidencia y acciones territoriales. La entrega incluye el caso de Cali preparado con datos del repositorio real.

---

## Requisitos y preparación

- **Navegador web**: Cualquier navegador moderno con soporte de JavaScript, descargas locales y elemento `<dialog>`.
- **Python (opcional para visualización estática, requerido para servidor y recorte)**: Python 3.12 o superior con las dependencias fijadas en `requirements.txt` (`geopandas`, `pyogrio`, `pyproj`, `shapely`, `pandas`, `numpy`, `pyarrow`, `openpyxl`).
- **Node.js (para pruebas unitarias de frontend)**: Node.js 18+ (utiliza el ejecutor nativo `node --test`).

### Preparación del entorno
En una instalación nueva o clon del repositorio, ejecute una única vez con conexión a internet:
```cmd
INSTALAR.bat
```
Este script crea el entorno virtual local en `.venv/` e instala las dependencias de `requirements.txt` sin alterar la configuración global del sistema.

---

## Modos de inicio

### Modo 1: Con servidor local (Recomendado para trabajo completo)
1. Haga doble clic en **`INICIAR.bat`** (o ejecute `python servidor.py --open` desde la consola).
2. El servidor local se iniciará en `http://127.0.0.1:8516` y abrirá automáticamente la aplicación en su navegador predeterminado.
3. Mantenga abierta la consola durante su sesión y ciérrela con `Ctrl+C` al terminar. El servicio no se expone a la red ni a internet.

### Modo 2: Consulta autónoma sin servidor
Si no dispone de Python o solo desea consultar el escenario cargado de Cali sin procesar nuevas carpetas de microplanificación:
- Abra directamente el archivo **`index.html`** en la raíz (el cual redirige a `app/index.html`).
- La aplicación cargará el recorte inicial de Cali desde `app/js/initial.js` en memoria del navegador.

---

## Cargar la carpeta de microplanificación

1. Inicie la aplicación en modo servidor con **`INICIAR.bat`** y diríjase al módulo **Repositorio**.
2. La ruta por defecto configurada es `D:\00000-PAHO-OMS\0-Priorizacion\COL`, pero puede seleccionar su carpeta principal o utilizar el explorador interactivo (**Explorar carpetas**).
3. Pulse **Leer repositorio**: el sistema inspecciona la carpeta sin modificar, renombrar ni mover ningún archivo original.
4. Revise las capas detectadas, sus categorías automáticas y el campo seleccionado como nombre. Las versiones alternativas no se fusionan automáticamente; desmarque capas redundantes para evitar duplicados.
5. Seleccione el ámbito territorial (por defecto **Valle del Cauca → Cali**) y pulse **Generar geoportal de Cali**. El servidor recorta las capas vectoriales utilizando el límite municipal oficial.
6. En el módulo **Geoportal**, active las capas deseadas, busque lugares y consulte sus atributos de origen.

> **Nota sobre el recorte incluido de Cali:**  
> La entrega integra el recorte preparado de Cali con **12 capas, 49.343 elementos, 1.091 registros de salud y 42 localidades** (conteos directos sin deduplicación entre fuentes ni certificación de cobertura). La red vial contiene 42.842 arcos y conecta vértices compartidos.  
> Las sedes se incorporan inicialmente como **Sin verificar**, sin asignación clínica automática de condiciones, servicios ni perfiles. Utilice la ficha de cada sede y la función **Caracterizar para ECNT** para documentar su validación.

---

## Flujo de la aplicación

La arquitectura del prototipo desacopla la lectura pesada de datos geográficos en disco (procesada por el backend en Python) del análisis interactivo espacial y clínico (ejecutado en el cliente web mediante JavaScript).

```mermaid
flowchart TD
    subgraph UI_Layer["1. Interfaz de Usuario (Navegador)"]
        SPA["Cliente Web SPA (app/index.html & app/js/app.js)"]
        MAP["Visor Cartográfico (Leaflet / CSS)"]
        CORE["Motor Geoespacial y Clínico (app/js/core.js)"]
        ADAPT["Adaptador Territorial (app/js/repository-core.js)"]
    end

    subgraph API_Layer["2. Backend Local (servidor.py)"]
        SRV["Servidor HTTP Multihilo (127.0.0.1:8516)"]
        AUTH["Seguridad: Token X-IETS-Token & CORS Local"]
        STORE["Gestor SQLite (Store: current_state & history)"]
    end

    subgraph Processing_Layer["3. Procesamiento y Extracción (repositorio.py & microplan/)"]
        JOBS["Planificador de Trabajos Asíncronos (start_job)"]
        INVENT["Inventario y Descubrimiento (microplan/sources.py)"]
        CLIP["Recorte Espacial (boundary_for & GeoPandas)"]
        ACCES["Accesibilidad por Lotes (read_accessibility & PyOgrio)"]
        EXP["Exportador de Paquetes Autónomos (exportar.py)"]
    end

    subgraph Storage_Layer["4. Datos, Almacenamiento y Salidas"]
        DISK_REPO[("Carpeta de Microplanificación (Shapefiles, GPKG, Tablas)")]
        DB_SQLITE[("Base SQLite (datos/observatorio.sqlite)")]
        CACHE_DIR[("Caché Local Parquet (cache/accesibilidad)")]
        REF_GEO[("Límites Oficiales (referencia/COL_adm2_v03.geojson.gz)")]
        OUT_ZIP["Paquete Territorial Autónomo (salidas/IETS_*.zip)"]
    end

    SPA -->|Carga interfaz y estado inicial| SRV
    SPA -->|POST /api/repository/inspect| SRV
    SRV --> AUTH
    AUTH --> JOBS
    JOBS --> INVENT
    INVENT -->|Escanea sin modificar| DISK_REPO

    SPA -->|POST /api/repository/load| SRV
    JOBS --> CLIP
    CLIP -->|Filtra por límite municipal| REF_GEO
    CLIP -->|Lee capas vectoriales| DISK_REPO
    JOBS --> ACCES
    ACCES -->|Procesa y almacena caché| CACHE_DIR
    JOBS -->|Retorna capas recortadas en GeoJSON| SRV
    SRV -->|GET /api/repository/job/:id| SPA

    SPA --> ADAPT
    ADAPT --> CORE
    CORE --> MAP

    SPA -->|PUT /api/state (If-Match: revision)| SRV
    AUTH --> STORE
    STORE -->|Persistencia transaccional| DB_SQLITE

    SPA -->|POST /api/export| SRV
    AUTH --> EXP
    EXP -->|Genera ZIP con visor offline| OUT_ZIP
```

### Recorrido paso a paso del ciclo de vida

1. **Entrada y sesión de trabajo**:
   - Al ejecutar `INICIAR.bat` (`servidor.py`), se levanta un servidor multihilo en `127.0.0.1:8516`. Se genera un token criptográfico local aleatorio (`X-IETS-Token`) para prevenir peticiones de orígenes no autorizados.
   - El cliente carga `app/index.html`. La aplicación solicita `GET /api/session`; el servidor responde con la revisión actual y el estado persistido en SQLite (`datos/observatorio.sqlite`). Si la base es nueva, se inicializa a partir de la instantánea de Cali (`datos/ejemplo_cali.json`).

2. **Inspección del repositorio de microplanificación**:
   - En el módulo **Repositorio**, el usuario especifica la ruta de los datos y el cliente envía un `POST /api/repository/inspect`.
   - `servidor.py` delega a `repositorio.py`, que lanza un hilo en segundo plano con `microplan/sources.py` y `microplan/discovery.py`.
   - El motor inspecciona archivos vectoriales (Shapefile `.shp`, GeoPackage `.gpkg`, GeoJSON), tablas con columnas de latitud/longitud (`microplan/coordinates.py`) y rásteres (clasificados para inventario). Ningún insumo original es alterado.

3. **Recorte territorial y extracción de capas**:
   - El usuario selecciona las capas a cargar y los filtros de ámbito (ej. Valle del Cauca → Cali) y presiona "Generar geoportal". El cliente despacha `POST /api/repository/load`.
   - `repositorio.py` busca el límite municipal mediante `boundary_for`, consultando capas del propio repositorio o la cartografía base de referencia (`referencia/COL_adm2_v03.geojson.gz`).
   - Para capas nacionales masivas de accesibilidad hospitalaria, `read_accessibility` utiliza `pyogrio` con un generador Arrow y recorte geométrico elemento por elemento mediante `shapely`, guardando el resultado en caché Parquet (`cache/accesibilidad/`).
   - El resultado se transforma a EPSG:4326 con atributos normalizados (`_iets_id`, `_nombre`, `source_id`), validando que no supere los límites de seguridad (máximo 150.000 entidades por capa y 100 MB de tamaño).

4. **Adaptación clínica y análisis en cliente**:
   - El cliente consulta periódicamente `GET /api/repository/job/<id>`. Al completar la lectura, `app/js/repository-core.js` adapta las capas de salud y localidades al esquema de trabajo sin inferir condiciones clínicas no certificadas.
   - `app/js/core.js` ejecuta en el navegador los algoritmos de análisis espacial y de continuidad:
     - **Cálculo de distancias euclidianas y geodésicas** mediante fórmula de Haversine.
     - **Ruteo y accesibilidad sobre red vial**: Grafo no dirigido evaluado con el algoritmo de Dijkstra sobre vértices compartidos (con tolerancia de ajuste a 500 m).
     - **Consultas espaciales punto en polígono**: Ray-casting con verificación de anillos interiores y exteriores.
     - **Priorización multicriterio**: Normalización proporcional de pesos sin penalizar valores nulos con cero.

5. **Persistencia y exportación de resultados**:
   - **Guardado continuo**: Las modificaciones se envían mediante `PUT /api/state` con encabezado `If-Match: revision`. `servidor.py` almacena de forma transaccional en `datos/observatorio.sqlite`, registrando hasta 20 versiones en la tabla de historial para prevención de conflictos.
   - **Paquete territorial descargable**: Al solicitar la exportación territorial, `exportar.py` comprime en disco (`salidas/IETS_<municipio>_<id>.zip`) una versión autocontenida con `Consulta_territorial.html`, capas en GeoJSON, hojas CSV con saneamiento de inyección de fórmulas, fuentes catalogadas y los manuales HTML completos.

---

## Módulos del sistema

| Módulo | Descripción y funcionalidad |
| --- | --- |
| **Repositorio** | Selección de carpeta de microplanificación, inspección de insumos vectoriales y generación del recorte territorial. |
| **Geoportal** | Visualizador Leaflet para encendido/apagado de capas, búsqueda de lugares y consulta de atributos nativos de la fuente. |
| **Oferta y acceso** | Inventario de sedes de salud, caracterización clínica para ECNT, análisis de proximidad y ruteo sobre red vial. |
| **Priorización** | Evaluación multicriterio de indicadores territoriales con ponderación explícita (los faltantes no se convierten en cero). |
| **Evidencia y guías** | Registro y documentación de preguntas orientadoras, referencias bibliográficas, síntesis y revisión técnica. |
| **Acciones** | Registro de compromisos, alternativas de intervención, responsables, plazos y verificación de cumplimiento. |
| **Datos y paquetes** | Importación de insumos propios, respaldo integral en JSON y generación de paquetes territoriales ZIP autónomos. |

---

## Manuales y documentación técnica

La documentación detallada se encuentra en la carpeta `manuales/` en formato Markdown y HTML imprimible:

- [Manual de usuario](manuales/usuario.html): Guía de uso, carga de repositorio y recorrido funcional de cada módulo.
- [Manual del sistema](manuales/sistema.html): Arquitectura técnica, requisitos de entorno, especificación de API HTTP y SQLite.
- [Diccionario de datos](manuales/datos.html): Estructura de atributos nativos, esquemas JSON y formatos de intercambio CSV/GeoJSON.
- [Alcance y verificación](manuales/alcance.html): Antecedentes de v5, batería de pruebas y limitaciones del prototipo.

---

## Estructura del proyecto

| Archivo / Directorio | Función dentro del sistema |
| --- | --- |
| `INICIAR.bat` | Script de arranque rápido en Windows con validación de entorno virtual. |
| `INSTALAR.bat` | Script de instalación automática de dependencias en `.venv/`. |
| `servidor.py` | Servidor HTTP local multihilo, validación de Host/Origin, autenticación local y almacén SQLite. |
| `repositorio.py` | Adaptador del repositorio de microplanificación, gestión de trabajos en segundo plano y recorte vectorial. |
| `exportar.py` | Generador en disco de paquetes territoriales ZIP autónomos con visualizador offline. |
| `index.html` | Redirección directa hacia `app/index.html` para apertura sin servidor. |
| `app/` | Aplicación web (SPA): interfaz HTML, estilos CSS (`assets/`), catálogo de territorios (`js/territories.js`), lógica de negocio (`js/core.js`, `js/repository-core.js`, `js/app.js`), y dependencias locales Leaflet/fflate (`vendor/`). |
| `microplan/` | Lector original reutilizado de v5 (`sources.py`, `discovery.py`, `coordinates.py`, `accessibility.py`, `catalogue.py`). |
| `datos/` | Base operativa local SQLite (`observatorio.sqlite`) e instantánea de arranque (`ejemplo_cali.json`). |
| `cache/` | Recortes espaciales cacheados en formato Parquet y archivos temporales de lectura. |
| `referencia/` | Cartografía oficial de soporte (`COL_adm1.geojson.gz`, `COL_adm2_v03.geojson.gz`), hashes de integridad e inventario. |
| `manuales/` | Manuales técnicos y de usuario en Markdown y HTML. |
| `herramientas/` | Utilidades de empaquetado (`empaquetar.py`), renderizado de manuales (`render_manuales.py`) y conversión de capas. |
| `tests/` | Pruebas unitarias de servidor, repositorio, exportación y funciones centrales de JavaScript. |

---

## Verificación y pruebas

Para validar el funcionamiento completo de los componentes, ejecute las pruebas correspondientes:

```bash
# 1. Pruebas unitarias del motor JavaScript (35 pruebas)
node --test tests/core.test.js tests/repository.test.js

# 2. Pruebas del servidor HTTP local y base SQLite (11 pruebas)
py tests/test_servidor.py

# 3. Pruebas del generador de paquetes y exportaciones ZIP (4 pruebas)
py tests/test_exportar.py

# 4. Pruebas del lector de repositorio y recorte geográfico (requiere geopandas)
py tests/test_repositorio.py

# 5. Recompilación de manuales y actualización de bundle integrado
py herramientas/render_manuales.py
py herramientas/empaquetar.py
```

> **Nota sobre `datos/ejemplo_cali.json`:**  
> Por defecto, `datos/*.json` está excluido del control de versiones en `.gitignore`. Si el archivo `datos/ejemplo_cali.json` no está presente, puede generarse a partir de `app/js/initial.js` ejecutando:  
> `node -e "const fs=require('fs'); const t=fs.readFileSync('app/js/initial.js','utf8'); fs.writeFileSync('datos/ejemplo_cali.json', t.replace(/^window\.IETS_INITIAL=/,'').replace(/;$/,''));"`

---

## Alcance y consideraciones

1. **Uso local y monousuario**: El sistema está concebido como una estación de trabajo local para un analista territorial, sin autenticación institucional ni sincronización en la nube.
2. **Fuentes no modificadas**: Los datos de microplanificación originales nunca son sobreescritos ni modificados. Todo recorte y caché se almacena exclusivamente dentro del directorio del prototipo.
3. **No certificación clínica ni catastral**: Los conteos y registros corresponden a las fuentes cartográficas procesadas; no certifican habilitación en REPS/CAC ni representan cartografía catastral legal.
4. **Caracterización progresiva**: La identificación de servicios y condiciones de salud para ECNT requiere verificación documentada del usuario en la ficha de cada sede.
