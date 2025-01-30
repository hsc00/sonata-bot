import requests

def search_streaming_links(query, api_key, cx):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cx
    }
    response = requests.get(url, params=params)
    results = response.json()

    streaming_links = {}
    for item in results.get('items', []):
        link = item.get('link')
        for service in ['spotify.com', 'apple.com', 'bandcamp.com', 'soundcloud.com', 'youtube.com']:
            if service in link and service not in streaming_links:
                streaming_links[service] = link
    
    return list(streaming_links.values())

# Example usage
api_key = 'AIzaSyB1iV2-ng6qnTkUiBDxHO9-3LEpnwwu8p0'
cx = '675a4e2c9985340ed'
query = "charli xcx brat album"
links = search_streaming_links(query, api_key, cx)
print(links)

##este algoritmo funciona, so tens de o fazer dar para artistas tambem
