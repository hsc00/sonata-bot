<div align=center>
   <img src="logo.png" width=250>

   <br>

   <quote>A Discord bot for music lovers</quote>

   <br>
</div>

---

**Sonata** is a Discord bot that brings [RateYourMusic](https://rateyourmusic.com/) ratings to your Discord server. Share your music taste, discover new albums, and explore what your community is listening to!

## 📖 Documentation

Full documentation is available at: **[Sonata Documentation](https://hsc00.github.io/sonata-bot/)**

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Discord Bot Token
- Last.fm API Key
- Genius API Token

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/hsc00/sonata-bot.git
cd sonata-bot
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
# or
just install
```

3. **Configure environment variables**

Create a `.env` file with your API keys:

```env
DISCORD_TOKEN=your_discord_bot_token
LASTFM_API_KEY=your_lastfm_api_key
LASTFM_API_SECRET=your_lastfm_api_secret
GENIUS_API_TOKEN=your_genius_token
```

4. **Run the bot**

```bash
python bot/bot.py
# or
just run
```

See the [full setup guide](https://hsc00.github.io/sonata-bot/setup/) for detailed instructions.

## 🛠️ Development

Uses [Just](https://github.com/casey/just) for task automation:

```bash
just setup      # Setup development environment
just run        # Run the bot
just lint       # Check code quality
just format     # Format code
just docs-serve # Serve documentation locally
```
