import discord
from discord import app_commands
from discord.ext import commands
from config import Config

class ClaimsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.claimed = {}  # {channel_id: staff_member}

    def es_ticket(self, channel: discord.TextChannel) -> bool:
        return channel.name.startswith(("denuncia-", "soporte-"))

    @app_commands.command(name="claim", description="Atender este ticket")
    @app_commands.checks.has_any_role(*Config.staff_roles_ids)
    async def claim(self, interaction: discord.Interaction):
        if not self.es_ticket(interaction.channel):
            return await interaction.response.send_message("Este comando solo funciona dentro de tickets.", ephemeral=True)
        if interaction.channel.id in self.claimed:
            return await interaction.response.send_message("Este ticket ya está siendo atendido.", ephemeral=True)

        self.claimed[interaction.channel.id] = interaction.user
        rol_mas_alto = max(interaction.user.roles, key=lambda r: r.position)
        embed = discord.Embed(
            description=f"Hola {interaction.channel.mention}, en este momento tu ticket está siendo atendido por {interaction.user.mention} del departamento **{rol_mas_alto.name}**.",
            color=0x00d4aa
        )
        await interaction.channel.send(embed=embed)

        # Bloquear escritura al resto de staff
        for role_id in Config.STAFF_ROLES:
            role = interaction.guild.get_role(role_id)
            if role and role != rol_mas_alto:
                await interaction.channel.set_permissions(role, send_messages=False)

        await interaction.response.send_message("✅ Ticket reclamado.", ephemeral=True)

    @app_commands.command(name="unclaim", description="Libera el ticket")
    @app_commands.checks.has_any_role(*Config.staff_roles_ids)
    async def unclaim(self, interaction: discord.Interaction):
        if not self.es_ticket(interaction.channel):
            return await interaction.response.send_message("Este comando solo funciona dentro de tickets.", ephemeral=True)
        if self.claimed.get(interaction.channel.id) != interaction.user:
            return await interaction.response.send_message("No eres el usuario que reclamó este ticket.", ephemeral=True)

        self.claimed.pop(interaction.channel.id)
        embed = discord.Embed(description="El ticket ha sido liberado. Cualquier miembro del staff puede reclamarlo.", color=0xfaa61a)
        await interaction.channel.send(embed=embed)

        # Restaurar permisos
        for role_id in Config.STAFF_ROLES:
            role = interaction.guild.get_role(role_id)
            if role:
                await interaction.channel.set_permissions(role, send_messages=True)

        await interaction.response.send_message("✅ Ticket liberado.", ephemeral=True)

    @app_commands.command(name="adjuntar", description="Solicita más información al usuario")
    @app_commands.checks.has_any_role(*Config.staff_roles_ids)
    async def adjuntar(self, interaction: discord.Interaction):
        if not self.es_ticket(interaction.channel):
            return await interaction.response.send_message("Este comando solo funciona dentro de tickets.", ephemeral=True)

        # Buscar al creador del ticket (primer mención del canal)
        async for msg in interaction.channel.history(oldest_first=True, limit=10):
            if msg.mentions:
                user = msg.mentions[0]
                break
        else:
            return await interaction.response.send_message("No encontré al creador del ticket.", ephemeral=True)

        embed = discord.Embed(
            description=f"Hola {user.mention}, para continuar con tu caso necesitamos que por favor nos detalles más o complementes la información. **Toda esa información debe enviarse en un mismo mensaje.**",
            color=0x5865f2
        )
        await interaction.channel.send(content=user.mention, embed=embed)
        await interaction.response.send_message("✅ Solicitud enviada.", ephemeral=True)    


async def setup(bot: commands.Bot):
    await bot.add_cog(ClaimsCog(bot), guild=discord.Object(id=Config.GUILD_ID))