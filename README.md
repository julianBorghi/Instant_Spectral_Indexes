WebApp para calcular Indices Espectrales de cualquier lugar Instantaneamente usando GEE y Streamlit

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)
[![Earth Engine](https://img.shields.io/badge/Earth-Engine-4285F4)](https://earthengine.google.com/)

## 🚀 Demo

[https://t9cjpdsbnpqew36ejug6f6.streamlit.app/](https://t9cjpdsbnpqew36ejug6f6.streamlit.app/)

Hosted en Streamlit cloud

## Tabla de Contenidos
- [Características](#características)
- [Índices Disponibles](#índices-disponibles)
- [Uso](#uso)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)

## Características

- **19+ Índices Espectrales** - Vegetación, agua, suelo y más
- **Selección de Área** - Dibuja en el mapa o ingresa coordenadas manualmente
- **Filtro Temporal** - Selecciona rangos de fechas personalizados
- **Control de Nubes** - Ajusta el porcentaje de tolerancia de nubes
- **Vista Previa** - Visualización instantánea del índice seleccionado
- **Exportación** - Descarga resultados a Google Drive (GeoTIFF/TFRecord)
- **Detección de Calidad** - Verifica automáticamente la cobertura de datos
- **Muy Facil de Actualizar y Escalar** - Con Streamlit, Python y arquitectura Minimalista

## Índices Disponibles

### Vegetación
| Índice | Nombre | Aplicación |
|--------|--------|------------|
| NDVI | Normalized Difference Vegetation Index | Salud de vegetación |
| SAVI | Soil Adjusted Vegetation Index | Vegetación en suelos desnudos |
| EVI | Enhanced Vegetation Index | Áreas con alta biomasa |
| NDMI | Normalized Difference Moisture Index | Contenido de humedad |
| GNDVI | Green NDVI | Concentración de clorofila |
| IPVI | Infrared Percentage Vegetation Index | Versión simplificada de NDVI |
| GARI | Globally Adapted Relative Index | Condiciones globales |
| ARVI | Atmospherically Resistant VI | Resistente a efectos atmosféricos |

### Agua
| Índice | Nombre | Aplicación |
|--------|--------|------------|
| NDWI | Normalized Difference Water Index | Cuerpos de agua |
| MNDWI | Modified NDWI | Mejor detección de agua |

###  Suelo
| Índice | Nombre | Aplicación |
|--------|--------|------------|
| MBI | Modified Bare Soil Index | Suelo desnudo |
| EMBI | Enhanced Modified Bare Index | Versión mejorada |
| BaI | Bare Soil Index | Índice de suelo desnudo |
| DBI | Dry Bareness Index | Aridez del suelo |
| CALI | Canopy Adjusted LI | Cobertura de dosel |
| DOLI | Dry Organic LI | Materia orgánica seca |

### Otros
| Índice | Nombre | Aplicación |
|--------|--------|------------|
| NDSI | Normalized Difference Snow Index | Nieve y hielo |
| NDGI | Normalized Difference Greenness Index | Verdor general |
| FEAI | Feature Extraction AI | Extracción de características |


## Dependencias

streamlit>=1.28.0

earthengine-api>=0.1.370

folium>=0.14.0

streamlit-folium>=0.15.0

numpy>=1.24.0

google-auth>=2.23.0

google-cloud-storage>=2.10.0

## Uso
### Paso 1: Definir Área de Interés

Opción A: Dibuja un rectángulo en el mapa

Opción B: Ingresa coordenadas manualmente

### Paso 2: Seleccionar Parámetros

Rango de fechas (recomendado: 2-3 meses para buena cobertura)

Tolerancia de nubes (20-50% para áreas nubladas)

Elegir indice espectral deseado

### Paso 3: Generar Vista Previa

Haz clic en "Generar Vista Previa"

Espera a que se procese (10-30 segundos)

### Paso 4: Exportar (opcional)

Configura nombre, carpeta y formato

Exporta a Google Drive


## Roadmap
Soporte para Landsat (bandas térmicas)

Series temporales y gráficos de tendencias

Descarga de estadísticas zonales (CSV)

Más índices (NDRE, CVI, etc.)

Soporte para múltiples idiomas

Comparación lado a lado de índices


## Licencia
Distribuido bajo licencia MIT. Ver LICENSE para más información.

## Agradecimientos
Google Earth Engine - Plataforma de análisis geoespacial

Streamlit - Framework para aplicaciones de datos

Copernicus Sentinel-2 - Imágenes satelitales

## Contacto
Julian Eduardo Borghi - juedborghi@ejemplo.com - tambien en LinkedIn

Link del Proyecto: https://github.com/tuusername/gee-spectral-indices

⭐️ ¡No olvides darle una estrella si este proyecto te fue útil!
