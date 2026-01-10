# Artist commands

## !artist_ratings (`!ar`)

Shows user's ratings for a specific artist, ordered by score.

If no artist is provided, the command will use the last artist you listened to on Last.fm.

### Options:

- **User** – Select another user by mention or Discord user.
- **Artist** – The artist you want to search for.

!!! note "Examples" 
	`!artist_ratings Radiohead`  
	`!artist_ratings @user Radiohead`  

!!! warning "Order of arguments" 
	If an user is specified, it must come before the artist name.

## !best_rated_artists (`!bra`)

Shows the best rated artists, ranked using a weighted formula.

If no user is specified, this command shows the best rated artists across the entire server.  
If a user is specified, only that user’s ratings are taken into account.

!!! note "Examples" 
	`!best_rated_artists`  
	`!best_rated_artists @user`  

## !most_rated_artists (`!mrr`)

Shows the artists with the most ratings.

If no user is specified, this command shows the most rated artists across the entire server.
If a user is specified, only that user’s ratings are taken into account.

!!! note "Examples" 
	`!most_rated_artists`  
	`!most_rated_artists @user`