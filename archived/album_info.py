import json
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import logging

class Album:
    def __init__(self, name, artist, date):
        self.name = name
        self.artist = artist
        self.release_date = date

    def to_JSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=0)

class AlbumMethods:
    def __init__(self):
        self.upcoming_album_class = "albumBlock five small"
        self.aoty_albums_per_page = 60
        self.page_limit = 21

    def album_details(self, album_id):
        url = f"https://www.albumoftheyear.org/album/{album_id}/"
        self.req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        ugly_album_page = urlopen(self.req).read()
        album_page = BeautifulSoup(ugly_album_page, "html.parser")

        try:
            album_title = album_page.find("div", class_="albumTitle").find("span", itemprop="name").get_text().strip()
        except AttributeError:
            album_title = "Album title not found"
            logging.warning("Album title not found")

        try:
            artist_name = album_page.find("div", class_="artist").find("span", itemprop="name").get_text().strip()
        except AttributeError:
            artist_name = "Artist name not found"
            logging.warning("Artist name not found")

        try:
            release_date = album_page.find("div", class_="detailRow").get_text().strip()
            release_date = release_date.split("/")[0].strip()  # Clean up the release date
        except AttributeError:
            release_date = "Release date not found"
            logging.warning("Release date not found")

        try:
            genre = ", ".join([genre.get_text().strip() for genre in album_page.find_all("a", itemprop="genre")])
        except AttributeError:
            genre = "Genre not found"
            logging.warning("Genre not found")

        try:
            label = ", ".join([label.get_text().strip() for label in album_page.find_all("div", class_="detailRow")[2].find_all("a")])
        except AttributeError:
            label = "Label not found"
            logging.warning("Label not found")

        try:
            cover_url = album_page.find("div", class_="albumTopBox cover").find("img")["src"]
        except AttributeError:
            cover_url = "Cover image not found"
            logging.warning("Cover image not found")

        try:
            user_score = album_page.find("div", class_="albumUserScore").find("a").get_text().strip()
        except AttributeError:
            user_score = "User score not found"
            logging.warning("User score not found")

        try:
            num_ratings = album_page.find("div", class_="albumUserScoreBox").find("div", class_="text numReviews").find("a").find("strong").get_text().strip()
        except AttributeError:
            num_ratings = "Number of ratings not found"
            logging.warning("Number of ratings not found")

        try:
            rank_of_year = album_page.find("div", class_="albumUserScoreBox").find("div", class_="text gray").find_all("a")[0].get_text().strip()
        except AttributeError:
            rank_of_year = "Rank of the year not found"
            logging.warning("Rank of the year not found")

        try:
            alltime_rank = album_page.find("div", class_="albumUserScoreBox").find("div", class_="text gray").find_all("a")[1].get_text().strip()
        except AttributeError:
            alltime_rank = "All-time rank not found"
            logging.warning("All-time rank not found")

        try:
            critic_score = album_page.find("div", class_="albumCriticScore").find("a").get_text().strip()
        except AttributeError:
            critic_score = "Critic score not found"
            logging.warning("Critic score not found")

        try:
            buy_buttons = album_page.find("div", class_="buyButtons")
            streaming_links = []
            for link in buy_buttons.find_all("a"):
                href = link["href"]
                if "amzn.to" not in href and "vinyl" not in href and "amazon" not in href:
                    name = link.text.strip()  # Extract the name of the streaming service
                    streaming_links.append({"name": name, "url": href})
        except AttributeError:
            streaming_links = "Streaming links not found"
            logging.warning("Streaming links not found")

        return {
            "album_title": album_title,
            "artist_name": artist_name,
            "release_date": release_date,
            "genre": genre,
            "label": label,
            "cover_url": cover_url,
            "user_score": user_score,
            "num_ratings": num_ratings,
            "rank_of_year": rank_of_year,
            "alltime_rank": alltime_rank,
            "critic_score": critic_score,
            "streaming_links": streaming_links
        }
