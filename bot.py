import json

import discord
from discord import app_commands
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import BaseSettings

transport = AIOHTTPTransport(url="https://grackdb.fogo.sh/query")

GET_USER_FOR_DISCORD_ACCOUNT_QUERY = gql(
    """
    query($discord_id: String!) {
      discordAccounts(first: 1, where: { discordID: $discord_id }) {
        edges {
          node {
            owner {
              id
              username
            }
            bot {
              id
            }
          }
        }
      }
    }
    """
)


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


@tree.context_menu(guild=guild, name="Lookup in GrackDB")
async def lookup(interaction: discord.Interaction, user: discord.User):
    async with Client(transport=transport, fetch_schema_from_transport=True) as session:
        resp = await session.execute(
            GET_USER_FOR_DISCORD_ACCOUNT_QUERY,
            variable_values={"discord_id": str(user.id)},
        )

        if len(resp["discordAccounts"]["edges"]) == 0:
            await interaction.response.send_message(
                "That user could not be found in GrackDB.", ephemeral=True
            )
            return

        # account = resp["discordAccounts"]["edges"][0]["node"]

        await interaction.response.send_message(f"```json\n{json.dumps(resp)}\n```")


@client.event
async def on_ready():
    print("Bot ready, syncing commands")
    await tree.sync(guild=guild)


client.run(config.token)
