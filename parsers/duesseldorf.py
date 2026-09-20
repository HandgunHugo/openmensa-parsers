from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re
from datetime import datetime
from pyopenmensa.feed import LazyBuilder
from utils import Parser

def parse_url(url, **kwargs):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req).read()
    soup = BeautifulSoup(html, 'lxml')
    
    feed = LazyBuilder()

    # 1. Datum extrahieren
    page_text = soup.get_text()
    date_match = re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', page_text)
    
    if date_match:
        current_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"
    else:
        current_date = datetime.now().strftime("%Y-%m-%d")

    # 2. Gerichte suchen
    meal_elements = soup.find_all(["p", "div", "span"], class_=re.compile("aw-meal-description", re.I))

    for item in meal_elements:
        dish_name = item.get_text(strip=True)
        if not dish_name or "Heute keine Essensausgabe" in dish_name:
            continue

        # 3. Den übergeordneten Container finden, der Name UND Preis enthält.
        # Wir klettern Ebene für Ebene nach oben, bis wir das Euro-Zeichen finden (max. 4 Ebenen).
        current_node = item
        container_text = ""
        for _ in range(4):
            current_node = current_node.parent
            if not current_node:
                break
            container_text = current_node.get_text(" ", strip=True)
            if '€' in container_text:
                break

        # 4. Preis extrahieren
        price_match = re.search(r'(\d+),(\d{2})\s*€', container_text)
        if price_match:
            price_str = f"{price_match.group(1)}.{price_match.group(2)}"
            prices = {'student': price_str}
        else:
            prices = {}

        # 5. Kalorien extrahieren
        notes = []
        calories_match = re.search(r'(\d+)\s*kcal', container_text)
        if calories_match:
            notes.append(f"{calories_match.group(1)} kcal")

        # 6. Zum Feed hinzufügen (mit genau 8 Leerzeichen Einrückung)
        feed.addMeal(current_date, 'Tagesgericht', dish_name, prices=prices, notes=notes)

    return feed.toXMLFeed()

# Setup für das Framework
parser = Parser(
    'duesseldorf',
    handler=parse_url,
    shared_prefix='https://www.imensa.de/duesseldorf/'
)

parser.define('universitaetsstrasse', suffix='mensa-universitaetsstrasse/')