# 🎮 SF6 Daily Move Bot

A Discord bot that posts a random Street Fighter 6 move every day — complete with **frame data** and a **hitbox GIF** link from [Ultimate Frame Data](https://ultimateframedata.com/sf6/).

---

## Features

| Feature | Description |
|---|---|
| ⏰ Daily Post | Posts one random SF6 move at **12:00 UTC** every day |
| 🖼 Hitbox GIF | Animated hitbox visualization embedded directly in Discord |
| 📊 Frame Data | Startup / Active / Recovery / On-Hit / On-Block / Damage |
| 🎲 `/randommove` | Pull a random move on demand |
| 🥊 `/character <name>` | Random move for a specific character |
| ⚙️ `/setchannel` | Configure which channel gets the daily post |

---

## Setup

### 1. Create a Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** → give it a name
3. Go to **Bot** → click **Add Bot**
4. Under **Privileged Gateway Intents**, enable **Message Content Intent**
5. Copy your **Bot Token**
6. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Read Message History`, `View Channels`
7. Open the generated URL to invite the bot to your server

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Your Bot Token

**Option A — environment variable (recommended):**
```bash
export DISCORD_TOKEN="your_token_here"
python bot.py
```

**Option B — edit `bot.py`:**
```python
TOKEN = "your_token_here"
```

### 4. Run the Bot

```bash
python bot.py
```

---

## Commands

| Command | Description | Permission |
|---|---|---|
| `/setchannel #channel` | Set the daily post channel | Manage Server |
| `/randommove` | Get a random move immediately | Anyone |
| `/character <name>` | Random move for a character | Anyone |
| `/sf6help` | Show all commands | Anyone |

---

## Customizing the Daily Time

In `bot.py`, change these two constants:

```python
ANNOUNCE_HOUR   = 12   # Hour in UTC (0–23)
ANNOUNCE_MINUTE = 0    # Minute (0–59)
```

---

## Adding More Moves

Open `move_data.py` and add entries to the `SF6_MOVES` list:

```python
{
    "character": "Ryu",
    "name": "Crouching MP",
    "input": "↓ + MP",
    "startup": 5,
    "active": 3,
    "recovery": 11,
    "on_hit": "+7",
    "on_block": "+3",
    "damage": "600",
    "cancel_options": "Special, Super Art",
    "notes": "Ryu's cr.MP is a great combo starter and pressure button.",
    "hitbox_gif": "https://ultimateframedata.com/hitboxes/sf6/ryu/crmp.gif",
},
```

### Finding Hitbox GIF URLs

1. Visit [ultimateframedata.com/sf6/\<character\>](https://ultimateframedata.com/sf6/)
2. Find the move and right-click the hitbox GIF → **Copy Image Address**
3. Paste it as the `hitbox_gif` value

---

## Hosting Options

| Option | Cost | Notes |
|---|---|---|
| [Railway](https://railway.app) | Free tier | Easy deploy, just set `DISCORD_TOKEN` env var |
| [Fly.io](https://fly.io) | Free tier | Docker-based, great for always-on bots |
| [VPS / Home Server](https://ubuntu.com) | ~$5/mo | Full control, use `screen` or `systemd` |
| Raspberry Pi | One-time hardware | Run 24/7 on your LAN |

### Example systemd service (Linux VPS)

```ini
[Unit]
Description=SF6 Discord Bot
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/sf6-bot
Environment=DISCORD_TOKEN=your_token_here
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Data Sources

- **Frame data** curated from [Ultimate Frame Data](https://ultimateframedata.com/sf6/) by MetalMusicMan
- **Hitbox GIFs** created by MetalMusicMan using the Hitbox Viewer by WistfulHopes
- This bot is a fan project and is not affiliated with Capcom

---

## File Structure

```
sf6-bot/
├── bot.py            # Main bot logic, commands, daily task
├── move_data.py      # SF6 move database (frame data + hitbox GIF URLs)
├── requirements.txt  # Python dependencies
├── guild_settings.json  # Auto-created: maps servers → channels
└── README.md
```
