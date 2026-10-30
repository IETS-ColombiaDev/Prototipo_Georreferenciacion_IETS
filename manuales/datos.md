# Diccionario y preparación de datos

Georreferenciación para la acción · Observatorio IETS · Versión 1.0.0

Este documento establece el contrato de carga del prototipo. Prepare insumos agregados o institucionales con procedencia, fecha y responsable. La aplicación no geocodifica direcciones ni consulta registros externos; necesita coordenadas o geometrías ya disponibles.

## Dos vías de incorporación

**Repositorio** lee directamente la carpeta de microplanificación: no exige los campos del formato de intercambio descrito más abajo. Conserva los nombres y atributos originales. Añade identificador de fuente, identificador de registro, nombre de consulta, huella de geometría y procedencia. Las tablas de coordenadas se descubren con las reglas de v5 en carpetas de geocodificación. Los vectores sin CRS comprobable se excluyen con una observación.

Las sedes geográficas no requieren condiciones, servicios ni perfiles para aparecer en el mapa. Esos campos quedan vacíos hasta su caracterización documentada. El estado inicial es Sin verificar. Los indicadores de localidades quedan nulos. La fecha de modificación de archivo no se presenta como fecha de corte; esta permanece sin informar.

**Datos y paquetes** incorpora registros específicos del Observatorio mediante CSV/GeoJSON normalizados. Para esta segunda vía se aplican los campos y validaciones siguientes. Su límite es 15 MB y 15.000 registros; no corresponde al límite de lectura directa del repositorio.

## Formatos y convenciones

Los puntos se cargan como CSV UTF-8 o GeoJSON FeatureCollection. Las áreas, vías y polígonos de accesibilidad se cargan como GeoJSON. El sistema de coordenadas es EPSG:4326, con longitud antes de latitud y punto como separador decimal. No incluya CRS proyectado en un GeoJSON destinado a esta interfaz.

CSV admite coma o punto y coma como delimitador, campos entre comillas, comillas duplicadas y saltos de línea dentro de un campo. Los encabezados deben ser únicos y cada fila debe tener el mismo número de columnas. Los campos multivalor se separan con |. Conserve los códigos como texto, incluidos ceros iniciales.

La carga admite hasta 15 MB y 15.000 registros por archivo. La base de servidor admite un estado JSON de hasta 120 MB; este límite no constituye una prueba de desempeño para cualquier geometría. Divida insumos grandes y reduzca su complejidad de forma documentada.

## Metadatos de la fuente

| Campo del formulario | Regla |
| --- | --- |
| Nombre | Título comprensible del conjunto. Obligatorio. |
| Procedencia / referencia | Institución, documento, archivo o URL que permita identificar el origen. Obligatorio. |
| Fecha de corte | Fecha válida AAAA-MM-DD de la información. Obligatoria. |
| Versión | Identificador de la entrega del insumo. Obligatorio. |
| Responsable | Persona o unidad responsable del conjunto. Obligatorio. |
| Condiciones de uso | Licencia, autorización o limitación de uso. Obligatorio. |
| Cobertura | Territorios, servicios, periodos y límites de completitud conocidos. Recomendada. |

La aplicación genera un id de fuente y lo registra en source_id de cada registro aceptado. También conserva nombre del archivo, fecha de validación, número de aceptados y observaciones. demo=false significa que el usuario incorporó el registro; no certifica su carácter oficial, veracidad o validación científica.

## Campos comunes de puntos

| Campo | Tipo y regla | Ejemplo |
| --- | --- | --- |
| id | Texto único dentro de la colección. Obligatorio. | SEDE-001 |
| name | Nombre legible. Obligatorio. | Sede del ejercicio |
| department | Código de dos caracteres del catálogo incluido. Obligatorio. | 76 |
| municipality | Código de cinco caracteres compatible con department. Obligatorio. | 76001 |
| area | Id de área cargada o etiqueta de ensayo. Opcional. | AREA-001 |
| lon | Longitud numérica. Obligatoria en CSV. | -76.531 |
| lat | Latitud numérica. Obligatoria en CSV. | 3.470 |
| conditions | Uno o más valores admitidos separados por |. Obligatorio. | Diabetes\|Hipertensión |
| services | Uno o más servicios separados por |. Obligatorio. | Seguimiento ambulatorio |
| profiles | Uno o más perfiles separados por |. Obligatorio. | Medicina\|Enfermería |

En GeoJSON, lon y lat se toman de la geometría Point. Los demás campos van dentro de properties. No hay asignación automática de municipio ni de comuna. El punto debe pertenecer al municipio declarado según los límites de referencia. Si area se refiere a un polígono incorporado, se comprueba también pertenencia y municipio del área. Las etiquetas de ensayo no tienen geometría oficial para esa comprobación.

## Catálogos de valores

| Campo | Valores admitidos |
| --- | --- |
| conditions | Diabetes; Hipertensión; Cáncer; Todas las ECNT |
| services | Seguimiento ambulatorio; Medicamentos; Oncología; Laboratorio; Rehabilitación |
| profiles | Coordinación territorial; Medicina; Enfermería; Farmacia; Gestión de servicios |
| status de sede | Operativa; Capacidad limitada; No operativa; Sin verificar |
| status de acción | Pendiente; En curso; Bloqueada; Cerrada |
| Estado editorial | Borrador; En revisión; Revisión registrada |
| unit de accesibilidad | min; h; s; km; m |

Use los textos exactos, incluidas tildes. Todas las ECNT permite que un registro resulte compatible con cualquiera de las condiciones individuales del filtro. Los servicios y perfiles deben declararse; no se infieren a partir del nombre de una sede.

## Sedes y servicios

Además de los campos comunes, facilities requiere status con uno de los cuatro estados. notes es una observación libre opcional. Esta versión utiliza una fila por sede con lista de servicios; el estado funcional aplica al registro completo. Si servicios de una misma institución tienen estados distintos, represéntelos con identificadores diferentes y nombres que indiquen el servicio, documentando esa desagregación.

El conteo de sedes es un conteo de registros. No deduplica instituciones por nombre o proximidad ni calcula camas, capacidad o cupos. El control de duplicados usa id. Los registros ya existentes no se sobrescriben durante una carga.

## Necesidades e indicadores

| Campo adicional de origins | Definición en el prototipo |
| --- | --- |
| gap | Porcentaje de brecha de continuidad, entre 0 y 100, o vacío. |
| barrier | Porcentaje de barrera reportada, entre 0 y 100, o vacío. |
| disruption | Porcentaje de interrupción del servicio, entre 0 y 100, o vacío. |
| indicator_note | Descripción de la población, numerador, denominador, método, periodo y límites. |

Los tres porcentajes son insumos del índice exploratorio. Deben representar unidades y poblaciones comparables. La interfaz no calcula automáticamente esos porcentajes ni verifica sus denominadores. Documente en indicator_note cómo se obtuvieron y conserve el soporte externo. Un vacío se mantiene como nulo; no se convierte en cero. Cero significa un valor observado explícitamente en el conjunto.

La fila representa un punto de necesidad territorial o institucional, no una persona. No se suministran nombres, documentos o direcciones de pacientes en la distribución. No use un centroide como origen de viaje sin un fundamento explícito en el conjunto.

## Áreas submunicipales

areas admite Polygon o MultiPolygon. properties debe contener id, name, department y municipality. Los anillos deben estar cerrados y tener al menos cuatro posiciones. Puede representar comuna, corregimiento o área de análisis, con un nombre que haga clara su naturaleza.

La carga comprueba códigos, estructura, rangos de coordenadas y cierre de anillos. No comprueba exhaustivamente autointersecciones, superposiciones, huecos, contención de todo el polígono en el municipio ni topología entre áreas. Verifique estos aspectos con una herramienta geográfica antes de incorporar el archivo. No mezcle límites de versiones diferentes sin documentarlo.

## Red vial

roads admite LineString o MultiLineString. Cada registro necesita id, name, department y municipality. bridge, tunnel y layer son opcionales. Declare bridge=no, tunnel=no y layer=0 únicamente cuando corresponda a la fuente. Un valor explícito de puente/túnel o una capa diferente de cero excluye el segmento del cálculo.

La red debe estar segmentada en los cruces válidos con vértices compartidos. La aplicación no divide segmentos en intersecciones visuales ni conecta automáticamente un punto al interior de una línea. Ajusta cada punto al vértice más cercano hasta 500 m. El redondeo de vértices a seis decimales puede unir posiciones muy cercanas; revise la resolución y la calidad del insumo.

Las vías se filtran por el territorio declarado en sus atributos; no se recortan geométricamente al ámbito. Una vía que atraviese varios municipios requiere preparación apropiada del insumo. El recorrido no modela restricciones de sentido, tráfico, seguridad, estado real ni tiempos.

## Polígonos de accesibilidad

| Campo de properties | Regla |
| --- | --- |
| id y name | Identificación única y nombre legible. |
| department y municipality | Códigos compatibles con el catálogo. |
| service | Un servicio del catálogo. |
| threshold | Umbral numérico positivo. |
| unit | min, h, s, km o m. Se conserva sin conversión automática. |

La geometría debe ser Polygon o MultiPolygon y los umbrales deben formar una serie comparable para el mismo servicio y fuente. Declare en los metadatos método, modo de viaje, unidad, condiciones y alcance. El prototipo no valida que los polígonos estén correctamente anidados ni que su modelación sea apropiada; revise esos supuestos antes del uso.

El intervalo se deriva de los umbrales de la misma fuente, servicio y unidad. No mezcle fuentes en una serie ni compare minutos y kilómetros como si fueran la misma medida. Un punto fuera de todos los polígonos queda sin intervalo disponible; no se extrapola un tiempo.

## Acciones y evidencia

Las acciones se crean en formularios y conservan id, título, territorio, condición, servicio, perfil, problema, alternativas, criterio, responsable, plazo, estado y verificación. Las referencias originId, facilityId y evidenceId son opcionales. context guarda los filtros, pesos y versiones de fuentes al crear. history registra los cambios de contenido y estado.

Las fichas de evidencia contienen título, pregunta, población/contexto, alternativa, resultados, diseño/métodos, certeza, aplicabilidad, síntesis, referencia, revisor, fechas, versión y destinatarios. La revisión editorial es un registro local, sin firma ni verificación de identidad. Las versiones previas se conservan en history.

## Qué verifica la carga

| Comprobación | Comportamiento |
| --- | --- |
| Metadatos obligatorios y fecha válida | Rechaza si faltan o son inválidos. |
| Id duplicado en archivo o colección | Rechaza la carga completa. |
| Código municipal y departamental | Rechaza combinaciones incompatibles con el catálogo incluido. |
| Puntos sin coordenadas, fuera de Colombia o municipio | Rechaza y señala el registro. |
| Servicio, condición, perfil o estado desconocido | Rechaza y solicita valores del diccionario. |
| Porcentajes fuera de 0–100 | Rechaza. Los vacíos se mantienen nulos. |
| Geometría no admitida o anillo abierto | Rechaza y señala el registro. |
| Validez topológica completa y calidad científica | Requiere revisión externa; no se certifica automáticamente. |

No se aceptan parcialmente archivos con errores. El informe de validación muestra hasta treinta mensajes en pantalla para facilitar la corrección. La base previa permanece sin cambios hasta que una carga sin errores se incorpora explícitamente.

## Ejemplo de preparación

1. Descargue la plantilla correspondiente en Datos y paquetes.
2. Reemplace la fila ilustrativa, conservando encabezados y códigos como texto.
3. Confirme que longitud y latitud corresponden a EPSG:4326 y al municipio.
4. Declare listas de condiciones, servicios y perfiles con |, sin inventar equivalencias.
5. Complete los metadatos, incluidos corte y límites de cobertura.
6. Valide, corrija errores e incorpore; revise en el mapa y una ficha.
7. Exporte un respaldo y conserve el archivo de origen autorizado junto a sus metadatos.
