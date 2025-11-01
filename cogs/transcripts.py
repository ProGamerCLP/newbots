import discord, asyncio, datetime
from discord import app_commands
from discord.ext import commands
from config import Config
from utils.github_utils import save_transcript_to_github
from pathlib import Path

class TranscriptsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def es_ticket(self, channel: discord.TextChannel) -> bool:
        return channel.name.startswith(("denuncia-", "soporte-"))

    @app_commands.command(name="cerrar", description="Cierra el ticket y deja html en transcript-channel")
    @app_commands.checks.has_any_role(*Config.staff_roles_ids)
    async def cerrar(self, interaction: discord.Interaction):
        await self._cerrar(interaction, md=False)

    @app_commands.command(name="cerrar_md", description="Igual que /cerrar pero también envía el html al MD del usuario")
    @app_commands.checks.has_any_role(*Config.staff_roles_ids)
    async def cerrar_md(self, interaction: discord.Interaction):
        await self._cerrar(interaction, md=True)

    async def _cerrar(self, interaction: discord.Interaction, md: bool):
        if not self.es_ticket(interaction.channel):
            return await interaction.response.send_message("Este comando solo funciona dentro de tickets.", ephemeral=True)

        # Defer para permitir followups fiables
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("⏳ Este ticket se cerrará en 10 segundos...", ephemeral=True)
        await asyncio.sleep(10)

        # Recolectar mensajes
        messages = [msg async for msg in interaction.channel.history(limit=None, oldest_first=True)]
        metadata = {
            "guild_name": interaction.guild.name,
            "guild_icon": str(interaction.guild.icon.url) if interaction.guild.icon else "",
            "guild_id": interaction.guild.id,
            "channel_name": interaction.channel.name,
            "participation": {},  # lo calcularemos después
            "type": interaction.channel.name.split("-")[0],  # denuncia o soporte
            "creator": interaction.channel.name.split("-")[-1],
            "closer": str(interaction.user)
        }

        html_path = await save_transcript_to_github(messages, interaction.channel.name, metadata)
        if not html_path:
            return await interaction.followup.send("❌ Error al generar transcript.", ephemeral=True)

        # Resolver creador del ticket para mostrar en el embed y para posible MD
        creator: discord.User | None = None
        async for msg in interaction.channel.history(oldest_first=True, limit=50):
            if msg.mentions:
                creator = msg.mentions[0]
                break
        if not creator and interaction.channel.overwrites:
            for target, perms in interaction.channel.overwrites.items():
                if isinstance(target, discord.Member) and not target.bot and perms.read_messages:
                    creator = target
                    break

        # Preparar datos del embed
        first_msg = messages[0] if messages else None
        last_msg = messages[-1] if messages else None
        opened_at = first_msg.created_at if first_msg and hasattr(first_msg, 'created_at') else None
        last_author = getattr(last_msg.author, 'mention', str(last_msg.author)) if last_msg and hasattr(last_msg, 'author') else "—"
        last_content = getattr(last_msg, 'content', '') if last_msg else ''
        last_preview = (last_content[:100] + ('…' if len(last_content) > 100 else '')) if last_content else '—'

        # Enviar archivo a transcript-channel con embed detallado
        transcript_ch = interaction.guild.get_channel(Config.TRANSCRIPT_CHANNEL_ID)
        file = discord.File(html_path, filename=Path(html_path).name)
        embed = discord.Embed(title="📄 Ticket cerrado", timestamp=datetime.datetime.utcnow(), color=0x546e7a)
        embed.add_field(name="Canal", value=f"`{interaction.channel.name}`", inline=False)
        embed.add_field(name="Creado por", value=(creator.mention if creator else "`desconocido`"), inline=True)
        embed.add_field(name="Cerrado por", value=interaction.user.mention, inline=True)
        embed.add_field(name="Último mensaje", value=f"{last_author}: {last_preview}", inline=False)
        embed.add_field(name="Transcripción", value=f"Archivo HTML: `{Path(html_path).name}`", inline=False)
        if opened_at:
            embed.add_field(name="Fecha de apertura", value=f"{opened_at:%d/%m/%Y}", inline=True)
        embed.set_footer(text=f"ID: {interaction.channel.id}")

        if transcript_ch:
            await transcript_ch.send(embed=embed, file=file)
        else:
            await interaction.channel.send(embed=embed, file=file)

        # MD al usuario creador si se pidió
        if md:
            # Enviar DM si lo encontramos
            if creator:
                try:
                    dm_file = discord.File(html_path, filename=Path(html_path).name)
                    await creator.send("Aquí tienes la transcripción de tu ticket.", file=dm_file)
                except discord.Forbidden:
                    pass

        # Borrar canal y, si la categoría queda vacía, eliminarla
        category = interaction.channel.category
        remaining_in_category = len(category.text_channels) - 1 if category else 0
        await interaction.followup.send("✅ Ticket cerrado y transcripción generada.", ephemeral=True)
        await interaction.channel.delete(reason=f"Ticket cerrado por {interaction.user}")
        if category and remaining_in_category <= 0:
            try:
                await category.delete(reason="Categoría vacía tras cierre de ticket")
            except Exception:
                pass

    @app_commands.command(name="escalar", description="Mueve el ticket a otra categoría")
    @app_commands.checks.has_any_role(*Config.staff_roles_ids)
    async def escalar(self, interaction: discord.Interaction):
        if not self.es_ticket(interaction.channel):
            return await interaction.response.send_message("Este comando solo funciona dentro de tickets.", ephemeral=True)

        # Modal simple: seleccionar categoría
        class EscalarModal(discord.ui.Modal, title="Escalar ticket"):
            categoria = discord.ui.TextInput(label="Nombre de la nueva categoría", placeholder="ESCALADOS", max_length=100)

            async def on_submit(self, interaction: discord.Interaction):
                nueva_cat = discord.utils.get(interaction.guild.categories, name=self.categoria.value)
                if not nueva_cat:
                    nueva_cat = await interaction.guild.create_category(self.categoria.value)
                await interaction.channel.edit(category=nueva_cat)
                embed = discord.Embed(description=f"✅ Ticket escalado a **{self.categoria.value}**.", color=0xfaa61a)
                await interaction.channel.send(embed=embed)
                await interaction.response.send_message("Hecho ✅", ephemeral=True)

        await interaction.response.send_modal(EscalarModal())

async def setup(bot: commands.Bot):
    await bot.add_cog(TranscriptsCog(bot), guild=discord.Object(id=Config.GUILD_ID))