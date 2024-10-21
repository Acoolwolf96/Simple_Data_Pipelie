import openai.error
import psycopg2
import requests
from app.config import config, config_render
from dotenv import load_dotenv
import os
import openai
import time


cache = {}


def configure():
    load_dotenv()
    openai.api_key = os.getenv("openai_api_key")
    

def get_database_config():

    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # Use config_render if DATABASE_URL is set (server/hosting environment)
        print("Using config_render() for database configuration.")
        return config_render()
    else:
        # Use config if DATABASE_URL is not set (local environment)
        print("Using config() for database configuration.")
        return config()




def extract(city):
    #Extract city data
    print(f'Extracting data for: {city}')

    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={os.getenv("API_KEY")}&units=metric'


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
                'description': data['weather'][0]['description'],
                'timezone': data['timezone']
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
        return city, temperature, humidity, wind, pressure, description
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
        params = get_database_config()
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
    



def get_nearby_places(location, recommendations, radius=1500):
    print(f'location from: {location}, recommendations: {recommendations}')
    
    latitude,longitude = location.split(',')
    print(f'latitude:{latitude} longitude:{longitude}')
    
    types = map_recommendation_to_types(recommendations)
    
    if not types:
        print("No valid types found from recommendations.")
        return []
    
    places = []
    for place_type in types:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={place_type}&key={os.getenv('google_api')}"

        response = requests.get(url)
        data = response.json()
        #print(f'DATA for: {data}') #Debugging
        
        
        if response.status_code != 200:
            print(f"API request failed for type {place_type}: {data.get('error_message', 'Unknown error')}")
            continue

        for place in data.get('results', []):
            place_info = {
                'name': place.get('name', 'Unnamed'),
                'rating': place.get('rating', 'N/A'),
                'vicinity': place.get('vicinity', 'N/A'),
                'open_now': place.get('opening_hours', {}).get('open_now', 'Unknown'),
                'icon': place.get('icon', ''),
                'location': place.get('geometry', {}).get('location', {})
            }
            places.append(place_info)

    return places

    
# def get_nearby_places(location, recommendations, radius=1500):
#     """
#     Retrieves nearby places of interest based on the types derived from recommendations.
#     location: String formatted as 'latitude,longitude'.
#     recommendations: String of recommendations, which will be mapped to types (e.g., 'museum', 'restaurant').
#     radius: Search radius in meters (default is 1500 meters).
#     """
#     print(f'location from: {location}, recommendations: {recommendations}')

#     latitude,longitude = location.split(',')
#     print(f'latitude:{latitude}longitude:{longitude}')
    

#     # First, ensure that recommendations map to valid types
#     types = map_recommendation_to_types(recommendations)
    
#     if not types:
#         print("No valid types found from recommendations.")
#         return []
    
#     print(f"Mapped types: {types}")


#     print(f'latitude: {latitude}, longitude: {longitude}')

#     places = []
#     for place_type in types:
#         print(f"Fetching places of type: {place_type}")
        
#         # Use the location string directly in the URL
#         url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type={place_type}&key={os.getenv('google_api')}"
        
#         response = requests.get(url)
#         data = response.json()
        
#         if response.status_code != 200:
#             print(f"API request failed for type {place_type}: {data.get('error_message', 'Unknown error')}")
#             continue

#         # Extract relevant data for each place
#         for place in data.get('results', []):
#             place_info = {
#                 'name': place.get('name', 'Unnamed'),
#                 'rating': place.get('rating', 'N/A'),
#                 'vicinity': place.get('vicinity', 'N/A'),
#                 'open_now': place.get('opening_hours', {}).get('open_now', 'Unknown'),
#                 'icon': place.get('icon', '')
#             }
#             places.append(place_info)

#     return places




# def get_geocoding_nominatim(city):
#     """Get geocoding data from Nominatim or cache."""
#     try:
#         # Connect to the database
#         params = get_database_config()
#         with psycopg2.connect(**params) as connection:
#             with connection.cursor() as crsr:
#                 # Check if the city is in the cache
#                 crsr.execute("SELECT lat, lng FROM geocoding_cache WHERE city = %s;", (city,))
#                 result = crsr.fetchone()

#                 if result:
#                     print(f"Returning cached data for {city}: {result}")
#                     return {"lat": result[0], "lng": result[1]}
    
#     except (Exception, psycopg2.DatabaseError) as error:
#         print(f'Error connecting to the database: {error}')

#     # If not found in cache, make a request to Nominatim
#     url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
 
    
#     print(f"Geocoding request URL: {url}")  # Debugging the URL

#     try:
#         response = requests.get(url)

#         if response.status_code == 200:
#             results = response.json()
#             print(f"Nominatim API response: {results}")  # Debugging the response
            
#             if results:
#                 location = {
#                     "lat": float(results[0]["lat"]),
#                     "lng": float(results[0]["lon"])
#                 }

#                 # Cache the result in the database
#                 with psycopg2.connect(**params) as connection:
#                     with connection.cursor() as crsr:
#                         crsr.execute(
#                             "INSERT INTO geocoding_cache (city, lat, lng) VALUES (%s, %s, %s) "
#                             "ON CONFLICT (city) DO UPDATE SET lat = %s, lng = %s;",
#                             (city, location['lat'], location['lng'], location['lat'], location['lng'])
#                         )
#                         connection.commit()

#                 print(f"Cached new data for {city}: {location}")  # Debugging the cached location
#                 return location

#         # Handle specific response codes
#         if response.status_code == 403:
#             print(f"Access denied to Nominatim API for {city}. Please check usage policy.")
#         elif response.status_code == 429:
#             print(f"Rate limit exceeded for Nominatim API for {city}.")
#         else:
#             print(f"Failed to retrieve data for {city}, Status code: {response.status_code}, Reason: {response.text}")

#     except Exception as error:
#         print(f"Error fetching geocoding data for {city}: {error}")

#     return None




def get_nearby_place_by_city(city, recommendations):
    location_data = get_geocoding_opencage(city)
    if location_data:
        latitude = location_data['lat']
        longitude = location_data['lng']
        #print(f"Found coordinates for {city}: {latitude},{longitude}")
        
        nearby_places = get_nearby_places(f'{latitude},{longitude}', recommendations=recommendations)
        # print(f"Nearby places for {city}: {nearby_places}")
        return nearby_places
    else:
        print(f"Could not find coordinates for city: {city}")
        return []






def get_nearby_places_by_coords(latitude, longitude):
    # Step 1: Get nearby places first to determine the types available
    nearby_places = get_nearby_places(f"{latitude},{longitude}", recommendations="")
    return nearby_places
      


#Using AI based suggestion activities

def openai_activities_suggestions(weather_data, stay_duration, nearby_places=[]):
    description = weather_data.get('description', '')
    temperature = weather_data.get('temperature', '')
    city = weather_data.get('city', '')
    timezone = weather_data.get('timezone', 0)
    local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + timezone))
    
    # Adjust the prompt based on the duration of the stay
    duration_text = f"for {stay_duration} days" if stay_duration else "for today"
    prompt =  f'The local time is {local_time} in {city}, and the weather is {description} with a temperature of {temperature}°C. Based on the current weather, time, and {duration_text}, suggest an itinerary, including activities and places to visit."'

    if nearby_places:
        prompt += f" Here are some nearby places: {', '.join(nearby_places)}."

    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        return response.choices[0].message['content'].strip()

    except openai.error.RateLimitError:
        print('Rate limit exceeded. Waiting before retrying...')
        time.sleep(10)
        return openai_activities_suggestions(weather_data, stay_duration, nearby_places)
    
    except Exception as e:
        print(f'An error occurred: {e}')
        return 'Sorry, I could not retrieve recommendations at the moment'





def map_recommendation_to_types(recommendations):
    # Mapping common place recommendations to Google Places API types
    if not recommendations:
        return []
    
    recommendation_to_types = {
        'museum': ['museum'],
        'art': ['museum'],
        'breakfast': ['cafe'],
        'brunch': ['cafe'],
        'park': ['park'],
        'restaurant': ['restaurant'],
        'bar': ['bar'],
        'shopping': ['shopping_mall'],
        'church': ['church'],
        'winery': ['bar'],
        'hiking': ['park'],
        'sightseeing': ['tourist_attraction'],
        'cafe': ['cafe'],
        'hotel': ['hotel']
    }

    matched_types = []
    recommendation_phrases = [rec.strip().lower() for rec in recommendations.split(',') if rec]

    for rec in recommendation_phrases:
        for key, types in recommendation_to_types.items():
            if key in rec:
                matched_types.extend(types)

    return matched_types


def get_geocoding_opencage(city):
    """Get geocoding data from OpenCage or cache."""

    api_key = os.getenv('opencage_api')
    try:
        # Connect to the database
        params = get_database_config()
        with psycopg2.connect(**params) as connection:
            with connection.cursor() as crsr:
                # Check if the city is in the cache
                crsr.execute("SELECT lat, lng FROM geocoding_cache WHERE city = %s;", (city,))
                result = crsr.fetchone()

                if result:
                    print(f"Returning cached data for {city}: {result}")
                    return {"lat": result[0], "lng": result[1]}
    
    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error connecting to the database: {error}')

    # If not found in cache, make a request to OpenCage
    url = f'https://api.opencagedata.com/geocode/v1/json?q={city}&key={api_key}'
    
    #print(f"Geocoding request URL: {url}")  # Debugging the URL

    try:
        response = requests.get(url)

        if response.status_code == 200:
            results = response.json()
            #print(f"OpenCage API response: {results}")  # Debugging the response
            
            if results['results']:
                location = {
                    "lat": float(results['results'][0]['geometry']['lat']),
                    "lng": float(results['results'][0]['geometry']['lng'])
                }

                # Cache the result in the database
                with psycopg2.connect(**params) as connection:
                    with connection.cursor() as crsr:
                        crsr.execute(
                            "INSERT INTO geocoding_cache (city, lat, lng) VALUES (%s, %s, %s) "
                            "ON CONFLICT (city) DO UPDATE SET lat = %s, lng = %s;",
                            (city, location['lat'], location['lng'], location['lat'], location['lng'])
                        )
                        connection.commit()

                print(f"Cached new data for {city}: {location}")  # Debugging the cached location
                return location

        # Handle specific response codes
        if response.status_code == 403:
            print(f"Access denied to OpenCage API for {city}. Please check usage policy.")
        elif response.status_code == 429:
            print(f"Rate limit exceeded for OpenCage API for {city}.")
        else:
            print(f"Failed to retrieve data for {city}, Status code: {response.status_code}, Reason: {response.text}")

    except Exception as error:
        print(f"Error fetching geocoding data for {city}: {error}")

    return None
