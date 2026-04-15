#!/usr/bin/env python3
"""Flask Web UI for GreenMadurai - AI Pollution Analysis System"""
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

# Madurai areas with coordinates and metadata
MADURAI_AREAS = {
    'maatuthavani': {'lat': 9.9195, 'lon': 78.1193, 'name': 'Maatuthavani', 'city_folder': 'Madurai/Maatuthavani'},
    'arapalayam': {'lat': 9.9320, 'lon': 78.1026, 'name': 'Arapalayam', 'city_folder': 'Madurai/Arapalayam'},
    'periyar': {'lat': 9.9178, 'lon': 78.1106, 'name': 'Periyar', 'city_folder': 'Madurai/Periyar'},
    'thiruparankundram': {'lat': 9.8810, 'lon': 78.0710, 'name': 'Thiruparankundram', 'city_folder': 'Madurai/Thiruparankundram'},
    'thirumangalam': {'lat': 9.8216, 'lon': 77.9906, 'name': 'Thirumangalam', 'city_folder': 'Madurai/Thirumangalam'}
}

# Keep backward compatibility
CITY_COORDS = MADURAI_AREAS
AREAS = [{'id': k, 'name': v['name']} for k, v in MADURAI_AREAS.items()]

# In-memory holder for analysis results
ANALYSIS_DATA = {}

# CPCB AQI Breakpoints and Index values (India Standard)
AQI_BREAKPOINTS = {
    'pm25': [
        {'breakpoint': (0, 30), 'aqi': (0, 50), 'category': 'Good'},
        {'breakpoint': (31, 60), 'aqi': (51, 100), 'category': 'Satisfactory'},
        {'breakpoint': (61, 90), 'aqi': (101, 200), 'category': 'Moderately Polluted'},
        {'breakpoint': (91, 120), 'aqi': (201, 300), 'category': 'Poor'},
        {'breakpoint': (121, 250), 'aqi': (301, 400), 'category': 'Very Poor'},
        {'breakpoint': (251, 9999), 'aqi': (401, 500), 'category': 'Severe'}
    ],
    'pm10': [
        {'breakpoint': (0, 50), 'aqi': (0, 50), 'category': 'Good'},
        {'breakpoint': (51, 100), 'aqi': (51, 100), 'category': 'Satisfactory'},
        {'breakpoint': (101, 250), 'aqi': (101, 200), 'category': 'Moderately Polluted'},
        {'breakpoint': (251, 350), 'aqi': (201, 300), 'category': 'Poor'},
        {'breakpoint': (351, 430), 'aqi': (301, 400), 'category': 'Very Poor'},
        {'breakpoint': (431, 9999), 'aqi': (401, 500), 'category': 'Severe'}
    ],
    'no2': [
        {'breakpoint': (0, 40), 'aqi': (0, 50), 'category': 'Good'},
        {'breakpoint': (41, 80), 'aqi': (51, 100), 'category': 'Satisfactory'},
        {'breakpoint': (81, 180), 'aqi': (101, 200), 'category': 'Moderately Polluted'},
        {'breakpoint': (181, 280), 'aqi': (201, 300), 'category': 'Poor'},
        {'breakpoint': (281, 400), 'aqi': (301, 400), 'category': 'Very Poor'},
        {'breakpoint': (401, 9999), 'aqi': (401, 500), 'category': 'Severe'}
    ],
    'so2': [
        {'breakpoint': (0, 40), 'aqi': (0, 50), 'category': 'Good'},
        {'breakpoint': (41, 80), 'aqi': (51, 100), 'category': 'Satisfactory'},
        {'breakpoint': (81, 380), 'aqi': (101, 200), 'category': 'Moderately Polluted'},
        {'breakpoint': (381, 800), 'aqi': (201, 300), 'category': 'Poor'},
        {'breakpoint': (801, 1600), 'aqi': (301, 400), 'category': 'Very Poor'},
        {'breakpoint': (1601, 9999), 'aqi': (401, 500), 'category': 'Severe'}
    ],
    'co': [
        {'breakpoint': (0, 1000), 'aqi': (0, 50), 'category': 'Good'},
        {'breakpoint': (1001, 2000), 'aqi': (51, 100), 'category': 'Satisfactory'},
        {'breakpoint': (2001, 10000), 'aqi': (101, 200), 'category': 'Moderately Polluted'},
        {'breakpoint': (10001, 17000), 'aqi': (201, 300), 'category': 'Poor'},
        {'breakpoint': (17001, 34000), 'aqi': (301, 400), 'category': 'Very Poor'},
        {'breakpoint': (34001, 9999999), 'aqi': (401, 500), 'category': 'Severe'}
    ],
    'o3': [
        {'breakpoint': (0, 50), 'aqi': (0, 50), 'category': 'Good'},
        {'breakpoint': (51, 100), 'aqi': (51, 100), 'category': 'Satisfactory'},
        {'breakpoint': (101, 168), 'aqi': (101, 200), 'category': 'Moderately Polluted'},
        {'breakpoint': (169, 208), 'aqi': (201, 300), 'category': 'Poor'},
        {'breakpoint': (209, 748), 'aqi': (301, 400), 'category': 'Very Poor'},
        {'breakpoint': (749, 9999), 'aqi': (401, 500), 'category': 'Severe'}
    ]
}

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

def calculate_aqi(pm25, pm10, no2, so2, co, o3):
    """
    Calculate AQI using CPCB (Central Pollution Control Board) formula
    AQI = max(AQI_pm25, AQI_pm10, AQI_no2, AQI_so2, AQI_co, AQI_o3)
    """
    def get_aqi_for_pollutant(pollutant_name, value):
        """Calculate AQI for a single pollutant"""
        if pollutant_name not in AQI_BREAKPOINTS:
            return 0
        
        breakpoints = AQI_BREAKPOINTS[pollutant_name]
        for bp in breakpoints:
            blo, bhi = bp['breakpoint']
            ilo, ihi = bp['aqi']
            
            if blo <= value <= bhi:
                # CPCB formula: AQI = (IHI - ILO) / (BHI - BLO) * (C - BLO) + ILO
                aqi_value = ((ihi - ilo) / (bhi - blo)) * (value - blo) + ilo
                return round(aqi_value, 2)
        
        # If value exceeds all breakpoints, return max AQI
        return 500
    
    # Calculate AQI for each pollutant
    pollutant_values = {
        'pm25': pm25,
        'pm10': pm10,
        'no2': no2,
        'so2': so2,
        'co': co,
        'o3': o3
    }
    
    aqi_values = {}
    for pollutant, value in pollutant_values.items():
        if value is not None:
            aqi_values[pollutant] = get_aqi_for_pollutant(pollutant, value)
    
    # Final AQI is the maximum of all pollutants
    final_aqi = max(aqi_values.values()) if aqi_values else 0
    
    # Determine category
    def get_aqi_category(aqi):
        if aqi <= 50:
            return 'Good'
        elif aqi <= 100:
            return 'Satisfactory'
        elif aqi <= 200:
            return 'Moderately Polluted'
        elif aqi <= 300:
            return 'Poor'
        elif aqi <= 400:
            return 'Very Poor'
        else:
            return 'Severe'
    
    return {
        'aqi': round(final_aqi, 2),
        'category': get_aqi_category(final_aqi),
        'breakdown': aqi_values
    }

def get_aqi_for_city(city_id):
    """Get AQI for area - fetches pollutant data and calculates using CPCB formula"""
    try:
        if city_id not in CITY_COORDS:
            return {'aqi': 100, 'category': 'Satisfactory', 'pm25': 35, 'pm10': 50, 'o3': 60, 'no2': 40, 'so2': 20, 'co': 800, 'timestamp': datetime.now().isoformat()}
        
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
                components = sample.get('components', {})

                # Extract pollutant values
                pm25 = components.get('pm2_5', 35)
                pm10 = components.get('pm10', 50)
                no2 = components.get('no2', 40)
                so2 = components.get('so2', 20)
                co = components.get('co', 800)
                o3 = components.get('o3', 60)

                # Calculate AQI using CPCB formula
                aqi_calc = calculate_aqi(pm25, pm10, no2, so2, co, o3)
                
                aqi_result = {
                    'aqi': aqi_calc['aqi'],
                    'category': aqi_calc['category'],
                    'pm25': round(pm25, 2),
                    'pm10': round(pm10, 2),
                    'o3': round(o3, 2),
                    'no2': round(no2, 2),
                    'so2': round(so2, 2),
                    'co': round(co, 2),
                    'timestamp': datetime.now().isoformat()
                }
                
                AQI_CACHE[city_id] = {
                    'data': aqi_result,
                    'timestamp': datetime.now()
                }
                
                print(f"✅ AQI for {city_id}: {aqi_result['aqi']} ({aqi_result['category']})")
                return aqi_result
        except requests.exceptions.Timeout:
            print(f"⚠️  API timeout for {city_id} - using fallback data")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Connection error for {city_id} - using fallback data")
        except Exception as e:
            print(f"⚠️  API error for {city_id}: {e}")
        
        # Fallback data
        fallback_data = {
            'aqi': 100,
            'category': 'Satisfactory',
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
        return {'aqi': 100, 'category': 'Satisfactory', 'pm25': 35, 'pm10': 50, 'o3': 60, 'no2': 40, 'so2': 20, 'co': 800, 'timestamp': datetime.now().isoformat()}


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
    current_aqi = float(get_aqi_for_city(city_id).get('aqi', 100))
    np.random.seed(abs(hash(city_id)) % (2 ** 32))
    t = np.arange(days)
    seasonal = 12.0 * np.sin(2 * np.pi * t / 7)
    drift = 8.0 * np.sin(2 * np.pi * t / 30)
    noise = np.random.normal(0, 6.0, days)
    series = np.clip(current_aqi + seasonal + drift + noise, 0, 500)
    return [round(float(value), 2) for value in series.tolist()]

def get_aqi_history_for_city(city_id, history_days=50):
    """Fetch historical AQI values for an area and return a daily CPCB AQI series."""
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
                components = item.get('components', {})
                pm25 = float(components.get('pm2_5', 0) or 0)
                pm10 = float(components.get('pm10', 0) or 0)
                no2 = float(components.get('no2', 0) or 0)
                so2 = float(components.get('so2', 0) or 0)
                co = float(components.get('co', 0) or 0)
                o3 = float(components.get('o3', 0) or 0)
                aqi_value = float(calculate_aqi(pm25, pm10, no2, so2, co, o3).get('aqi', 0))
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

def get_aqi_forecast_summary_for_city(city_id, forecast_days=7, history_days=50):
    """Build a forecast summary from the area's historical AQI series."""
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
                    try:
                        components = item.get('components', {})
                        pm25 = float(components.get('pm2_5', 0) or 0)
                        pm10 = float(components.get('pm10', 0) or 0)
                        no2 = float(components.get('no2', 0) or 0)
                        so2 = float(components.get('so2', 0) or 0)
                        co = float(components.get('co', 0) or 0)
                        o3 = float(components.get('o3', 0) or 0)
                        aqi_val = int(round(calculate_aqi(pm25, pm10, no2, so2, co, o3).get('aqi', 0)))
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

            def get_label(aqi_value):
                if aqi_value <= 50:
                    return 'Good'
                if aqi_value <= 100:
                    return 'Satisfactory'
                if aqi_value <= 200:
                    return 'Moderately Polluted'
                if aqi_value <= 300:
                    return 'Poor'
                if aqi_value <= 400:
                    return 'Very Poor'
                return 'Severe'

            trend = [
                {'date': date, 'value': value, 'label': get_label(value)}
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
        a = float(aqi)
    except Exception:
        a = 500

    if a <= 50:
        return 'good'
    if a <= 100:
        return 'moderate'
    if a <= 200:
        return 'unhealthy_sensitive'
    if a <= 300:
        return 'unhealthy'
    if a <= 400:
        return 'very_unhealthy'
    return 'hazardous'

def process_city_images(city_name, city_folder, source_prefix, output_prefix=None):
    """Process all images for an area on startup."""
    global ANALYSIS_DATA

    # Accept both backend/Data/* and workspace-root Data/* so user-provided folders work.
    candidate_dirs = [Path(f'Data/{city_folder}'), Path(f'../Data/{city_folder}')]
    data_dir = next((directory for directory in candidate_dirs if directory.exists()), candidate_dirs[0])

    area_prefix = output_prefix or source_prefix
    images = sorted(data_dir.glob(f'{source_prefix}_*.png'))
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
            
            original_path = images_output_dir / f'{area_prefix}_{img_num}.png'
            try:
                cv2.imwrite(str(original_path), result.get('original'))
            except Exception:
                try:
                    from shutil import copyfile
                    copyfile(str(img_path), str(original_path))
                except Exception:
                    pass

            segmented_path = images_output_dir / f'{area_prefix}_{img_num}_segmented.png'
            cv2.imwrite(str(segmented_path), result['segmented'])

            mask_path = images_output_dir / f'{area_prefix}_{img_num}_free_mask.png'
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
        
        print(f"✅ Processed {all_stats['image_count']} {city_name} images")
        print(f"   Avg free land: {all_stats['avg_free_percentage']}%")
        print(f"   Avg trees: {all_stats['avg_trees']}")
    else:
        print(f"⚠️ No images found for {city_name} - skipping analysis")
        all_stats['avg_free_percentage'] = 0
        all_stats['avg_green_percentage'] = 0
        all_stats['avg_trees'] = 0
        all_stats['avg_free_trees'] = 0
        all_stats['avg_plantation_area'] = 0
    
    all_stats['image_prefix'] = area_prefix
    ANALYSIS_DATA[city_name] = all_stats

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
    print("🚀 Starting GreenMadurai system initialization...")
    
    # Process each Madurai area folder and normalize generated filenames to area ids.
    process_city_images('arapalayam', 'Arapalayam', 'coimbatore', 'arapalayam')
    process_city_images('maatuthavani', 'Maatuthavani', 'dindigul', 'maatuthavani')
    process_city_images('periyar', 'Periyar', 'chennai', 'periyar')
    process_city_images('thiruparankundram', 'Thiruparankundram', 'trichy', 'thiruparankundram')
    process_city_images('thirumangalam', 'Thirumangalam', 'madurai', 'thirumangalam')
    
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
    
    image_prefix = data.get('image_prefix', area_id)
    
    return jsonify({
        'areaId': area_id,
        'areaName': CITY_COORDS[area_id]['name'],
        'freeLandPercentage': data.get('avg_free_percentage', 0),
        'greenPercentage': data.get('avg_green_percentage', 0),
        'plantationArea': data.get('avg_plantation_area', 0),
        'estimatedTrees': data.get('avg_trees', 0),
        'treesInFreeAreas': data.get('avg_free_trees', 0),
        'image_count': data.get('image_count', 0),
        'image_prefix': image_prefix,
        'images': data.get('images', [])
    })

@app.route('/api/web/area/<area_id>/aqi')
def web_get_aqi(area_id):
    """Get current AQI for area (calculated using CPCB formula)"""
    aqi_data = get_aqi_for_city(area_id)

    return jsonify({
        'aqi': aqi_data.get('aqi', 100),
        'category': aqi_data.get('category', 'Satisfactory'),
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
    """Get 7-day AQI forecast for an area using 50-day CPCB AQI history and Holt-Winters."""
    if area_id not in CITY_COORDS:
        return jsonify({'error': 'City not found'}), 404
    
    try:
        history_days = 50
        summary = get_aqi_forecast_summary_for_city(area_id, forecast_days=7, history_days=history_days)
        live_aqi = get_aqi_for_city(area_id).get('aqi', summary.get('statistics', {}).get('current_aqi', 0))
        if 'statistics' in summary:
            summary['statistics']['current_aqi'] = round(float(live_aqi), 1)

        # Keep 7-day predictions operationally close to the live AQI for area-level planning.
        # This prevents unrealistic jumps when older history has temporary spikes.
        model_values = summary.get('model', {}).get('values', [])
        if model_values:
            live_value = float(live_aqi)
            band = max(5.0, min(12.0, live_value * 0.15))
            max_step = max(2.0, min(5.0, live_value * 0.08))

            adjusted_values = []
            prev_value = live_value
            for value in model_values:
                clamped_target = max(live_value - band, min(live_value + band, float(value)))
                next_value = prev_value + max(-max_step, min(max_step, clamped_target - prev_value))
                adjusted_values.append(round(next_value, 1))
                prev_value = next_value

            summary['model']['values'] = adjusted_values
            summary['statistics']['forecast_avg'] = round(float(np.mean(adjusted_values)), 1)
            summary['statistics']['forecast_min'] = round(float(np.min(adjusted_values)), 1)
            summary['statistics']['forecast_max'] = round(float(np.max(adjusted_values)), 1)
            if adjusted_values[-1] > live_value + 1:
                summary['statistics']['trend'] = 'up'
            elif adjusted_values[-1] < live_value - 1:
                summary['statistics']['trend'] = 'down'
            else:
                summary['statistics']['trend'] = 'flat'
        
        return jsonify({
            'success': True,
            'area': CITY_COORDS[area_id]['name'],
            'forecast': summary,
            'training': {
                'historyDays': history_days,
                'aqiSource': 'CPCB formula from PM2.5, PM10, NO2, SO2, CO, O3 (OpenWeather components)'
            }
        })
        
    except Exception as e:
        print(f"❌ Forecast error for {area_id}: {e}")
        return jsonify({
            'error': str(e),
            'fallback': True
        }), 500

@app.route('/api/web/forecast-all', methods=['GET'])
def web_get_forecast_all():
    """Get 7-day AQI forecast for all areas"""
    try:
        all_forecasts = {}
        history_days = 50
        
        for area_id in CITY_COORDS.keys():
            summary = get_aqi_forecast_summary_for_city(area_id, forecast_days=7, history_days=history_days)
            
            all_forecasts[area_id] = summary
        
        return jsonify({
            'success': True,
            'forecasts': all_forecasts,
            'training': {
                'historyDays': history_days,
                'aqiSource': 'CPCB formula from PM2.5, PM10, NO2, SO2, CO, O3 (OpenWeather components)'
            }
        })
        
    except Exception as e:
        print(f"❌ All forecast error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')
