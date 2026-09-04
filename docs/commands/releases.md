# 💿 Release Commands

Browse albums, discover highly-rated releases, and explore what your server community is listening to.

---

## 🔍 Search & Information

### !release (`!r`, `!a`, `!album`)

Shows detailed information about a specific release from RateYourMusic, including ratings, genres, release date, and more.

If no release name is provided, the bot will use the release you're currently listening to on Last.fm.

**Options:**

- **Name** (optional) – The name of the release you want to search for. Defaults to your currently playing track on Last.fm.

!!! example "Usage Examples"
`     !release
    !release OK Computer
    !album Radiohead OK Computer
    `

---

## 👥 Community Ratings

### !whoratedrelease (`!wr`, `!wa`)

Shows a list of server members who have rated a specific release, sorted by their rating scores.

The command displays the average rating and total number of ratings for the release within your server.

**Options:**

- **Name** (optional) – The name of the release you want to search for. You can use `artist - album` or `album by artist` to disambiguate releases with the same name.

!!! example "Usage Examples"
`     !whoratedrelease
     !whoratedrelease OK Computer
     !wr Radiohead - In Rainbows
     `

### !bestratedreleases (`!brr`, `!brab`)

Shows the top-rated releases among server members, ranked using a weighted formula that considers both average rating and number of ratings.

Only releases with more than 3 ratings are included to ensure meaningful results.

!!! example "Usage Examples"
`     !bestratedreleases
    !brr
    `

!!! tip
This is a great way to discover highly-regarded albums within your community!

!!! info "Bayesian Average Formula"
Releases are ranked using a Bayesian average, inspired by RYM's chart approach:
`     bayesian_avg = (rating_count × average_rating + 3 × global_avg) / (rating_count + 3)
    `
Where `global_avg` is the server's overall average rating. This prevents albums with only a few ratings from dominating the rankings by pulling them toward the server average.

### !worstratedreleases (`!wrr`, `!wrab`)

Shows the lowest-rated releases among server members, ranked using the same weighted formula as `!bestratedreleases`, but sorted from lowest to highest score.

Only releases with more than 3 ratings are included to ensure meaningful results.

!!! example "Usage Examples"
`     !worstratedreleases
     !wrr
     `

### !mostratedreleases (`!mrr`, `!mrab`)

Shows the most-rated releases among server members, sorted by the number of ratings received.

!!! example "Usage Examples"
`     !mostratedreleases
    !mrr
    `

---

## 🎲 Discovery & Fun

### !randomrating (`!rdr`)

Shows a random release rated by a server member, with an optional filter for high or low ratings.

**Options:**

- **Filter** (optional) – Filter to apply to the random selection:
  - `glaze` – Only high ratings (4.5+ out of 5)
  - `roast` – Only low ratings (2.0 or lower)

!!! example "Usage Examples"
`     !randomrating
    !randomrating glaze
    !randomrating roast
    `

### !newreleases (`!nr`)

Displays new releases of the current week from various artists.

This command fetches the latest releases from Sputnikmusic and shows information about them, including ratings if available on RateYourMusic.

!!! example "Usage Examples"
`     !newreleases
    !nr
    `

---

## 📅 Year-based

### !albumoftheyear (`!aoty`)

Shows the best-rated releases of a specific year for the server or a specific user, sorted by rating score.

Discover personal or community favorites from any year!

When no user is specified, shows the server's highest-rated releases of that year using Bayesian averaging. When a user is specified, shows only that user's ratings.

Only ratings of **3.5 or higher** are included to ensure meaningful results.

**Options:**

- **Year** (optional) – The year you want to search for. If not provided, the current year will be used.
- **User** (optional) – The user whose ratings you want to check. If not provided, shows the server-wide best rated releases.

!!! example "Usage Examples"
`     !albumoftheyear
     !aoty 2025
     !aoty 2025 @username
     `

!!! info
Year must be between 1900 and the current year.

---

## 📈 Rating History

### !history (`!h`)

Check the rating history for a specific release. The bot tracks rating score changes over time and displays them in a paginated embed.

**Options:**

- **Name** (optional) – The name of the release you want to search for. Defaults to your currently playing track on Last.fm.

!!! example "Usage Examples"
    ```
    !history
    !h OK Computer
    !history Radiohead - In Rainbows
    ```

!!! info
    The bot refreshes album ratings every 7 days in the background. If no history is available, it means the rating hasn't changed since tracking began.

---

### !lowestratedalbumsoftheyear (`!laoty`, `!aotyl`)

Shows the lowest-rated releases of a specific year for the server or a specific user, sorted by rating score from lowest to highest.

Discover the most divisive releases from any year!

When no user is specified, shows the server's lowest-rated releases of that year using Bayesian averaging. When a user is specified, shows only that user's ratings.

Only ratings of **2.0 or lower** are included to ensure meaningful results.

**Options:**

- **Year** (optional) – The year you want to search for. If not provided, the current year will be used.
- **User** (optional) – The user whose ratings you want to check. If not provided, shows the server-wide worst rated releases.

!!! example "Usage Examples"
`     !lowestratedalbumsoftheyear
      !laoty 2025
      !laoty 2025 @username
      `

!!! info
Year must be between 1900 and the current year.
