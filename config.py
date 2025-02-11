import os
from dotenv import load_dotenv

load_dotenv()

google_tokens = [
    os.getenv('GOOGLE_TOKEN_1'),
    os.getenv('GOOGLE_TOKEN_2'),
    os.getenv('GOOGLE_TOKEN_3'),
]
cse_id = os.getenv('GOOGLE_CSE_ID')
cse_id_streaming = os.getenv('GOOGLE_CSE_ID_STREAMING')
genius_api_key = os.getenv('GENIUS_API_KEY')
lastfm_api_key = os.getenv('LASTFM_API_KEY')
setlist_api_key = os.getenv('SETLIST_API_KEY')