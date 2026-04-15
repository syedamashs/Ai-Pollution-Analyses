#!/usr/bin/env python3
"""Flask Web UI for GreenTamilNadu - AI Pollution Analysis System"""
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pathlib import Path
import os
import requests
import numpy as np
import cv2
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
import threading
from scripts.tree_recommendation_model import get_tree_recommendation_model
from scripts.forecasting import get_aqi_forecaster

# Configuration and defaults
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'b94f9c7458972cd296068cfa48e2db31')

# City coordinates and simple area list
CITY_COORDS = {
    'madurai': {'lat': 9.9252, 'lon': 78.1198, 'name': 'Madurai'},
    'chennai': {'lat': 13.0827, 'lon': 80.2707, 'name': 'Chennai'},
    'coimbatore': {'lat': 11.0081, 'lon': 76.8956, 'name': 'Coimbatore'},
    'dindigul': {'lat': 10.3673, 'lon': 77.9757, 'name': 'Dindigul'},
    'trichy': {'lat': 10.7905, 'lon': 78.7047, 'name': 'Trichy'}
}

AREAS = [{'id': k, 'name': v['name']} for k, v in CITY_COORDS.items()]

# In-memory holder for analysis results
ANALYSIS_DATA = {}

# In-memory cache for AQI data (to avoid repeated API calls)
AQI_CACHE = {}
AQI_CACHE_TIMEOUT = 600  # Cache for 10 minutes

# In-memory cache for historical AQI backfill used by forecasting
AQI_HISTORY_CACHE = {}
AQI_HISTORY_CACHE_TIMEOUT = 1800  # Cache for 30 minutes

# Flask app
BASE_DIR = Path(__file__).resolve().parent.parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / 'templates'),
    static_folder=str(BASE_DIR / 'static'),
)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# Model singleton for AQI-based tree ranking
try:
    TREE_MODEL = get_tree_recommendation_model()
except Exception as model_init_error:
    TREE_MODEL = None
    print(f"⚠️  Tree model init failed: {model_init_error}")

# Tree recommendations by air quality category (US EPA AQI ranges)
TREE_RECOMMENDATIONS = {
    'good': [
        {'id': '1', 'name': 'Neem (நீம்)', 'scientificName': 'Azadirachta indica', 'reason': 'Tamil: Veppai - Medicinal, antibacterial properties', 'pollutionAbsorption': 'Very High', 'benefits': 'Medicinal value, pest control'},
        {'id': '2', 'name': 'Mango (மாமரம்)', 'scientificName': 'Mangifera indica', 'reason': 'Tamil: Maa - Provides fruit yield while purifying air', 'pollutionAbsorption': 'Medium', 'benefits': 'Fruit production, shade provider'},
        {'id': '3', 'name': 'Pongamia (பொங்கம்)', 'scientificName': 'Pongamia pinnata', 'reason': 'Tamil: Pungai - Biofuel potential, nitrogen-fixer', 'pollutionAbsorption': 'High', 'benefits': 'Oil production, nitrogen-fixer'},
        {'id': '4', 'name': 'Tamarind (புளி)', 'scientificName': 'Tamarindus indica', 'reason': 'Tamil: Puli - Long-lived, provides fruit and shade', 'pollutionAbsorption': 'Medium', 'benefits': 'Spice source, longgevity (200+ years)'},
        {'id': '5', 'name': 'Pipal (அரசு)', 'scientificName': 'Ficus religiosa', 'reason': 'Tamil: Aracu - Releases oxygen 24/7, sacred tree', 'pollutionAbsorption': 'Very High', 'benefits': 'Oxygen production, religious significance'},
        {'id': '6', 'name': 'Banana (வாழை)', 'scientificName': 'Musa species', 'reason': 'Tamil: Vaalai - Good oxygen production, fruit yield', 'pollutionAbsorption': 'Medium', 'benefits': 'Fruit, leaves, and fiber production'},
    ],
    'moderate': [
        {'id': '1', 'name': 'Neem (நீம்)', 'scientificName': 'Azadirachta indica', 'reason': 'Tamil: Veppai - Excellent pollution tolerance and air purification', 'pollutionAbsorption': 'Very High', 'benefits': 'Medicinal, pest control agent'},
        {'id': '2', 'name': 'Pongamia (பொங்கம்)', 'scientificName': 'Pongamia pinnata', 'reason': 'Tamil: Pungai - Hardy species that thrives in moderate pollution', 'pollutionAbsorption': 'Very High', 'benefits': 'Nitrogen-fixer, biofuel source'},
        {'id': '3', 'name': 'Tamarind (புளி)', 'scientificName': 'Tamarindus indica', 'reason': 'Tamil: Puli - Tolerates pollution with excellent oxygen release', 'pollutionAbsorption': 'High', 'benefits': 'Spice source, longgevity'},
        {'id': '4', 'name': 'Coconut (தென்னை)', 'scientificName': 'Cocos nucifera', 'reason': 'Tamil: Thennai - Air purification with economic benefits', 'pollutionAbsorption': 'High', 'benefits': 'Fruit, fiber, oil production'},
        {'id': '5', 'name': 'Jackfruit (பலா)', 'scientificName': 'Artocarpus heterophyllus', 'reason': 'Tamil: Pala - Good air purification and fruit yield', 'pollutionAbsorption': 'High', 'benefits': 'Large fruits, shade provider'},
        {'id': '6', 'name': 'Cassia (கசக்கா)', 'scientificName': 'Cassia fistula', 'reason': 'Tamil: Golden flower tree for moderate pollution', 'pollutionAbsorption': 'Medium', 'benefits': 'Beautiful flowers, medicinal'},
    ],
    'unhealthy_sensitive': [
        {'id': '1', 'name': 'Neem (நீம்)', 'scientificName': 'Azadirachta indica', 'reason': 'Tamil: Veppai - Most effective CO2 absorber, releases oxygen 24/7', 'pollutionAbsorption': 'Very High', 'benefits': 'Best for pollution, medicinal'},
        {'id': '2', 'name': 'Pipal (அரசு)', 'scientificName': 'Ficus religiosa', 'reason': 'Tamil: Aracu - Absorbs harmful gases and particulate matter', 'pollutionAbsorption': 'Very High', 'benefits': 'Oxygen production, air purification'},
        {'id': '3', 'name': 'Pongamia (பொங்கம்)', 'scientificName': 'Pongamia pinnata', 'reason': 'Tamil: Pungai - Extremely hardy in poor air quality', 'pollutionAbsorption': 'Very High', 'benefits': 'Biofuel, nitrogen-fixer'},
        {'id': '4', 'name': 'Banyan (ஆலம்)', 'scientificName': 'Ficus benghalensis', 'reason': 'Tamil: Aalam - Large canopy filters pollutants effectively', 'pollutionAbsorption': 'Very High', 'benefits': 'Massive shade, wildlife shelter'},
        {'id': '5', 'name': 'Tamarind (புளி)', 'scientificName': 'Tamarindus indica', 'reason': 'Tamil: Puli - Highly pollution-tolerant with air filtering', 'pollutionAbsorption': 'Very High', 'benefits': 'Spice source, medicinal'},
        {'id': '6', 'name': 'Acacia (கருவேல்)', 'scientificName': 'Acacia nilotica', 'reason': 'Tamil: Karuveli - Resilient to pollution', 'pollutionAbsorption': 'Very High', 'benefits': 'Drought resistant, gum production'},
    ],
    'unhealthy': [
        {'id': '1', 'name': 'Neem (நீம்)', 'scientificName': 'Azadirachta indica', 'reason': 'Tamil: Veppai - Top choice, maximum CO2 absorption', 'pollutionAbsorption': 'Very High', 'benefits': 'Best performer in poor air'},
        {'id': '2', 'name': 'Pongamia (பொங்கம்)', 'scientificName': 'Pongamia pinnata', 'reason': 'Tamil: Pungai - Extreme pollution tolerance', 'pollutionAbsorption': 'Very High', 'benefits': 'Nitrogen-fixer, biofuel'},
        {'id': '3', 'name': 'Palash (பல)', 'scientificName': 'Butea monosperma', 'reason': 'Tamil: Pala - Hardy nitrogen-fixer for degraded soils', 'pollutionAbsorption': 'Very High', 'benefits': 'Nitrogen-fixing, medicinal'},
        {'id': '4', 'name': 'Acacia (கருவேல்)', 'scientificName': 'Acacia nilotica', 'reason': 'Tamil: Karuveli - Highly resilient to extreme pollution', 'pollutionAbsorption': 'Very High', 'benefits': 'Drought resistant'},
        {'id': '5', 'name': 'Babul (கொசு)', 'scientificName': 'Acacia arabica', 'reason': 'Tamil: Kosu - Extreme hardiness in poor conditions', 'pollutionAbsorption': 'Very High', 'benefits': 'Tannin source'},
        {'id': '6', 'name': 'Pipal (அரசு)', 'scientificName': 'Ficus religiosa', 'reason': 'Tamil: Aracu - Releases oxygen 24/7 effectively', 'pollutionAbsorption': 'Very High', 'benefits': 'Oxygen production'},
        {'id': '7', 'name': 'Khejri (சிறுமகிழ)', 'scientificName': 'Prosopis cineraria', 'reason': 'Tamil: Sirumagizh - Survival tree for harsh conditions', 'pollutionAbsorption': 'Very High', 'benefits': 'Extreme hardiness'},
    ],
    'very_unhealthy': [
        {'id': '1', 'name': 'Neem (நீம்)', 'scientificName': 'Azadirachta indica', 'reason': 'Tamil: Veppai - Most pollution-tolerant, exceptional resilience', 'pollutionAbsorption': 'Very High', 'benefits': 'Top choice for severe'},
        {'id': '2', 'name': 'Pongamia (பொங்கம்)', 'scientificName': 'Pongamia pinnata', 'reason': 'Tamil: Pungai - Survives severe pollution with productivity', 'pollutionAbsorption': 'Very High', 'benefits': 'Biofuel, nitrogen-fixing'},
        {'id': '3', 'name': 'Palash (பல)', 'scientificName': 'Butea monosperma', 'reason': 'Tamil: Pala - Exceptional hardiness for severe conditions', 'pollutionAbsorption': 'Very High', 'benefits': 'Medicinal, nitrogen-fixer'},
        {'id': '4', 'name': 'Acacia (கருவேல்)', 'scientificName': 'Acacia nilotica', 'reason': 'Tamil: Karuveli - Maximum tolerance for severe pollution', 'pollutionAbsorption': 'Very High', 'benefits': 'Extreme hardiness'},
        {'id': '5', 'name': 'Babul (கொசு)', 'scientificName': 'Acacia arabica', 'reason': 'Tamil: Kosu - Extreme pollution tolerance with N-fixing', 'pollutionAbsorption': 'Very High', 'benefits': 'Tannin production'},
        {'id': '6', 'name': 'Khejri (சிறுமகிழ)', 'scientificName': 'Prosopis cineraria', 'reason': 'Tamil: Sirumagizh - Ultimate survival tree', 'pollutionAbsorption': 'Very High', 'benefits': 'Extreme hardiness'},
        {'id': '7', 'name': 'Mesquite (மெசன்)', 'scientificName': 'Prosopis juliflora', 'reason': 'Survives worst pollution with exceptional durability', 'pollutionAbsorption': 'Very High', 'benefits': 'Deep roots, hardiness'},
        {'id': '8', 'name': 'Safed Siris (சுண்ணாம்பு)', 'scientificName': 'Albizia procera', 'reason': 'High pollution absorption with nitrogen-fixing', 'pollutionAbsorption': 'Very High', 'benefits': 'Fast growing, soil improvement'},
    ],
    'hazardous': [
        {'id': '1', 'name': 'Neem (நீம்)', 'scientificName': 'Azadirachta indica', 'reason': 'Tamil: Veppai - Most pollution-tolerant species', 'pollutionAbsorption': 'Very High', 'benefits': 'Top choice for severe pollution'},
        {'id': '2', 'name': 'Pongamia (பொங்கம்)', 'scientificName': 'Pongamia pinnata', 'reason': 'Tamil: Pungai - Survives severe pollution conditions', 'pollutionAbsorption': 'Very High', 'benefits': 'Biofuel, nitrogen-fixing, resilient'},
        {'id': '3', 'name': 'Palash (பல)', 'scientificName': 'Butea monosperma', 'reason': 'Tamil: Pala - Exceptional hardiness for severe conditions', 'pollutionAbsorption': 'Very High', 'benefits': 'Medicinal, nitrogen-fixer'},
        {'id': '4', 'name': 'Acacia (கருவேல்)', 'scientificName': 'Acacia nilotica', 'reason': 'Tamil: Karuveli - Maximum tolerance for severe pollution', 'pollutionAbsorption': 'Very High', 'benefits': 'Extreme hardiness, useful products'},
        {'id': '5', 'name': 'Babul (கொசு)', 'scientificName': 'Acacia arabica', 'reason': 'Tamil: Kosu - Extreme pollution tolerance with N-fixing', 'pollutionAbsorption': 'Very High', 'benefits': 'Tannin production, resilient'},
        {'id': '6', 'name': 'Khejri (சிறுமகிழ)', 'scientificName': 'Prosopis cineraria', 'reason': 'Tamil: Sirumagizh - Ultimate survival tree', 'pollutionAbsorption': 'Very High', 'benefits': 'Extreme drought/pollution tolerance'},
        {'id': '7', 'name': 'Mesquite (மெசன்)', 'scientificName': 'Prosopis juliflora', 'reason': 'Survives worst pollution with exceptional durability', 'pollutionAbsorption': 'Very High', 'benefits': 'Deep roots, extreme hardiness'},
        {'id': '8', 'name': 'Safed Siris (சுண்ணாம்பு)', 'scientificName': 'Albizia procera', 'reason': 'High pollution absorption with nitrogen-fixing properties', 'pollutionAbsorption': 'Very High', 'benefits': 'Fast growing, soil improvement'},
    ],
}

def segment_image(image_path):
    """Segment satellite image using K-means clustering to find free land area"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Resize for faster processing
        img_resized = cv2.resize(img, (200, 200))
        
        # Reshape image to 2D array of pixels
        pixels = img_resized.reshape((-1, 3))
        pixels = np.float32(pixels)
        
        # K-means clustering with 4 clusters
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, 4, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert centers to uint8
        centers = np.uint8(centers)
        
        # Create segmented image
        segmented = centers[labels.flatten()]
        segmented_img = segmented.reshape(img_resized.shape)
        
        # Resize back to original size
        segmented_img = cv2.resize(segmented_img, (img.shape[1], img.shape[0]))
        
        # Convert to HSV for analysis
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define range for green (vegetation) - HSV
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(img_hsv, lower_green, upper_green)
        
        # Find free land (non-vegetation, non-water) - brownish/grayish areas
        lower_free = np.array([10, 30, 50])
        upper_free = np.array([30, 150, 200])
        mask_free = cv2.inRange(img_hsv, lower_free, upper_free)
        
        # Calculate percentages
        total_pixels = img.shape[0] * img.shape[1]
        green_pixels = cv2.countNonZero(mask_green)
        free_pixels = cv2.countNonZero(mask_free)
        
        green_percentage = (green_pixels / total_pixels) * 100
        free_percentage = (free_pixels / total_pixels) * 100
        
        # Estimate trees (roughly 20 pixels per tree in satellite image)
        estimated_trees = int(green_pixels / 20)
        
        # Estimate trees in free areas (roughly 10% of free land can have trees)
        trees_in_free = int((free_pixels * 0.1) / 20)
        
        # Plantation area in sq meters
        plantation_area = int(free_pixels * 480000 / total_pixels)
        
        return {
            'free_percentage': round(free_percentage, 2),
            'green_percentage': round(green_percentage, 2),
            'estimated_trees': estimated_trees,
            'trees_in_free': trees_in_free,
            'plantation_area': plantation_area,
            'mask': mask_free,
            'mask_green': mask_green,
            'segmented': segmented_img,
            'original': img
        }
    except Exception as e:
        print(f"Error segmenting image {image_path}: {e}")
        return None

def get_aqi_for_city(city_id):
    """Get current AQI from OpenWeatherMap API with caching and fallback"""
    try:
        if city_id not in CITY_COORDS:
            return {'aqi': 2, 'pm25': 35, 'pm10': 50, 'o3': 60, 'no2': 40, 'so2': 20, 'co': 800}
        
        # Check cache first
        if city_id in AQI_CACHE:
            cached_data = AQI_CACHE[city_id]
            if (datetime.now() - cached_data['timestamp']).total_seconds() < AQI_CACHE_TIMEOUT:
                return cached_data['data']
        
        coords = CITY_COORDS[city_id]
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={coords['lat']}&lon={coords['lon']}&appid={OPENWEATHER_API_KEY}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'list' in data and len(data['list']) > 0:
                sample = data['list'][0]
                main = sample.get('main', {})
                components = sample.get('components', {})

                aqi_cat = main.get('aqi', 0)

                aqi_result = {
                    'aqi': int(aqi_cat) if isinstance(aqi_cat, (int, float)) else 0,
                    'pm25': round(components.get('pm2_5', 0), 2),
                    'pm10': round(components.get('pm10', 0), 2),
                    'o3': round(components.get('o3', 0), 2),
                    'no2': round(components.get('no2', 0), 2),
                    'so2': round(components.get('so2', 0), 2),
                    'co': round(components.get('co', 0), 2),
                    'timestamp': datetime.now().isoformat()
                }
                
                AQI_CACHE[city_id] = {
                    'data': aqi_result,
                    'timestamp': datetime.now()
                }
                
                return aqi_result
        except requests.exceptions.Timeout:
            print(f"⚠️  API timeout for {city_id} - using fallback data")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Connection error for {city_id} - using fallback data")
        except Exception as e:
            print(f"⚠️  API error for {city_id}: {e}")
        
        fallback_data = {
            'aqi': 2,
            'pm25': 35,
            'pm10': 50,
            'o3': 60,
            'no2': 40,
            'so2': 20,
            'co': 800,
            'timestamp': datetime.now().isoformat()
        }
        
        AQI_CACHE[city_id] = {
            'data': fallback_data,
            'timestamp': datetime.now()
        }
        
        return fallback_data
    except Exception as e:
        print(f"Error in get_aqi_for_city: {e}")
        return {'aqi': 2, 'pm25': 35, 'pm10': 50, 'o3': 60, 'no2': 40, 'so2': 20, 'co': 800}


# Legacy HTML pages for the non-React UI
@app.route('/')
def index():
    """Homepage with statistics."""
    aggregated = aggregate_all_cities_data()
    aqi_data = get_aqi_for_city('madurai')
    aqi_value = aqi_data.get('aqi', 0)

    aqi_categories = {1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very Poor'}
    aqi_category = aqi_categories.get(aqi_value, 'Unknown')

    stats_list = [
        {'icon': 'MapPin', 'label': 'Total Cities', 'value': '5', 'color': 'green'},
        {'icon': 'Wind', 'label': 'Avg AQI', 'value': str(aqi_value), 'color': 'blue'},
        {
            'icon': 'TrendingUp',
            'label': 'Total Plantation Area',
            'value': f"{aggregated['total_plantation_area']:,} m²",
            'color': 'blue',
        },
        {
            'icon': 'TreePine',
            'label': 'Total Trees Recommended',
            'value': f"{aggregated['total_trees']:,}",
            'color': 'green',
        },
    ]

    return render_template(
        'index.html',
        stats=stats_list,
        areas=AREAS,
        aqi_value=aqi_value,
        aqi_category=aqi_category,
        pm25=aqi_data.get('pm25', 0),
    )


@app.route('/area-analysis')
def area_analysis():
    """Area analysis page."""
    return render_template('area_analysis.html', areas=AREAS)


@app.route('/aqi-trees')
def aqi_trees():
    """AQI and trees page."""
    return render_template('aqi_trees.html', areas=AREAS)


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html', areas=AREAS)


@app.route('/model-evaluation')
def model_evaluation():
    """Model evaluation dashboard."""
    return render_template('model_evaluation.html', areas=AREAS)


@app.route('/forecasting')
def forecasting():
    """Forecasting page."""
    return render_template('forecasting.html', areas=AREAS)

def _build_synthetic_aqi_history(city_id, days=100):
    """Build a smooth fallback AQI history when the API history is unavailable."""
    current_aqi = float(get_aqi_for_city(city_id).get('aqi', 2))
    np.random.seed(abs(hash(city_id)) % (2 ** 32))
    t = np.arange(days)
    seasonal = 0.25 * np.sin(2 * np.pi * t / 7)
    drift = 0.05 * np.sin(2 * np.pi * t / 30)
    noise = np.random.normal(0, 0.12, days)
    series = np.clip(current_aqi + seasonal + drift + noise, 1, 5)
    return [round(float(value), 2) for value in series.tolist()]

def get_aqi_history_for_city(city_id, history_days=100):
    """Fetch historical AQI values for a city and return a daily series."""
    try:
        if city_id not in CITY_COORDS:
            return []

        cache_key = f"{city_id}:{history_days}"
        if cache_key in AQI_HISTORY_CACHE:
            cached_data = AQI_HISTORY_CACHE[cache_key]
            if (datetime.now() - cached_data['timestamp']).total_seconds() < AQI_HISTORY_CACHE_TIMEOUT:
                return cached_data['data']

        coords = CITY_COORDS[city_id]
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=history_days)
        url = (
            "https://api.openweathermap.org/data/2.5/air_pollution/history"
            f"?lat={coords['lat']}&lon={coords['lon']}"
            f"&start={int(start_time.timestamp())}&end={int(end_time.timestamp())}"
            f"&appid={OPENWEATHER_API_KEY}"
        )

        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

        daily_values = {}
        for item in data.get('list', []):
            timestamp = item.get('dt')
            if not timestamp:
                continue

            try:
                aqi_value = float(item.get('main', {}).get('aqi', 0))
            except Exception:
                continue

            if aqi_value <= 0:
                continue

            date_key = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
            daily_values.setdefault(date_key, []).append(aqi_value)

        current_aqi = get_aqi_for_city(city_id).get('aqi')
        if current_aqi is not None:
            daily_values.setdefault(end_time.strftime('%Y-%m-%d'), []).append(float(current_aqi))

        historical_series = [
            round(float(np.mean(values)), 2)
            for _, values in sorted(daily_values.items())
            if values
        ]

        if len(historical_series) < 14:
            historical_series = _build_synthetic_aqi_history(city_id, days=history_days)
        else:
            historical_series = historical_series[-history_days:]

        AQI_HISTORY_CACHE[cache_key] = {
            'data': historical_series,
            'timestamp': datetime.now()
        }

        return historical_series
    except Exception as e:
        print(f"⚠️  Historical AQI error for {city_id}: {e}")
        fallback_series = _build_synthetic_aqi_history(city_id, days=history_days)
        AQI_HISTORY_CACHE[f"{city_id}:{history_days}"] = {
            'data': fallback_series,
            'timestamp': datetime.now()
        }
        return fallback_series

def get_aqi_forecast_summary_for_city(city_id, forecast_days=7, history_days=100):
    """Build a forecast summary from the city's historical AQI series."""
    forecaster = get_aqi_forecaster()
    forecaster.historical_data = get_aqi_history_for_city(city_id, history_days=history_days)
    return forecaster.get_forecast_summary(forecast_days=forecast_days)

def get_aqi_trend(city_id):
    """Get 7-day AQI trend from OpenWeatherMap history - aggregated by day (max value)"""
    try:
        if city_id not in CITY_COORDS:
            return []
        
        coords = CITY_COORDS[city_id]
        now = datetime.now()
        today_str = now.strftime('%Y-%m-%d')
        end_timestamp = int(now.timestamp())
        start_timestamp = int((now - timedelta(days=7)).timestamp())
        
        url = f"https://api.openweathermap.org/data/2.5/air_pollution/history?lat={coords['lat']}&lon={coords['lon']}&start={start_timestamp}&end={end_timestamp}&appid={OPENWEATHER_API_KEY}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            daily_aqi = {}
            
            if 'list' in data:
                for item in data['list']:
                    main = item.get('main', {})
                    aqi_cat = main.get('aqi', 0)
                    try:
                        aqi_val = int(aqi_cat)
                    except Exception:
                        aqi_val = 0

                    dt = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                    if dt not in daily_aqi:
                        daily_aqi[dt] = aqi_val
                    else:
                        daily_aqi[dt] = max(daily_aqi[dt], aqi_val)
            
            current_aqi = get_aqi_for_city(city_id)
            if current_aqi and 'aqi' in current_aqi:
                daily_aqi[today_str] = current_aqi['aqi']
            
            label_map = {1: 'Good', 2: 'Fair', 3: 'Moderate', 4: 'Poor', 5: 'Very Poor'}

            trend = [
                {'date': date, 'value': value, 'label': label_map.get(value, 'Unknown')}
                for date, value in sorted(daily_aqi.items())
            ]
            return trend[-7:]
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            print(f"⚠️  API connection issue for trend {city_id} - returning empty trend")
        except Exception as e:
            print(f"⚠️  Error fetching trend for {city_id}: {e}")
    
    except Exception as e:
        print(f"Error in get_aqi_trend: {e}")
    
    return []

def get_tree_category(aqi):
    """Determine tree recommendation category based on AQI"""
    try:
        a = int(aqi)
    except Exception:
        a = 0

    mapping = {
        1: 'good',
        2: 'moderate',
        3: 'unhealthy_sensitive',
        4: 'unhealthy',
        5: 'very_unhealthy'
    }

    return mapping.get(a, 'hazardous')

def process_city_images(city_name, city_folder, image_prefix):
    """Process all images for a city on startup"""
    global ANALYSIS_DATA
    
    data_dir = Path(f'Data/{city_folder}')
    images = sorted(data_dir.glob(f'{image_prefix}_*.png'))
    images_output_dir = Path('../static/images')
    images_output_dir.mkdir(parents=True, exist_ok=True)
    
    all_stats = {
        'total_free_percentage': 0,
        'total_green_percentage': 0,
        'total_trees': 0,
        'total_free_trees': 0,
        'total_plantation_area': 0,
        'image_count': 0,
        'images': []
    }
    
    for img_path in images:
        result = segment_image(str(img_path))
        if result:
            img_num = img_path.stem.split('_')[1]
            
            original_path = images_output_dir / f'{image_prefix}_{img_num}.png'
            try:
                cv2.imwrite(str(original_path), result.get('original'))
            except Exception:
                try:
                    from shutil import copyfile
                    copyfile(str(img_path), str(original_path))
                except Exception:
                    pass

            segmented_path = images_output_dir / f'{image_prefix}_{img_num}_segmented.png'
            cv2.imwrite(str(segmented_path), result['segmented'])

            mask_path = images_output_dir / f'{image_prefix}_{img_num}_free_mask.png'
            cv2.imwrite(str(mask_path), result['mask'])
            
            all_stats['total_free_percentage'] += result['free_percentage']
            all_stats['total_green_percentage'] += result['green_percentage']
            all_stats['total_trees'] += result['estimated_trees']
            all_stats['total_free_trees'] += result['trees_in_free']
            all_stats['total_plantation_area'] += result['plantation_area']
            all_stats['image_count'] += 1
            
            all_stats['images'].append({
                'id': img_num,
                'freeLandPercentage': result['free_percentage'],
                'greenPercentage': result['green_percentage'],
                'estimatedTrees': result['estimated_trees'],
                'treesInFreeAreas': result['trees_in_free'],
                'plantationArea': result['plantation_area']
            })
    
    if all_stats['image_count'] > 0:
        all_stats['avg_free_percentage'] = round(all_stats['total_free_percentage'] / all_stats['image_count'], 2)
        all_stats['avg_green_percentage'] = round(all_stats['total_green_percentage'] / all_stats['image_count'], 2)
        all_stats['avg_trees'] = int(all_stats['total_trees'] / all_stats['image_count'])
        all_stats['avg_free_trees'] = int(all_stats['total_free_trees'] / all_stats['image_count'])
        all_stats['avg_plantation_area'] = int(all_stats['total_plantation_area'] / all_stats['image_count'])
    
    ANALYSIS_DATA[city_name] = all_stats
    
    print(f"✅ Processed {all_stats['image_count']} {city_name} images")
    print(f"   Avg free land: {all_stats['avg_free_percentage']}%")
    print(f"   Avg trees: {all_stats['avg_trees']}")

def aggregate_all_cities_data():
    """Aggregate data from all processed cities"""
    global ANALYSIS_DATA
    
    total_trees = 0
    total_free_trees = 0
    total_plantation_area = 0
    cities_processed = 0
    
    for city_id in ANALYSIS_DATA:
        data = ANALYSIS_DATA[city_id]
        if data.get('image_count', 0) > 0:
            total_trees += data.get('total_trees', 0)
            total_free_trees += data.get('total_free_trees', 0)
            total_plantation_area += data.get('total_plantation_area', 0)
            cities_processed += 1
    
    return {
        'total_trees': total_trees,
        'total_free_trees': total_free_trees,
        'total_plantation_area': total_plantation_area,
        'cities_processed': cities_processed
    }

def startup_initialization():
    """Initialize data on app startup"""
    print("🚀 Starting GreenTamilNadu system initialization...")
    
    process_city_images('madurai', 'Madurai', 'madurai')
    process_city_images('dindigul', 'Dindigul', 'dindigul')
    process_city_images('chennai', 'Chennai', 'chennai')
    process_city_images('coimbatore', 'Coimbatore', 'coimbatore')
    process_city_images('trichy', 'Trichy', 'trichy')
    
    print("✅ System initialized successfully")

startup_initialization()

# API Endpoints
@app.route('/api/web/area/<area_id>', methods=['GET'])
def web_get_area(area_id):
    """Get area info"""
    if area_id not in CITY_COORDS:
        return jsonify({'error': 'Area not found'}), 404
    
    return jsonify(CITY_COORDS[area_id])

@app.route('/api/web/area/<area_id>/analysis')
def web_get_analysis(area_id):
    """Get area analysis data"""
    if area_id not in CITY_COORDS:
        return jsonify({'error': 'City not found'}), 404
    
    if area_id not in ANALYSIS_DATA:
        return jsonify({'error': 'Analysis data not available'}), 404
    
    data = ANALYSIS_DATA[area_id]
    
    image_prefix_map = {
        'madurai': 'madurai',
        'dindigul': 'dindigul',
        'chennai': 'chennai',
        'coimbatore': 'coimbatore',
        'trichy': 'trichy'
    }
    image_prefix = image_prefix_map.get(area_id, 'madurai')
    
    return jsonify({
        'areaId': area_id,
        'areaName': CITY_COORDS[area_id]['name'],
        'freeLandPercentage': data.get('avg_free_percentage', 0),
        'greenPercentage': data.get('avg_green_percentage', 0),
        'plantationArea': data.get('avg_plantation_area', 0),
        'estimatedTrees': data.get('avg_trees', 0),
        'treesInFreeAreas': data.get('avg_free_trees', 0),
        'image_count': data.get('image_count', 0),
        'images': data.get('images', [])
    })

@app.route('/api/web/area/<area_id>/aqi')
def web_get_aqi(area_id):
    """Get current AQI for area"""
    aqi_data = get_aqi_for_city(area_id)
    
    aqi_value = aqi_data.get('aqi', 0)
    def us_aqi_level(aqi):
        try:
            v = int(aqi)
        except Exception:
            return 'Unknown'
        return {
            1: 'Good',
            2: 'Fair',
            3: 'Moderate',
            4: 'Poor',
            5: 'Very Poor'
        }.get(v, 'Unknown')

    return jsonify({
        'aqi': aqi_value,
        'level': us_aqi_level(aqi_value),
        'pm25': aqi_data.get('pm25', 0),
        'pm10': aqi_data.get('pm10', 0),
        'o3': aqi_data.get('o3', 0),
        'no2': aqi_data.get('no2', 0),
        'so2': aqi_data.get('so2', 0),
        'co': aqi_data.get('co', 0),
        'timestamp': aqi_data.get('timestamp', '')
    })

@app.route('/api/web/area/<area_id>/aqi-trend')
def web_get_aqi_trend(area_id):
    """Get 7-day AQI trend"""
    trend = get_aqi_trend(area_id)
    return jsonify(trend)

@app.route('/api/web/area/<area_id>/trees')
def web_get_trees(area_id):
    """Get tree recommendations"""
    if area_id not in CITY_COORDS:
        return jsonify({'error': 'City not found', 'recommendations': []}), 404
    
    aqi_data = get_aqi_for_city(area_id)
    aqi_value = aqi_data.get('aqi', 0)
    
    try:
        if TREE_MODEL is None:
            raise RuntimeError('Tree model unavailable')
        model_results = TREE_MODEL.recommend(int(aqi_value), city_id=area_id, top_k=6)
        if isinstance(model_results, list):
            return jsonify({'recommendations': model_results})
        elif isinstance(model_results, dict) and 'recommendations' in model_results:
            return jsonify(model_results)
        else:
            return jsonify({'recommendations': model_results if isinstance(model_results, list) else []})
    except Exception as e:
        print(f"⚠️  Tree model error: {e}")
        category = get_tree_category(aqi_value)
        recommendations = TREE_RECOMMENDATIONS.get(category, [])
        return jsonify({'recommendations': recommendations, 'source': 'fallback'}), 200

@app.route('/api/model/evaluation')
def web_model_evaluation():
    """Return model validation metrics for dashboard display."""
    try:
        if TREE_MODEL is None:
            return jsonify({'error': 'Tree model unavailable'}), 500
        return jsonify({
            'suitabilityModel': TREE_MODEL.evaluate(),
            'impactModel': TREE_MODEL.evaluate_impact_model(),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/web/area/<area_id>/scenario', methods=['POST'])
def web_scenario_simulation(area_id):
    """Estimate species mix and tree count to move from current to target AQI category."""
    if area_id not in CITY_COORDS:
        return jsonify({'error': 'City not found'}), 404

    if TREE_MODEL is None:
        return jsonify({'error': 'Tree model unavailable'}), 500

    payload = request.get_json(silent=True) or {}
    target_aqi = payload.get('targetAQI', 1)
    aqi_data = get_aqi_for_city(area_id)
    current_aqi = int(aqi_data.get('aqi', 1))

    result = TREE_MODEL.simulate_scenario(
        city_id=area_id,
        current_aqi=current_aqi,
        target_aqi=int(target_aqi),
    )
    return jsonify(result)

@app.route('/api/web/area/<area_id>/impact-estimate', methods=['POST'])
def web_impact_estimation(area_id):
    """Estimate PM2.5 impact for a user-defined species mix and tree count."""
    if area_id not in CITY_COORDS:
        return jsonify({'error': 'City not found'}), 404

    if TREE_MODEL is None:
        return jsonify({'error': 'Tree model unavailable'}), 500

    payload = request.get_json(silent=True) or {}
    tree_count = int(payload.get('treeCount', 100))
    species_mix = payload.get('speciesMix', [])

    if not isinstance(species_mix, list):
        return jsonify({'error': 'speciesMix must be a list'}), 400

    aqi_data = get_aqi_for_city(area_id)
    aqi_value = int(aqi_data.get('aqi', 1))

    result = TREE_MODEL.estimate_mix_impact(
        city_id=area_id,
        aqi_value=aqi_value,
        tree_count=tree_count,
        species_mix=species_mix,
    )
    return jsonify(result)

@app.route('/api/web/feedback', methods=['POST'])
def web_store_feedback():
    """Store recommendation feedback for future model retraining."""
    if TREE_MODEL is None:
        return jsonify({'error': 'Tree model unavailable'}), 500

    payload = request.get_json(silent=True) or {}
    city_id = payload.get('cityId', '')
    if city_id not in CITY_COORDS:
        return jsonify({'error': 'Invalid cityId'}), 400

    aqi_data = get_aqi_for_city(city_id)
    aqi_value = int(aqi_data.get('aqi', 1))
    shown_tree_ids = payload.get('shownTreeIds', [])
    selected_tree_ids = payload.get('selectedTreeIds', [])
    note = payload.get('note', '')

    result = TREE_MODEL.store_feedback(
        city_id=city_id,
        aqi_value=aqi_value,
        shown_tree_ids=[str(item) for item in shown_tree_ids],
        selected_tree_ids=[str(item) for item in selected_tree_ids],
        note=str(note),
    )
    return jsonify(result)

@app.route('/api/web/area/<area_id>/forecast', methods=['GET'])
def web_get_forecast(area_id):
    """Get 7-day AQI forecast for a city using historical AQI and Holt-Winters."""
    if area_id not in CITY_COORDS:
        return jsonify({'error': 'City not found'}), 404
    
    try:
        summary = get_aqi_forecast_summary_for_city(area_id, forecast_days=7, history_days=100)
        
        return jsonify({
            'success': True,
            'city': CITY_COORDS[area_id]['name'],
            'forecast': summary
        })
        
    except Exception as e:
        print(f"❌ Forecast error for {area_id}: {e}")
        return jsonify({
            'error': str(e),
            'fallback': True
        }), 500

@app.route('/api/web/forecast-all', methods=['GET'])
def web_get_forecast_all():
    """Get 7-day AQI forecast for all cities"""
    try:
        all_forecasts = {}
        
        for area_id in CITY_COORDS.keys():
            summary = get_aqi_forecast_summary_for_city(area_id, forecast_days=7, history_days=100)
            
            all_forecasts[area_id] = summary
        
        return jsonify({
            'success': True,
            'forecasts': all_forecasts
        })
        
    except Exception as e:
        print(f"❌ All forecast error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')
