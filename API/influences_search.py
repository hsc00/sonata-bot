import requests
from bs4 import BeautifulSoup
import json
import os

def get_list(artist_name, list_id):
    url = f"https://inflooenz.com/?artist={artist_name}&submit=Search"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the section that contains the relevant list
        list_section = soup.find('ul', id=list_id)
        
        if list_section is None:
            return []

        # Extract names or details, while filtering out unwanted elements
        names = [
            item.get_text() for item in list_section.find_all('a')
            if item.get_text().strip() != "" and "playlist" not in item.get_text().lower() 
               and "Get featured here!" not in item.get_text()
        ]
        
        return names
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return []

def save_to_cache(artist_name, list_type, names):
    # Only save if names are not empty
    if not names:
        return False
    
    # Create the data structure
    artist_key = artist_name.replace(" ", "-")
    
    # Define the cache file path
    cache_file_path = "cache/influences-cache.json"
    
    # Load existing data from the cache file if it exists, else initialize an empty dictionary
    cache_data = {}
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, "r") as cache_file:
                cache_data = json.load(cache_file)
        except json.JSONDecodeError:
            pass

    # Update the cache data with the new data
    if artist_key in cache_data:
        cache_data[artist_key][list_type] = names
    else:
        cache_data[artist_key] = {
            "artist_name": artist_name,
            list_type: names
        }

    # Write the updated data back to the cache file
    with open(cache_file_path, "w") as cache_file:
        json.dump(cache_data, cache_file, indent=4)
    
    return True

def load_from_cache(artist_name):
    # Define the cache file path
    cache_file_path = "cache/influences-cache.json"
    
    # Check if the cache file exists
    if os.path.exists(cache_file_path):
        try:
            with open(cache_file_path, "r") as cache_file:
                cache_data = json.load(cache_file)
                artist_key = artist_name.replace(" ", "-")
                if artist_key in cache_data:
                    return cache_data[artist_key]
        except json.JSONDecodeError:
            pass
    
    return None
