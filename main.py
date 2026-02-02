"""A Python file with discord bot run configurations."""

import discord.ui
from discord import Activity, ActivityType, Status, ButtonStyle, SelectOption, app_commands
from helper import *
from typing import Optional
import abc


##############################################
# Set up discord bot client variables
##############################################
intents = discord.Intents.default()
intents.message_content = True
activity = Activity(name='the best chicken sandwich discoveries', type=ActivityType.competing)
client = discord.Client(intents=intents, activity=activity)
tree = app_commands.CommandTree(client)


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
