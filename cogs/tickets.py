import discord
from discord import app_commands
from discord.ext import commands
from config import Config
import yaml
from pathlib import Path
from utils.modals import Paso1Modal
from utils.ticket_utils import crear_ticket_instantaneo

YAML_PATH = Path(__file__).parent.parent / "assets" / "embeds.yaml"

with open(YAML_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

PANEL_EMBED = CONFIG["panel"]
OPTIONS = CONFIG["options"]

class TicketMenu(discord.ui.Select):
    def __init__(self):
        opts = [
            discord.SelectOption(label=opt["label"], value=opt["value"], emoji=opt["emoji"])
            for opt in OPTIONS
        ]
        super().__init__(placeholder="Selecciona un trámite...", options=opts, custom_id="ticket_menu")

    async def callback(self, interaction: discord.Interaction):
        selected = [o for o in OPTIONS if o["value"] == self.values[0]][0]
        if selected["questions"] == 0:
            await interaction.response.send_message("Abriendo ticket instantáneo...", ephemeral=True)
            await crear_ticket_instantaneo(interaction, selected)
            # Reiniciar la vista del panel para que el select quede limpio
            try:
                await interaction.message.edit(view=TicketView())
            except Exception:
                pass
        else:
            await interaction.response.send_modal(Paso1Modal(selected))
            # Al cerrar el modal, Discord resetea la selección, pero aseguramos re-render
            try:
                await interaction.message.edit(view=TicketView())
            except Exception:
                pass

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketMenu())

class TicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Registrar la vista persistente para que el menú funcione tras reinicios
        try:
            self.bot.add_view(TicketView())
        except Exception:
            pass

    @app_commands.command(name="enviar_panel", description="Envía el panel de tickets (solo staff)")
    @app_commands.checks.has_any_role(*Config.staff_roles_ids)
    async def enviar_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=PANEL_EMBED["title"],
            description=PANEL_EMBED["description"],
            color=PANEL_EMBED["color"]
        )
        if PANEL_EMBED["thumbnail"]:
            embed.set_thumbnail(url=PANEL_EMBED["thumbnail"])
        if PANEL_EMBED["image"]:
            embed.set_image(url=PANEL_EMBED["image"])
        if PANEL_EMBED["footer"]:
            embed.set_footer(text=PANEL_EMBED["footer"])

        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("Panel enviado ✅", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(TicketsCog(bot), guild=discord.Object(id=Config.GUILD_ID))