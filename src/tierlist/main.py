"""A Python file with discord bot run configurations."""

import discord.ui
from discord import Activity, ActivityType, Status, ButtonStyle, SelectOption, app_commands
from helper import *
from typing import Optional
import abc
import os


##############################################
# Set up discord bot client variables
##############################################
intents = discord.Intents.default()
intents.message_content = True
activity = Activity(name='the best chicken sandwich discoveries', type=ActivityType.competing)
client = discord.Client(intents=intents, activity=activity)
tree = app_commands.CommandTree(client)

# Load OWNER ID from .env
OWNER_ID = int(os.getenv("author_id"))


##############################################
# Bot commands / events
##############################################
@client.event
async def on_ready() -> None:
    """When the bot is ready, sync the slash commands."""
    print(f'We have logged in as {client.user}')
    await tree.sync()


@tree.command(name='tierlist', description='Shows the tierlist in an embed')
async def tierlist_command(interaction: discord.Interaction) -> None:
    """Shows the tierlist image in an embed.

    Args:
        interaction (discord.Interaction): The interaction that triggered this command.
    """
    embed_description = "There is C between B and D. That is, between Birth and Death, there is Chicken."
    embed = discord.Embed(title='Tierlist', description=embed_description, color=0x00ff00)
    image = open(TIERLIST_IMAGE_NAME, 'rb')
    embed.set_image(url='attachment://{}'.format(TIERLIST_IMAGE_NAME))
    await interaction.response.send_message(embed=embed, file=discord.File(image, TIERLIST_IMAGE_NAME))


@tree.command(name='alt1', description='Tier List with year tags of first visit')
async def alt1_tierlist_command(interaction: discord.Interaction) -> None:
    """Shows the tierlist image with year of first visit tags in an embed."""
    title = "Tier List (First Visit)"
    description = "Tier List with year tags of first visit"
    embed = discord.Embed(title=title, description=description, color=0x00ff00)
    image = open(TIERLIST_IMAGE_NAME_WITH_YEAR_FIRST_VISITED_TAG, 'rb')
    embed.set_image(url='attachment://{}'.format(TIERLIST_IMAGE_NAME_WITH_YEAR_FIRST_VISITED_TAG))
    await interaction.response.send_message(embed=embed, file=discord.File(image, TIERLIST_IMAGE_NAME_WITH_YEAR_FIRST_VISITED_TAG))


@tree.command(name='alt2', description='Tier List with year tags when the ranks have been (re)evaluated')
async def alt2_tierlist_command(interaction: discord.Interaction) -> None:
    """Shows the tierlist image with year of evaluation tags in an embed."""
    title = "Tier List (Evaluation)"
    description = "Tier List with year tags when the ranks have been (re)evaluated"
    embed = discord.Embed(title=title, description=description, color=0x00ff00)
    image = open(TIERLIST_IMAGE_NAME_WITH_YEAR_TAG, 'rb')
    embed.set_image(url='attachment://{}'.format(TIERLIST_IMAGE_NAME_WITH_YEAR_TAG))
    await interaction.response.send_message(embed=embed, file=discord.File(image, TIERLIST_IMAGE_NAME_WITH_YEAR_TAG))


##############################################
# DM Debug System (Owner Only)
##############################################
@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.author.id != OWNER_ID:
        return

    if message.guild is not None:
        return

    content = message.content.strip().lower()

    if content == "servers":
        await send_servers_debug(message)

    elif content == "ping":
        await message.channel.send(f"Pong! {round(client.latency * 1000)}ms")


async def send_servers_debug(message: discord.Message):
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chunks = []
    current_chunk = f"**Server Report** ({now})\n"

    for guild in client.guilds:
        owner_display = guild.owner.name if guild.owner else f"`{guild.owner_id}`"

        total_members = guild.member_count or 0
        bot_count = sum(1 for m in guild.members if m.bot)
        human_count = total_members - bot_count
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        role_count = len(guild.roles)
        perms = guild.me.guild_permissions
        perm_summary = (
            f"Send:{'✅' if perms.send_messages else '❌'} "
            f"ManageMsg:{'✅' if perms.manage_messages else '❌'} "
            f"ManageRoles:{'✅' if perms.manage_roles else '❌'} "
            f"Admin:{'✅' if perms.administrator else '❌'}"
        )

        created = guild.created_at.strftime('%Y-%m-%d')
        joined = guild.me.joined_at.strftime('%Y-%m-%d') if guild.me.joined_at else "Unknown"

        block = (
            f"**{guild.name}** (`{guild.id}`)\n"
            f"👑 Owner: {owner_display}\n"
            f"👥 {total_members} (Humans:{human_count} | Bots:{bot_count})\n"
            f"💬 {text_channels} text | 🔊 {voice_channels} voice | 🎭 {role_count} roles\n"
            f"🤖 Perms: {perm_summary}\n"
            f"📅 Created: {created} | Joined: {joined}\n"
        )

        # Handle 2000 char limit (safe chunking)
        if len(current_chunk) + len(block) > 2000:
            chunks.append(current_chunk)
            current_chunk = block
        else:
            current_chunk += "\n" + block

    if current_chunk:
        chunks.append(current_chunk)

    if not chunks:
        chunks = ["Not connected to any servers."]

    # Send all chunks
    for chunk in chunks:
        await message.channel.send(chunk)

if __name__ == '__main__':
    # Check that .env file exists
    if not os.path.exists('.env'):
        raise FileNotFoundError('.env file not found')
    # print(collection.count_documents({}))
    print("Number of restaurants visited: {}".format(len(RESTAURANT_NAMES)))
    count = sum([len(files) for _, _, files in os.walk('logos')])
    # assert count == len(RESTAURANT_NAMES)
    if test_token:
        print("Test token exists. Running test bot...")
        client.run(test_token)
    else:
        client.run(token)
