from typing import Optional
from discord.ext import commands
import discord
from bot_class import DBBot
from discord import app_commands
import hashlib



class Gaming(commands.Cog):
    def __init__(self, bot:DBBot):
        self.bot = bot
        self.db = bot.db

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

    async def user_games_autocomplete(self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        m = hashlib.sha256()
        m.update(str(interaction.user.id).encode())
        username_hash = m.hexdigest()
        profile:dict = await self.db.profile.find_one({"gid":interaction.guild_id, "uid":username_hash})
        ret_list = [
            app_commands.Choice(name=choice["name"], value=choice["name"])
            for choice in profile["platforms"]
        ]
        return ret_list


    @app_commands.command(name="settag", description="Adds one of the server's valid platform tags to your /gt profile.")
    @app_commands.autocomplete(platform=games_autocomplete)
    async def gtset(self, interaction:discord.Interaction, platform:str, tag:str):
        guild_config:dict = await self.db.guild_config.find_one({"gid":interaction.guild_id})
        if platform not in guild_config["platforms"]:
            await interaction.response.send_message(f"{platform} is not available on this server!")
            return
        m = hashlib.sha256()
        m.update(str(interaction.user.id).encode())
        username_hash = m.hexdigest()
        await self.db.profile.update_one(
            {
                "gid":interaction.guild_id,
                "uid":username_hash,
            },
            {
                "$pull": {f"platforms":{"name":platform}}
            },
            upsert = True)
        await self.db.profile.update_one(
            {
                "gid":interaction.guild_id,
                "uid":username_hash,
            },
            {
                "$push": {"platforms":{"name":platform, "tag":tag}}
            },
            upsert = True)
        await interaction.response.send_message(f"Successfully added {platform} to your profile!")
    
    @app_commands.command(name="removetag", description="Removes one of the server's valid platform tags from your /gt profile.")
    @app_commands.autocomplete(platform=user_games_autocomplete)
    async def gtremove(self, interaction:discord.Interaction, platform:str):
        guild_config:dict = await self.db.guild_config.find_one({"gid":interaction.guild_id})
        if platform not in guild_config["platforms"]:
            await interaction.response.send_message(f"{platform} is not available on this server!")
            return
        m = hashlib.sha256()
        m.update(str(interaction.user.id).encode())
        username_hash = m.hexdigest()
        await self.db.profile.update_one(
            {
                "gid":interaction.guild_id,
                "uid":username_hash
            },
            {
                "$pull": {f"platforms":{"name":platform}}
            },
            upsert = True)
        await interaction.response.send_message(f"Successfully removed {platform} from your profile!")

    @app_commands.command(name="gt", description="Displays a user's gt profile which has their provided social/game/friend tags.")
    async def gt(self, interaction:discord.Interaction, user:Optional[discord.Member]):
        chosen_member = interaction.user if user == None else user
        # get user profile info
        m = hashlib.sha256()
        m.update(str(chosen_member.id).encode())
        username_hash = m.hexdigest()
        profile:dict | None = await self.db.profile.find_one({"gid":interaction.guild_id, "uid":username_hash})

        if profile == None:
            profile = {
                "gid":interaction.guild_id,
                "uid":username_hash,
                "platforms":[]
            }
            await self.db.profile.insert_one(profile)
        #create embed
        embed = discord.Embed(title=f"{chosen_member.name}'s Friend Tags", description=f"", color=47103)
        embed.set_thumbnail(url=chosen_member.avatar.url)
        for platform in profile["platforms"]:
            embed.add_field(name=f"{platform['name']}", value=f"> {platform['tag']}", inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Gaming(client))