import discord
from discord import Activity, ActivityType, Status, app_commands, ButtonStyle, SelectOption
from discord.ext import commands
import typing
import googlemaps
from googlemaps import places
import requests
from tierlist import get_restaurants_info ,tier_colour_hex_dict, get_first_tier_indexes, MANUAL_EMBED_RESTAURANTS
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from keep_alive import keep_alive

load_dotenv()

keep_alive()
token = os.getenv("token")
key = os.getenv("key")

TIERLIST_IMAGE = 'tierlist.png'
gmaps = googlemaps.Client(key=key)

RESTAURANTS = get_restaurants_info()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
TIER_PREFIX = {
    'S': 'Spectacular',
    'A': 'Acclaimed',
    'B': 'Better',
    'C': 'Common',
    'D': 'Derogatory',
    'E': 'Enervating',
    'F': "Freakin' Raw"
}
tiers = ['S', 'A', 'B', 'C', 'D', 'E', 'F']
restaurant_names = [restaurant[0][6:-4] for restaurant in RESTAURANTS]


class PaginationView(discord.ui.View):
    def __init__(self, current_page=0):
        super().__init__(timeout=None)
        self.page = current_page
        self.min_page = 0
        self.max_page = len(RESTAURANTS) - 1
        self.previous_restaurant_name, self.next_restaurant_name = None, None
        self.update_previous_and_next()
        self.thumbnail_file, self.embed = create_embed(self.page)

    def update_previous_and_next(self):
        self.previous_restaurant_name = RESTAURANTS[self.page - 1][0][6:-4] if self.page > 0 else None
        self.next_restaurant_name = RESTAURANTS[self.page + 1][0][
                                    6:-4] if self.page < self.max_page else None

    @discord.ui.button(label='⏮️', style=ButtonStyle.green, disabled=True, custom_id='first')
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        self.update_previous_and_next()
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='◀️', style=ButtonStyle.blurple, disabled=True, custom_id='previous')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.update_previous_and_next()
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    # TODO: Change label manually when there is a change in S tier order
    @discord.ui.button(label='▶️ Penny\'s Hot Chicken', style=ButtonStyle.blurple, disabled=False, custom_id='next')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        if self.page == 0:
            assert self.children[1].label[3:] == self.next_restaurant_name
        self.update_previous_and_next()
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='⏭️', style=ButtonStyle.green, disabled=False, custom_id='last')
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.max_page
        self.update_previous_and_next()
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.select(placeholder='Jump to...', options=[
        SelectOption(label=TIER_PREFIX[tier], value=tier) for tier in tiers])
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        tier = interaction.data['values'][0]
        index = get_first_tier_indexes()[tier]
        self.page = index
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    async def update_interaction(self, interaction: discord.Interaction):
        self.thumbnail_file, self.embed = create_embed(self.page)
        await interaction.message.edit(embed=self.embed, attachments=[self.thumbnail_file])
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page == 0
        self.children[2].disabled = self.page == self.max_page
        self.children[3].disabled = self.page == self.max_page
        self.update_previous_and_next()
        if self.children[1].disabled:
            self.children[1].label = '◀️'
        else:
            self.children[1].label = '◀️ {}'.format(self.previous_restaurant_name)
        if self.children[2].disabled:
            self.children[2].label = '▶️'
        else:
            self.children[2].label = '{} ▶️'.format(self.next_restaurant_name)


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
    image = open(TIERLIST_IMAGE, 'rb')
    embed.set_image(url='attachment://tierlist.png')
    await interaction.response.send_message(embed=embed, file=discord.File(image, 'tierlist.png'))


@tree.command(name='list', description='Paginates the restaurants')
async def list_command(interaction):
    view = PaginationView()
    thumbnail_file, embed = create_embed(view.page)
    await interaction.response.send_message(embed=embed, file=thumbnail_file, view=view)


def create_embed(current_page):
    # [link to logo image, price range, address, description (catchphrase), tier]
    title = RESTAURANTS[current_page][0][6:-4]
    if title in MANUAL_EMBED_RESTAURANTS:
        return create_manual_embed(current_page, RESTAURANTS)
    description = RESTAURANTS[current_page][3]
    address = RESTAURANTS[current_page][2]
    price_range = RESTAURANTS[current_page][1]
    tier = RESTAURANTS[current_page][4]

    gmaps_info = get_gmaps_info(title, address)

    embed = discord.Embed(title=title, description=description, color=tier_colour_hex_dict[tier],
                          url=gmaps_info[1])
    thumbnail_file = get_thumbnail_file(current_page, RESTAURANTS)
    embed.set_thumbnail(url='attachment://image.jpg')
    embed.set_author(name=TIER_PREFIX[tier])
    embed.add_field(name='Address', value=address, inline=True)
    if gmaps_info[0] is not None:
        embed.add_field(name='Open Status', value=gmaps_info[0], inline=True)
    embed.add_field(name='Price Range', value="$" * int(price_range), inline=True)
    if gmaps_info[3] is not None:
        embed.add_field(name='Opening hours', value=gmaps_info[3], inline=False)
    if title == "Cabano's Comfort Food":
        assert gmaps_info[2] is None
        embed.add_field(name='Website', value="https://www.cabanos.ca/", inline=False)
    elif title == "Hero Certified Burgers":
        assert gmaps_info[2] is None
        embed.add_field(name='Website', value="https://heroburgers.com/", inline=False)
    if gmaps_info[2] is not None:
        if title == "Top Gun Burgers":
            embed.add_field(name='Website', value="https://topgunburgerto.com/", inline=False)
        elif title == "Subway":
            embed.add_field(name='Website', value="https://restaurants.subway.com/canada/on/toronto/1102-bay-st",
                            inline=False)
        elif title == "Jollibee":
            embed.add_field(name='Website', value="https://locations.jollibeefoods.com/ca/on/toronto/334-yonge-street",
                            inline=False)
        else:
            embed.add_field(name='Website', value=gmaps_info[2], inline=False)
    embed.add_field(name='Tier', value="**" + tier + "**", inline=True)
    return (thumbnail_file, embed)


def get_thumbnail_file(current_page, restaurants_info):
    thumbnail_path = Path(__file__).parent / restaurants_info[current_page][0]
    thumbnail_file = discord.File(thumbnail_path, 'image.jpg')
    return thumbnail_file


def create_manual_embed(current_page, restaurants_info):
    restaurant_name = restaurants_info[current_page][0][6:-4]
    if restaurant_name == "Bubba's Crispy Fried Chicken":
        return _bubbas_embed(current_page, restaurants_info)
    elif restaurant_name == "Foodie":
        return _foodie_embed(current_page, restaurants_info)


def _bubbas_embed(current_page, restaurants_info):
    embed = discord.Embed(title='Bubba\'s Crispy Fried Chicken',
                          description="Bubba's (and everyone's) past favorite",
                          color=tier_colour_hex_dict['S'])
    thumbnail_file = get_thumbnail_file(current_page, restaurants_info)
    embed.set_thumbnail(url='attachment://image.jpg')
    embed.set_author(name=TIER_PREFIX['S'])
    embed.add_field(name='Address', value='521 Bloor St W', inline=True)
    embed.add_field(name='Open Status', value='Permanently Closed', inline=True)
    embed.add_field(name='Price Range', value="$$", inline=True)
    embed.add_field(name='Website', value='https://www.bubbascrispyfriedchicken.com/', inline=False)
    embed.add_field(name='Tier', value='**S**', inline=True)
    return (thumbnail_file, embed)


def _foodie_embed(current_page, restaurants_info):
    embed = discord.Embed(title='Foodie',
                          description="UofT's only pink truck",
                          color=tier_colour_hex_dict['C'])
    thumbnail_file = get_thumbnail_file(current_page, restaurants_info)
    embed.set_thumbnail(url='attachment://image.jpg')
    embed.set_author(name=TIER_PREFIX['C'])
    embed.add_field(name='Address', value='255 Huron St', inline=True)
    embed.add_field(name='Open Status', value='Operational (Unknown)', inline=True)
    embed.add_field(name='Price Range', value="$", inline=True)
    embed.add_field(name='Tier', value='**C**', inline=True)
    return (thumbnail_file, embed)


def ceil_dt(dt, delta):
    return dt + (datetime.min - dt) % delta


def get_gmaps_info(title, address):
    """Return open status, link to google maps link, and the website, if available.

    Args:
        title (str): The title of the restaurant
        address (str): The address of the restaurant

    Returns:
        [str, str, str, str]: [open status, link to google maps link, website, opening hours]
    """
    if title in MANUAL_EMBED_RESTAURANTS:
        return
    gmaps_info = places.find_place(gmaps, title + " " + address, 'textquery')
    url = "https://maps.googleapis.com/maps/api/place/details/json?placeid={}&key={}".format(
        gmaps_info['candidates'][0]['place_id'], gmaps.key)
    json_result = requests.get(url).json()
    # assert address in json_result['result']['formatted_address']
    # Get the business status if the key exists, otherwise return None
    # Redo capitalization to only capitalize the first letters of each word
    business_status = " ".join(reversed([word.capitalize() for word in json_result['result']
                                        .get('business_status').split('_')]))
    # assert business_status in ['Operational', 'Permanently Closed', 'Temporarily Closed']
    opening_hours = json_result['result'].get('opening_hours')
    if opening_hours is not None:
        open_now = opening_hours.get('open_now')
    else:
        open_now = None
    if business_status == 'Permanently Closed' or business_status == 'Temporarily Closed' or open_now is None:
        open_status = business_status
    else:
        if open_now:
            open_status = business_status + ' (Open Now)'
        else:
            open_status = business_status + ' (Closed Now)'
    gmaps_link = json_result['result'].get('url')
    website = json_result['result'].get('website')
    human_readable_opening_hours = reformat_opening_hours(
        json_result['result'].get('opening_hours').get('weekday_text'))
    return [open_status, gmaps_link, website, human_readable_opening_hours]


def reformat_opening_hours(opening_hours):
    """Reformat the opening hours to be human readable.
    The parameter contains \u2009 or \u202f characters, which are unicode characters. Remove them.
    """
    return "\n".join([opening_hour.replace('\u2009', ' ').replace('\u202f', ' ') for opening_hour in opening_hours])

client.run(token)
