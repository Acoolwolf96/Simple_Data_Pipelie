import psycopg2
import requests
from config import config
from collections import defaultdict
from dotenv import load_dotenv
import os



def configure():
    load_dotenv()


def extract(city):
    #Extract city data
    print(f'Extracting data for: {city}')

    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={os.getenv('API_KEY')}&units=metric'

    try:
        #send GET request to the API
        response = requests.get(url)
        data = response.json()

        #verify if response contains the weather data
        if response.status_code == 200:
            weather_data = {
                'city': city,
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind': data['wind']['speed'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description']
            }
            return weather_data
        else:
            print(f"Failed to retrieve data for {city}, Reason: {data['message']}")
            return None
    except Exception as error:
        print(f'Error fetching data for {city}: {error}')
        return None    


def transform(weather):
    if weather is not None:
        city = weather['city']
        temperature = weather['temperature']
        humidity = weather['humidity']
        wind = weather['wind']
        pressure = weather['pressure']
        description = weather['description']
        return(city, temperature, humidity, wind, pressure, description)
    else:
        print("No data to transform")
        return None
    

def load(weather):
    #load transformed data into database
    if weather is None:
        print("No data to load.")
        return
    connection = None
    try:
        #connect to database   
        params = config()
        connection = psycopg2.connect(**params)
        crsr = connection.cursor()

        #Insert into Table
        insert_query = """
        INSERT INTO weather_data (city, temperature, humidity, wind, pressure, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        crsr.execute(insert_query,weather)

        connection.commit()

        print(f'Data for {weather[0]} loaded successfuly.')

    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error updating  data into database { error}')

    finally:
        if connection is not None:
            connection.close()
            print('Database connection closed')        
  

def get_weather_by_coords(latitude, longitude):
     #Extracting lats and lon
    print(f'Extracting data for: {latitude}, {longitude}')
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={os.getenv('API_KEY')}&units=metric"
    try:
        #send GET request to the API
        response = requests.get(url)
        data = response.json()

        #verify if response contains the weather data
        if response.status_code == 200:
            city = data.get('name', 'Unknown Location')
            weather_data = {
                'city': city,
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind': data['wind']['speed'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description']
            }
            return weather_data
        else:
            print("Failed to extract data for these coordinates")
            return None
    except Exception as error:
        print(f"Error fetching data for coordinates: {error}")
        return None 
    
def get_nearby_places(location, radius=1500, types=None):
    if types is None:
        types =['restaurant', 'cafe', 'bar', 'shopping_mall', 'store', 'museum', 'point_of_interest']
    
    places = []
    for place_type in types:
        response = requests.get(f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={place_type}&key={os.getenv('google_api')}')
        data = response.json()
        if 'results' in data:
            places.extend(data['results'])

    return places
    

def get_geocoding(city):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={os.getenv('google_api')}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            location = results[0]['geometry']['location']
            return location
    return None

def get_nearby_place_by_city(city):
    location_data = get_geocoding(city)
    if location_data:
        latitude = location_data['lat']
        longitude = location_data['lng']
        return get_nearby_places(f"{latitude}, {longitude}")
    else:
        return []

    
# def get_nearby_places_by_coords(latitude, longitude):
#     url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=1500&type=tourist_attraction&key={os.getenv('google_api')}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         return response.json().get('results', [])
#     else:
#         return []

def get_nearby_places_by_coords(latitude, longitude):
    # Step 1: Get nearby places first to determine the types available
    nearby_places = get_nearby_places(f"{latitude},{longitude}")
    
    if not nearby_places:
        print("No nearby places found.")
        return []
    
    # Step 2: Extract unique types from the nearby places
    types = set()
    for place in nearby_places:
        types.update(place.get('types', []))

    if not types:
        print("No types found for nearby places.")
        return []

    # Step 3: Use the extracted types to get places by coordinates
    places = []
    radius = 1500  # You can adjust the radius as needed

    for place_type in types:
        response = requests.get(f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={place_type}&key={os.getenv('google_api')}')
        data = response.json()
        if 'results' in data:
            places.extend(data['results'])

    return places

    
def collaborative_filtering(nearby_places):
    # simple collaborative filtering
    place_ratings = defaultdict(list)

    for place in nearby_places:
        place_name = place['name']
        rating = place.get('rating', 0)
        review_count = place.get('user_ratings_total', 0)  # Total number of reviews
        address = place.get('vicinity', 'N/A')  # Add address or vicinity if available
        place_type = place.get('types', ['N/A'])[0]  # Include type of place

        # Use both rating and review count for better filtering
        place_ratings[(rating, review_count)].append({
            'name': place_name,
            'rating': rating,
            'address': address,
            'type': place_type
        })

    # Sort primarily by rating and then by number of reviews
    sorted_places = sorted(place_ratings.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True)

    # Return recommended places
    recommendation = []
    for (rating, review_count), places in sorted_places:
        for place in places:
            recommendation.append(place)  # This now contains more details
            if len(recommendation) >= 10:
                return recommendation
    return recommendation
