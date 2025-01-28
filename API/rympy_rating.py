class Rating:
    def __init__(self, *, id=None, first_name="", last_name="", first_name_localized="", 
                 last_name_localized="", title=None, release_year=None, rating=None, 
                 ownership=None, purchase_date=None, media_type=None, review=None, url=None, release=None) -> None:
        self.id = id
        self.artist_name = (first_name + " " + last_name).strip()
        self.artist_name_localized = (first_name_localized + " " + last_name_localized).strip()
        self.title = title
        self.release_year = release_year
        self.rating = rating
        self.ownership = ownership
        self.purchase_date = purchase_date
        self.media_type = media_type
        self.review = review
        self.url = url
        self.release = release

    def __eq__(self, other) -> bool:
        return self.id == other.id or (self.url and len(self.url) and self.url == other.url)