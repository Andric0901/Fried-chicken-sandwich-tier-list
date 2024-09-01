"""A Python file with Tierlist configurations."""

from PIL import Image, ImageDraw, ImageFont
from helper import TIER_DICT, TIER_COLOUR_HEX_DICT, TIERLIST_IMAGE_NAME, TIERLIST_IMAGE_NAME_WITH_YEAR_TAG

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


def make_tier_restaurants(tier, with_year_tag: bool = False):
    """Make a tier image"""
    tier_img = make_tier_background(tier)
    restaurants = []
    for restaurant_name in TIER_DICT[tier]:
        restaurant_info = TIER_DICT[tier][restaurant_name]
        restaurant_logo, price, is_vegan, is_year = (restaurant_info["path_to_logo_image"],
                                                     restaurant_info["price"],
                                                     restaurant_info.get("vegan", False),
                                                     restaurant_info["year"])
        # get the image of the restaurant
        logo_img, price_img, is_vegan_img, is_year_img = (Image.open(restaurant_logo),
                                                          Image.open("assets/{}.png".format(price)),
                                                          Image.open("assets/Vegan.png") if is_vegan else None,
                                                          Image.open("assets/{}.png".format(
                                                              is_year)) if is_year != -1 and with_year_tag else None)
        # get the width and height of the restaurant's logo
        width, height = logo_img.size
        price_width, price_height = price_img.size
        # resize the logo, preserving the aspect ratio, so that the height is 100 pixels
        logo_img = logo_img.resize((int(width * DEFAULT_WIDTH / height), DEFAULT_WIDTH))
        price_img = price_img.resize((int(price_width * DEFAULT_WIDTH / (price_height * TAG_LARGE_SIZE_MULTIPLIER)),
                                      int(DEFAULT_WIDTH / TAG_LARGE_SIZE_MULTIPLIER)))
        logo_img.paste(price_img, (logo_img.size[0] - price_img.size[0], 0), price_img)
        if is_vegan_img:
            is_vegan_width, is_vegan_height = is_vegan_img.size
            if with_year_tag:
                # If year tag is present, make the vegan tag smaller
                is_vegan_img = is_vegan_img.resize((int(is_vegan_width * DEFAULT_WIDTH / (is_vegan_height * TAG_SMALL_SIZE_MULTIPLIER)),
                                                    int(DEFAULT_WIDTH / TAG_SMALL_SIZE_MULTIPLIER)))
            else:
                is_vegan_img = is_vegan_img.resize((int(is_vegan_width * DEFAULT_WIDTH / (is_vegan_height * TAG_LARGE_SIZE_MULTIPLIER)),
                                                    int(DEFAULT_WIDTH / TAG_LARGE_SIZE_MULTIPLIER)))
            logo_img.paste(is_vegan_img, (logo_img.size[0] - is_vegan_img.size[0],
                                          logo_img.size[1] - is_vegan_img.size[1]),
                           is_vegan_img)

        if is_year_img:
            is_year_width, is_year_height = is_year_img.size
            is_year_img = is_year_img.resize((int(is_year_width * DEFAULT_WIDTH / (is_year_height * TAG_SMALL_SIZE_MULTIPLIER)),
                                              int(DEFAULT_WIDTH / TAG_SMALL_SIZE_MULTIPLIER)))
            logo_img.paste(is_year_img, (0, 0), is_year_img)

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


def make_one_complete_tier(tier, with_year_tag: bool = False):
    """Make a tier image"""
    tier_indicator = make_tier_indicator(tier)
    tier_restaurants = make_tier_restaurants(tier, with_year_tag=with_year_tag)
    tier_img = Image.new('RGB', (tier_indicator.size[0] + tier_restaurants.size[0] + DEFAULT_GAP,
                                 DEFAULT_WIDTH * TIER_NUM_ROWS[tier] +
                                 GAPS_BETWEEN_RESTAURANTS * (TIER_NUM_ROWS[tier] - 1)), (0, 0, 0))
    tier_img.paste(tier_indicator, (0, 0))
    tier_img.paste(tier_restaurants, (tier_indicator.size[0] + DEFAULT_GAP, 0))
    return tier_img


def make_tierlist(with_year_tag: bool = False):
    """Make a tierlist image, with margins equal to DEFAULT_GAP"""
    sum_of_num_rows = sum(TIER_NUM_ROWS.values())
    image_width, image_height = DEFAULT_WIDTH + BACKGROUND_WIDTH + 3 * DEFAULT_GAP, \
                                sum_of_num_rows * DEFAULT_WIDTH + 8 * DEFAULT_GAP + \
                                (sum_of_num_rows - 7) * GAPS_BETWEEN_RESTAURANTS
    tierlist = Image.new('RGB', (image_width, image_height), (0, 0, 0))
    y_offset = DEFAULT_GAP
    for tier in TIER_DICT:
        tier_img = make_one_complete_tier(tier, with_year_tag=with_year_tag)
        tierlist.paste(tier_img, (DEFAULT_GAP, y_offset))
        y_offset += tier_img.size[1] + DEFAULT_GAP
    return tierlist


if __name__ == "__main__":
    print("Number of logos per row: {}".format(NUM_LOGOS_PER_ROW))
    tierlist = make_tierlist()
    tierlist.save(TIERLIST_IMAGE_NAME)
    tierlist_with_year_tag = make_tierlist(with_year_tag=True)
    tierlist_with_year_tag.save(TIERLIST_IMAGE_NAME_WITH_YEAR_TAG)
