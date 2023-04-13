"""A Python file with Tierlist configurations."""

from PIL import Image, ImageDraw, ImageFont
from helper import TIER_DICT, TIER_COLOUR_HEX_DICT, TIERLIST_IMAGE_NAME

DEFAULT_WIDTH = 200
DEFAULT_GAP = 20
DEFAULT_FONT = "arialbd.ttf"
FONT_SIZE = 50
GAPS_BETWEEN_RESTAURANTS = 10
# TODO: Change the width if needed
BACKGROUND_WIDTH = 1800
BACKGROUND_COLOUR = (26, 26, 26)
# TODO: Change tier_num_rows to be variable, not hard-coded
tier_num_rows = {
    'S': 1,
    'A': 1,
    'B': 2,
    'C': 2,
    'D': 1,
    'E': 1,
    'F': 1
}

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
    for restaurant_name in TIER_DICT[tier]:
        restaurant_info = TIER_DICT[tier][restaurant_name]
        restaurant_logo, price = restaurant_info["path_to_logo_image"], restaurant_info["price"]
        # get the image of the restaurant
        logo_img, price_img = Image.open(restaurant_logo), Image.open("assets/{}.png".format(price))
        # get the width and height of the restaurant's logo
        width, height = logo_img.size
        price_width, price_height = price_img.size
        # resize the logo, preserving the aspect ratio, so that the height is 100 pixels
        logo_img = logo_img.resize((int(width * DEFAULT_WIDTH / height), DEFAULT_WIDTH))
        price_img = price_img.resize((int(price_width * DEFAULT_WIDTH / (price_height * 5)),
                                      int(DEFAULT_WIDTH / 5)))
        logo_img.paste(price_img, (logo_img.size[0] - price_img.size[0], 0), price_img)
        # append the logo to the list of restaurants
        restaurants.append(logo_img)
    # paste the restaurants into the tier image, with a gap between each
    x_offset, y_offset = 0, 0
    for restaurant_logo in restaurants:
        restaurant_width, restaurant_height = restaurant_logo.size
        if x_offset + restaurant_width > BACKGROUND_WIDTH:
            x_offset = 0
            y_offset += restaurant_height + GAPS_BETWEEN_RESTAURANTS
        tier_img.paste(restaurant_logo, (x_offset, y_offset))
        x_offset += restaurant_logo.size[0] + GAPS_BETWEEN_RESTAURANTS
    return tier_img

def make_one_complete_tier(tier):
    """Make a tier image"""
    tier_indicator = make_tier_indicator(tier, TIER_COLOUR_HEX_DICT[tier])
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
    for tier in TIER_DICT:
        tier_img = make_one_complete_tier(tier)
        tierlist.paste(tier_img, (DEFAULT_GAP, y_offset))
        y_offset += tier_img.size[1] + DEFAULT_GAP
    return tierlist

if __name__ == "__main__":
    tierlist = make_tierlist()
    tierlist.save(TIERLIST_IMAGE_NAME)
