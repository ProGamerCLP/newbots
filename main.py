import discord
from discord.ext import commands
from config import Config
from keep_alive import keep_alive
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",  # solo para fallback, usaremos slash
    intents=intents,
    help_command=None,
    application_id=Config.APPLICATION_ID
)

@bot.event
async def on_ready():
    print(f"🟢 {bot.user} conectado")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=Config.GUILD_ID))
        print(f"📟 Slash sincronizados: {len(synced)}")
    except Exception as e:
        print("❌ Error al sincronizar:", e)

async def load_cogs():
    for cog in ("cogs.tickets", "cogs.claims", "cogs.transcripts"):
        try:
            await bot.load_extension(cog)
            print(f"📦 {cog} cargado")
        except Exception as e:
            print(f"❌ {cog} falló:", e)

async def main_app():
    keep_alive()
    await load_cogs()
    await bot.start(Config.TOKEN)

if __name__ == '__main__':
    asyncio.run(main_app())