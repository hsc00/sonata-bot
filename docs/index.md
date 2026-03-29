# Welcome to Sonata 🎵

**Sonata** is a Discord bot that brings [RateYourMusic](https://rateyourmusic.com/) ratings and music discovery features to your Discord server. Connect with your community, share your favorite albums, and explore music tastes together!

---

## 📋 Features

- Retrieve information about music releases.
- Check user profiles and statistics.
- Explore ratings within your Discord server.

---

## 🚀 Getting Started

### 1. Set up Last.fm (Recommended)

Start by linking your Last.fm account to enable automatic track detection:

```
!setlastfm your_lastfm_username
```

This allows commands to automatically use the track you're currently listening to.

### 2. Import Your Ratings

Then, import your ratings from RateYourMusic:

1. Go to [RateYourMusic Export](https://rateyourmusic.com/musicexport)
2. Click "Begin export..." and download your CSV file
3. Use the import command with your CSV file attached:

```
!importratings
```

!!! warning "Warning"
    Depending on the number of ratings you have, the import process may take a while. Please be patient and do not try to re-run the command while the import is still in progress.

### 3. Explore Commands

Now you're all set! Check out the available [commands](commands/releases.md).

---

## 💡 Popular Commands

Here are some commands to get you started:

| Command | Description |
|---------|-------------|
| `!profile` | View your rating statistics |
| `!release OK Computer` | Get information about an album |
| `!artistratings Radiohead` | See all your ratings for an artist |
| `!bestratedreleases` | View the server's top-rated albums |
| `!lyrics` | Get lyrics for your current track |
| `!samples` | Discover samples in your current track |
| `!aoty` | View best albums of the year |

---

## 📖 Support & Links

- **[Setup Guide](setup.md)** – Install and configure your own instance
- **[GitHub Repository](https://github.com/hsc00/sonata-bot)** – Source code and issues
- **[RateYourMusic](https://rateyourmusic.com/)** – Where your ratings come from
- **[Last.fm](https://www.last.fm/)** – Automatic track detection

---

!!! warning "Data privacy"
    All rating data is stored locally on the bot's instance. No data is shared with third parties beyond the API calls to fetch public music information.