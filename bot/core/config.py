import os

from dotenv import load_dotenv

load_dotenv()

google_token = os.getenv("GOOGLE_API_KEY")
cse_id = os.getenv("GOOGLE_CSE_ID")
cse_id_streaming = os.getenv("GOOGLE_CSE_ID_STREAMING")
genius_api_key = os.getenv("GENIUS_API_KEY")
lastfm_api_key = os.getenv("LASTFM_API_KEY")
setlist_api_key = os.getenv("SETLIST_API_KEY")
spotify_id = os.getenv("SPOTIFY_ID")
spotify_secret = os.getenv("SPOTIFY_SECRET")
