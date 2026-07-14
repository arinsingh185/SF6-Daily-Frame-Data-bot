import discord
from discord.ext import commands, tasks
import random
import datetime
import json
import os
import re
import aiohttp

#Config
TOKEN          = os.environ.get("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
ANNOUNCE_HOUR   = 12
ANNOUNCE_MINUTE = 0

FAT_JSON_URL = (
    "https://raw.githubusercontent.com/D4RKONION/FAT/main"
    "/src/js/constants/framedata/SF6FrameData.json"
)

SETTINGS_FILE = "guild_settings.json"

#Cancel option labels
CANCEL_LABELS = {
    "ch": "Chain", "sp": "Special", "su": "Super",
    "su1": "SA1", "su2": "SA2", "su3": "SA3",
    "tc": "Target Combo", "ju": "Juggle",
}

#Character colours
CHAR_COLOURS = {
    "Ryu": 0xC0392B,     "Ken": 0xE67E22,     "Luke": 0x3498DB,
    "Chun-Li": 0x9B59B6, "Guile": 0x27AE60,   "Zangief": 0xE74C3C,
    "Dhalsim": 0xF39C12, "E.Honda": 0x1ABC9C,  "Blanka": 0x2ECC71,
    "Cammy": 0x16A085,   "Dee Jay": 0xF1C40F,  "Juri": 0xE91E63,
    "Manon": 0xAB47BC,   "Marisa": 0xBF360C,   "JP": 0x455A64,
    "Lily": 0x26C6DA,    "Jamie": 0xFFA726,    "Kimberly": 0xEC407A,
    "Rashid": 0xFFEB3B,  "A.K.I.": 0x7E57C2,  "Ed": 0x42A5F5,
    "Akuma": 0x880E4F,   "M.Bison": 0x6A1A9A,  "Terry": 0xD32F2F,
    "Mai": 0xF06292,     "Elena": 0x00ACC1,    "Ingrid": 0xCE93D8,
    "Alex": 0x26A69A,    "Sagat": 0xF57F17,    "C.Viper": 0xE53935,
}

#Helpers
def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())

def ufd_char_url(char: str) -> str:
    return f"https://ultimateframedata.com/sf6/{_slug(char)}"

def ufd_hitbox_url(char: str, move_name: str) -> str:
    """
    Best-guess UFD hitbox GIF URL. Will 404 for some moves (embed just
    won't render an image in that case — Discord handles it gracefully).
    """
    return f"https://ultimateframedata.com/hitboxes/sf6/{_slug(char)}/{_slug(move_name)}.gif"

#Data loading
_move_pool: list[dict] = []

async def fetch_fat_data() -> list[dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get(FAT_JSON_URL) as resp:
            resp.raise_for_status()
            raw = await resp.json(content_type=None)

    pool = []
    for char_name, char_data in raw.items():
        for _category, moves in char_data.get("moves", {}).items():
            for _move_name, move in moves.items():
                if move.get("startup") is None:
                    continue 
                pool.append({"character": char_name, **move})
    return pool

#Embed builder
def build_embed(move: dict) -> discord.Embed:
    char      = move["character"]
    name      = move.get("moveName", "Unknown Move")
    cmd       = move.get("plnCmd") or move.get("numCmd") or "?"
    startup   = move.get("startup",  "?")
    active    = move.get("active",   None)
    recovery  = move.get("recovery", "?")
    on_hit    = move.get("onHit",    "?")
    on_block  = move.get("onBlock",  "?")
    damage    = move.get("dmg",      "?")
    move_type = move.get("movesList") or move.get("moveType", "").title() or "Normal"

    # Format on-hit / on-block with +/- sign
    def fmt_adv(v):
        if isinstance(v, int):
            return f"+{v}" if v > 0 else str(v)
        return str(v) if v is not None else "?"

    # Cancel options
    xx_raw = move.get("xx", [])
    cancels = ", ".join(CANCEL_LABELS.get(x, x.upper()) for x in xx_raw) if xx_raw else "None"

    extra = move.get("extraInfo", [])
    notes = "\n".join(f"• {e}" for e in extra[:3]) if extra else ""

    colour   = CHAR_COLOURS.get(char, 0xFF6F00)
    char_url = ufd_char_url(char)

    embed = discord.Embed(
        title=f"🎮  Move of the Day — {char}: {name}",
        description=f"**Input:** `{cmd}`  •  *{move_type}*",
        colour=colour,
        url=char_url,
    )

    embed.add_field(name="▶️ Startup",   value=f"`{startup}f`",                          inline=True)
    embed.add_field(name="⚡ Active",    value=f"`{active}f`" if active else "`—`",      inline=True)
    embed.add_field(name="🔄 Recovery",  value=f"`{recovery}f`",                         inline=True)
    embed.add_field(name="🤜 On Hit",    value=f"`{fmt_adv(on_hit)}`",                   inline=True)
    embed.add_field(name="🛡 On Block",  value=f"`{fmt_adv(on_block)}`",                 inline=True)
    embed.add_field(name="💥 Damage",    value=f"`{damage}`",                            inline=True)
    embed.add_field(name="🔗 Cancels",   value=cancels,                                  inline=False)

    if notes:
        embed.add_field(name="📝 Notes", value=notes, inline=False)

    embed.set_image(url=ufd_hitbox_url(char, name))

    embed.add_field(
        name="🔍 Full Frame Data",
        value=(
            f"[View on Ultimate Frame Data]({char_url})\n"
            f"*Data via [FAT](https://github.com/D4RKONION/FAT) by D4RKONION*"
        ),
        inline=False,
    )

    embed.set_footer(text="SF6 Move of the Day • Data: FAT / ultimateframedata.com")
    embed.timestamp = discord.utils.utcnow()
    return embed

#Settings
def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return {}

def save_settings(data: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

#Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

guild_settings: dict = {}

#Daily task
@tasks.loop(time=datetime.time(hour=ANNOUNCE_HOUR, minute=ANNOUNCE_MINUTE,
                               tzinfo=datetime.timezone.utc))
async def daily_move():
    if not _move_pool:
        return
    move  = random.choice(_move_pool)
    embed = build_embed(move)
    for guild_id, cfg in guild_settings.items():
        ch = bot.get_channel(cfg["channel_id"])
        if ch:
            try:
                await ch.send(content="🔥 **SF6 Move of the Day!** Study up.", embed=embed)
            except discord.Forbidden:
                print(f"[WARN] No send permission in guild {guild_id}")

@daily_move.before_loop
async def before_daily():
    await bot.wait_until_ready()

#Commands
@bot.tree.command(name="setchannel", description="Set the channel for daily SF6 move posts")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_settings[str(interaction.guild_id)] = {"channel_id": channel.id}
    save_settings(guild_settings)
    await interaction.response.send_message(
        f"✅ Daily SF6 moves will post in {channel.mention} at "
        f"{ANNOUNCE_HOUR:02d}:{ANNOUNCE_MINUTE:02d} UTC.",
        ephemeral=True,
    )

@bot.tree.command(name="randommove", description="Pull a random SF6 move right now")
async def randommove(interaction: discord.Interaction):
    if not _move_pool:
        await interaction.response.send_message(
            "⚠️ Frame data still loading, try again in a moment.", ephemeral=True)
        return
    move  = random.choice(_move_pool)
    embed = build_embed(move)
    await interaction.response.send_message(content="🎲 Random SF6 move:", embed=embed)

@bot.tree.command(name="character", description="Get a random move for a specific character")
async def character(interaction: discord.Interaction, name: str):
    if not _move_pool:
        await interaction.response.send_message("⚠️ Frame data still loading.", ephemeral=True)
        return
    matches = [m for m in _move_pool if m["character"].lower() == name.lower()]
    if not matches:
        chars = ", ".join(sorted(set(m["character"] for m in _move_pool)))
        await interaction.response.send_message(
            f"❌ `{name}` not found.\n**Available:** {chars}", ephemeral=True)
        return
    embed = build_embed(random.choice(matches))
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sf6help", description="Show SF6 bot commands")
async def sf6help(interaction: discord.Interaction):
    chars = ", ".join(sorted(set(m["character"] for m in _move_pool))) if _move_pool else "Loading…"
    embed = discord.Embed(
        title="SF6 Daily Move Bot — Commands",
        colour=0xFF6F00,
        description=(
            "Frame data powered by **[FAT](https://github.com/D4RKONION/FAT)** by D4RKONION\n"
            "Hitboxes from **[ultimateframedata.com](https://ultimateframedata.com/sf6)**\n\n"
            "**`/setchannel #channel`** — Set where daily posts go *(Manage Server)*\n"
            "**`/randommove`** — Pull a random move instantly\n"
            "**`/character <name>`** — Random move for a specific character\n"
            "**`/sf6help`** — This menu\n\n"
            f"Daily posts fire at **{ANNOUNCE_HOUR:02d}:{ANNOUNCE_MINUTE:02d} UTC**\n\n"
            f"**Roster:** {chars}"
        ),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

#on_ready
@bot.event
async def on_ready():
    global guild_settings, _move_pool
    guild_settings = load_settings()

    print(f"[SF6 Bot] Logged in as {bot.user} | Fetching FAT frame data...")
    try:
        _move_pool = await fetch_fat_data()
        chars = len(set(m["character"] for m in _move_pool))
        print(f"[SF6 Bot] Loaded {len(_move_pool)} moves across {chars} characters")
    except Exception as e:
        print(f"[SF6 Bot] ERROR loading FAT data: {e}")

    daily_move.start()
    await bot.tree.sync()
    print(f"[SF6 Bot] Ready | {len(bot.guilds)} server(s) | "
          f"Daily post at {ANNOUNCE_HOUR:02d}:{ANNOUNCE_MINUTE:02d} UTC")

bot.run(TOKEN)