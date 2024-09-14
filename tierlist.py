"""A Python file with Tierlist configurations."""
import os

from PIL import Image, ImageDraw, ImageFont
from helper import TIER_DICT, TIER_COLOUR_HEX_DICT, TIERLIST_IMAGE_NAME, TIERLIST_IMAGE_NAME_WITH_YEAR_TAG, TIERLIST_IMAGE_NAME_WITH_YEAR_FIRST_VISITED_TAG

DEFAULT_WIDTH = 200
DEFAULT_GAP = 20
DEFAULT_FONT = "arialbd.ttf"
DEFAULT_FONT_DIR = "./assets/arialbd.ttf"
FONT_SIZE = 50
GAPS_BETWEEN_RESTAURANTS = 10
TAG_LARGE_SIZE_MULTIPLIER = 5  # Tag's height will be 1/5 of the logo's height
TAG_SMALL_SIZE_MULTIPLIER = 7  # Tag's height will be 1/7 of the logo's height


def evaluate_num_logos_per_row(min_val: int = 10, threshold: int = 10) -> int:
    """Evaluate the ideal number of logos per row, such that
    the ratio between the width and height is closest to the golden ratio."""
    min_difference = 100
    num_logos_per_row = 0
    for i in range(min_val, min_val + threshold):
        tier_num_rows = get_num_rows_per_tier(i)
        total_width = DEFAULT_WIDTH * (i + 1) + GAPS_BETWEEN_RESTAURANTS * (i - 1) + \
                      DEFAULT_GAP * 3
        total_height = sum(tier_num_rows[tier] * DEFAULT_WIDTH + \
                           GAPS_BETWEEN_RESTAURANTS * (tier_num_rows[tier] - 1) \
                           for tier in tier_num_rows) + DEFAULT_GAP * (len(tier_num_rows) + 1)
        current_diff = abs(total_width / total_height - 1.618)
        if current_diff < min_difference:
            min_difference = current_diff
            num_logos_per_row = i
    return num_logos_per_row


def get_num_rows_per_tier(num_rows: int) -> dict:
    """Get the number of rows per tier, given the number of logos per row."""
    tier_num_rows = {}
    for k in TIER_DICT:
        if len(TIER_DICT[k]) % num_rows == 0:
            tier_num_rows[k] = len(TIER_DICT[k]) // num_rows
        else:
            tier_num_rows[k] = len(TIER_DICT[k]) // num_rows + 1
    return tier_num_rows


NUM_LOGOS_PER_ROW = evaluate_num_logos_per_row()
BACKGROUND_WIDTH = DEFAULT_WIDTH * NUM_LOGOS_PER_ROW + GAPS_BETWEEN_RESTAURANTS * (NUM_LOGOS_PER_ROW - 1)
BACKGROUND_COLOUR = (26, 26, 26)
TIER_NUM_ROWS = get_num_rows_per_tier(NUM_LOGOS_PER_ROW)


def total_num_restaurants():
    return sum(TIER_NUM_ROWS[tier] for tier in TIER_NUM_ROWS)


def make_tier_indicator(tier):
    """A tier indicator is a square of 100 x 100 pixels, with the text centered"""
    color = TIER_COLOUR_HEX_DICT[tier]
    image_width, image_height = DEFAULT_WIDTH, \
        DEFAULT_WIDTH * TIER_NUM_ROWS[tier] + GAPS_BETWEEN_RESTAURANTS * (TIER_NUM_ROWS[tier] - 1)
    img = Image.new('RGB', (image_width, image_height), color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(DEFAULT_FONT, FONT_SIZE)
    except OSError:
        font = ImageFont.truetype(DEFAULT_FONT_DIR, FONT_SIZE)
    left, top, right, bottom = draw.textbbox((0, 0), tier, font=font)
    w, h = right - left, bottom - top
    draw.text(((image_width - w) / 2, (image_height - h) / 2 - 4), tier, font=font, fill=(0, 0, 0))
    return img


def make_tier_background(tier):
    """A tier background is a rectangle which can be extended to the right
    color: (26, 26, 26))"""
    background_width, background_height = BACKGROUND_WIDTH, \
        DEFAULT_WIDTH * TIER_NUM_ROWS[tier] + GAPS_BETWEEN_RESTAURANTS * (TIER_NUM_ROWS[tier] - 1)
    img = Image.new('RGB', (background_width, background_height), BACKGROUND_COLOUR)
    return img


def _resize_tag_image(filepath: str, small: bool = False):
    """Given the file path, opens the tag image and resizes accordingly for better usability.
    
    By default, it will resize it to a larger sized tag, unless specified by the `small` parameter.
    """
    img = Image.open(filepath)
    width, height = img.size
    size_multiplier = TAG_LARGE_SIZE_MULTIPLIER
    if small:
        size_multiplier = TAG_SMALL_SIZE_MULTIPLIER
    return img.resize((int(width * DEFAULT_WIDTH / (height * size_multiplier)), int(DEFAULT_WIDTH / size_multiplier)))

TAGS_BASE_PATH = "assets/png/"
def _make_tags_image_dict():
    """Creates a tags image dictionary with the following attributes:
    
        - Price tags denoted by 1-4.png (never resized)
        - Year tags denoted by 2022-...png (small size by default for alternative tierlist image)
        - Vegan tag denoted by Vegan.png ("vegan_small" if year tags present, "vegan_large" otherwise)
    """
    tags_image_dict = {}
    png_names = os.listdir(TAGS_BASE_PATH)
    for name in png_names:
        if name.endswith(".png"):
            filepath, head = TAGS_BASE_PATH + name, name[:-4]
            if head == "Vegan":
                tags_image_dict["vegan_large"] = _resize_tag_image(filepath)
                tags_image_dict["vegan_small"] = _resize_tag_image(filepath, small=True)
            elif int(head) in (1, 2, 3, 4):
                # Price tag
                tags_image_dict[int(head)] = _resize_tag_image(filepath)
            else:
                # Year tag
                tags_image_dict[int(head)] = _resize_tag_image(filepath, small=True)
    return tags_image_dict
TAGS_IMAGE_DICT = _make_tags_image_dict()


def make_tier_restaurants(tier, with_year_tag: bool = False, with_year_first_visited_tag: bool = False):
    """Make a tier image"""
    # TODO: some variables here do not need to be resized every iteration, pull out as constants
    tier_img = make_tier_background(tier)
    restaurants = []
    for restaurant_name in TIER_DICT[tier]:
        restaurant_info = TIER_DICT[tier][restaurant_name]
        restaurant_logo, price, is_vegan, is_year, is_year_first_visited = (restaurant_info["path_to_logo_image"],
                                                     restaurant_info["price"],
                                                     restaurant_info.get("vegan", False),
                                                     restaurant_info["year"],
                                                     restaurant_info["year_first_visited"])
        # get the image of the restaurant
        # logo_img, price_img, is_vegan_img, is_year_img, is_year_first_visited_img = (Image.open(restaurant_logo),
        #                                                   Image.open("assets/png/{}.png".format(price)),
        #                                                   Image.open("assets/png/Vegan.png") if is_vegan else None,
        #                                                   Image.open("assets/png/{}.png".format(
        #                                                       is_year)) if is_year != -1 and with_year_tag else None,
        #                                                   Image.open("assets/png/{}.png".format(
        #                                                       is_year_first_visited)) if is_year_first_visited != -1 and with_year_first_visited_tag else None)
        logo_img, price_img, is_year_img, is_year_first_visited_img = (Image.open(restaurant_logo),
                                                                                     TAGS_IMAGE_DICT[price],
                                                                                     TAGS_IMAGE_DICT[is_year],
                                                                                     TAGS_IMAGE_DICT[is_year_first_visited])
        # get the width and height of the restaurant's logo
        width, height = logo_img.size
        price_width, price_height = price_img.size
        # resize the logo, preserving the aspect ratio, so that the height is 100 pixels
        logo_img = logo_img.resize((int(width * DEFAULT_WIDTH / height), DEFAULT_WIDTH))
        logo_img.paste(price_img, (logo_img.size[0] - price_img.size[0], 0), price_img)
        if is_vegan:
            if with_year_tag or with_year_first_visited_tag:
                # If either year tag is present, make the vegan tag smaller
                is_vegan_img = TAGS_IMAGE_DICT["vegan_small"]
            else:
                is_vegan_img = TAGS_IMAGE_DICT["vegan_large"]
            logo_img.paste(is_vegan_img, (logo_img.size[0] - is_vegan_img.size[0],
                                          logo_img.size[1] - is_vegan_img.size[1]),
                           is_vegan_img)

        if with_year_tag:
            logo_img.paste(is_year_img, (0, 0), is_year_img)
        elif with_year_first_visited_tag:
            logo_img.paste(is_year_first_visited_img, (0, 0), is_year_first_visited_img)

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


def make_one_complete_tier(tier, with_year_tag: bool = False, with_year_first_visited_tag: bool = False):
    """Make a tier image"""
    tier_indicator = make_tier_indicator(tier)
    tier_restaurants = make_tier_restaurants(tier, with_year_tag=with_year_tag, with_year_first_visited_tag=with_year_first_visited_tag)
    tier_img = Image.new('RGB', (tier_indicator.size[0] + tier_restaurants.size[0] + DEFAULT_GAP,
                                 DEFAULT_WIDTH * TIER_NUM_ROWS[tier] +
                                 GAPS_BETWEEN_RESTAURANTS * (TIER_NUM_ROWS[tier] - 1)), (0, 0, 0))
    tier_img.paste(tier_indicator, (0, 0))
    tier_img.paste(tier_restaurants, (tier_indicator.size[0] + DEFAULT_GAP, 0))
    return tier_img


def make_tierlist(with_year_tag: bool = False, with_year_first_visited_tag: bool = False):
    """Make a tierlist image, with margins equal to DEFAULT_GAP"""
    if with_year_tag and with_year_first_visited_tag:
        # This function should not be called with both booleans set to True
        raise ValueError('make_tierlist should not be called with both year tag booleans set to True')
    sum_of_num_rows = sum(TIER_NUM_ROWS.values())
    image_width, image_height = DEFAULT_WIDTH + BACKGROUND_WIDTH + 3 * DEFAULT_GAP, \
                                sum_of_num_rows * DEFAULT_WIDTH + 8 * DEFAULT_GAP + \
                                (sum_of_num_rows - 7) * GAPS_BETWEEN_RESTAURANTS
    tierlist = Image.new('RGB', (image_width, image_height), (0, 0, 0))
    y_offset = DEFAULT_GAP
    for tier in TIER_DICT:
        tier_img = make_one_complete_tier(tier, with_year_tag=with_year_tag, with_year_first_visited_tag=with_year_first_visited_tag)
        tierlist.paste(tier_img, (DEFAULT_GAP, y_offset))
        y_offset += tier_img.size[1] + DEFAULT_GAP
    return tierlist


if __name__ == "__main__":
    print("Number of logos per row: {}".format(NUM_LOGOS_PER_ROW))
    tierlist = make_tierlist()
    tierlist.save(TIERLIST_IMAGE_NAME)
    tierlist_with_year_tag = make_tierlist(with_year_tag=True)
    tierlist_with_year_tag.save(TIERLIST_IMAGE_NAME_WITH_YEAR_TAG)
    tierlist_with_year_first_visited_tag = make_tierlist(with_year_first_visited_tag=True)
    tierlist_with_year_first_visited_tag.save(TIERLIST_IMAGE_NAME_WITH_YEAR_FIRST_VISITED_TAG)
