# Greater Toronto Area Fried Chicken Sandwich Tierlist + Discord Bot
*Last Updated README.md: February 28th, 2026*

*This project is still in progress!*

A small project to rank ALL the fried chicken sandwich restaurants in GTA (Greater Toronto Area). 

# Current Tier List
![Tier List](https://github.com/Andric0901/Fried-chicken-sandwich-tier-list/blob/main/tierlist.png?raw=true)

# Alternative Tier Lists
### Tier List with year tags of first visit
![Tier List with year tags of first visit](https://github.com/Andric0901/Fried-chicken-sandwich-tier-list/blob/main/tierlist_with_year_first_visited_tag.png?raw=true)

### Tier List with year tags when the ranks have been (re)evaluated
![Tier List with year tags when the ranks have been (re)evaluated](https://github.com/Andric0901/Fried-chicken-sandwich-tier-list/blob/main/tierlist_with_year_tag.png?raw=true)

# How to run
If you want to play with this tierlist code (requires Python 3.12.3)...

 1. Clone this repository.
 1. Run `make` command
 1. Install all dependencies in `requirements.txt`: `pip install -r requirements.txt`.
 1. Run `python tierlist.py` to generate 3 types of tierlist images as shown above.

Editor UI allows you to create your own version of the tierlist, as well as add new restaurants to the tierlist. To run the editor UI for easier tierlist editing:

 1. Run `python editor_server.py`.
 1. Go to http://localhost:8000/editor.html in your browser (change the port if modified in `editor_server.py`)

Tips for using the editor UI:

 1. To add your own restaurant logos, simply add the logo (png or jpg format required, 1:1 square aspect ratio recommended for better visual experience, future works planned to improve this) to the `logos` folder. This new restaurant will then show up in the "Unassigned" dropdown in the top left corner for you to modify the metadata. (There are some works planned in the future to natively support adding logos through the UI)
 1. The editor UI automatically saves any changes to the local `tier_dict.json` file.
 1. Drag and drop any restaurant in the tierlist to move restaurants between tiers or reorder within a tier.
 1. Double click on any restaurant in the tierlist to open the metadata editor.
 1. Clicking the "Export Imgs" button on the top right corner will run `tierlist.py` file to generate the tierlist images as shown above. You can find the generated images at the root directory of this repository, if modified at all.

# Discord Bot
Click on [this link](https://discord.com/api/oauth2/authorize?client_id=1077364191494668420&permissions=8&scope=bot) to invite the bot to your server.
