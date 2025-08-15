#Import necessary libraries
import requests
from dotenv import load_dotenv
import os
from airflow.models import Variable

# Pega a chave diretamente do Airflow Variables
api_key = Variable.get("API_KEY")
api_url = f"http://api.weatherstack.com/current?access_key={api_key}&query=Rio de Janeiro"

# Function to fetch weather data from Weatherstack API
def fetch_data():
    print("Fetching data from Weatherstack API...")
    try: # Use try-except to handle potential errors
        response = requests.get(api_url)
        response.raise_for_status() # Check if the request was successful
        print("API response received successfully.")
        print(response.json()) # Print the JSON response for debugging
        return response.json() # Return the JSON response
    except requests.exceptions.RequestException as e: 
        print(f"An error occurred: {e}")
        raise

def mock_fetch_data(): # Mock function to simulate API response
    return {'request': {'type': 'City', 'query': 'Rio De Janeiro, Brazil', 'language': 'en', 'unit': 'm'}, 'location': {'name': 'Rio De Janeiro', 'country': 'Brazil', 'region': 'Rio de Janeiro', 'lat': '-22.900', 'lon': '-43.233', 'timezone_id': 'America/Sao_Paulo', 'localtime': '2025-08-03 16:01', 'localtime_epoch': 1754236860, 'utc_offset': '-3.0'}, 'current': {'observation_time': '07:01 PM', 'temperature': 23, 'weather_code': 113, 'weather_icons': ['https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0001_sunny.png'], 'weather_descriptions': ['Sunny'], 'astro': {'sunrise': '06:25 AM', 'sunset': '05:33 PM', 'moonrise': '12:23 PM', 'moonset': '01:33 AM', 'moon_phase': 'Waxing Gibbous', 'moon_illumination': 64}, 'air_quality': {'co': '582.75', 'no2': '93.98', 'o3': '27', 'so2': '12.765', 'pm2_5': '42.92', 'pm10': '44.4', 'us-epa-index': '3', 'gb-defra-index': '3'}, 'wind_speed': 11, 'wind_degree': 101, 'wind_dir': 'E', 'pressure': 1018, 'precip': 0, 'humidity': 69, 'cloudcover': 0, 'feelslike': 25, 'uv_index': 1, 'visibility': 10, 'is_day': 'yes'}}
