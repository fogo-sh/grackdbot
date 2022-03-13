from typing import Any, Dict

import dateutil.parser
import discord
from discord import app_commands
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import BaseSettings

transport = AIOHTTPTransport(url="https://grackdb.fogo.sh/query")

GET_DATA_FOR_DISCORD_ACCOUNT_QUERY = gql(
    """
    query($discord_id: String!) {
      discordAccounts(first: 1, where: { discordID: $discord_id }) {
        edges {
          node {
            owner {
              id
              username
              githubAccounts {
                username
              }
            }
            bot {
              id
              project {
                id
                name
                description
                startDate
                endDate
              }
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


def render_project_embed(data: Dict[str, Any]) -> discord.Embed:
    embed = discord.Embed()
    embed.title = data["name"]
    embed.url = f"https://grackdb.fogo.sh/project/{data['id']}"
    embed.description = data["description"]
    embed.colour = discord.Colour.blue()
    embed.add_field(
        name="Start Date",
        value=f"<t:{int(dateutil.parser.isoparse(data['startDate']).timestamp())}>",
    )
    embed.add_field(
        name="End Date",
        value=f"<t:{int(dateutil.parser.isoparse(data['endDate']).timestamp())}>"
        if data["endDate"] is not None
        else "Ongoing",
    )
    return embed


def render_user_embed(data: Dict[str, Any]) -> discord.Embed:
    embed = discord.Embed()
    embed.title = data["username"]
    embed.url = f"https://grackdb.fogo.sh/user/{data['username']}"
    embed.colour = discord.Colour.gold()

    if githubAccount := next(iter(data["githubAccounts"]), None):
        embed.add_field(
            name="GitHub",
            value=f"[{githubAccount['username']}](https://github.com/{githubAccount['username']})",
        )
    return embed


@tree.context_menu(guild=guild, name="Lookup in GrackDB")
async def lookup(interaction: discord.Interaction, user: discord.User):
    async with Client(transport=transport, fetch_schema_from_transport=True) as session:
        resp = await session.execute(
            GET_DATA_FOR_DISCORD_ACCOUNT_QUERY,
            variable_values={"discord_id": str(user.id)},
        )

        if len(resp["discordAccounts"]["edges"]) == 0:
            embed = discord.Embed(
                description="That account could not be found in GrackDB."
            )
            embed.colour = discord.Colour.red()
            await interaction.response.send_message(embed=embed)
            return

        account = resp["discordAccounts"]["edges"][0]["node"]
        if account["owner"] is not None:
            embed = render_user_embed(account["owner"])
        elif account["bot"] is not None and account["bot"]["project"] is not None:
            # TODO: Maybe try and figure a way to work the repo into this?
            embed = render_project_embed(account["bot"]["project"])
        else:
            embed = discord.Embed(
                description="Hmm, that account seems to exist but does not have an associated owner user or project. Check the data in GrackDB and try again."
            )
            embed.colour = discord.Colour.red()
        await interaction.response.send_message(embed=embed)


@client.event
async def on_ready():
    print("Bot ready, syncing commands")
    await tree.sync(guild=guild)


client.run(config.token)
