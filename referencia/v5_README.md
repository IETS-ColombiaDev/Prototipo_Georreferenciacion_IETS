# Herramienta de extracción para los cuadernillos de microplanificación

Versión 5.0. Aplicación Python para localhost. Genera exactamente tres cuadernillos Excel, CSV con procedencia, mapas, infografía y un Geoportal.html autónomo. Conserva los originales.

## Inicio en Windows

1. Instale Python 3.12 de 64 bits.
2. Extraiga la distribución completa en una carpeta nueva `microplanificacion_v5`.
3. Ejecute `INSTALAR.bat` una vez. Requiere internet para instalar dependencias.
4. Ejecute `INICIAR.bat`. Abra http://127.0.0.1:8505.
5. Seleccione territorio, fuentes y años. Genere un resultado nuevo.

La versión 4 conserva su carpeta y puerto 8504. Cierre la consola de la versión que termine de usar. Los archivos ya exportados no se actualizan al instalar v5.

## Paquete para GitHub

`Microplanificacion_v5_GitHub.zip` contiene código, pruebas y manuales. No contiene los datos nacionales ni las tablas preparadas. Copie localmente `data`, `geo` y `assets` de la distribución autorizada antes de ejecutar. `.gitignore` excluye datos, resultados, caché y entornos. No se ha publicado un repositorio remoto.

Estructura requerida:

```text
microplanificacion_v5/
  app.py
  microplan/
  assets/ops_logo-es.png (y en, fr, pt)
  data/ejemplos/ (exactamente tres XLSX originales)
  data/poblacion/ (tablas preparadas)
  data/coberturas/ (tablas preparadas)
  data/promt/ciudades.docx
  geo/adm0/ geo/adm1/ geo/adm2*/ geo/report/ geo/spatial/
  manuales/
  output/
```

Fuera del proyecto, organice cada país, por ejemplo `PER/Basicas`, `PER/PER_Escuelas`, `PER/PER_Healthsites`, `PER/PER_Vias`, `PER/PER_SitiosdeInteres`, `PER/PER_Edificios`, `PER/PER_Accesibilidad` y `PER/PER_ParaGeocodificar`. Mantenga juntos SHP, SHX, DBF y PRJ. Las tablas para geocodificar requieren columnas de latitud y longitud válidas.

## Cambios de versión 5

- Servicios de salud separados: hospitales, clínicas, farmacias, odontología, laboratorios y otros. Las farmacias no son destinos clínicos para el cálculo de recorridos.
- Localidades y comercios separados según atributos de fuente. No se deduce tipo únicamente por el nombre.
- Sitios de concentración con casilla propia según etiquetas de plazas, parques, mercados y centros comunitarios disponibles.
- Buscador con nombres alternativos, vías, coincidencias sin tildes y tecla Enter. Los nombres de vías y localidades aparecen al acercar el mapa.
- Recorridos filtrables por origen; se conservan las referencias rectas y los accesos fuera de red como capas distintas.
- Accesibilidad por servicio desde ADM0 recortada al área seleccionada. Se eliminan los selectores redundantes de categoría y escala. Permanecen medida, rangos y opacidad.
- Unidades HeiGIT: metros a km, segundos a horas y minutos. No se transforma una distancia en tiempo suponiendo velocidades.
- Intervalos sanitarios incorporables como estimaciones en los cuadernillos. Se requiere un punto único de localidad compatible; sin él se deja pendiente. La educación no se utiliza como distancia al centro de salud.

## Manuales

| Idioma | Usuario | Sistema |
| --- | --- | --- |
| Español | [PDF](manuales/usuario_es.pdf) · [Markdown](manuales/usuario_es.md) | [PDF](manuales/sistema_es.pdf) · [Markdown](manuales/sistema_es.md) |
| English | [PDF](manuales/usuario_en.pdf) · [Markdown](manuales/usuario_en.md) | [PDF](manuales/sistema_en.pdf) · [Markdown](manuales/sistema_en.md) |
| Français | [PDF](manuales/usuario_fr.pdf) · [Markdown](manuales/usuario_fr.md) | [PDF](manuales/sistema_fr.pdf) · [Markdown](manuales/sistema_fr.md) |
| Português | [PDF](manuales/usuario_pt.pdf) · [Markdown](manuales/usuario_pt.md) | [PDF](manuales/sistema_pt.pdf) · [Markdown](manuales/sistema_pt.md) |

## Desarrollo y pruebas

```powershell
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe scripts\example_chacao_v5.py --country-root "D:\ruta\VEN"
```

La prueba completa requiere los datos autorizados incluidos en la distribución local. GitHub Actions ejecuta las pruebas aisladas con datos sintéticos temporales. Para reconstruir manuales instale además `requirements-dev.txt` y ejecute `scripts/manuals_v5.py`.

Revise `Informe.json`, `Trazabilidad.json`, `Celdas_diligenciadas.csv` y `Datos/accesibilidad_localidades_salud.csv`. El ejemplo Chacao contiene las tres accesibilidades; la fuente puntual de localidades devuelve cero en ese recorte y sus tiempos localidad–salud quedan pendientes. Esto no se sustituye por un centroide ni por un tiempo inventado.

## Métodos y límites

La accesibilidad de HeiGIT describe umbrales modelados de viaje motorizado; no identifica necesariamente un establecimiento individual. Se toma el menor umbral que contiene el punto y su umbral anterior. Se conserva la categoría sanitaria y la procedencia. Los intervalos no son tiempos exactos.

Las rutas utilizan la red disponible dentro del recorte, sin verificación de transitabilidad ni velocidades. El destino es el más cercano entre los establecimientos clínicos disponibles dentro de esa red; no se garantiza el más cercano fuera del área. No se suman poblaciones entre isócronas acumuladas. Las pendientes de vacunación se llenan solo con información compatible.

Referencias: [unidades y categorías HeiGIT](https://giscience.github.io/gis-training-resource-center/en/GIS_AA/en_gaia_indicators_processing.html) y [metodología OpenAccessLens](https://heigit.org/global-data-on-healthcare-and-education-accessibility-with-openaccesslens/).

Vea [correspondencia con los ajustes solicitados](docs/REQUISITOS_V5.md). Antes de distribuir datos o logotipos fuera del entorno autorizado, respete sus condiciones de uso. Las bibliotecas incluidas conservan sus avisos en `vendor`.
