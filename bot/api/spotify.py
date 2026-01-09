import requests
import spotipy
from classes.token_manager import TokenManager
from core.config import spotify_id, spotify_secret
from spotipy.oauth2 import SpotifyClientCredentials

# Initialize the global TokenManager
token_manager = TokenManager()


def get_token_manager(user_id):
    return token_manager


# Function to get Spotify links (not currently used)
def get_spotify_links(query):
    client_id = spotify_id
    client_secret = spotify_secret

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    results = sp.search(q=query, type="album")

    if results["albums"]["items"]:
        first_link = results["albums"]["items"][0]["external_urls"]["spotify"]
        return first_link
    return None


async def get_currently_playing(user_id):
    global token_manager  # Ensure we are using the global instance

    # Get the access token from the manager
    access_token = token_manager.get_access_token(user_id)

    if not access_token:
        # Token expired, use refresh token to get a new access token
        refresh_token = token_manager.get_refresh_token(user_id)

        if not refresh_token:
            return {
                "error": "You need to setup your spotify permissions. Type `!setspotify`, follow the instructions and try again ^_^"}

        token_url = "https://accounts.spotify.com/api/token"
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": spotify_id,
            "client_secret": spotify_secret,
        }
        token_response = requests.post(token_url, data=token_data)
        token_info = token_response.json()

        if "access_token" in token_info:
            access_token = token_info["access_token"]
            expires_in = token_info["expires_in"]
            token_manager.update_tokens(user_id, access_token, refresh_token, expires_in)
        else:
            print("Error refreshing access token.")
            return {
                "error": "You need to setup your spotify permissions again. Type `!setspotify`, follow the instructions and try again ^_^"}

    # Use the access token to get the currently playing track
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)

    if response.status_code == 200:
        track_info = response.json()
        track_name = track_info["item"]["name"]
        artists = ", ".join([artist["name"] for artist in track_info["item"]["artists"]])
        position_ms = track_info["progress_ms"]

        # Convert milliseconds to hours:minutes:seconds
        position_sec = position_ms // 1000
        hours = position_sec // 3600
        minutes = (position_sec % 3600) // 60
        seconds = position_sec % 60
        timestamp = f"{hours:02}:{minutes:02}:{seconds:02}"

        return {
            "track_name": track_name,
            "artists": artists,
            "timestamp": timestamp,
        }

    if response.status_code == 204:
        return {"error": "No track is currently playing 🤔"}

    return {"error": "Error fetching currently playing track 😞"}
