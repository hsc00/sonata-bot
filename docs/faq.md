# Frequently Asked Questions

## General Questions

### What is Sonata?

Sonata is a Discord bot that integrates RateYourMusic ratings with your Discord server, allowing you to share, compare, and discover music with your community.

### Is Sonata free?

Yes! Sonata is completely free and open-source. You can host your own instance or contribute to the project on [GitHub](https://github.com/hsc00/sonata-bot).

### Do I need a RateYourMusic account?

Yes, you need a RateYourMusic account to export your ratings. You can create one at [rateyourmusic.com](https://rateyourmusic.com/).

### Do I need a Last.fm account?

No, but it's highly recommended! Last.fm integration allows Sonata to automatically detect what you're currently listening to, making many commands easier to use.

---

## Setup & Configuration

### How do I add Sonata to my server?

If someone is hosting a public instance, they can provide you with an invite link. Otherwise, you'll need to host your own instance by following the [Setup Guide](setup.md).

### Where do I get the required API keys?

You'll need:

- **Discord Bot Token**: [Discord Developer Portal](https://discord.com/developers/applications)
- **Last.fm API Key**: [Last.fm API](https://www.last.fm/api/account/create)
- **Genius API Token**: [Genius API](https://genius.com/api-clients)

See the [Setup Guide](setup.md) for detailed instructions.

---

## Using the Bot

### How do I import my ratings?

1. Go to [RateYourMusic Export](https://rateyourmusic.com/musicexport)
2. Click "Begin export..." and download your CSV file
3. Use the command `!importratings` with your CSV file attached

See the [importratings command](commands/users.md#importratings-i) for more details.

### How long does the import take?

Import time depends on the number of ratings you have. For a few hundred ratings, it should take less than a minute. For thousands of ratings, it may take several minutes. The bot will notify you when the import is complete.

### Will importing delete my existing ratings?

Yes! Importing ratings will overwrite all your existing ratings in the bot. This ensures your data stays in sync with RateYourMusic.

### How do I link my Last.fm account?

Use the command:

```
!setlastfm your_lastfm_username
```

Replace `your_lastfm_username` with your actual Last.fm username.

### What's the difference between prefix commands and slash commands?

Sonata supports both:

- **Prefix commands** (e.g., `!release`) – Traditional Discord commands using the `!` prefix
- **Slash commands** (e.g., `/release`) – Modern Discord commands with autocomplete

Most commands support both methods.

---

## Commands

### Why isn't a command working?

Common reasons:

1. **Missing Last.fm setup**: Some commands require Last.fm to be set up with `!setlastfm`
2. **No ratings imported**: Many server statistics require at least some users to have imported ratings
3. **Insufficient permissions**: Make sure the bot has proper permissions in the channel
4. **Typo in command**: Double-check the command name and arguments

### Can I use commands without specifying a song?

Yes! Many commands can automatically detect what you're currently listening to on Last.fm. You must first link your account with `!setlastfm`.

### How are "best rated" rankings calculated?

Best rated commands use a weighted formula that considers:

- Average rating score
- Number of ratings
- Number of distinct releases (for artists)

This prevents albums/artists with only one or two highly-rated entries from dominating the rankings.

---

## Data & Privacy

### Where is my data stored?

All data is stored in a local SQLite database on the bot's host machine. Nothing is sent to external servers except for API calls to fetch public music information.

### Can other users see my ratings?

Yes, once you import your ratings, other server members can see them through various commands like `!whoratedrelease` and `!profile`.

### Can I delete my data?

Yes! You can delete all your ratings by importing an empty CSV file, or the bot owner can delete your data from the database.

### Does Sonata track my listening history?

No. Sonata only fetches your currently playing track from Last.fm when you use commands that need it. No listening history is stored.

---

## Troubleshooting

### The bot isn't responding to my commands

1. Check that the bot is online (green status indicator)
2. Verify the bot has "Read Messages" and "Send Messages" permissions
3. Try using the bot in a different channel
4. Check if slash commands work: `/profile`

### "No Last.fm username set" error

You need to link your Last.fm account first:

```
!setlastfm your_lastfm_username
```

### "No ratings found" error

This means either:

- You haven't imported your ratings yet (use `!importratings`)
- No one in the server has ratings for the specified artist/release
- The search query didn't match any results (try different keywords)

### Import failed

Common causes:

1. **Wrong file format**: Make sure you're uploading the CSV file from RateYourMusic
2. **Corrupted file**: Try exporting and downloading the file again
3. **Network issues**: Check your internet connection

### Lyrics not found

1. Not all songs have lyrics available on Genius
2. Make sure you're currently playing a song on Last.fm

---

## Features & Limitations

### Can I rate albums directly in Discord?

No, Sonata is designed to import and display ratings from RateYourMusic, not create new ones. You should rate albums on [rateyourmusic.com](https://rateyourmusic.com/) and then re-import your ratings.

### Does the bot support other music databases?

Currently, Sonata only supports RateYourMusic. Support for other platforms may be added in the future.

### Can I see ratings from outside my server?

No, all server-wide commands (like `!bestratedreleases`) only show ratings from members of your current server.

### Is there a limit to how many ratings I can import?

No! You can import as many ratings as you want from RateYourMusic.

### Can I use the bot in DMs?

Yes! Most commands work in direct messages with the bot. Server-specific commands (like `!bestratedreleases`) require you to be in a server.

---

## Contributing & Development

### How can I contribute?

Check out the [GitHub repository](https://github.com/hsc00/sonata-bot) to:

- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

### Can I host multiple instances?

Yes! Each instance has its own database, so you can run multiple bots for different servers or communities.

### What's the tech stack?

- **Language**: Python 3.10+
- **Discord Library**: discord.py
- **Database**: SQLite with Peewee ORM
- **APIs**: Last.fm, Genius, RateYourMusic (web scraping)

---

## Still Have Questions?

If your question isn't answered here:

1. Check the [Setup Guide](setup.md) for configuration help
2. Browse the [command documentation](commands/users.md)
3. Open an issue on [GitHub](https://github.com/hsc00/sonata-bot/issues)
