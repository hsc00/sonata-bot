# Users commands

## !set_lastfm

Sets your Last.fm username to link your Discord account with your Last.fm account. This allows the bot to fetch what you're currently listening to for other commands.

### Options:

- **Username** – Your [Last.fm](https://www.last.fm/) username to link with your Discord account.

!!! note "Examples" 
    `!set_lastfm @username`  

## !ratings_rank (`!rr`)

Show a ranked list of users based on the number of ratings they have submitted.

!!! note "Examples" 
    `!ratings_rank`

## !profile

Shows your profile with statistics about your ratings.

### Options:

- **User** – Select another user by mention or Discord user.

!!! note "Examples" 
    `!profile`  
    `!profile @user`

## !import_ratings (`!i`)

Import your ratings from a CSV file exported from RateYourMusic.   
A file can be obtained by going [here](https://rateyourmusic.com/music_export) and clicking `Begin export...`.  
Then, attach the downloaded CSV file to the command. You can do this by dragging and dropping the file into the message box or by clicking on the ➕ button left of the message box and then select `Upload a file`.

!!! note "Examples" 
    `!import_ratings <file>`

!!! info 
    The import process may take a while depending on the number of ratings you have. Please be patient and do not try to re-run the command while the import is still in progress.

!!! warning 
    Importing ratings will overwrite any existing ratings you have in the bot. 