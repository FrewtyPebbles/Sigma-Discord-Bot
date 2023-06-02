from discord.ext import commands
import discord
from bot_class import DBBot
from discord import app_commands



class Admin(commands.Cog):
    def __init__(self, bot:DBBot):
        self.bot = bot
        self.db = bot.db
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.bot.user}')

    async def games_autocomplete(self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        guild_config:dict = await self.db.guild_config.find_one({"gid":interaction.guild_id})
        ret_list = [
            app_commands.Choice(name=choice, value=choice)
            for choice in guild_config["platforms"]
        ]
        return ret_list

    @app_commands.command(name="addplatform", description="Adds specified platform option that people can add to their profile.")
    @app_commands.checks.has_permissions(administrator=True)
    async def addplatform(self, interaction:discord.Interaction, platform:str):
        await self.db.guild_config.update_one(
            {
                "gid":interaction.guild_id,
            },
            {
                "$push": {f"platforms":platform}
            },
            upsert = True)
        
        await interaction.response.send_message(f"Added *{platform}* to server platform list.")

    @app_commands.command(name="removeplatform", description="Removes a platform option from all users' profiles and the server.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.autocomplete(platform=games_autocomplete)
    async def removeplatform(self, interaction:discord.Interaction, platform:str):
        await self.db.guild_config.update_one({"gid":interaction.guild_id}, {
            "$pull": {f"platforms":platform}
        },
        upsert = True)
        
        await self.db.profile.update_many({"gid":interaction.guild_id}, {
            "$pull": {f"platforms":{"name":platform}}
        })

        await interaction.response.send_message(f"Removed *{platform}* from server platform list.")

    @commands.command(name='sigmasync', description='Owner only')
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: commands.Context):
        fmt = await ctx.bot.tree.sync()
        await ctx.send(f'{len(fmt)} commands synced with server.')

async def setup(client):
    await client.add_cog(Admin(client))