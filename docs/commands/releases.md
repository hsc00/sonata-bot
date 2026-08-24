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

- **Name** (optional) – The name of the release you want to search for. Defaults to your currently playing track on Last.fm.

!!! example "Usage Examples"
`     !whoratedrelease
    !whoratedrelease OK Computer
    !wr Radiohead In Rainbows
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

Shows the best-rated releases of a specific year for a user, sorted by rating score.

Discover personal or community favorites from any year!

**Options:**

- **Year** (optional) – The year you want to search for. If not provided, the current year will be used.
- **User** (optional) – The user whose ratings you want to check. If not provided, shows your own ratings.

!!! example "Usage Examples"
`     !albumoftheyear
    !aoty 2025
    !aoty 2025 @username
    `

!!! info
Year must be between 1900 and the current year.
