# Releases commands

## release (`!r`)

Shows information about a specific release from RateYourMusic.

### Options:

- **Name** – The name of the release you want to search for.

!!! note "Examples" 
    `!release`  
    `!release OK Computer`  

## who_rated_release (`!wr`, `!wrr`)

Shows a list of server members who have rated a specific release.

### Options:

- **Name** – The name of the release you want to search for.

!!! note "Examples" 
    `!who_rated_release`  
    `!who_rated_release OK Computer`  

## best_rated_releases (`!brr`)

Shows the top-rated releases among server members.

!!! note "Examples" 
    `!best_rated_releases`

## most_rated_releases (`!mrr`)

Shows the most-rated releases among server members.

!!! note "Examples" 
    `!most_rated_releases`

## random_rating (`!rdr`)

Shows a random release rated by server members, with an optional filter for high or low ratings.

### Options:

- **Filter**: – Filter to apply to the random selection. Possible values are:
    - `glaze` – Only include releases with high ratings (4 or 5 stars).
    - `roast` – Only include releases with low ratings (1 or 2 stars).

!!! note "Examples" 
    `!random_rating`  
    `!random_rating glaze`  
    `!random_rating roast`

## album_of_the_year (`!aoty`)

Shows the best-rated releases of an year for a specific user.

### Options:

- **Year** – The year you want to search for. If not provided, the current year will be used.
- **User** – The user whose ratings you want to check. If not provided, the command will check the ratings of the user who invoked the command.

!!! note "Examples" 
    `!album_of_the_year`  
    `!album_of_the_year 2025`  
    `!album_of_the_year 2025 @username`

