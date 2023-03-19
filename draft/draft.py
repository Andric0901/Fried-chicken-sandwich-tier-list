import googlemaps
from googlemaps import places
from selenium import webdriver
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By

LINK = "https://goo.gl/maps/pZzHhwouNNurRWS58"
gmaps = googlemaps.Client(key='AIzaSyAwoUam-gVyFg1RfmFZ6PuqgIPHewvTArE')


# def manual_scraper(link):
#     browser = webdriver.Chrome()
#     actions = webdriver.ActionChains(browser)
#     browser.get(link)
#     # TODO: change the number if it does not scrape all restaurants
#     for _ in range(35):
#         element = browser.find_element(By.CLASS_NAME, "m6QErb.DxyBCb.kA9KIf.dS8AEf")
#         size = element.size
#         actions.move_to_element_with_offset(element, -size["width"] / 2, -size["height"] / 2).click_and_hold(
#             element).move_by_offset(0, size["height"] / 2).perform()
#         browser.implicitly_wait(30)
#         element2 = browser.find_element(By.CLASS_NAME, "qCHGyb.ipilje")
#         actions.click(element2).perform()
#     # assign browser to beautiful soup
#     with open("soup_output.html", "w", encoding="utf-8", errors='ignore') as f:
#         soup = BeautifulSoup(browser.page_source, "html.parser")
#         f.write(str(soup.prettify()))

def get_search_queries():
    restaurants, addresses = get_restaurants_and_addresses()
    result = [restaurants[i] + " " + addresses[i] for i in range(len(restaurants))]
    return result

def get_restaurants_and_addresses():
    with open("soup_output.html", "r", encoding="utf-8", errors='ignore') as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    restaurants = [restaurant.text.strip() for restaurant in soup.find_all("h3", class_="kiaEld")]
    addresses = [address.text.strip() for address in soup.find_all("span", class_="fKEVAc")]
    assert len(restaurants) == len(addresses)
    return restaurants, addresses

if __name__ == '__main__':
    import pprint
    places_result = places.find_place(gmaps, "Top Gun Burgers 490 Bloor St W", "textquery")
    url = "https://maps.googleapis.com/maps/api/place/details/json?placeid={}&key={}".format(places_result["candidates"][0]["place_id"], "AIzaSyAwoUam-gVyFg1RfmFZ6PuqgIPHewvTArE")
    import requests
    r = requests.get(url)
    pprint.pprint(r.json())
    # manual_scraper("https://goo.gl/maps/pZzHhwouNNurRWS58")
    # result = get_search_queries()
    # print(len(result))
    # for i in range(len(result)):
    #     print(str(i + 1), result[i])


