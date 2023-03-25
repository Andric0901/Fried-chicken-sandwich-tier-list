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
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

##############################################
# Parent class for basic pagination
##############################################
class PaginationView(discord.ui.View, metaclass=abc.ABCMeta):
    """A parent class for pagination.

    This class implements basic PaginationView to be used in many occasions, including an embed,
    a thumbnail file (if available), and 4 buttons: first, previous, next, last.

    update_interaction is an abstract method to be implemented in the child class.

    Optionally, a child class may implement select() method to add a dropdown menu to the view.
    """
    def __init__(self, current_page: int = 0,
                 timeout: Optional[float] = None,
                 interaction: Optional[discord.Interaction] = None) -> None:
        super().__init__(timeout=timeout)
        self.page = current_page
        self.min_page = 0
        self.max_page = len(RESTAURANTS) - 1
        self.thumbnail_file, self.embed = None, None
        self.update_buttons()
        self.interaction = interaction

    @discord.ui.button(label='⏮️', style=ButtonStyle.green, custom_id='first')
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the first page.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
            button (discord.ui.Button): The button that was clicked.
        """
        self.page = 0
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='◀️', style=ButtonStyle.blurple, custom_id='previous')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the previous page.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
            button (discord.ui.Button): The button that was clicked.
        """
        self.page -= 1
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='▶️', style=ButtonStyle.blurple, custom_id='next')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the next page.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
            button (discord.ui.Button): The button that was clicked.
        """
        self.page += 1
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='⏭️', style=ButtonStyle.green, custom_id='last')
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to the last page.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
            button (discord.ui.Button): The button that was clicked.
        """
        self.page = self.max_page
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @abc.abstractmethod
    async def update_interaction(self, interaction: discord.Interaction):
        """Update the current interaction accordingly.

        This is an abstract method to be implemented in the child class.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
        """
        pass

    def update_buttons(self) -> None:
        """Update the buttons accordingly, enabling/disabling them based on the current page."""
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page == 0
        self.children[2].disabled = self.page == self.max_page
        self.children[3].disabled = self.page == self.max_page

##############################################
# Child class for pagination for compendium
##############################################
class CompendiumPagesView(PaginationView):
    """A child class for pagination for compendium.

    This class also allows a transition between the compendium and the individual restaurant page.
    """
    def __init__(self, current_page: int = 0, interaction: Optional[discord.Interaction] = None) -> None:
        super().__init__(current_page=current_page)
        self.restaurants_list, self.embed = create_list_embed(self.page)
        self.max_page = (len(RESTAURANTS) - 1) // 10
        self.interaction = interaction

    async def update_interaction(self, interaction: discord.Interaction):
        """Update the current interaction.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
        """
        self.restaurants_list, self.embed = create_list_embed(self.page)
        await interaction.message.edit(embed=self.embed, attachments=[])
        self.update_buttons()
        self.children[4].options = [
            SelectOption(label=element, value=element)
            for element in get_current_restaurants_list(self.page)
        ]

    @discord.ui.select(placeholder='Look at...', options=[
                       SelectOption(label=element, value=element)
                       for element in get_current_restaurants_list(0)])
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Select a restaurant to look at.

        The SelectOption label used for this select menu is the list of restaurants in the current page,
        without the star signs.

        This function creates a new instance for RestaurantsPagesView, and edits the message accordingly.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
            select (discord.ui.Select): The select menu that was clicked.
        """
        restaurant = interaction.data['values'][0].split(maxsplit=1)[-1]
        index = RESTAURANT_NAMES.index(restaurant)
        view = RestaurantsPagesView(current_page=index)
        # Let the discord API know that there will be a response later, so it doesn't time out
        await interaction.response.defer()
        await interaction.message.edit(embeds=[view.embed], view=view, attachments=[view.thumbnail_file])

##############################################
# Child class for pagination for each individual restaurant
##############################################
class RestaurantsPagesView(PaginationView):
    """A child class for pagination for each individual restaurant.

    This class also allows a transition between the compendium and the individual restaurant page.
    """
    def __init__(self, current_page: int = 0) -> None:
        super().__init__(current_page=current_page)
        self.thumbnail_file, self.embed = create_restaurants_embed(self.page)

    async def update_interaction(self, interaction: discord.Interaction):
        """Update the current interaction.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
        """
        self.thumbnail_file, self.embed = create_restaurants_embed(self.page)
        await interaction.message.edit(embed=self.embed, attachments=[self.thumbnail_file])
        self.update_buttons()

    @discord.ui.select(placeholder='Jump to...', options=[
        SelectOption(label=TIER_PREFIX[tier], value=tier) for tier in TIERS])
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Select a tier to jump to.

        The SelectOption label used for this select menu is the tier prefixes,
        which allows easy navigation to the tier.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
            select (discord.ui.Select): The select menu that was clicked.
        """
        tier = interaction.data['values'][0]
        index = get_first_tier_indexes()[tier]
        self.page = index
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='Go back to compendium', style=ButtonStyle.blurple, custom_id='compendium')
    async def compendium(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to the compendium.

        This function creates a new instance for CompendiumPagesView, and edits the message accordingly.

        Args:
            interaction (discord.Interaction): The interaction that triggered this button.
            button (discord.ui.Button): The button that was clicked.
        """
        index = self.page // 10
        view = CompendiumPagesView(current_page=index, interaction=interaction)
        await interaction.response.defer()
        await view.update_interaction(interaction)
        await interaction.message.edit(view=view, embed=view.embed, attachments=[])

class FeedbackModal(discord.ui.Modal):
    """A modal for feedback forms.

    Allows user to write a feedback and submit it, which will be sent to the bot owner.
    """
    def __init__(self):
        super().__init__(title='Feedback Forms')

    name = discord.ui.TextInput(label='Name (Optional)', style=discord.TextStyle.short, required=False)
    answer = discord.ui.TextInput(label='Answer', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        dm_title = "Anonymous" if self.name.value == "" else self.name.value
        dm_embed = discord.Embed(title=f'Feedback from {dm_title}',
                                 description=self.answer.value)
        author = await client.fetch_user(author_id)
        await author.send(embed=dm_embed)
        response_embed = discord.Embed(title='Thank you!',
                                       description='Your feedback has been submitted. '
                                                   'We really appreciate it!')
        await interaction.response.send_message(embed=response_embed, ephemeral=True)

##############################################
# Bot commands / events
##############################################
@client.event
async def on_ready() -> None:
    """When the bot is ready, change the presence and sync the slash commands."""
    print(f'We have logged in as {client.user}')
    activity = Activity(name='the best chicken sandwich discoveries', type=ActivityType.competing)
    await client.change_presence(status=Status.online, activity=activity)
    await tree.sync()

@tree.command(name='hello', description='Says hello!')
async def hello_command(interaction: discord.Interaction) -> None:
    """Says hello!

    Args:
        interaction (discord.Interaction): The interaction that triggered this command.
    """
    await interaction.response.send_message('Hello!')

@tree.command(name='goodbye', description='Says goodbye!')
async def goodbye_command(interaction: discord.Interaction) -> None:
    """Says goodbye!

    Args:
        interaction (discord.Interaction): The interaction that triggered this command.
    """
    await interaction.response.send_message('Goodbye!')

@tree.command(name='ping', description='Pings the bot')
async def ping_command(interaction: discord.Interaction) -> None:
    """Says pong!

    Args:
        interaction (discord.Interaction): The interaction that triggered this command.
    """
    await interaction.response.send_message('Pong!')


@tree.command(name='tierlist', description='Shows the tierlist in an embed')
async def tierlist_command(interaction: discord.Interaction) -> None:
    """Shows the tierlist image in an embed.

    Args:
        interaction (discord.Interaction): The interaction that triggered this command.
    """
    embed = discord.Embed(title='Tierlist', description='Still in progress!', color=0x00ff00)
    image = open(TIERLIST_IMAGE_NAME, 'rb')
    embed.set_image(url='attachment://{}'.format(TIERLIST_IMAGE_NAME))
    await interaction.response.send_message(embed=embed, file=discord.File(image, TIERLIST_IMAGE_NAME))

@tree.command(name='list', description='Show a list of all restaurants')
async def list_command(interaction: discord.Interaction) -> None:
    """Shows a list of all restaurants in an embed.

    Uses the CompendiumPagesView class to paginate the list.

    Args:
        interaction (discord.Interaction): The interaction that triggered this command.
    """
    view = CompendiumPagesView()
    _, embed = create_list_embed(view.page)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name='feedback', description='Fill out a feedback form')
async def feedback_command(interaction: discord.Interaction) -> None:
    """Shows a feedback form for users to fill out.

    Args:
        interaction (discord.Interaction): The interaction that triggered this command.
    """
    modal = FeedbackModal()
    await interaction.response.send_modal(modal)

if __name__ == '__main__':
    print(collection.count_documents({}))
    print(len(get_restaurants_info()))
    if collection.count_documents({}) != len(get_restaurants_info()):
        setup_db()
    count = sum([len(files) for _, _, files in os.walk('logos')])
    assert count == sum([len(TIER_DICT[tier]) for tier in TIER_DICT])
    client.run(token)
