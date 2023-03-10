import time

import discord.ui
from discord import Activity, ActivityType, Status, ButtonStyle, SelectOption
from tierlist import get_first_tier_indexes
from helper import *
import random

FACTS = [
    "The first fried chicken sandwich was created in 1946 by the founder of Chick-fil-A.",
    "In 2019, Popeyes Chicken released a new chicken sandwich that sold out in two weeks.",
    "The term 'chicken burger' is sometimes used to describe a fried chicken sandwich.",
    "The McChicken sandwich from McDonald's was first introduced in 1980.",
    "Some people call the breading on a fried chicken sandwich the 'crunch factor'.",
    "The first KFC restaurant opened in 1930 and served primarily fried chicken sandwiches.",
    "Many fast food chains now offer spicy variations of the classic fried chicken sandwich.",
    "Some fried chicken sandwiches are served with a side of pickles.",
    "In 2015, a Nashville hot chicken sandwich gained popularity in the US.",
    "The Chick-fil-A chicken sandwich is often served with a side of waffle fries.",
    "The breading on a fried chicken sandwich can be made with a variety of ingredients, including flour, cornmeal, and breadcrumbs.",
    "In 2017, KFC released a fried chicken sandwich with a bun made of fried chicken.",
    "A chicken patty used in a sandwich is often marinated in a buttermilk mixture before being breaded and fried.",
    "The classic fried chicken sandwich typically includes lettuce, tomato, and mayonnaise.",
    "In 2021, McDonald's released a new crispy chicken sandwich in the US.",
    "Fried chicken sandwiches are often served on a toasted bun.",
    "The Nashville hot chicken sandwich is typically served with a side of coleslaw.",
    "In some parts of the US, a fried chicken sandwich is also known as a 'chicken filet'.",
    "Some fried chicken sandwiches are served with a spicy sauce.",
    "A chicken breast is often used to make a fried chicken sandwich.",
    "The classic Chick-fil-A chicken sandwich includes two pickles.",
    "In 2018, Wendy's released a new chicken sandwich with a breading made of crumbled crackers.",
    "Some restaurants offer a vegetarian version of a fried chicken sandwich made with a plant-based patty.",
    "Fried chicken sandwiches can be served with a variety of toppings, including cheese and bacon.",
    "In 2019, a fried chicken sandwich craze swept the US and resulted in several viral internet debates.",
    "The first recorded recipe for fried chicken was published in 1747.",
    "In 2015, a fried chicken sandwich with donuts as the bun gained popularity.",
    "The classic Popeyes chicken sandwich includes pickles, mayonnaise, and a brioche bun.",
    "In some parts of the world, a fried chicken sandwich is served with a side of rice.",
    "Fried chicken sandwiches are often served with a side of fries.",
    "The first Chick-fil-A restaurant was opened in Atlanta, Georgia.",
    "In 2020, a fried chicken sandwich was sent to space by a marketing campaign.",
    "The breading on a fried chicken sandwich can be flavored with a variety of spices, including cayenne pepper and paprika.",
    "Fried chicken sandwiches are often served on a soft bun.",
    "In 2016, a fried chicken sandwich with a doughnut as the bun was released in Australia.",
    "Some fried chicken sandwiches are served with a honey mustard sauce.",
    "In some parts of the world, a fried chicken sandwich is known as a 'chicken burger'.",
    "In 2021, KFC released a new chicken sandwich with a donut as the bun.",
    "The classic McDonald's McChicken sandwich includes shredded lettuce and mayonnaise.",
    "In some parts of the US, a fried chicken sandwich is served with a side of mashed potatoes and gravy.",
    "In 2019, Popeyes Chicken and Chick-fil-A engaged in a Twitter feud over their respective chicken sandwiches.",
    "Some restaurants serve a fried chicken sandwich with a side of macaroni and cheese.",
    "The classic KFC chicken sandwich includes a brioche bun and pickles.",
    "In some parts of the world, a fried chicken sandwich is served with a side of corn on the cob.",
    "Fried chicken sandwiches are often served with a spicy mayonnaise or aioli.",
    "In 2020, McDonald's released a new spicy chicken sandwich in the US.",
    "The classic Wendy's chicken sandwich includes a toasted bun, mayonnaise, and tomato.",
    "Fried chicken sandwiches are often served with a side of coleslaw.",
    "In some parts of the US, a fried chicken sandwich is also known as a 'chicken sandwich'.",
    "The classic Nashville hot chicken sandwich includes a spicy seasoning made with cayenne pepper.",
    "In 2019, a Popeyes Chicken sandwich sold for over $120,000 on eBay.",
    "Some restaurants serve a fried chicken sandwich with a side of baked beans.",
    "The breading on a fried chicken sandwich can be made with a gluten-free flour for those with dietary restrictions.",
    "In 2018, a fried chicken sandwich with a bun made of ramen noodles gained popularity.",
    "Fried chicken sandwiches are often served with a side of sweet potato fries.",
    "In some parts of the world, a fried chicken sandwich is served with a side of plantains.",
    "The classic Chick-fil-A chicken sandwich is served on a buttered bun.",
    "In 2020, a viral TikTok video claimed that a McDonald's employee had revealed a secret menu item: a fried chicken sandwich with Big Mac sauce.",
    "Some fried chicken sandwiches are served with a slaw made of carrots and cabbage.",
    "The first KFC franchise opened in Utah in 1952.",
    "In 2021, McDonald's released a new crispy chicken sandwich with a potato roll.",
    "Fried chicken sandwiches are often served with a side of hot sauce.",
    "In some parts of the US, a fried chicken sandwich is known as a 'chicken fillet sandwich'.",
    "The classic Wendy's chicken sandwich includes a breaded chicken patty and lettuce.",
    "In 2019, a fried chicken sandwich was featured in a Beyonce music video.",
    "Some restaurants offer a fried chicken sandwich with a side of honey butter.",
    "The breading on a fried chicken sandwich can be made with a mixture of flour and cornstarch for a lighter texture.",
    "In 2016, KFC released a fried chicken sandwich with a bun made of fried chicken and bacon.",
    "Fried chicken sandwiches are often served with a side of ranch dressing.",
    "In some parts of the world, a fried chicken sandwich is served with a side of yuca fries.",
    "The classic Popeyes chicken sandwich includes a spicy Cajun sauce.",
    "In 2018, a fast food chain in Japan released a fried chicken sandwich with a black bun made of squid ink.",
    "Some fried chicken sandwiches are served with a sauce made of honey and mustard.",
    "In 2021, Shake Shack introduced a Korean-style fried chicken sandwich with gochujang sauce.",
    "Fried chicken sandwiches are a popular menu item at fast food chains such as McDonald's, KFC, and Chick-fil-A.",
    "In some parts of the world, a fried chicken sandwich is served with a side of sweet chili sauce.",
    "The classic Bojangles' chicken sandwich includes a Cajun-spiced chicken breast and a toasted bun.",
    "In 2019, a man in Maryland created a 1,500-foot-long fried chicken sandwich.",
    "Fried chicken sandwiches can be made with a variety of different breads, including brioche, potato rolls, and sourdough.",
    "In some parts of the US, a fried chicken sandwich is served with a side of hushpuppies.",
    "The classic Chick-fil-A chicken sandwich is marinated in a blend of spices and pickle juice.",
    "In 2020, KFC introduced a new chicken sandwich with a donut as the bun.",
    "Some restaurants offer a fried chicken sandwich with a side of garlic fries.",
    "Fried chicken sandwiches are often topped with a slice of cheese, such as cheddar or pepper jack.",
    "In some parts of the world, a fried chicken sandwich is served with a side of fried plantains.",
    "The classic Shake Shack chicken sandwich includes buttermilk-marinated chicken breast and a potato roll.",
    "In 2021, McDonald's introduced a new crispy chicken sandwich with a spicy pepper sauce.",
    "Fried chicken sandwiches can be made with boneless or bone-in chicken.",
    "In some parts of the US, a fried chicken sandwich is known as a 'chicken on a bun'.",
    "The classic Zaxby's chicken sandwich includes a chicken breast fillet and Zax sauce.",
    "In 2019, a fried chicken sandwich pop-up shop opened in New York City and had lines around the block.",
    "Fried chicken sandwiches are often served with a side of waffle fries.",
    "In some parts of the world, a fried chicken sandwich is served with a side of fried rice.",
    "The classic Raising Cane's chicken sandwich includes a chicken finger and Cane's sauce.",
    "In 2020, Wendy's introduced a new chicken sandwich with a spicy jalapeno popper sauce.",
    "Some restaurants offer a fried chicken sandwich with a side of roasted vegetables.",
    "Fried chicken sandwiches can be seasoned with a variety of spices, including paprika, cumin, and garlic powder.",
    "In some parts of the US, a fried chicken sandwich is served with a side of collard greens.",
    "The classic Jack in the Box chicken sandwich includes a chicken patty and mayo.",
    "In 2019, a food critic for The New Yorker declared that the Popeyes chicken sandwich was 'the fast-food item of the year'.",
    "Fried chicken sandwiches are often served with a side of potato salad.",
    "In some parts of the world, a fried chicken sandwich is served with a side of cornbread.",
    "The classic Arby's chicken sandwich includes a chicken breast fillet and honey mustard sauce.",
    "In 2020, Popeyes introduced a new chicken sandwich with a garlic pepper sauce.",
    "Some restaurants offer a fried chicken sandwich with a side of grilled pineapple.",
    "Fried chicken sandwiches can be served on a variety of breads, including ciabatta, focaccia, and baguette."
]

# class ListPagesView(discord.ui.View):
#     def __init__(self, current_page=0):
#         super().__init__(timeout=None)
#         self.page = current_page
#         self.min_page = 0
#         self.max_page = len(RESTAURANTS) - 1


class RestaurantsPagesView(discord.ui.View):
    def __init__(self, current_page=0):
        super().__init__(timeout=None)
        self.page = current_page
        self.min_page = 0
        self.max_page = len(RESTAURANTS) - 1
        # self.previous_restaurant_name, self.next_restaurant_name = None, None
        # self.update_previous_and_next()
        self.thumbnail_file, self.embed = create_restaurants_embed(self.page)
        self.update_buttons()

    # def update_previous_and_next(self):
    #     self.previous_restaurant_name = RESTAURANTS[self.page - 1][0][6:-4] if self.page > 0 else None
    #     self.next_restaurant_name = RESTAURANTS[self.page + 1][0][
    #                                 6:-4] if self.page < self.max_page else None

    @discord.ui.button(label='⏮', style=ButtonStyle.green, custom_id='first')
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        # self.update_previous_and_next()
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='◀', style=ButtonStyle.blurple, custom_id='previous')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        # self.update_previous_and_next()
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='▶', style=ButtonStyle.blurple, custom_id='next')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        # self.update_previous_and_next()
        await self.update_interaction(interaction)
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label='⏭', style=ButtonStyle.green, custom_id='last')
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.max_page
        # self.update_previous_and_next()
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
        self.thumbnail_file, self.embed = create_restaurants_embed(self.page)
        await interaction.message.edit(embed=self.embed, attachments=[self.thumbnail_file])
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page == 0
        self.children[2].disabled = self.page == self.max_page
        self.children[3].disabled = self.page == self.max_page
        # self.update_previous_and_next()
        # if self.children[1].disabled:
        #     self.children[1].label = '◀️'
        # else:
        #     self.children[1].label = '◀️ {}'.format(self.previous_restaurant_name)
        # if self.children[2].disabled:
        #     self.children[2].label = '▶️'
        # else:
        #     self.children[2].label = '{} ▶️'.format(self.next_restaurant_name)


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


@tree.command(name='restaurants', description='Show each restaurant in the tierlist')
async def restaurants_command(interaction):
    view = RestaurantsPagesView(current_page=6)
    thumbnail_file, embed = create_restaurants_embed(view.page)
    await interaction.response.send_message(embed=embed, file=thumbnail_file, view=view)

client.run(token)
