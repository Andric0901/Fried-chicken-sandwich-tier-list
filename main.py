from discord import Activity, ActivityType, Status, ButtonStyle, SelectOption
from tierlist import get_first_tier_indexes
from helper import *

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


@tree.command(name='restaurants', description='Show each restaurant in the tierlist')
async def restaurants_command(interaction):
    view = PaginationView()
    thumbnail_file, embed = create_embed(view.page)
    await interaction.response.send_message(embed=embed, file=thumbnail_file, view=view)

client.run(token)
