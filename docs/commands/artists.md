# 🧑‍🎤 Artist Commands

Explore artist ratings, discover top-rated artists, and view statistics about your favorite musicians.

---

## ⭐ Artist Ratings

### !artistratings (`!ar`)

View all ratings for a specific artist, organized by release year and score.

If no artist is provided, the bot automatically uses the artist you're currently listening to on Last.fm. Results include the average score across all ratings for that artist.

**Options:**

- **User** (optional) – Select another user by mention or Discord user ID. If not provided, shows your own ratings.
- **Artist** (optional) – The artist you want to search for. If not provided, uses your currently playing artist on Last.fm.

!!! example "Usage Examples"
    ```
    !artistratings
    !artistratings Radiohead
    !ar @user Radiohead
    ```

!!! warning "Order of Arguments"
    If specifying a user, they must come **before** the artist name in your command.

!!! info "Last.fm Required"
    You must have set your Last.fm username with `!setlastfm` to use this command without specifying an artist.

---

## 🏆 Rankings & Statistics

### !bestratedartists (`!bra`)

Discover the best rated artists ranked using a sophisticated weighted formula that considers:

- Average rating score
- Total number of ratings
- Number of distinct releases

**Scope:**

- **No user specified**: Shows the best rated artists across the entire server
- **User specified**: Shows only that user's best rated artists

Only artists with more than 3 ratings are included to ensure meaningful results.

!!! example "Usage Examples"
    ```
    !bestratedartists
    !bra @user
    ```

!!! tip
    This is perfect for discovering consensus favorites in your community!

### !mostratedartists (`!mra`)

See which artists have received the most ratings, sorted by total rating count.

Find out which artists are most popular and widely listened to in your server!

**Scope:**

- **No user specified**: Shows the most rated artists across the entire server
- **User specified**: Shows only that user's most rated artists

!!! example "Usage Examples"
    ```
    !mostratedartists
    !mra @user
    ```