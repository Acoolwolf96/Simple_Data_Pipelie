from flask import Flask, request, render_template
from app.pipeline import (
    configure, extract, transform, load, 
    get_weather_by_coords, get_nearby_place_by_city, 
    get_nearby_places_by_coords, get_nearby_places, 
    openai_activities_suggestions, map_recommendation_to_types
)
from connection import create_table, connect, create_cache_table

app = Flask(__name__)
connect()
create_table()  
create_cache_table()

@app.route('/', methods=['GET', 'POST'])
def pipeline():
    configure()
    if request.method == 'POST':
        city = request.form.get('city')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        weather_data = None
        nearby_places = []
        ai_recommendations = None
        filtered_nearby_places = []

        # 1. Get weather data and nearby places by city or coordinates
        if city:
            weather_data = extract(city)
            if weather_data:
                # 2a. Transform and load weather data into the database
                transform_data = transform(weather_data)
                if transform_data:
                    load(transform_data)

                    # 2b. Get activity recommendations from OpenAI based on weather
                    ai_recommendations = openai_activities_suggestions(weather_data)
                    
                    # 2c. Map OpenAI activity suggestions to place types
                    if ai_recommendations:
                        place_types = map_recommendation_to_types(ai_recommendations)
                        print(f'Place Types are : {place_types}')  # Debugging

                        # 2d. Fetch nearby places based on OpenAI recommendations
                        if place_types:
                            recommendation_string = ', '.join(place_types)
                            print(f'Recommendation String: {recommendation_string}')  # Debug
                            nearby_places = get_nearby_place_by_city(city, recommendation_string)  # No recommendations yet, just get city coordinates
                            print(f'This is city:{city}, and RECOMMENDATION: {nearby_places}')  # Debugging

            print(f"Weather Data: {weather_data}")  # Debugging output
            print(f"Nearby Places: {nearby_places}")  # Debugging output
            print(f"Recommendations: {ai_recommendations}")  # Debugging output

            return render_template('result.html', weather=weather_data, nearby_places=nearby_places, recommendations=ai_recommendations)
            
        elif latitude and longitude:
            weather_data = get_weather_by_coords(latitude, longitude)
            nearby_places = get_nearby_places_by_coords(latitude, longitude)

            # 2. If weather data is available, process further
            if weather_data:
                # 2a. Transform and load weather data into the database
                transform_data = transform(weather_data)
                if transform_data:
                    load(transform_data)

                    # 2b. Get activity recommendations from OpenAI based on weather
                    ai_recommendations = openai_activities_suggestions(weather_data)
                    
                    # 2c. Map OpenAI activity suggestions to place types
                    if ai_recommendations:
                        place_types = map_recommendation_to_types(ai_recommendations)

                        # 2d. Fetch nearby places based on OpenAI recommendations
                        if place_types:
                            recommendation_string = ', '.join(place_types)
                            filtered_nearby_places = get_nearby_places(f"{latitude},{longitude}", recommendations=recommendation_string)
                        else:
                            # Fallback to default nearby places if no place types are matched
                            filtered_nearby_places = nearby_places
                    else:
                        # Fallback to default nearby places if no AI recommendations
                        filtered_nearby_places = nearby_places

            return render_template('result.html', weather=weather_data, nearby_places=filtered_nearby_places, recommendations=ai_recommendations)

    return render_template('index.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
