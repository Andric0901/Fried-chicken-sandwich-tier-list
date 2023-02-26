import os

from PIL import Image, ImageDraw, ImageFont
import json

DEFAULT_WIDTH = 200
DEFAULT_GAP = 20
DEFAULT_FONT = "arialbd.ttf"
FONT_SIZE = 50
GAPS_BETWEEN_RESTAURANTS = 10
# TODO: Change the width if needed
BACKGROUND_WIDTH = 1800
BACKGROUND_COLOUR = (26, 26, 26)
tier_colour_dict = {
    'S': (255, 127, 127),
    'A': (255, 191, 127),
    'B': (255, 255, 127),
    'C': (127, 255, 127),
    'D': (127, 191, 255),
    'E': (127, 127, 255),
    'F': (255, 127, 255)
}

tier_colour_hex_dict = {
    'S': 0xff7f7f,
    'A': 0xffbf7f,
    'B': 0xffff7f,
    'C': 0x7fff7f,
    'D': 0x7fbfff,
    'E': 0x7f7fff,
    'F': 0xff7fff
}

tier_num_rows = {
    'S': 1,
    'A': 1,
    'B': 1,
    'C': 2,
    'D': 1,
    'E': 1,
    'F': 1
}

MANUAL_EMBED_RESTAURANTS = ["Bubba's Crispy Fried Chicken", "Foodie"]

tier_dict = json.load(open('tier_dict.json'))

def total_num_restaurants():
    return sum(tier_num_rows[tier] for tier in tier_num_rows)

def make_tier_indicator(tier, color):
    """A tier indicator is a square of 100 x 100 pixels, with the text centered"""
    image_width, image_height = DEFAULT_WIDTH, \
        DEFAULT_WIDTH * tier_num_rows[tier] + GAPS_BETWEEN_RESTAURANTS * (tier_num_rows[tier] - 1)
    img = Image.new('RGB', (image_width, image_height), color)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(DEFAULT_FONT, FONT_SIZE)
    left, top, right, bottom = draw.textbbox((0, 0), tier, font=font)
    w, h = right - left, bottom - top
    draw.text(((image_width - w) / 2, (image_height - h) / 2 - 4), tier, font=font, fill=(0, 0, 0))
    return img

def make_tier_background(tier):
    """A tier background is a rectangle which can be extended to the right
    color: (26, 26, 26))"""
    background_width, background_height = BACKGROUND_WIDTH, \
        DEFAULT_WIDTH * tier_num_rows[tier] + GAPS_BETWEEN_RESTAURANTS * (tier_num_rows[tier] - 1)
    img = Image.new('RGB', (background_width, background_height), BACKGROUND_COLOUR)
    return img

def make_tier_restaurants(tier):
    """Make a tier image"""
    tier_img = make_tier_background(tier)
    restaurants = []
    for restaurant_info in tier_dict[tier]:
        assert len(restaurant_info) == 5
        restaurant, price_range = restaurant_info[0], restaurant_info[1]
        # get the image of the restaurant
        img, price_img = Image.open(restaurant), Image.open("assets/{}.png".format(price_range))
        # get the width and height of the restaurant's logo
        width, height = img.size
        price_width, price_height = price_img.size
        # resize the logo, preserving the aspect ratio, so that the height is 100 pixels
        img = img.resize((int(width * DEFAULT_WIDTH / height), DEFAULT_WIDTH))
        price_img = price_img.resize((int(price_width * DEFAULT_WIDTH / (price_height * 5)),
                                      int(DEFAULT_WIDTH / 5)))
        img.paste(price_img,
                         (img.size[0] - price_img.size[0], 0), price_img)
        # append the logo to the list of restaurants
        restaurants.append(img)
    # paste the restaurants into the tier image, with a gap between each
    x_offset, y_offset = 0, 0
    for restaurant in restaurants:
        restaurant_width, restaurant_height = restaurant.size
        if x_offset + restaurant_width > BACKGROUND_WIDTH:
            x_offset = 0
            y_offset += restaurant_height + GAPS_BETWEEN_RESTAURANTS
        tier_img.paste(restaurant, (x_offset, y_offset))
        x_offset += restaurant.size[0] + GAPS_BETWEEN_RESTAURANTS
    return tier_img

def make_one_complete_tier(tier):
    """Make a tier image"""
    tier_indicator = make_tier_indicator(tier, tier_colour_dict[tier])
    tier_restaurants = make_tier_restaurants(tier)
    tier_img = Image.new('RGB', (tier_indicator.size[0] + tier_restaurants.size[0] + DEFAULT_GAP,
                                 DEFAULT_WIDTH * tier_num_rows[tier] +
                                 GAPS_BETWEEN_RESTAURANTS * (tier_num_rows[tier] - 1)), (0, 0, 0))
    tier_img.paste(tier_indicator, (0, 0))
    tier_img.paste(tier_restaurants, (tier_indicator.size[0] + DEFAULT_GAP, 0))
    return tier_img

def make_tierlist():
    """Make a tierlist image, with margins equal to DEFAULT_GAP"""
    sum_of_num_rows = sum(tier_num_rows.values())
    image_width, image_height = DEFAULT_WIDTH + BACKGROUND_WIDTH + 3 * DEFAULT_GAP, \
        sum_of_num_rows * DEFAULT_WIDTH + 8 * DEFAULT_GAP + \
        (sum_of_num_rows - 7) * GAPS_BETWEEN_RESTAURANTS
    tierlist = Image.new('RGB', (image_width, image_height), (0, 0, 0))
    y_offset = DEFAULT_GAP
    for tier in tier_dict:
        tier_img = make_one_complete_tier(tier)
        tierlist.paste(tier_img, (DEFAULT_GAP, y_offset))
        y_offset += tier_img.size[1] + DEFAULT_GAP
    return tierlist

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

if __name__ == '__main__':
    # Count the number of images under the directory logos
    count = sum([len(files) for _, _, files in os.walk('logos')])
    assert count == sum([len(tier_dict[tier]) for tier in tier_dict])
    tierlist = make_tierlist()
    tierlist.save('tierlist.png')

