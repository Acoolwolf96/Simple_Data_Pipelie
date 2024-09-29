from flask import Flask, request, render_template
from pipeline import configure, extract, transform, load, get_weather_by_coords, collaborative_filtering, get_nearby_place_by_city, get_nearby_places_by_coords
from connection import create_table, connect
from collections import defaultdict

app = Flask(__name__)
connect()
create_table()  

@app.route('/', methods=['GET', 'POST'])
def pipeline():
    configure()
    if request.method == 'POST':
        city = request.form.get('city')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')

        weather_data = None
        nearby_places = []
        recommendations = []

        # Handle the case where the city is provided
        if city:
            weather_data = extract(city)
            nearby_places = get_nearby_place_by_city(city)
        
        # Handle the case where latitude and longitude are provided
        elif latitude and longitude:
            weather_data = get_weather_by_coords(latitude, longitude)
            nearby_places = get_nearby_places_by_coords(latitude, longitude)

        # Check if weather data was successfully fetched
        if weather_data:
            transform_data = transform(weather_data)
            if transform_data:
                load(transform_data)

        # Generate recommendations if there are nearby places
        if nearby_places:
            recommendations = collaborative_filtering(nearby_places)
        
        # Log for debugging purposes
        print(f'Weather Data: {weather_data}')
        print(f'Nearby Places: {nearby_places}')
        print(f'Recommendations: {recommendations}')

        # Return the result page with all data
        return render_template('result.html', weather=weather_data, nearby_places=nearby_places, recommendations=recommendations)
    
    return render_template('index.html')



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

    
