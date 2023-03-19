"""A helper file containing functions used by tierlist.py and main.py"""

import discord
import googlemaps
from googlemaps import places
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os
import pymongo
import certifi
import pytz
import json

##############################################
# Set up environment variables
##############################################
load_dotenv()
connection_string = os.getenv("connection")
token = os.getenv("token")
key = os.getenv("key")
try:
    gmaps = googlemaps.Client(key=key)
except ValueError:
    # Likely tierlist.py has been called without defined key in the env file
    pass
client = pymongo.MongoClient(connection_string, tlsCAFile=certifi.where())
db = client["fried-chicken-sandwich-bot"]
collection = db["gmaps_infos"]

tier_dict = json.load(open('tier_dict.json'))

##############################################
# Tierlist helper functions
##############################################
def get_restaurants_info():
    """Get the list of restaurants and their price ranges"""
    restaurants_info = []
    for tier in tier_dict:
        for restaurant_info in tier_dict[tier]:
            assert len(restaurant_info) == 5
            restaurants_info.append(restaurant_info)
    return restaurants_info

def get_first_tier_indexes():
    """Get the first index of each tier"""
    first_tier_indexes = {"S": 0}
    tiers = list(tier_dict.keys())
    for tier in tier_dict:
        if tier == "S":
            pass
        else:
            first_tier_indexes[tier] = first_tier_indexes[tiers[tiers.index(tier) - 1]] + \
                                       len(tier_dict[tiers[tiers.index(tier) - 1]])
    return first_tier_indexes

##############################################
# Set up constants
##############################################
RESTAURANTS = get_restaurants_info()
MANUAL_EMBED_RESTAURANTS = ["Bubba's Crispy Fried Chicken", "Foodie"]
TIERLIST_IMAGE = 'tierlist.png'
TIMEZONE = pytz.timezone('America/Toronto')
TIERS = ['S', 'A', 'B', 'C', 'D', 'E', 'F']
RESTAURANT_NAMES = [restaurant[0][6:-4] for restaurant in RESTAURANTS]
TIER_PREFIX = {
    'S': 'Spectacular',
    'A': 'Acclaimed',
    'B': 'Better',
    'C': 'Common',
    'D': 'Derogatory',
    'E': 'Enervating',
    'F': "Freakin' Raw"
}
TIER_COLOUR_HEX_DICT = {
    'S': "#ff7f7f",
    'A': "#ffbf7f",
    'B': "#ffff7f",
    'C': "#7fff7f",
    'D': "#7fbfff",
    'E': "#7f7fff",
    'F': "#ff7fff"
}

##############################################
# Set up the database
##############################################
def setup_db():
    for i in range(len(RESTAURANT_NAMES)):
        restaurant = RESTAURANT_NAMES[i]
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

##############################################
# Discord bot helper functions
##############################################
def create_list_embed(current_page):
    title = "Fried chicken sandwich compendium"
    restaurants_formatted = []
    if current_page != (len(RESTAURANTS) - 1) // 10 or len(RESTAURANTS) % 10 == 0:
        for i in range(10):
            restaurant_name = RESTAURANTS[current_page * 10 + i][0][6:-4]
            restaurants_formatted.append("**{}.** {}".format(current_page * 10 + i + 1, restaurant_name))
    else:
        for i in range(len(RESTAURANTS) % 10):
            restaurant_name = RESTAURANTS[current_page * 10 + i][0][6:-4]
            restaurants_formatted.append("**{}.** {}".format(current_page * 10 + i + 1, restaurant_name))
    description = "\n".join(restaurants_formatted)
    embed = discord.Embed(title=title, description=description, color=0xd4af37)
    return restaurants_formatted, embed

def get_current_restaurants_list(current_page):
    # remove star signs from each element and return
    # return create_list_embed(current_page)[0]
    return [element.replace("*", "") for element in create_list_embed(current_page)[0]]

def create_restaurants_embed(current_page):
    # [link to logo image, price range, address, description (catchphrase), tier]
    title = RESTAURANTS[current_page][0][6:-4]
    if title in MANUAL_EMBED_RESTAURANTS:
        return create_manual_embed(current_page, RESTAURANTS)
    description = RESTAURANTS[current_page][3]
    address = RESTAURANTS[current_page][2]
    price_range = RESTAURANTS[current_page][1]
    tier = RESTAURANTS[current_page][4]

    gmaps_info = get_gmaps_info(current_page)

    embed = discord.Embed(title=title, description=description, color=discord.Color.from_str(TIER_COLOUR_HEX_DICT[tier]),
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
                          color=discord.Color.from_str(TIER_COLOUR_HEX_DICT['S']))
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
                          color=discord.Color.from_str(TIER_COLOUR_HEX_DICT['C']))
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
        human_readable_opening_hours = reformat_opening_hours_text(
            json_result['result'].get('opening_hours').get('weekday_text'),
            append_dummy_hours(opening_hours))
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
        if i > len(opening_hours) - 1 or opening_hours[i]['open']['day'] != i:
            opening_hours.insert(i, None)
    return opening_hours

def codify_opening_hours(opening_hours):
    """Return a list of opening hours in the format [(open, close)].

    open and close should have the format "DHHMM", where D is the day of the week (0-6),
    HH is the hour (00-23), and MM is the minute (00-59).

    If a restaurant is open 24 hours, return the same element without modification.

    append_dummy_hours() should be called before this function.

    Optionally, the element can be None if the restaurant is closed on that day.

    Args:
        opening_hours (dict): The opening hours of the restaurant

    Returns:
        list: A list of opening hours in the format [(open, close)]
    """
    assert len(opening_hours) == 7
    codified_opening_hours = []
    if all(opening_hours[i] is None for i in range(1, 7)) and opening_hours[0] is not None:
        return opening_hours
    for day in opening_hours:
        if day is None:
            codified_opening_hours.append(None)
        else:
            codified_opening_hours.append((str(day["open"]["day"]) + day["open"]["time"],
                                           str(day["close"]["day"]) + day["close"]["time"]))
    return codified_opening_hours

def get_maps_current_day(codified_opening_hours, codified_date_time):
    """Return the day that it would appear as the current day on Google Maps.

    For example, if a restaurant is open until 2am on Monday, and it is currently 1am on Tuesday,
    then the current day would appear as open on Monday on Google Maps.

    Args:
        codified_opening_hours (list): The codified opening hours of the restaurant
        codified_date_time (str): The codified date and time

    Returns:
        int: The day that it would appear as the current day on Google Maps
    """
    current_day = int(codified_date_time[0])
    if codified_opening_hours[current_day] is None or codified_opening_hours[current_day - 1] is None:
        return current_day
    if current_day != 0:
        if codified_opening_hours[current_day - 1][1] > codified_date_time:
            return current_day - 1
        else:
            return current_day
    else:
        _, close_hours_previous = codified_opening_hours[6]
        if close_hours_previous[0] == "0" and codified_date_time < close_hours_previous:
            return 6
        else:
            return 0

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
    current_day = time_date_dict["day"]
    codified_date_time = str(current_day) + time_date_dict["time"]
    codified_opening_hours = codify_opening_hours(append_dummy_hours(opening_hours))
    maps_current_day = get_maps_current_day(codified_opening_hours, codified_date_time)
    if codified_opening_hours[maps_current_day] is None:
        return False
    open_time, close_time = codified_opening_hours[maps_current_day]
    if maps_current_day != 6 or (maps_current_day == 6 and current_day == 6):
        return open_time <= codified_date_time < close_time
    else:
        assert maps_current_day == 6 and current_day == 0
        return codified_date_time < close_time

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

def reformat_opening_hours_text(opening_hours_text, opening_hours):
    """Reformat the opening hours text to be human readable.
    The parameter contains \u2009 or \u202f characters, which are unicode characters. Remove them.

    append_dummy_hours(opening_hours) should be called before this function.

    Args:
        opening_hours_text (list): The opening hours text of the restaurant
        opening_hours (dict): The opening hours of the restaurant

    Returns:
        str: The reformatted opening hours text
    """
    assert len(opening_hours) == 7
    plain_list = [opening_hour.replace('\u2009', ' ').replace('\u202f', ' ') for opening_hour in opening_hours_text]
    plain_list = [plain_list[-1]] + plain_list[:-1]
    time_date_dict = current_date_and_time()
    current_day = time_date_dict["day"]
    codified_date_time = str(current_day) + time_date_dict["time"]
    codified_opening_hours = codify_opening_hours(opening_hours)
    maps_current_day = get_maps_current_day(codified_opening_hours, codified_date_time)
    modified_list = ["**" + plain_list[opening_hour] + "**" if opening_hour == maps_current_day
                     else plain_list[opening_hour] for opening_hour in range(len(plain_list))]
    return "\n".join(modified_list)

if __name__ == "__main__":
    setup_db()
