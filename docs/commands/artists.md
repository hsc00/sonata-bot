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

!!! info "Bayesian Average Formula"
    Artists are ranked using a Bayesian average, inspired by RYM's chart approach:
    ```
    bayesian_avg = (distinct_user_count × average_score + 3 × global_avg) / (distinct_user_count + 3)
    ```
    Where `global_avg` is the server's overall average rating. Using `distinct_user_count` prevents a single user from artificially inflating an artist's ranking.

### !worstratedartists (`!wra`)

Discover the worst rated artists ranked using the same Bayesian average formula as `!bestratedartists`, sorted from lowest to highest score.

**Scope:**

- **No user specified**: Shows the worst rated artists across the entire server
- **User specified**: Shows only that user's worst rated artists

Only artists with more than 3 ratings are included to ensure meaningful results.

!!! example "Usage Examples"
    ```
    !worstratedartists
    !wra @user
    ```

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

---

## 🔗 Influences & Followers

### !influences (`!inf`)

Check an artist's influences from Wikidata.

Displays artists that have influenced the queried artist, based on Wikidata's `P737` property.

**Options:**

- **Artist** (optional) – The artist you want to search for. Defaults to your currently playing artist on Last.fm.

!!! example "Usage Examples"
    ```
    !influences
    !inf Radiohead
    ```

!!! info "Data Source"
    Data is sourced from Wikidata and cached for 7 days. Coverage varies by artist.

### !followers (`!fl`)

Check artists influenced by an artist.

Displays artists that were influenced by the queried artist, based on Wikidata's `P737` property (reverse lookup).

**Options:**

- **Artist** (optional) – The artist you want to search for. Defaults to your currently playing artist on Last.fm.

!!! example "Usage Examples"
    ```
    !followers
    !fl Radiohead
    ```

!!! info "Data Source"
    Data is sourced from Wikidata and cached for 7 days. Coverage varies by artist.