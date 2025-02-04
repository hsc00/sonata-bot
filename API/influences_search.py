import requests
from bs4 import BeautifulSoup
import json
import os

def get_lists(artist_name):
    url = f"https://inflooenz.com/?artist={artist_name}&submit=Search"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the image URL
        img_tag = soup.find('img', class_='main')
        img_url = img_tag['src'] if img_tag else None

        # Find the sections that contain the relevant lists
        influencers_section = soup.find('ul', id='influencers-list')
        followers_section = soup.find('ul', id='followers-list')
        
        # Extract names or details, while filtering out unwanted elements
        influencers = [
            item.get_text() for item in influencers_section.find_all('a')
            if item.get_text().strip() != "" and "playlist" not in item.get_text().lower() 
               and "Get featured here!" not in item.get_text()
        ] if influencers_section else []

        followers = [
            item.get_text() for item in followers_section.find_all('a')
            if item.get_text().strip() != "" and "playlist" not in item.get_text().lower() 
               and "Get featured here!" not in item.get_text()
        ] if followers_section else []
        
        return {"artist_image": img_url, "influences": influencers, "followers": followers}
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return {"artist_image": None, "influences": [], "followers": []}

def save_to_cache(artist_name, data):
    # Only save if there is data to save
    if not data["influences"] and not data["followers"]:
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
    cache_data[artist_key] = {
        "artist_name": artist_name,
        "artist_image": data["artist_image"],
        "influences": data["influences"],
        "followers": data["followers"]
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
