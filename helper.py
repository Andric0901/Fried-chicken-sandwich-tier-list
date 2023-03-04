import discord
from discord import app_commands
import googlemaps
from googlemaps import places
import requests
from tierlist import get_restaurants_info ,tier_colour_hex_dict, MANUAL_EMBED_RESTAURANTS
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os
import pymongo
import certifi
import pytz

load_dotenv()

connection_string = os.getenv("connection")
client = pymongo.MongoClient(connection_string, tlsCAFile=certifi.where())
db = client["fried-chicken-sandwich-bot"]
collection = db["gmaps_infos"]

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

TIMEZONE = pytz.timezone('America/Toronto')

def setup_db():
    for i in range(len(restaurant_names)):
        restaurant = restaurant_names[i]
        if restaurant in MANUAL_EMBED_RESTAURANTS:
            collection.update_one({"index": i}, {"$set": {"json": None}}, upsert=True)
        else:
            restaurant_name, restaurant_address = RESTAURANTS[i][0][6:-4], RESTAURANTS[i][2]
            place_id = \
            places.find_place(gmaps, restaurant_name + ' ' + restaurant_address, 'textquery')['candidates'][0][
                'place_id']
            url = "https://maps.googleapis.com/maps/api/place/details/json?placeid={}&key={}".format(place_id, key)
            response = requests.get(url)
            data = response.json()
            collection.update_one({"index": i}, {"$set": {"json": data}}, upsert=True)

def create_embed(current_page):
    # [link to logo image, price range, address, description (catchphrase), tier]
    title = RESTAURANTS[current_page][0][6:-4]
    if title in MANUAL_EMBED_RESTAURANTS:
        return create_manual_embed(current_page, RESTAURANTS)
    description = RESTAURANTS[current_page][3]
    address = RESTAURANTS[current_page][2]
    price_range = RESTAURANTS[current_page][1]
    tier = RESTAURANTS[current_page][4]

    gmaps_info = get_gmaps_info(current_page)

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

def get_gmaps_info(current_page):
    """Return open status, link to google maps link, and the website, if available.

    Args:
        current_page (int): The current page of the embed

    Returns:
        [str, str, str, str]: [open status, link to google maps link, website, opening hours]
    """
    json_result = dict(collection.find_one({"index": current_page}))["json"]
    # assert address in json_result['result']['formatted_address']
    # Get the business status if the key exists, otherwise return None
    # Redo capitalization to only capitalize the first letters of each word
    business_status = " ".join(reversed([word.capitalize() for word in json_result['result']
                                        .get('business_status').split('_')]))
    # assert business_status in ['Operational', 'Permanently Closed', 'Temporarily Closed']
    if business_status == 'Operational':
        opening_hours = json_result['result'].get('opening_hours').get('periods')
    else:
        opening_hours = None
    if opening_hours is not None:
        open_now = is_open_now(opening_hours)
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
    if opening_hours is not None:
        human_readable_opening_hours = reformat_opening_hours(
            json_result['result'].get('opening_hours').get('weekday_text'))
    else:
        human_readable_opening_hours = None
    return [open_status, gmaps_link, website, human_readable_opening_hours]

def append_dummy_hours(opening_hours):
    """Modify the opening hours so that the opening_hours list is 7 elements long.

    Google Maps API automatically skips an element if the restaurant is closed on that day.
    This function inserts a None element in its place if the restaurant is closed on that day.
    """
    opening_hours = opening_hours.copy()
    for i in range(7):
        if opening_hours[i]['open']['day'] != i:
            opening_hours.insert(i, None)
    return opening_hours

def is_open_now(opening_hours):
    """Return True if the restaurant is open now, False otherwise.

    Args:
        opening_hours (dict): The opening hours of the restaurant

    Returns:
        bool: True if the restaurant is open now, False otherwise
    """
    if len(opening_hours) == 1 and opening_hours[0]["open"]["day"] == 0 and opening_hours[0]["open"]["time"] == "0000":
        return True
    time_date_dict = current_date_and_time()
    current_day, current_time = time_date_dict["day"], time_date_dict["time"]
    if len(opening_hours) == 7:
        opening_hours_today = opening_hours[current_day]
    else:
        opening_hours_today = append_dummy_hours(opening_hours)[current_day]
    if opening_hours_today is None:
        return False
    opening_day_and_time, closing_day_and_time = opening_hours_today["open"], opening_hours_today["close"]
    opening_day, opening_time = opening_day_and_time["day"], opening_day_and_time["time"]
    closing_day, closing_time = closing_day_and_time["day"], closing_day_and_time["time"]
    if opening_day == closing_day:
        return opening_time <= current_time <= closing_time
    else:
        return opening_time <= current_time or current_time <= closing_time
def current_date_and_time():
    """Return the current date and time in the format of Google Maps API opening hours.

    This should return a dict containing two keys:
    - day: The day of the week: 0 (Sunday) to 6 (Saturday)
    - time: The time of day in 24-hour hhmm format.

    Returns:
        dict: {"day": int, "time": str}
    """
    current_datetime = datetime.now(TIMEZONE)
    current_day = get_current_day()
    current_time = current_datetime.strftime("%H%M")
    return {"day": current_day, "time": current_time}

def get_current_day():
    """Return the current day of the week.

    This follows the Google Maps API format, where 0 is Sunday and 6 is Saturday.

    Returns:
        str: The current day of the week
    """
    current_day = datetime.now(TIMEZONE).weekday() + 1
    if current_day == 7:
        current_day = 0
    return current_day
def reformat_opening_hours(opening_hours):
    """Reformat the opening hours to be human readable.
    The parameter contains \u2009 or \u202f characters, which are unicode characters. Remove them.
    """
    plain_list = [opening_hour.replace('\u2009', ' ').replace('\u202f', ' ') for opening_hour in opening_hours]
    current_day = datetime.now(TIMEZONE).weekday()
    modified_list = ["**" + plain_list[opening_hour] + "**" if opening_hour == current_day
                     else plain_list[opening_hour] for opening_hour in range(len(plain_list))]
    return "\n".join(modified_list)

if __name__ == '__main__':
    setup_db()
