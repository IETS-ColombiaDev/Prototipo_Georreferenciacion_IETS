# Manual de usuario

Georreferenciación para la acción · Observatorio IETS · Versión 1.0.0

Este manual explica cómo consultar un territorio, comparar alternativas y dejar una decisión con seguimiento. La herramienta trabaja únicamente con Colombia y funciona localmente. Las fuentes propias se incorporan de forma explícita; el ejemplo inicial de Cali utiliza el repositorio geográfico real de microplanificación, con el ensayo sintético desactivado.

## Inicio y conservación del trabajo

Abra INICIAR.bat en la carpeta completa. Con el entorno geográfico incluido en este equipo, se abrirá el servidor local y la cabecera indicará **Guardado en disco**. Mantenga abierta la consola mientras usa la aplicación. Al finalizar, exporte un respaldo y cierre la consola con Ctrl+C.

Si falta el entorno, ejecute INSTALAR.bat una vez. ABRIR_SIN_SERVIDOR.html permite consultar el recorte ya preparado, sin leer nuevas carpetas. La cabecera dirá **Guardado en navegador**. Los cambios quedan asociados al navegador y a esa ubicación; mover la carpeta o limpiar el navegador puede hacer que dejen de estar disponibles. Transfiera el trabajo mediante respaldo y restauración.

La apertura local y la apertura mediante servidor tienen almacenes distintos. Para cambiar de modalidad, descargue un respaldo de la anterior y restáurelo en la nueva.

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

## Seleccionar el ámbito

Los filtros aparecen en todos los módulos. Primero seleccione el departamento y después el municipio o distrito. Cambiar de departamento limpia municipio y área; cambiar de municipio limpia el área. La opción Cali regresa al escenario inicial y Limpiar filtros abre el ámbito nacional.

El selector Comuna / corregimiento / área muestra las áreas registradas para ese municipio. Las seis etiquetas iniciales están marcadas como ensayo. No hay polígonos oficiales de comunas en la distribución; una etiqueta no demuestra la pertenencia geográfica real. Para usar límites submunicipales, incorpore su GeoJSON en Datos y paquetes.

Condición crónica permite Diabetes, Hipertensión o Cáncer. Servicio requerido distingue seguimiento ambulatorio, medicamentos, oncología, laboratorio y rehabilitación. Perfil profesional organiza la consulta para coordinación territorial, medicina, enfermería, farmacia y gestión de servicios. Un perfil seleccionado no autentica a la persona ni restringe permisos.

Desmarque Mostrar datos de ensayo para trabajar con los registros incorporados. Si no hay información, verá un resultado vacío. Esto no implica ausencia de personas con una condición, de necesidades o de servicios en el territorio.

## Leer el mapa

Geoportal muestra cuatro conteos: sedes geográficas, oferta funcional, puntos territoriales y acciones abiertas. Son registros que cumplen los filtros. Oferta funcional suma sedes operativas y sedes con capacidad limitada; no representa capacidad instalada ni cupos.

Los círculos con signo más identifican sedes. Verde significa Operativa; amarillo, Capacidad limitada; rojo, No operativa; gris, Sin verificar. Los rombos numerados representan puntos de necesidad. Al pulsar un marcador puede consultar la ficha o iniciar el análisis de acceso.

El panel de capas permite activar límites, áreas, oferta, necesidades, red vial y accesibilidad. La vista inicial usa límites vectoriales y no consulta mapas en línea. Ajustar vista encuadra los puntos disponibles o, si no hay puntos, el ámbito territorial.

La red y las accesibilidades del repositorio son fuentes geográficas aportadas. El modo opcional Mostrar datos de ensayo añade una red radial y polígonos ficticios, identificados como tales. Ese ensayo no describe la circulación real de Cali.

## Revisar oferta y acceso

En Oferta y acceso, seleccione un punto de necesidad. La tabla muestra sedes compatibles con los filtros, sus estados, procedencia y distancia recta al origen. El buscador acepta nombres, códigos o servicios y no diferencia tildes. El selector de estado restringe la tabla.

Incluir alternativas de todo el municipio amplía únicamente el filtro de área. Mantiene departamento, municipio, condición, servicio y perfil. Es útil para examinar una sede fuera de la comuna de origen. La exportación de sedes del módulo Datos conserva los filtros territoriales originales.

La alternativa por proximidad es la sede operativa o limitada con menor distancia geodésica entre los registros compatibles. No constituye recomendación de atención, asignación de pacientes ni confirmación de disponibilidad.

Calcular recorrido sobre red emplea los vértices compartidos de las vías cargadas y el algoritmo de Dijkstra. Excluye puentes, túneles y capas distintas de cero cuando esos atributos están declarados. Busca la conexión a un vértice dentro de 500 metros y presenta por separado kilómetros de red y metros fuera de red. No calcula tiempo a partir de una velocidad supuesta.

Cuando el origen no conecta o no existe un destino funcional conectado, el resultado explica el motivo. No se sustituye una ruta ausente por una línea recta. Si hay polígonos de accesibilidad compatibles, se muestra el menor umbral de la fuente que contiene el origen y su umbral anterior. Estos intervalos no son tiempos exactos ni identifican necesariamente una sede.

## Comparar prioridades

Priorización combina tres porcentajes aportados por cada punto de necesidad: brecha de continuidad, barrera reportada e interrupción del servicio. Los pesos iniciales son 40, 35 y 25. Puede mover los controles; la herramienta normaliza los pesos por su suma y muestra la fórmula utilizada.

El puntaje se calcula solo si los tres porcentajes son numéricos entre cero y cien. Un valor faltante deja la fila sin puntaje. El orden cambia con los pesos; la columna Cambio de orden compara con el escenario inicial 40 / 35 / 25. Los empates se ordenan por identificador para que el resultado sea reproducible.

Este índice es exploratorio y no está validado para decisiones institucionales ni para estimar riesgo clínico. Las variables, sus denominadores, métodos de obtención y pesos deben acordarse antes de un uso real. Exportar escenario conserva valores, pesos, filtros, fuentes y fecha de generación.

## Organizar evidencia

Las tres fichas iniciales son plantillas en Borrador. Consultar abre la pregunta, población, alternativa, resultados, métodos, certeza, aplicabilidad, referencia y datos editoriales. Editar ficha permite completar esos campos; Nueva ficha crea un registro propio.

Seleccione al menos una condición, un servicio y un perfil. Los estados disponibles son Borrador, En revisión y Revisión registrada. Este último exige referencia, revisor, fechas, métodos, síntesis, aplicabilidad, versión y los demás campos de revisión. La próxima revisión debe ser posterior a la fecha de revisión y esta no puede estar en el futuro.

El estado Revisión registrada conserva la declaración del usuario. La aplicación no evalúa la calidad científica ni certifica aprobación del IETS. Las referencias externas se abren en otra pestaña y requieren conexión. Los textos de las fuentes no se descargan automáticamente ni se incluyen como documentos en los paquetes.

## Registrar y seguir una acción

Puede comenzar desde Acciones, una necesidad priorizada, una sede o un resultado de acceso. Complete título, territorio, condición, servicio, perfil, problema, alternativas examinadas, criterio aplicado, responsable y plazo. Puede vincular una sede y una ficha de evidencia.

Vincular una ficha en borrador no convierte su contenido en evidencia revisada. El criterio debe explicar los límites de información y las verificaciones pendientes. Marque la acción como demostración cuando forme parte de un ejercicio.

Los estados son Pendiente, En curso, Bloqueada y Cerrada. El tablero agrupa las acciones según ese estado; una acción abierta con plazo anterior a la fecha de Colombia aparece como vencida. Abra su tarjeta para editarla. El cierre exige diligenciar Verificación del cierre. Registre qué se comprobó y con qué soporte, sin incluir datos identificables de pacientes.

Cada guardado conserva fecha, estado, responsable y contenido de la decisión en el historial. El contexto inicial almacena filtros, pesos y referencias de fuentes. El historial facilita la revisión del prototipo; no es una auditoría inmutable ni una firma electrónica.

## Incorporar una fuente

En Datos y paquetes seleccione Cargar archivo. Escoja el tipo: sedes, necesidades, áreas, vías o accesibilidad. Seleccione CSV para puntos o GeoJSON para las capas. Complete nombre, procedencia, corte, versión, responsable y condiciones de uso; describa la cobertura.

Pulse Validar archivo. La aplicación muestra registros válidos, errores y observaciones. Ante cualquier error se rechaza toda la carga, conservando la base anterior. Corrija el archivo y vuelva a validarlo. Cuando no haya errores, pulse Incorporar registros. La incorporación es explícita; la validación por sí sola no guarda datos.

Las plantillas CSV incluyen una fila ficticia para explicar el formato. Reemplace esa fila por el insumo autorizado antes de cargar. Los valores múltiples se separan con |. Consulte el diccionario para códigos, estados y campos obligatorios.

## Exportar y respaldar

Las exportaciones de CSV y GeoJSON conservan identificadores y source_id. El informe HTML presenta oferta, priorización, acciones y fuentes del ámbito. Puede abrirlo en el navegador e imprimirlo como PDF.

Respaldar todo descarga un JSON completo. Restaurar respaldo reemplaza la base actual después de seleccionar el archivo y confirmar la sustitución. Descargue primero el respaldo vigente. La validación comprueba la estructura; use únicamente respaldos de procedencia conocida.

Paquete territorial genera un ZIP con una consulta HTML autónoma, informe, CSV, GeoJSON, metadatos y estado territorial. Las acciones se incluyen solo si marca la opción correspondiente. Extraiga el ZIP y abra Consulta_territorial.html. Los cambios en esa copia no se sincronizan con el original; use un respaldo si necesita conservarlos. Para generar nuevos paquetes, regrese a la aplicación completa.

## Ejercicio de recepción

1. Abra Cali y seleccione Diabetes, Seguimiento ambulatorio y Enfermería.
2. Revise sedes y analice el acceso desde uno de los puntos de necesidad.
3. Cambie los pesos de priorización y exporte el escenario.
4. Abra la plantilla de evidencia pertinente y verifique que está en borrador.
5. Cree una acción de ensayo con responsable y plazo. Pruebe su actualización y registre una verificación de cierre.
6. Recargue la aplicación para comprobar persistencia. Exporte un respaldo.
7. Genere un paquete territorial, extraiga el ZIP y abra la consulta sin conexión.

El ejercicio comprueba funciones del prototipo. La aceptación institucional requiere datos, tareas, usuarios y criterios acordados con el equipo receptor.
