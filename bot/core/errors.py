class SonataError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NoLastFMUsername(SonataError):
    def __init__(self):
        super().__init__(
            "❌ No last.fm username set. Please provide a search term or set your last.fm username by running `!set_lastfm <username>`."
        )


class InvalidUserMention(SonataError):
    def __init__(self, user_id: str | None = None):
        message = f"❌ Invalid user mention: \"{user_id}\". Please provide a valid mention." if user_id else "❌ Missing user mention. Please provide a valid mention."

        super().__init__(message)


class NoRatingsFound(SonataError):
    def __init__(self, title: str | None = None):
        message = f"❌ No ratings found for \"{title}\"." if title else "❌ No ratings found."

        super().__init__(message)


class NoLyricsFound(SonataError):
    def __init__(self):
        super().__init__("❌ No lyrics found for the requested track.")


class InvalidYear(SonataError):
    def __init__(self, query: str):
        super().__init__(f"❌ Invalid year: {query}. Please provide a valid year.")

class RatingsImportFailed(SonataError):
    def __init__(self):
        super().__init__(f"❌ Failed to import ratings.")

class NoFileAttached(SonataError):
    def __init__(self):
        super().__init__("❌ No file attached. Please attach a valid CSV file with ratings.")