import requests
from bs4 import BeautifulSoup

# URL of the page to scrape
url = "https://www.last.fm/music/Portishead"

# Send a GET request to the page
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the div with the background image
div = soup.find('div', class_='header-new-background-image')
if div and 'style' in div.attrs:
    # Extract the URL from the style attribute
    style = div['style']
    start = style.find('url(') + 4
    end = style.find(')', start)
    image_url = style[start:end]
    print(image_url)
else:
    print("Image not found")
