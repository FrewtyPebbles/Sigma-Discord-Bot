from discord.ext import commands
import discord
from bot_class import DBBot
from discord import app_commands



class Admin(commands.Cog):
    def __init__(self, bot:DBBot):
        self.bot = bot
        self.db = bot.db

    @app_commands.command(name="info", description="Displays info about SIGMA Bot.")
    async def info(self, interaction:discord.Interaction):
        #create embed
        embed = discord.Embed(title=f"SIGMA Discord Bot", description=f"A bot for helping people connect easier developed by *William A. L.*", color=47103)
        embed.add_field(name=f"Github", value=f"> https://github.com/FrewtyPebbles", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Displays commands and help info.")
    async def help(self, interaction:discord.Interaction):
        #create embed
        embed = discord.Embed(title=f"Commands", description=f"A bot for making your social/gamer tags easily accessable to other users.", color=47103)
        embed.add_field(name=f"/gt", value=f"View your /gt profile.  A /gt profile is a way for users to make their gamer-tags/friend-tags for different platforms accessable to other users.", inline=False)
        embed.add_field(name=f"/gt user", value=f"View a user's /gt profile.", inline=False)
        embed.add_field(name=f"/settag platform_name user_tag", value=f"Add tags for different games/platforms to your /gt profile.", inline=False)
        embed.add_field(name=f"/removetag platform_name", value=f"Remove tags from your /gt profile.", inline=False)
        if interaction.user.guild_permissions.administrator:
            embed.add_field(name=f"/addplatform platform_name", value=f"Add platforms/games that users are allowed to add to their /gt profile.", inline=False)
            embed.add_field(name=f"/removeplatform platform_name", value=f"Remove platforms/games from the list of platforms/games that users are allowed to add to their /gt profile.", inline=False)
        embed.add_field(name=f"/info", value=f"Show info about the Sigma Bot and its developer.", inline=False)
        await interaction.response.send_message(embed=embed)
    
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