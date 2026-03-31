import streamlit as st
import ee
import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import os
import time
import numpy as np
import json
from google.oauth2 import service_account

st.set_page_config(layout="wide")
st.title("🌍 Índices Espectrales con Earth Engine")

# --- Initialize Session State ---
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'coords': [None, None, None, None],
        'thumb_created': False,
        'image': None,
        'thumb_url': None,
        'export_name': "Image_Export",
        'export_folder': "GEE_Exports",
        'export_format': "GeoTIFF",
        'export_crs': "EPSG:32719",
        'export_scale': 10,
        'last_draw_coords': None,
        'last_error': None,
        'processing': False,
        'data_quality': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Google Cloud Project (Top Left) ---
top_left, top_right = st.columns([1, 1])
with top_left:
    st.subheader("☁️ Proyecto de Google Cloud")
    try:
        # Try to load service account from secrets
        if "earth_engine" in st.secrets:
            # Convert TOML back to dict for Google auth
            service_account_info = dict(st.secrets["earth_engine"])
        
            # The private key comes with escaped newlines, need to handle carefully
            if "private_key" in service_account_info:
                # Ensure proper line breaks in private key
                service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
        
            # Create credentials
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/earthengine']
            )
        
            # Initialize Earth Engine with service account
            ee.Initialize(credentials, project=creds_info['project_id'])
            ee.Authenticate()
            st.success("✅ Earth Engine connected via Service Account!")
        
        else:
            # Fall back to individual user projects
            st.info("ℹ️ No service account found. Using individual Google Cloud projects.")
            # Your existing project selection code here...
        
    except Exception as e:
        st.error(f"❌ Failed to initialize Earth Engine: {e}")
        st.stop()
 



# --- Visualization Parameters (Top Right) ---
with top_right:
    st.subheader("🎨 Parámetros de Visualización")
    
    col1, col2 = st.columns(2)
    with col1:
        color1 = st.color_picker("Color para valor mínimo", "#000000")
        vis_min = st.number_input("Valor mínimo", value=0.0, step=0.1, format="%.2f")
    
    with col2:
        color2 = st.color_picker("Color para valor máximo", "#00FF00")
        vis_max = st.number_input("Valor máximo", value=1.0, step=0.1, format="%.2f")
    
    selected_palette = [color1, color2]
    
    # Add option to mask missing data
    mask_missing = st.checkbox("🖼️ Enmascarar áreas sin datos", value=False, 
                               help="Las áreas sin información se mostrarán en gris")

# --- Index Information Dictionary ---
INDEX_INFO = {
    "NDVI": "🌿 **Normalized Difference Vegetation Index** - Mide la salud de la vegetación. (-1 a 1, valores altos = vegetación densa)",
    "SAVI": "🌱 **Soil Adjusted Vegetation Index** - Similar al NDVI pero corrige por brillo del suelo. Usa factor L=0.5",
    "EVI": "🌳 **Enhanced Vegetation Index** - Optimizado para áreas con mucha biomasa, reduce influencia atmosférica",
    "NDMI": "💧 **Normalized Difference Moisture Index** - Mide contenido de humedad en vegetación",
    "GNDVI": "🍃 **Green NDVI** - Sensible a la concentración de clorofila en cultivos",
    "IPVI": "📊 **Infrared Percentage Vegetation Index** - Versión simplificada del NDVI",
    "MNDWI": "🌊 **Modified Normalized Difference Water Index** - Mejor para detectar cuerpos de agua",
    "GARI": "🌈 **Globally Adapted Relative Index** - Adaptado para diferentes condiciones globales",
    "NDWI": "💦 **Normalized Difference Water Index** - Detecta cuerpos de agua",
    "MBI": "🏜️ **Modified Bare Soil Index** - Identifica suelo desnudo",
    "EMBI": "🏝️ **Enhanced Modified Bare Index** - Versión mejorada para suelo desnudo",
    "BaI": "⛰️ **Bare Soil Index** - Índice de suelo desnudo",
    "DBI": "🏜️ **Dry Bareness Index** - Índice de aridez del suelo",
    "CALI": "🌾 **Canopy Adjusted LI** - Ajustado para cobertura de dosel",
    "DOLI": "🍂 **Dry Organic LI** - Índice de materia orgánica seca",
    "NDSI": "❄️ **Normalized Difference Snow Index** - Detecta nieve y hielo",
    "NDGI": "🧪 **Normalized Difference Greenness Index** - Mide verdor",
    "ARVI": "🌍 **Atmospherically Resistant Vegetation Index** - Resistente a efectos atmosféricos",
    "FEAI": "🏗️ **Feature Extraction AI** - Índice para extracción de características"
}

# --- Helper function to get dataset recommendations ---
def get_dataset_recommendations(error_message):
    """Provide dataset recommendations based on error type"""
    error_lower = str(error_message).lower()
    
    if "no images" in error_lower or "no se encontraron" in error_lower:
        return {
            "title": "📸 No se encontraron imágenes",
            "message": "No hay imágenes disponibles para el área y período seleccionados.",
            "suggestions": [
                "🔍 **Ampliar el rango de fechas** - Prueba con un período de 2-3 meses",
                "🗺️ **Seleccionar un área más grande** - El área actual puede ser muy pequeña o estar sin cobertura",
                "☁️ **Aumentar tolerancia a nubes** - Algunas áreas tienen mucha nubosidad constante",
                "📅 **Usar fechas más recientes** - Las imágenes Sentinel-2 están disponibles desde 2015"
            ]
        }
    elif "cloud" in error_lower or "cloudy" in error_lower:
        return {
            "title": "☁️ Problemas con nubes",
            "message": "Las imágenes disponibles tienen demasiada cobertura de nubes.",
            "suggestions": [
                "📅 **Ampliar el rango de fechas** - Más días aumentan la probabilidad de encontrar días despejados",
                "☁️ **Aumentar el porcentaje de nubes permitido** - Prueba con 50% o 80%",
                "🗺️ **Seleccionar un área diferente** - Algunas zonas son naturalmente más nubladas",
                "🔧 **Usar colección con filtro de nubes** - Ya estamos usando S2_SR_HARMONIZED que tiene corrección atmosférica"
            ]
        }
    elif "geometry" in error_lower or "bounds" in error_lower:
        return {
            "title": "🗺️ Problemas con el área seleccionada",
            "message": "El área seleccionada no es válida o está fuera de los límites.",
            "suggestions": [
                "📍 **Verificar coordenadas** - Asegúrate que latitud esté entre -90 y 90, longitud entre -180 y 180",
                "📏 **Aumentar el tamaño del área** - El área puede ser demasiado pequeña",
                "🖱️ **Dibujar nuevamente** - Intenta dibujar el rectángulo otra vez en el mapa"
            ]
        }
    elif "timeout" in error_lower or "too large" in error_lower:
        return {
            "title": "⏱️ Tiempo de procesamiento excedido",
            "message": "La solicitud está tomando demasiado tiempo o el área es muy grande.",
            "suggestions": [
                "🗺️ **Reducir el área de interés** - El área actual puede ser demasiado extensa",
                "📏 **Aumentar la escala** - Prueba con una resolución espacial mayor (30m o 60m)",
                "📅 **Reducir el rango de fechas** - Menos imágenes para procesar"
            ]
        }
    else:
        return {
            "title": "⚠️ Error inesperado",
            "message": f"Ocurrió un error al procesar los datos: {error_message}",
            "suggestions": [
                "🔄 **Intentar nuevamente** - A veces es un problema temporal",
                "📅 **Ampliar el rango de fechas** - Más datos pueden ayudar",
                "🗺️ **Seleccionar un área diferente** - Prueba con otra ubicación",
                "💬 **Verificar conexión** - Asegúrate de que Earth Engine esté funcionando correctamente"
            ]
        }

# --- Helper function to check data coverage ---
def check_data_coverage(image, geometry, index_name):
    """Check if the image has sufficient data coverage"""
    try:
        # Get pixel count and statistics
        stats = image.reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=geometry,
            scale=1000,  # 1km resolution for quick check
            maxPixels=1e9,
            bestEffort=True
        )
        
        pixel_count = stats.get('index').getInfo()
        
        if pixel_count is None or pixel_count == 0:
            return {
                'has_data': False,
                'message': "⚠️ No se encontraron datos válidos en el área seleccionada.",
                'suggestion': "📅 Prueba con un rango de fechas más amplio (2-3 meses) para tener más imágenes disponibles."
            }
        
        # Check if the area is partially covered
        total_pixels = geometry.area().divide(1000 * 1000).getInfo()  # Approximate 1km pixels
        coverage_ratio = pixel_count / total_pixels if total_pixels > 0 else 0
        
        if coverage_ratio < 0.3:
            return {
                'has_data': True,
                'coverage_ratio': coverage_ratio,
                'warning': f"⚠️ Solo {coverage_ratio:.1%} del área tiene datos válidos.",
                'suggestion': "📅 Considera ampliar el rango de fechas para obtener mejor cobertura espacial."
            }
        
        return {
            'has_data': True,
            'coverage_ratio': coverage_ratio,
            'quality': 'good'
        }
        
    except Exception as e:
        return {
            'has_data': False,
            'message': f"Error al verificar la cobertura de datos: {str(e)}"
        }

# --- Coordinates (Middle Left) & Time (Middle Right) ---
middle_left, middle_right = st.columns([1.5, 1])
with middle_left:
    st.subheader("📍 Coordenadas Manualmente")
    
    col1, col2 = st.columns(2)
    with col1:
        lon_min = st.number_input("Longitud Mín", value=st.session_state.coords[0] or -76.5, format="%.6f")
        lat_min = st.number_input("Latitud Mín", value=st.session_state.coords[1] or -16.5, format="%.6f")
    with col2:
        lon_max = st.number_input("Longitud Máx", value=st.session_state.coords[2] or -75.5, format="%.6f")
        lat_max = st.number_input("Latitud Máx", value=st.session_state.coords[3] or -15.5, format="%.6f")

    if lon_max > lon_min and lat_max > lat_min:
        manual_geometry = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max])
        st.session_state.coords = [lon_min, lat_min, lon_max, lat_max]
        # Check area size
        area_width = lon_max - lon_min
        area_height = lat_max - lat_min
        area_size = area_width * area_height
        if area_size < 0.0001:
            st.warning("⚠️ El área seleccionada es muy pequeña. Considera ampliarla para mejores resultados.")
        st.success(f"✅ Área manual: ({lon_min:.4f}, {lat_min:.4f}) a ({lon_max:.4f}, {lat_max:.4f})")
    else:
        manual_geometry = None
        st.warning("⚠️ Ingrese coordenadas válidas (máx > mín)")

with middle_right:
    st.subheader("📅 Rango de tiempo")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha inicial", value=datetime.date(2025, 4, 1))
    with col2:
        end_date = st.date_input("Fecha final", value=datetime.date(2025, 5, 1))
    
    st.subheader("☁️ Tolerancia de nubes (%)")
    cloud_tolerance = st.slider(
        "Maxima covertura permitida",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        help="Porcentaje máximo de nubes permitido en las imágenes. Valores más altos incluyen más imágenes pero pueden tener nubes."
    )
    
    # Calculate date range length
    date_range_days = (end_date - start_date).days
    if date_range_days < 30:
        st.info(f"ℹ️ Rango de {date_range_days} días. Si no hay datos, amplía a 2-3 meses.")
    elif date_range_days > 180:
        st.info(f"ℹ️ Rango de {date_range_days} días. Procesar muchas imágenes puede tomar tiempo.")
    
    # Validate date range
    if start_date >= end_date:
        st.error("❌ La fecha final debe ser posterior a la inicial")
        valid_dates = False
    else:
        valid_dates = True

# --- Bottom Layout: Map Left, Preview/Export Right ---
bottom_left, bottom_right = st.columns([1.5, 1])

with bottom_left:
    st.subheader("🗺️ Dibujar Rectángulo en el Mapa")
    
    # Calculate map center
    if all(c is not None for c in st.session_state.coords):
        center = [
            (st.session_state.coords[1] + st.session_state.coords[3]) / 2,
            (st.session_state.coords[0] + st.session_state.coords[2]) / 2
        ]
    else:
        center = [-16.0, -76.0]  # Default center (Peru coast)

    m = folium.Map(location=center, zoom_start=8)

    # Draw existing rectangle if coordinates exist
    if all(c is not None for c in st.session_state.coords):
        try:
            rect = folium.Rectangle(
                bounds=[
                    [st.session_state.coords[1], st.session_state.coords[0]],
                    [st.session_state.coords[3], st.session_state.coords[2]]
                ],
                color="blue",
                fill=True,
                fill_opacity=0.2,
                popup="Área seleccionada"
            )
            rect.add_to(m)
            
            # Add markers for corners
            folium.Marker([st.session_state.coords[1], st.session_state.coords[0]], 
                         popup="Esquina SO", icon=folium.Icon(color='green', icon='info-sign')).add_to(m)
            folium.Marker([st.session_state.coords[3], st.session_state.coords[2]], 
                         popup="Esquina NE", icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
        except:
            pass

    # Add drawing tools
    Draw(
        export=False,
        draw_options={
            'rectangle': {
                'shapeOptions': {
                    'color': '#FF0000',
                    'weight': 3
                }
            },
            'polyline': False,
            'polygon': False,
            'circle': False,
            'marker': False,
            'circlemarker': False
        },
        position='topleft'
    ).add_to(m)

    # Display map
    draw_result = st_folium(m, width=700, height=500, key="map")

    # Process drawing result
    if draw_result and draw_result.get("last_active_drawing"):
        geom = draw_result["last_active_drawing"].get("geometry")
        if geom and geom["type"] == "Polygon":
            coords = geom["coordinates"][0]
            d_lon_min = min(p[0] for p in coords)
            d_lon_max = max(p[0] for p in coords)
            d_lat_min = min(p[1] for p in coords)
            d_lat_max = max(p[1] for p in coords)
            
            # Update session state
            st.session_state.coords = [d_lon_min, d_lat_min, d_lon_max, d_lat_max]
            st.session_state.last_draw_coords = [d_lon_min, d_lat_min, d_lon_max, d_lat_max]
            
            st.success(f"""
                ✅ Rectángulo dibujado:
                ({d_lon_min:.4f}, {d_lat_min:.4f}) a ({d_lon_max:.4f}, {d_lat_max:.4f})
            """)
            st.rerun()
        else:
            st.warning("⚠️ Por favor, dibuje solo un rectángulo")

# Define geometry if coordinates are valid
if all(c is not None for c in st.session_state.coords):
    geometry = ee.Geometry.Rectangle(st.session_state.coords)
else:
    geometry = None

# --- Index Selection, Preview and Export (Bottom Right) ---
with bottom_right:
    st.subheader("📊 Selección de Índice")
    
    # Index categories
    index_groups = {
        "🌿 Vegetación": ["NDVI", "SAVI", "EVI", "NDMI", "GNDVI", "IPVI", "GARI", "ARVI"],
        "💧 Agua": ["NDWI", "MNDWI"],
        "🏜️ Suelo": ["MBI", "EMBI", "BaI", "DBI", "CALI", "DOLI"],
        "❄️ Otros": ["NDSI", "NDGI", "FEAI"]
    }

    # Create selectbox with categories
    index_options = []
    for category, items in index_groups.items():
        index_options.append(f"─── {category} ───")
        index_options.extend(items)
    
    valid_indices = []
    for items in index_groups.values():
        valid_indices.extend(items)
    
    selected_raw = st.selectbox("Seleccionar índice espectral", index_options, index=2)
    
    # Get actual index name
    if selected_raw.startswith("───"):
        index = valid_indices[0]  # Default to first valid index
    else:
        index = selected_raw
    
    # Show index information
    if index in INDEX_INFO:
        st.info(INDEX_INFO[index])
    
    # Preview generation button
    col1, col2 = st.columns(2)
    with col1:
        generate_preview = st.button("🖼️ Generar Vista Previa", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Limpiar", use_container_width=True):
            st.session_state.thumb_created = False
            st.session_state.image = None
            st.session_state.last_error = None
            st.session_state.processing = False
            st.session_state.data_quality = None
            st.rerun()
    
    # Generate preview
    if generate_preview:
        if not geometry:
            st.error("❌ Primero defina un área de interés (dibuje en el mapa o ingrese coordenadas)")
        elif not valid_dates:
            st.error("❌ Verifique el rango de fechas")
        else:
            # Set processing state
            st.session_state.processing = True
            st.session_state.thumb_created = False
            
            # Create status placeholder
            status_placeholder = st.empty()
            status_placeholder.info("📡 Buscando imágenes disponibles...")
            
            try:
                # Get image collection with cloud filtering
                collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
                    .filterBounds(geometry) \
                    .filterDate(str(start_date), str(end_date)) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_tolerance))
                
                # Check if collection has images
                count = collection.size().getInfo()
                if count == 0:
                    # No images found - show helpful message
                    recommendations = get_dataset_recommendations("No images found")
                    status_placeholder.error(f"❌ {recommendations['title']}")
                    st.warning(recommendations['message'])
                    st.markdown("### 💡 Sugerencias:")
                    for suggestion in recommendations['suggestions']:
                        st.markdown(suggestion)
                    st.session_state.last_error = "no_images"
                    st.session_state.processing = False
                    st.stop()
                
                status_placeholder.info(f"✅ {count} imágenes encontradas. Creando compuesto mediano...")
                composite = collection.median()
                
                # Calculate selected index
                if index == "NDVI":
                    image = composite.normalizedDifference(['B8', 'B4']).rename('index')
                elif index == "SAVI":
                    image = composite.expression(
                        '((NIR - RED) / (NIR + RED + L)) * (1 + L)', {
                        'NIR': composite.select('B8'),
                        'RED': composite.select('B4'),
                        'L': 0.5
                    }).rename('index')
                elif index == "EVI":
                    image = composite.expression(
                        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
                        'NIR': composite.select('B8'),
                        'RED': composite.select('B4'),
                        'BLUE': composite.select('B2')
                    }).rename('index')
                elif index == "NDMI":
                    image = composite.normalizedDifference(['B8', 'B11']).rename('index')
                elif index == "GNDVI":
                    image = composite.normalizedDifference(['B8', 'B3']).rename('index')
                elif index == "IPVI":
                    image = composite.expression('NIR / (NIR + RED)', {
                        'NIR': composite.select('B8'),
                        'RED': composite.select('B4')
                    }).rename('index')
                elif index == "NDWI":
                    image = composite.normalizedDifference(['B3', 'B8']).rename('index')
                elif index == "MNDWI":
                    image = composite.normalizedDifference(['B3', 'B11']).rename('index')
                elif index == "GARI":
                    image = composite.expression(
                        '(NIR - (GREEN - (BLUE - RED))) / (NIR + (GREEN - (BLUE - RED)))', {
                        'NIR': composite.select('B8'),
                        'GREEN': composite.select('B3'),
                        'BLUE': composite.select('B2'),
                        'RED': composite.select('B4')
                    }).rename('index')
                elif index == "ARVI":
                    image = composite.expression(
                        '(NIR - (2*RED - BLUE)) / (NIR + (2*RED - BLUE))', {
                        'NIR': composite.select('B8'),
                        'RED': composite.select('B4'),
                        'BLUE': composite.select('B2')
                    }).rename('index')
                elif index == "MBI":
                    image = composite.expression(
                        '((SWIR1 - NIR) / (SWIR1 + NIR) + 0.5) - ((GREEN - NIR) / (GREEN + NIR) + 0.5)', {
                            'SWIR1': composite.select('B11'),
                            'NIR': composite.select('B8'),
                            'GREEN': composite.select('B3')
                        }).rename('index')
                elif index == "EMBI":
                    image = composite.expression(
                        '(((((S1 - S2 - N) / (S1 + S2 + N)) + 0.5) - ((G - S1) / (G + S1)) - 0.5) / '
                        '((((S1 - S2 - N) / (S1 + S2 + N)) + 0.5) + ((G - S1) / (G + S1)) + 1.5))', {
                            'S1': composite.select('B11'),
                            'S2': composite.select('B12'),
                            'N': composite.select('B8'),
                            'G': composite.select('B3'),
                        }).rename('index')
                elif index == "BaI":
                    image = composite.expression(
                        '(SWIR1 - NIR) / (SWIR1 + NIR)', {
                            'SWIR1': composite.select('B11'),
                            'NIR': composite.select('B8')
                        }).rename('index')
                elif index == "DBI":
                    image = composite.expression(
                        '(SWIR1 - GREEN) / (SWIR1 + GREEN)', {
                            'SWIR1': composite.select('B11'),
                            'GREEN': composite.select('B3')
                        }).rename('index')
                elif index == "CALI":
                    image = composite.expression(
                        '((NIR - RED) / (NIR + RED + L)) * (1 + L) * (1 - (BLUE / NIR))', {
                            'NIR': composite.select('B8'),
                            'RED': composite.select('B4'),
                            'BLUE': composite.select('B2'),
                            'L': 0.5
                        }).rename('index')
                elif index == "DOLI":
                    image = composite.expression(
                        '(SWIR1 - SWIR2) / (SWIR1 + SWIR2)', {
                            'SWIR1': composite.select('B11'),
                            'SWIR2': composite.select('B12')
                        }).rename('index')
                elif index == "NDSI":
                    image = composite.expression(
                        '(GREEN - SWIR1) / (GREEN + SWIR1)', {
                            'GREEN': composite.select('B3'),
                            'SWIR1': composite.select('B11')
                        }).rename('index')
                elif index == "NDGI":
                    image = composite.normalizedDifference(['B3', 'B4']).rename('index')
                elif index == "FEAI":
                    image = composite.expression(
                        '((NIR - RED) * (SWIR1 - GREEN)) / ((NIR + RED + SWIR1 + GREEN) + 1)', {
                            'NIR': composite.select('B8'),
                            'RED': composite.select('B4'),
                            'SWIR1': composite.select('B11'),
                            'GREEN': composite.select('B3')
                        }).rename('index')
                else:
                    st.error(f"❌ Fórmula para {index} no implementada aún")
                    st.session_state.processing = False
                    st.stop()
                
                # Apply mask to remove areas with no data (where index is NaN or outside bounds)
                if mask_missing:
                    # Create mask for valid data (within visualization range)
                    masked_image = image.updateMask(
                        image.gte(vis_min).And(image.lte(vis_max))
                    )
                    # Add a constant band for no-data areas to show as gray
                    no_data = masked_image.unmask(-9999)
                    display_image = no_data
                else:
                    display_image = image
                
                status_placeholder.info("🎨 Generando visualización...")
                
                # Generate thumbnail with custom visualization for masked areas
                if mask_missing:
                    # Use a custom palette that includes gray for no-data
                    thumb_params = {
                        'region': geometry,
                        'dimensions': 512,
                        'palette': selected_palette,
                        'min': vis_min,
                        'max': vis_max,
                        'format': 'png'
                    }
                else:
                    thumb_params = {
                        'region': geometry,
                        'min': vis_min,
                        'max': vis_max,
                        'dimensions': 512,
                        'palette': selected_palette,
                        'format': 'png'
                    }
                
                thumb_url = display_image.getThumbURL(thumb_params)
                
                # Check data coverage
                status_placeholder.info("🔍 Verificando cobertura de datos...")
                coverage_check = check_data_coverage(image, geometry, index)
                
                # Store in session state
                st.session_state.image = image
                st.session_state.thumb_url = thumb_url
                st.session_state.thumb_created = True
                st.session_state.data_quality = coverage_check
                st.session_state.last_error = None
                
                # Clear status placeholder
                status_placeholder.empty()
                
                # Show coverage warnings if needed
                if coverage_check.get('warning'):
                    st.warning(coverage_check['warning'])
                    st.info(coverage_check['suggestion'])
                elif not coverage_check.get('has_data'):
                    st.error(coverage_check['message'])
                    st.info(coverage_check['suggestion'])
                else:
                    st.success("✅ ¡Vista previa generada exitosamente!\nPuede tardar un momento en cargar.")
                
            except ee.ee_exception.EEException as e:
                error_msg = str(e)
                recommendations = get_dataset_recommendations(error_msg)
                
                status_placeholder.empty()
                st.error(f"❌ {recommendations['title']}")
                st.warning(recommendations['message'])
                st.markdown("### 💡 Sugerencias:")
                for suggestion in recommendations['suggestions']:
                    st.markdown(suggestion)
                
                with st.expander("🔧 Información técnica para depuración"):
                    st.code(error_msg)
                    st.markdown(f"**Área:** {geometry.getInfo() if geometry else 'No definida'}")
                    st.markdown(f"**Fechas:** {start_date} a {end_date}")
                    st.markdown(f"**Tolerancia de nubes:** {cloud_tolerance}%")
                
                st.session_state.last_error = error_msg
                st.session_state.processing = False
                
            except Exception as e:
                error_msg = str(e)
                recommendations = get_dataset_recommendations(error_msg)
                
                status_placeholder.empty()
                st.error(f"❌ {recommendations['title']}")
                st.warning(recommendations['message'])
                st.markdown("### 💡 Sugerencias:")
                for suggestion in recommendations['suggestions']:
                    st.markdown(suggestion)
                
                with st.expander("🔧 Información técnica para depuración"):
                    st.code(error_msg)
                
                st.session_state.last_error = error_msg
                st.session_state.processing = False
            
            finally:
                st.session_state.processing = False
    
    # Display preview if available
    if st.session_state.get("thumb_created", False) and st.session_state.thumb_url:
        st.image(st.session_state.thumb_url, caption=f"Vista previa de {index}", use_container_width=True)
        
        # Display data quality info if available
        if st.session_state.data_quality:
            quality = st.session_state.data_quality
            if quality.get('warning'):
                st.warning(quality['warning'])
                if st.button("💡 Sugerencia para mejorar cobertura", key="coverage_suggestion"):
                    st.info(quality['suggestion'])
            elif quality.get('has_data') is False:
                st.error(quality['message'])
                if st.button("💡 Ver sugerencias", key="no_data_suggestion"):
                    st.info(quality['suggestion'])
        
        # Export configuration
        with st.expander("⚙️ Configuración de Exportación", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.export_name = st.text_input("📝 Nombre del archivo", 
                                                            value=st.session_state.export_name)
                st.session_state.export_folder = st.text_input("📁 Carpeta en Drive", 
                                                              value=st.session_state.export_folder)
            with col2:
                st.session_state.export_format = st.selectbox("📦 Formato", 
                                                             ["GeoTIFF", "TFRecord"], 
                                                             index=0 if st.session_state.export_format == "GeoTIFF" else 1)
                st.session_state.export_crs = st.selectbox("🗺️ CRS", 
                                                          ["EPSG:32719", "EPSG:4326", "EPSG:3857"],
                                                          index=["EPSG:32719", "EPSG:4326", "EPSG:3857"].index(st.session_state.export_crs))
                st.session_state.export_scale = st.selectbox("📏 Escala (m/píxel)", 
                                                            [10, 20, 30, 60, 100, 250, 500],
                                                            index=[10, 20, 30, 60, 100, 250, 500].index(st.session_state.export_scale))
        
        # Export button
        if st.button("💾 Exportar a Google Drive", type="primary", use_container_width=True):
            if not geometry:
                st.error("❌ No hay geometría definida")
            else:
                try:
                    # Create export task
                    task = ee.batch.Export.image.toDrive(
                        image=st.session_state.image,
                        description=st.session_state.export_name,
                        folder=st.session_state.export_folder,
                        fileNamePrefix=st.session_state.export_name,
                        region=geometry,
                        scale=st.session_state.export_scale,
                        crs=st.session_state.export_crs,
                        fileFormat=st.session_state.export_format,
                        maxPixels=1e10,
                    )
                    task.start()
                    
                    # Monitor progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i in range(60):  # Monitor for up to 5 minutes (60 * 5s)
                        status = task.status()
                        state = status['state']
                        
                        # Update progress based on state
                        if state == 'READY':
                            progress_bar.progress(10)
                            status_text.info("⏳ Tarea preparada, esperando ejecución...")
                        elif state == 'RUNNING':
                            progress_bar.progress(50)
                            status_text.info("⚙️ Ejecutando exportación...")
                        elif state == 'COMPLETED':
                            progress_bar.progress(100)
                            status_text.success("✅ ¡Exportación completada exitosamente!")
                            break
                        elif state in ['FAILED', 'CANCELLED']:
                            error_msg = status.get('error_message', 'Error desconocido')
                            status_text.error(f"❌ Error: {error_msg}")
                            break
                        
                        time.sleep(5)
                    
                    if state not in ['COMPLETED', 'FAILED', 'CANCELLED']:
                        status_text.warning("⏱️ La exportación continúa en segundo plano. Verifique en Google Drive.")
                        
                except Exception as e:
                    st.error(f"❌ Error al iniciar exportación: {str(e)}")

# --- Sidebar with Help Information ---
with st.sidebar:
    st.header("ℹ️ Ayuda")
    st.markdown("""
    ### Cómo usar esta aplicación:
    
    1. **Conectar Earth Engine** con tu proyecto de Google Cloud
    2. **Seleccionar área de interés**:
       - Dibuja un rectángulo en el mapa
       - O ingresa coordenadas manualmente
    3. **Elegir fechas** para las imágenes
    4. **Ajustar tolerancia de nubes** si es necesario
    5. **Seleccionar índice espectral** de la lista
    6. **Generar vista previa** para ver el resultado
    7. **Exportar a Google Drive** si es necesario
    
    ### Índices disponibles:
    - **Vegetación**: NDVI, SAVI, EVI, NDMI, GNDVI, IPVI, GARI, ARVI
    - **Agua**: NDWI, MNDWI
    - **Suelo**: MBI, EMBI, BaI, DBI, CALI, DOLI
    - **Otros**: NDSI, NDGI, FEAI
    
    ### 📊 Calidad de datos:
    - La app verifica automáticamente la cobertura de datos
    - Recibirás advertencias si hay áreas sin información
    - Las áreas sin datos se muestran según la configuración de enmascarado
    
    ### 🔧 Solución de problemas:
    - **Sin datos**: Amplía el rango de fechas o aumenta tolerancia de nubes
    - **Cobertura parcial**: Usa un período de 2-3 meses para mejor cobertura
    - **Error de procesamiento**: Reduce el área o escala
    """)
    
    st.divider()
    st.caption("Desarrollado con 🌱 Earth Engine y Streamlit")
