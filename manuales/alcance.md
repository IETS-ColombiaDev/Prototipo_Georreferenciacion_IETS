# Alcance y verificación de la entrega

Georreferenciación para la acción · Observatorio IETS · Versión 1.0.0 · 30 de octubre de 2026

El prototipo desarrolla el flujo territorial propuesto en Georreferenciacion para la accion Observatorio IETS v2.docx, usando microplanificación v5 como antecedente y los activos visuales suministrados. La entrega es local y para un usuario, con Colombia como ámbito y Cali como demostración inicial.

## Cargar la misma carpeta de microplanificación

1. Abra **INICIAR.bat**. Entre en **Repositorio**.
2. La ruta inicial es `D:\00000-PAHO-OMS\0-Priorizacion\COL`. También puede elegir su carpeta principal o usar **Explorar carpetas**.
3. Pulse **Leer repositorio**. Se conserva su estructura: no convierta ni renombre los archivos.
4. Revise las capas detectadas, sus categorías y el campo que contiene el nombre. Las versiones alternativas no se fusionan automáticamente; evite duplicados.
5. Mantenga **Valle del Cauca → Cali** y pulse **Generar geoportal de Cali**. El servidor recorta las capas con el límite municipal del propio repositorio.
6. En **Geoportal**, active las capas, busque un nombre y consulte sus atributos y fuente. Cambiar filtros no vuelve a leer el disco: para otro municipio o área, regrese a Repositorio y genere ese ámbito.

La entrega ya incluye el recorte de Cali: **12 capas, 49.343 elementos, 1.091 registros de salud y 42 localidades**. Son conteos de los archivos leídos, sin deduplicación entre fuentes ni certificación de cobertura. Incluye educación, ríos, sitios de interés, vías y las tres accesibilidades nacionales recortadas. La red contiene 42.842 elementos. Los archivos originales se leen; los recortes y la caché se guardan en el prototipo.

Las sedes se inician como **Sin verificar**, sin asignación automática de condición crónica, servicio ni perfil. Abra su ficha y use **Caracterizar para ECNT**, con soporte de verificación, para habilitar esos filtros. Una localidad es una referencia geográfica; no se convierte en una necesidad clínica ni en una estimación de enfermedad. La recarga conserva la caracterización de identificadores estables que vuelvan a aparecer; respalde el trabajo antes de cambiar fuentes.

Las capas de accesibilidad conservan `category`, `range_type` y `range`: en estas fuentes TIME está en segundos y DISTANCE en metros. Se muestran separadas de las capas caracterizadas por servicio de ECNT. Los atributos poblacionales pertenecen al ámbito original; no se recalculan para Cali y no se deben sumar entre umbrales.

## Correspondencia funcional

| Necesidad del documento | Resultado en esta versión | Límite explícito |
| --- | --- | --- |
| Selección territorial de Colombia | Catálogo departamental y municipal; carga de áreas propias. | Corte y vigencia del catálogo heredado por confirmar; sin límites oficiales de comunas. |
| Relacionar necesidad, oferta y barreras | Mapa, puntos, estados funcionales, distancias y red local. | Sedes geográficas reales, con funcionamiento y servicios por verificar; indicadores clínicos sin datos. |
| Mantener unidades de accesibilidad | Consulta por fuente, servicio, unidad y umbral. | Calidad, acumulación y pertinencia de los polígonos se revisan externamente. |
| Comparar criterios de priorización | Pesos explícitos, puntaje y sensibilidad del orden. | Índice exploratorio sin validación metodológica institucional. |
| Vincular evidencia y guías | Fichas editoriales y guía operativa de uso. | No incluye guías clínicas aprobadas, búsqueda o evaluación automática de evidencia. |
| Registrar decisión y seguimiento | Alternativas, criterio, responsable, plazo, estado, cierre e historial. | Sin identidad autenticada ni auditoría inmutable. |
| Consulta con conectividad limitada | Recursos locales y paquete HTML autónomo con datos. | Referencias externas requieren conexión; no hay sincronización entre copias. |
| Transferencia | Código, pruebas, inventarios, README y manuales. | Recepción institucional y capacitación quedan por ejecutar. |

## Reutilización del antecedente

Se incorporan los GeoJSON de Colombia de geo/adm1 y geo/adm2_v03 y las bibliotecas Leaflet y fflate del ZIP entregado. Los originales geográficos, los archivos de referencia seleccionados y sus hashes se conservan en referencia. Los logotipos se copian desde la carpeta assets suministrada.

El motor de interfaz se implementó para ejecución en navegador sin dependencias adicionales. Conserva los principios de procedencia, distancias separadas, manejo explícito de faltantes y consulta autónoma. El lector Python de fuentes y sus auxiliares de v5 se ejecutan directamente para inventario y recorte. El adaptador nuevo optimiza la lectura de accesibilidades nacionales por geometría. El cálculo de rutas de la interfaz sigue siendo JavaScript y no reproduce todas las operaciones de red del motor Python de v5.

No se incluyeron los cuadernillos de vacunación, los datos poblacionales multinacionales ni los ejemplos de otros países. Tampoco se alteraron los archivos suministrados por la usuaria.

## Escenarios cubiertos

Continuidad oncológica se explora filtrando Cáncer y el servicio requerido, revisando oferta funcional y registrando una acción con evidencia vinculada. Seguimiento de diabetes e hipertensión se prueba con servicios ambulatorios, medicamentos y laboratorio. Recuperación territorial se representa mediante la comparación de criterios y el seguimiento de acciones. Los indicadores clínicos se prueban con el ensayo opcional. El mapa predeterminado usa el repositorio real y no atribuye capacidad clínica a sus registros.

El prototipo permite ensayar la secuencia completa. El resultado no demuestra efectividad clínica, adopción institucional ni utilidad operacional real. Las metas TRL y los periodos de validación del documento de proyecto son compromisos futuros, no atributos certificados por esta entrega.

## Pruebas reproducibles

La suite del motor cubre selección de territorio, combinación de filtros, pertenencia de puntos, CSV con caracteres especiales, neutralización de fórmulas, geometrías con huecos, Haversine, ponderación y faltantes, exclusión de destinos no funcionales, Dijkstra, desconexiones, exclusión de puentes, intervalos, códigos y coordenadas inválidas, duplicados, porcentajes, cierre documentado, fechas, respaldos y escape de texto.

La suite del servidor comprueba persistencia, conflictos de revisión, rechazo de esquemas incompletos, conservación de veinte revisiones, servicio de interfaz, restricción de origen/host, token para escritura y protección de archivos internos. Las pruebas usan bases temporales separadas de la entrega.

El registro final de comprobación se conserva en referencia/VERIFICACION.json. Describe las verificaciones efectivamente ejecutadas, su fecha y sus límites. Las pruebas son técnicas del prototipo y no sustituyen el plan de validación con usuarios del proyecto.

## Pendientes para evolucionar

1. Acordar fuentes, permisos, responsables y frecuencia de actualización de CAC, REPS y datos territoriales.
2. Verificar el catálogo territorial e incorporar límites oficiales submunicipales y una red vial pertinente.
3. Definir indicadores comparables, denominadores y criterios de priorización con el equipo metodológico.
4. Incorporar guías y evidencia revisadas con gobierno editorial y control de versiones institucional.
5. Implementar identidad, permisos, auditoría y operaciones multiusuario si se requieren.
6. Conectar el módulo con el Observatorio y comprobar interoperabilidad de códigos y unidades.
7. Ejecutar pruebas de desempeño, accesibilidad, recuperación, seguridad y uso con usuarios reales.
8. Formalizar titularidad y derechos del antecedente, activos y nuevos componentes antes de distribución externa.

## Criterio de aceptación de este prototipo

La recepción de esta versión consiste en abrirla localmente, filtrar el territorio, comprobar un caso de acceso, documentar una acción, recuperar su guardado, incorporar un archivo válido, rechazar uno inválido y consultar un paquete exportado sin conexión. La aceptación institucional de la solución final debe usar un protocolo propio, con criterios y evidencia de uso acordados.
