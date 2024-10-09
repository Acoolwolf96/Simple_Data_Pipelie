# Weather Data Itinerary Recommendation

This project is a weather-driven recommendation engine built using Python and Flask. It extracts current weather data from OpenWeatherMap, integrates it with the Google Places API to recommend nearby places and activities based on the weather and user preferences using OpenAI for AI-driven activity suggestions.

## Overview
This web application takes a user's location (by city or coordinates), fetches the current weather data, and provides personalized activity and place recommendations based on the weather conditions, duration of stay, and nearby locations. OpenAI is used to suggest tailored itineraries, which are then mapped to Google Places to offer nearby options such as restaurants, cafes, parks, and other points of interest.

## API Integration
OpenWeatherMap API: Fetches weather data using city or coordinates.
Google Places API: Retrieves nearby places (restaurants, parks, etc.) based on types derived from AI suggestions.
OpenAI API: Generates itinerary suggestions based on weather and time of day.
OpenCage API: Converts city names into latitude/longitude coordinates and caches them in a PostgreSQL database.

## Database
PostgreSQL: Used to cache geolocation data for cities and store historical weather information.
weather_data: Stores weather data like temperature, humidity, wind speed, etc.
geocoding_cache: Stores city names and their latitude/longitude for faster lookup and also reduce request to the API so as not to get blocked or abuse usage
