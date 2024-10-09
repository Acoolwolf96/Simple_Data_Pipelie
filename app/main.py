from flask import Flask, request, render_template
import os
from dotenv import load_dotenv
from datetime import datetime
from app.pipeline import (
    configure, extract, transform, load, 
    get_weather_by_coords, get_nearby_place_by_city, 
    get_nearby_places_by_coords, get_nearby_places, 
    openai_activities_suggestions, map_recommendation_to_types
)
from app.connection import create_table, connect, create_cache_table

app = Flask(__name__)
connect()
create_table()  
create_cache_table()
load_dotenv()

from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
def pipeline():
    configure()
    google_api_key = os.getenv("google_api") #loadiing google api for auto-complete
    if request.method == 'POST':
        city = request.form.get('city')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        checkin = request.form.get('checkin')
        checkout = request.form.get('checkout')

        # Calculate the number of days the user is staying
        stay_duration = None
        if checkin and checkout:
            checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
            checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
            stay_duration = (checkout_date - checkin_date).days

        weather_data = None
        nearby_places = []
        ai_recommendations = None
        filtered_nearby_places = []

        # 1. Get weather data and nearby places by city or coordinates
        if city:
            weather_data = extract(city)
            if weather_data:
                transform_data = transform(weather_data)
                if transform_data:
                    load(transform_data)

                    # Pass the stay duration to OpenAI activity suggestions
                    ai_recommendations = openai_activities_suggestions(weather_data, stay_duration)
                    
                    # Map OpenAI activity suggestions to place types
                    if ai_recommendations:
                        place_types = map_recommendation_to_types(ai_recommendations)
                        if place_types:
                            recommendation_string = ', '.join(place_types)
                            nearby_places = get_nearby_place_by_city(city, recommendation_string)

            return render_template('result.html', weather=weather_data, nearby_places=nearby_places, recommendations=ai_recommendations, stay_duration=stay_duration)

        elif latitude and longitude:
            weather_data = get_weather_by_coords(latitude, longitude)
            nearby_places = get_nearby_places_by_coords(latitude, longitude)

            if weather_data:
                transform_data = transform(weather_data)
                if transform_data:
                    load(transform_data)

                    ai_recommendations = openai_activities_suggestions(weather_data, stay_duration)

                    if ai_recommendations:
                        place_types = map_recommendation_to_types(ai_recommendations)
                        if place_types:
                            recommendation_string = ', '.join(place_types)
                            filtered_nearby_places = get_nearby_places(f"{latitude},{longitude}", recommendations=recommendation_string)
                        else:
                            filtered_nearby_places = nearby_places
                    else:
                        filtered_nearby_places = nearby_places

            return render_template('result.html', weather=weather_data, nearby_places=filtered_nearby_places, recommendations=ai_recommendations, stay_duration=stay_duration)

    return render_template('index.html', google_api_key= google_api_key)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
