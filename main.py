"""A Python file with discord bot run configurations."""

import discord.ui
from discord import Activity, ActivityType, Status, ButtonStyle, SelectOption, app_commands
from helper import *
import abc

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

class PaginationView(discord.ui.View, metaclass=abc.ABCMeta):
    def __init__(self, current_page=0, timeout=None, interaction=None):
        super().__init__(timeout=timeout)
        self.page = current_page
        self.min_page = 0
        self.max_page = len(RESTAURANTS) - 1
        self.thumbnail_file, self.embed = None, None
        self.update_buttons()
        self.interaction = interaction

    @discord.ui.button(label='⏮️', style=ButtonStyle.green, custom_id='first')
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='◀️', style=ButtonStyle.blurple, custom_id='previous')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='▶️', style=ButtonStyle.blurple, custom_id='next')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='⏭️', style=ButtonStyle.green, custom_id='last')
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.max_page
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @abc.abstractmethod
    async def update_interaction(self, interaction: discord.Interaction):
        pass

    def update_buttons(self):
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page == 0
        self.children[2].disabled = self.page == self.max_page
        self.children[3].disabled = self.page == self.max_page

class ListPagesView(PaginationView):
    def __init__(self, current_page=0, interaction=None):
        super().__init__(current_page=current_page)
        self.restaurants_list, self.embed = create_list_embed(self.page)
        self.max_page = (len(RESTAURANTS) - 1) // 10
        self.interaction = interaction

    async def update_interaction(self, interaction: discord.Interaction):
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
        restaurant = interaction.data['values'][0].split(maxsplit=1)[-1]
        index = RESTAURANT_NAMES.index(restaurant)
        view = RestaurantsPagesView(current_page=index)
        await interaction.response.defer()
        await interaction.message.edit(embeds=[view.embed], view=view, attachments=[view.thumbnail_file])

class RestaurantsPagesView(PaginationView):
    def __init__(self, current_page=0):
        super().__init__(current_page=current_page)
        self.thumbnail_file, self.embed = create_restaurants_embed(self.page)

    @discord.ui.select(placeholder='Jump to...', options=[
        SelectOption(label=TIER_PREFIX[tier], value=tier) for tier in TIERS])
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        tier = interaction.data['values'][0]
        index = get_first_tier_indexes()[tier]
        self.page = index
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    async def update_interaction(self, interaction: discord.Interaction):
        self.thumbnail_file, self.embed = create_restaurants_embed(self.page)
        await interaction.message.edit(embed=self.embed, attachments=[self.thumbnail_file])
        self.update_buttons()

    @discord.ui.button(label='Go back to compendium', style=ButtonStyle.blurple, custom_id='compendium')
    async def compendium(self, interaction: discord.Interaction, button: discord.ui.Button):
        index = self.page // 10
        view = ListPagesView(current_page=index, interaction=interaction)
        await interaction.response.defer()
        await view.update_interaction(interaction)
        await interaction.message.edit(view=view, embed=view.embed, attachments=[])

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    activity = Activity(name='the best chicken sandwich discoveries', type=ActivityType.competing)
    await client.change_presence(status=Status.online, activity=activity)
    await tree.sync()

@tree.command(name='hello', description='Says hello!')
async def hello_command(interaction):
    await interaction.response.send_message('Hello!')

@tree.command(name='goodbye', description='Says goodbye!')
async def goodbye_command(interaction):
    await interaction.response.send_message('Goodbye!')

@tree.command(name='ping', description='Pings the bot')
async def ping_command(interaction):
    await interaction.response.send_message('Pong!')


@tree.command(name='tierlist', description='Shows the tierlist in an embed')
async def tierlist_command(interaction):
    embed = discord.Embed(title='Tierlist', description='Still in progress!', color=0x00ff00)
    image = open(TIERLIST_IMAGE_NAME, 'rb')
    embed.set_image(url='attachment://{}'.format(TIERLIST_IMAGE_NAME))
    await interaction.response.send_message(embed=embed, file=discord.File(image, TIERLIST_IMAGE_NAME))

@tree.command(name='list', description='Show a list of all restaurants')
async def list_command(interaction):
    view = ListPagesView()
    _, embed = create_list_embed(view.page)
    await interaction.response.send_message(embed=embed, view=view)

if __name__ == '__main__':
    print(collection.count_documents({}))
    print(len(get_restaurants_info()))
    if collection.count_documents({}) != len(get_restaurants_info()):
        setup_db()
    count = sum([len(files) for _, _, files in os.walk('logos')])
    assert count == sum([len(TIER_DICT[tier]) for tier in TIER_DICT])
    client.run(token)
