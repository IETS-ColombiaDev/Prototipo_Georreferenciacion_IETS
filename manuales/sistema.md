# Manual del sistema

Georreferenciación para la acción · Observatorio IETS · Versión 1.0.0

La distribución permite consulta y registro local para un usuario. El navegador ejecuta el análisis; el servidor local lee el repositorio geográfico y almacena la base en SQLite. Esta separación permite abrir una consulta autónoma sin conexión y conservar el trabajo en disco cuando el servidor está disponible.

## Requisitos e inicio

Use un navegador moderno con JavaScript, almacenamiento local, descargas y soporte de dialog. La distribución incluye Leaflet y fflate; no necesita conexión para consultar la base incluida. Se recomienda comenzar con archivos pequeños y ampliar después de comprobar tiempos y tamaño del respaldo.

La lectura geográfica requiere Python 3.12 o superior y las dependencias fijadas en requirements.txt. En este equipo se entrega .venv preparado; INICIAR.bat lo usa directamente. En otro equipo, ejecute INSTALAR.bat con conexión a internet. La instalación crea un entorno dentro de esta carpeta, sin cambiar Python global. No transporte .venv a otro equipo: regenérelo allí. El ejecutable base de este equipo procede del runtime de Codex del perfil del usuario; si se elimina, ejecute de nuevo la instalación con Python disponible.

Para inicio explícito y puerto alternativo:

```text
python servidor.py --open
python servidor.py --port 8517 --open
```

El puerto predeterminado es 8516. La dirección de enlace es 127.0.0.1; no se publica el servicio en la red. Si el puerto está ocupado, cierre la instancia anterior o use otro puerto. Un puerto distinto conserva la misma base de disco si usa la misma carpeta; el almacenamiento de navegador, en cambio, depende del origen.

## Arquitectura y archivos

| Componente | Responsabilidad |
| --- | --- |
| app/index.html | Punto de entrada, idioma español y recursos locales. |
| app/assets/app.css | Diseño adaptativo, formularios, tablas, mapa e impresión. |
| app/js/core.js | Filtros, CSV, geometría, distancias, red, accesibilidad y validaciones. |
| app/js/territories.js | Catálogo geográfico de Colombia derivado del antecedente. |
| app/js/demo.js | Escenario sintético y plantillas iniciales. |
| app/js/app.js | Módulos, persistencia, formularios, exportación y paquete territorial. |
| app/js/bundle.js | Copia empaquetada de recursos para producir consultas autónomas. |
| servidor.py | HTTP local, comprobación de origen, control de revisión y SQLite. |
| datos/observatorio.sqlite | Base operativa creada en modalidad servidor. |

Los datos del navegador permanecen bajo la clave iets-georreferenciacion-v1. Cada paquete autónomo utiliza una clave distinta para no modificar la base principal. La consulta exportada tiene su propio conjunto de registros y no sincroniza cambios.

## Modelo y persistencia

La base JSON usa schema 1 y colecciones facilities, origins, areas, roads, accessibility, sources, evidence y actions. demoAreas contiene las etiquetas sintéticas de subáreas. Cada registro territorial conserva un identificador y source_id. Las acciones relacionan territorio, necesidad opcional, sede opcional y evidencia opcional.

SQLite contiene current_state con la revisión actual y el JSON completo, e history con las veinte revisiones anteriores. Cada escritura se realiza dentro de una transacción y cierra la conexión. La revisión esperada viaja en If-Match; si otra pestaña cambió la base, el servidor devuelve conflicto y no sobrescribe.

La aplicación mantiene los cambios en memoria hasta la confirmación del guardado. Si falla el servidor, se informa el error y no se cambia silenciosamente de almacenamiento. El límite del cuerpo de guardado es 120 MB. En modo navegador la cuota depende del navegador y puede ser menor.

## Interfaces locales

| Método y ruta | Función |
| --- | --- |
| GET / | Interfaz local. |
| GET /api/session | Revisión, estado y token de la instancia local. |
| PUT /api/state | Sustitución transaccional del estado con token y revisión. |
| GET /manuales/... | Manuales de la distribución. |

El servidor acepta únicamente Host local y un Origin local si está presente. Las escrituras requieren X-IETS-Token. No expone la base de datos ni el código del servidor como archivos descargables. La política de contenido restringe conexiones al mismo origen. Estas medidas reducen accesos accidentales desde páginas externas, pero no reemplazan autenticación institucional ni protección del equipo.

## Lectura del repositorio

repositorio.py coordina inventario, selección territorial y trabajos en segundo plano. microplan/sources.py y sus módulos auxiliares se reutilizan sin modificar desde v5. El inventario descubre vectores, contenedores, metadatos CRS de QGIS y tablas ubicadas en carpetas de geocodificación, siguiendo ese lector. SHP necesita sus componentes; KML depende del controlador disponible. Los raster se inventarían, pero no se analizan ni dibujan.

Para GeoPackage nacional de accesibilidad, el adaptador recorta una geometría a la vez, para reducir el pico de memoria. Conserva atributos nativos y huellas de geometría. El resultado es EPSG:4326 y usa el límite de Cali del repositorio, sin simplificar ese recorte. Los archivos ZIP se extraen en cache/archivos y los recortes en cache/recortes o cache/accesibilidad, dentro del prototipo. No se escribe en COL.

Límites de consulta: 150.000 elementos por capa, 250.000 totales y 100 MB de recorte serializado. Se rechaza la operación excedida sin reemplazar el estado existente. Son límites de protección del prototipo, no una garantía de rendimiento nacional. Seleccione municipio o área para capas voluminosas. La generación puede tardar varios minutos en la primera lectura.

Las rutas POST /api/repository/inspect, /load y /folders requieren el token local. GET /api/repository/job/ID permite seguir el trabajo. repositoryLayers conserva las geometrías y atributos nativos; repository conserva carpeta, ámbito, límite, catálogo y observaciones. app/js/repository-core.js adapta salud y localidades al modelo de la interfaz, sin inferir su caracterización clínica.

datos/ejemplo_cali.json inicializa una base sin guardados. app/js/initial.js permite abrir el mismo recorte sin servidor. Esta copia grande suele superar la cuota de almacenamiento del navegador: use el servidor para editar. Si se produce un error de cuota, la interfaz informa el fallo y no declara el cambio guardado. Las exportaciones autónomas permiten consulta y descarga de respaldo; no lectura de nuevas carpetas.

## Preparar y actualizar datos

Los registros se incorporan desde la interfaz después de validación y confirmación. Esta versión no edita ni elimina fuentes existentes desde la UI. Para corregir una fuente, prepare un respaldo completo revisado con identificadores y relaciones consistentes, consérvelo junto al original y restáurelo. Para una sustitución sistemática de catálogos, el equipo técnico debe versionar la distribución y repetir las pruebas.

Los límites originales comprimidos se conservan en referencia. preparar_base.py extrae exclusivamente los archivos de Colombia y recursos reutilizados desde el ZIP autorizado. Simplifica líneas mediante Douglas-Peucker con tolerancia de 0,00035 grados y redondea a cinco decimales para visualización. No constituye una precisión métrica garantizada, no es cartografía catastral y puede modificar bordes pequeños. Las validaciones de pertenencia usan estos límites de referencia; casos cercanos a fronteras requieren revisión del insumo original.

Para regenerar la base de distribución, indique la carpeta que contiene el ZIP y assets:

```text
python herramientas/preparar_base.py "D:\ruta\Georeferenciación"
python herramientas/render_manuales.py
python herramientas/empaquetar.py
```

Esta operación actualiza recursos de la distribución, no la base operativa ya guardada. Respáldela antes de actualizar. Los archivos originales del usuario no se modifican.

## Conversión opcional

convertir_capas.py transforma una capa vectorial a GeoJSON o una hoja de Excel a CSV. Requiere geopandas para formatos vectoriales o pandas y el lector correspondiente para Excel, en un entorno independiente. El entorno de esta entrega ya incluye esas dependencias. La conversión es auxiliar; Repositorio lee los formatos originales directamente.

```text
python herramientas/convertir_capas.py entrada.gpkg salida.geojson --capa sedes
python herramientas/convertir_capas.py entrada.xlsx salida.csv --hoja 0
```

El conversor exige destino nuevo, rechaza vectores sin CRS y geometrías inválidas, y reproyecta a EPSG:4326. No normaliza automáticamente nombres de columnas, códigos o categorías; complete esa preparación según el diccionario. En SHP mantenga los archivos SHP, SHX, DBF y PRJ juntos. La lectura de KML depende de los controladores del entorno geográfico.

## Métodos del análisis

La distancia recta usa Haversine sobre longitud y latitud, con radio terrestre medio de 6371,0088 km. El punto de origen es el registro suministrado; no se sustituyen necesidades por centroides de polígonos.

La red es no dirigida. Se conecta mediante vértices compartidos redondeados a seis decimales; cada segmento pesa su longitud geodésica. El origen y destinos se ajustan al vértice más cercano hasta 500 metros. Dijkstra encuentra el menor recorrido; la elección de destino considera recorrido y conexión de destino, y los accesos fuera de red se reportan separados. No se insertan puntos en segmentos ni se calculan cruces automáticos. Prepare una red correctamente segmentada. Un cruce aparente no conecta si no comparte vértice.

No se modelan sentidos de circulación, restricciones de vehículo, pendientes, cierres reales, rutas fluviales ni velocidades. Puentes/túneles/capas elevadas explícitos se excluyen para reducir falsas conexiones. Su ausencia en los atributos no demuestra que las vías estén a nivel. Estos límites son más restrictivos que el motor geoespacial Python v5 y están documentados para no equiparar capacidades.

Para accesibilidad se agrupan polígonos por fuente, servicio y unidad. Se conserva el menor umbral que contiene el punto y el mayor umbral inferior de la misma serie. Si la serie tiene un único umbral, el límite inferior es cero. La interpretación supone umbrales acumulados comparables; no se suman poblaciones ni se derivan velocidades.

## Respaldo y recuperación

Al terminar una sesión o antes de modificar fuentes, descargue un respaldo JSON desde Datos y paquetes. Nombre la copia con fecha y versión, y guárdela en la ubicación institucional autorizada. Un respaldo completo puede incluir nombres de responsables y decisiones; distribúyalo según su contenido.

Para restaurar, abra una instancia, exporte su estado actual, seleccione el respaldo, confirme la sustitución y compruebe conteos y una acción conocida. Para copia física de SQLite, cierre antes el servidor y copie datos/observatorio.sqlite. Nunca mezcle una base abierta y una copia parcial.

Las veinte revisiones de history permiten recuperación técnica adicional. Trabaje sobre una copia de la base cerrada; extraiga el JSON de la revisión elegida y envuélvalo como format IETS-backup con su objeto state. Compruebe la estructura y restaure mediante la interfaz. Esta operación no tiene un botón de recuperación en la versión actual.

## Control de calidad y mantenimiento

Ejecute las pruebas del motor y del servidor antes de distribuir cambios. Después pruebe selección territorial, filtros, creación y cierre de acción, recarga, carga válida e inválida, exportación y consulta autónoma. Use una base de pruebas indicada con --db para no modificar la base de trabajo.

```text
node --test tests/core.test.js
python tests/test_servidor.py
python servidor.py --port 8517 --db datos/pruebas.sqlite
```

Después de editar código o documentación, regenere bundle.js e INVENTARIO_SHA256.json con herramientas/empaquetar.py. Reinicie el servidor si cambió Python y recargue el navegador si cambió la interfaz. Conserve el historial de versiones y registre incidencias con fecha, pasos, resultado esperado, resultado observado y archivo de ejemplo sin datos sensibles.

## Resolución de problemas

| Situación | Qué revisar |
| --- | --- |
| El iniciador pide preparar el entorno | Ejecute INSTALAR.bat una vez con Python 3.12+ y conexión. Después abra INICIAR.bat. |
| El puerto está ocupado | Cierre la instancia anterior o use --port 8517. |
| La interfaz no guarda | Revise espacio, permisos, base en uso, cuota del navegador y mensaje mostrado. Exporte respaldo. |
| Conflicto de revisión | Otra pestaña guardó cambios. Conserve lo necesario y recargue antes de editar de nuevo. |
| No aparecen registros | Revise filtros y Mostrar datos de ensayo; confirme que la fuente contiene ese territorio y servicio. |
| Un punto cae fuera del municipio | Revise orden lon/lat, CRS, código territorial y borde simplificado de referencia. |
| No hay ruta | Revise segmentación, vértices compartidos, umbral de conexión y disponibilidad de destinos funcionales. |
| La consulta exportada no cambia con la base | Es una copia independiente. Genere un paquete nuevo o transfiera un respaldo. |

## Condiciones para una versión institucional

La evolución debe definir autenticación y roles reales, auditoría persistente, licencias y fuentes actualizadas, protección y conservación de datos, pruebas de volumen, integración con el Observatorio, revisión científica, accesibilidad con usuarios y soporte operativo. Esta entrega no acredita esos requisitos ni un nivel TRL final.

## Exportación en disco

Con servidor, Paquete territorial prepara el ZIP en salidas/ en segundo plano. La interfaz informa su ruta y ofrece Descargar ZIP. Las rutas locales POST /api/export y GET /api/export/job/ID gestionan el trabajo; /api/export/download/ID transmite el archivo. El cuerpo solicita filtros, inclusión opcional de acciones e informe; los datos se leen de la base del servidor. La página autónoma incorpora una sola copia del estado.
