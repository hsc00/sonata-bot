# Setup & Configuration

This guide will help you set up and run Sonata bot on your own Discord server.

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10+** installed on your system
- A **Discord Bot Token** from the [Discord Developer Portal](https://discord.com/developers/applications)
- A **Last.fm API key** from [Last.fm API](https://www.last.fm/api/account/create)
- A **Genius API token** from [Genius API](https://genius.com/api-clients)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/hsc00/sonata-bot.git
cd sonata-bot
```

### 2. Install Dependencies

You can install dependencies using pip:

```bash
pip install -r requirements.txt
```

Or use the justfile:

```bash
just install
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Discord Bot Token (Required)
DISCORD_TOKEN=your_discord_bot_token_here

# Last.fm API Credentials (Required)
LASTFM_API_KEY=your_lastfm_api_key_here
LASTFM_API_SECRET=your_lastfm_api_secret_here

# Genius API Token (Required for lyrics and samples commands)
GENIUS_API_TOKEN=your_genius_token_here

# Database Configuration (Optional)
DATABASE_PATH=./sonata.db
```

### 4. Set Up the Database

The bot uses SQLite for storing ratings and user information. The database will be created automatically on first run, but you can initialize it manually:

```bash
just migrate
```

Or:

```bash
python -c "from bot.database.migrations import run_migrations; run_migrations()"
```

## Running the Bot

Once everything is configured, you can start the bot:

```bash
just run
```

Or:

```bash
python bot/bot.py
```

The bot should now be online and ready to use!

## Discord Bot Setup

### Creating a Bot Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Navigate to the "Bot" section in the left sidebar
4. Click "Add Bot"
5. Under the "Token" section, click "Copy" to get your bot token
6. Paste this token into your `.env` file as `DISCORD_TOKEN`

### Bot Permissions

The bot requires the following permissions:

- **Read Messages/View Channels**
- **Send Messages**
- **Embed Links**
- **Attach Files**
- **Read Message History**
- **Use External Emojis**
- **Add Reactions**

Permission Integer: `397284600896`

### Inviting the Bot to Your Server

1. In the Developer Portal, go to the "OAuth2" > "URL Generator" section
2. Select the "bot" scope
3. Select the permissions listed above
4. Copy the generated URL and open it in your browser
5. Select the server you want to add the bot to and click "Authorize"

## API Keys

### Getting a Last.fm API Key

1. Visit [Last.fm API Account Creation](https://www.last.fm/api/account/create)
2. Fill out the form with your application details
3. You'll receive an API Key and Shared Secret
4. Add both to your `.env` file

### Getting a Genius API Token

1. Visit [Genius API Clients](https://genius.com/api-clients)
2. Click "New API Client"
3. Fill out the form with your application details
4. Once created, click "Generate Access Token"
5. Copy the token and add it to your `.env` file

## Troubleshooting

### Bot doesn't respond to commands

- Verify the bot has proper permissions in your server
- Check that the `DISCORD_TOKEN` in your `.env` file is correct
- Make sure the bot is online (check the console for any error messages)
- Try syncing slash commands: `!sync guild` or `!sync global`

### Import ratings fails

- Ensure your CSV file is exported correctly from RateYourMusic
- Check that the file format matches RYM's export format
- Wait for the import to complete - large libraries can take several minutes

### Last.fm integration not working

- Verify your `LASTFM_API_KEY` and `LASTFM_API_SECRET` are correct
- Make sure you've set your Last.fm username with `!setlastfm`
- Check that your Last.fm profile is public

### Lyrics/Samples not found

- Ensure your `GENIUS_API_TOKEN` is valid
- Not all tracks have lyrics or sample information available
- Try using the full artist and track name

## Development

For development work, you can use the development setup:

```bash
just setup
```

This will install the package in editable mode with development dependencies.

### Running Tests

```bash
just test
```

### Code Quality

Check code quality:

```bash
just check
```

Auto-fix linting issues:

```bash
just lint-fix
```

Format code:

```bash
just format
```

## Documentation

To build and serve the documentation locally:

```bash
just docs-serve
```

The documentation will be available at `http://127.0.0.1:8000/`.

## Support

If you encounter any issues or have questions:

1. Check the [GitHub Issues](https://github.com/hsc00/sonata-bot/issues) page
2. Review the documentation thoroughly
3. Make sure all API keys are configured correctly
4. Check the console output for detailed error messages
