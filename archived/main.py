from albumoftheyearapi.artist import ArtistMethods

artist_client = ArtistMethods()

# Get artist albums
artist_albums = artist_client.artist_albums('183-kanye-west')
print(artist_albums)

# Get artist mixtapes
artist_mixtapes = artist_client.artist_mixtapes('183-kanye-west')
print(artist_mixtapes)

# Get artist EPs
artist_eps = artist_client.artist_eps('183-kanye-west')
print(artist_eps)

# Get artist singles
artist_singles = artist_client.artist_singles('183-kanye-west')
print(artist_singles)

# Get album details
album_details = artist_client.album_details('262792-kanye-west-donda')
print(album_details)
