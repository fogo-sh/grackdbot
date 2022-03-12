from pydantic import BaseSettings
from discord import app_commands
import discord


class Config(BaseSettings):
    class Config:
        env_prefix = "grackdbot_"
        env_file = ".env"
        env_file_encoding = "utf-8"

    token: str
    guild_id: str = "497544520695808000"


config = Config()
guild = discord.Object(config.guild_id)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)


@tree.command(guild=guild, description="Hello world")
async def hello_world(interaction: discord.Interaction):
    await interaction.response.send_message(":grack:")


@client.event
async def on_ready():
    print("Bot ready, syncing commands")
    await tree.sync(guild=guild)


client.run(config.token)
