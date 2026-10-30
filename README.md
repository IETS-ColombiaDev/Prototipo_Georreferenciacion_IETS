# Georreferenciación para la acción

**Observatorio IETS · Colombia · Prototipo local 1.0.0 · 30 de octubre de 2026**

Geoportal y herramienta de trabajo territorial para continuidad de la atención de enfermedades crónicas. Lee **la misma carpeta de microplanificación**, conserva su estructura y permite documentar evidencia y acciones. La entrega incluye Cali preparado con datos del repositorio real.

## Abrir

1. Haga doble clic en **INICIAR.bat**. El entorno necesario ya está preparado para este equipo.
2. Entre en **Repositorio**. La ruta de COL y los filtros **Valle del Cauca → Cali** están listos.
3. Pulse **Abrir geoportal cargado** para ver el ejemplo; use **Leer repositorio → Generar geoportal de Cali** para volver a leer los archivos.

El servidor funciona únicamente en este equipo, en http://127.0.0.1:8516. Mantenga abierta su consola y ciérrela con Ctrl+C al terminar. No se publica en internet.

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

## Módulos

| Módulo | Para qué sirve |
| --- | --- |
| Repositorio | Elegir la carpeta, detectar capas y generar el recorte territorial. |
| Geoportal | Activar capas, buscar lugares y consultar atributos de origen. |
| Oferta y acceso | Consultar sedes, caracterizar servicios y comparar distancias y red. |
| Priorización | Comparar indicadores aportados y pesos explícitos; los faltantes no se convierten en cero. |
| Evidencia y guías | Registrar preguntas, referencias, síntesis y revisión editorial. |
| Acciones | Documentar alternativas, responsables, plazos y verificación de cierre. |
| Datos y paquetes | Incorporar insumos propios, respaldar y exportar consulta territorial autónoma. |

Colombia es el ámbito fijo; no hay selector de país. Las comunas/corregimientos se habilitan al incorporar sus límites. No se inventaron polígonos submunicipales. Los perfiles son filtros de trabajo, no cuentas de acceso.

## Manuales

- [Manual de usuario](manuales/usuario.html): carga del repositorio y recorrido completo.
- [Manual del sistema](manuales/sistema.html): instalación, arquitectura, métodos y mantenimiento.
- [Diccionario de datos](manuales/datos.html): atributos nativos y formatos de intercambio.
- [Alcance y verificación](manuales/alcance.html): adaptación de v5, pruebas y límites.

Los cuatro manuales incluyen índice, navegación, versión Markdown y formato de impresión. Puede guardarlos como PDF desde el navegador.

## Guardar y trasladar

El servidor guarda en datos/observatorio.sqlite, con revisión de conflictos y veinte versiones anteriores. **Datos y paquetes → Respaldar todo** produce una copia JSON. **Paquete territorial** genera un ZIP con HTML autónomo, informe, datos, capas GeoJSON, fuentes y manuales. Las acciones se incluyen solo cuando se marca esa opción. Las copias no se sincronizan.

ABRIR_SIN_SERVIDOR.html permite consultar el ejemplo ya preparado, sin explorar nuevas carpetas. Para editar bases grandes use INICIAR.bat: la cuota del navegador puede ser insuficiente. El ZIP de transferencia excluye el entorno instalado; en otro equipo con Python 3.12 o superior, ejecute INSTALAR.bat una vez con internet y luego INICIAR.bat. Conserve la estructura completa.

## Archivos principales

| Ubicación | Contenido |
| --- | --- |
| app/ | Interfaz, bibliotecas locales, catálogo colombiano y ejemplo de Cali. |
| servidor.py, repositorio.py, microplan/ | Servidor, adaptador y lector original de v5. |
| datos/ | Instantánea inicial y base operativa cuando se guarda. |
| cache/ | Recortes regenerables; nunca sustituye las fuentes originales. |
| manuales/ | Documentación de usuario, sistema, datos y alcance. |
| referencia/ | Antecedentes, hashes y registro de verificación. |
| tests/, herramientas/ | Pruebas y preparación de la distribución. |

## Desarrollo y verificación

```text
node --test tests/core.test.js tests/repository.test.js
.venv\Scripts\python.exe tests/test_servidor.py
.venv\Scripts\python.exe tests/test_repositorio.py
.venv\Scripts\python.exe herramientas/render_manuales.py
.venv\Scripts\python.exe herramientas/empaquetar.py
```

Después de editar interfaz o manuales, actualice el paquete incrustado con empaquetar.py. Las comprobaciones ejecutadas y sus límites se registran en referencia/VERIFICACION.json.

## Alcance

Prototipo funcional local para un usuario, sin conexión automática a CAC/REPS, cuentas institucionales ni trabajo simultáneo. El catálogo general procede de v5: 33 unidades departamentales y 1.122 municipales; estos conteos no certifican DIVIPOLA vigente. La lectura de Cali usa el límite original de COL.

El lector de fuentes se reutiliza desde v5; el análisis de red de la interfaz conecta vértices compartidos y no reproduce toda la segmentación de aquel motor. Los raster se detectan, sin análisis raster. Las fichas de evidencia iniciales son borradores vacíos; no se inventaron recomendaciones clínicas. El ensayo sintético permanece opcional y desactivado inicialmente. Las condiciones de uso de los insumos y activos se conservan.
