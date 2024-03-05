import requests
import sqlite3
import os

# Define the path to the database file in the backend directory
PROJECT_DIRECTORY = "C:\\Users\\17135\\MTGStocks\\scryfall_project"
DATABASE_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "backend")
DATABASE_NAME = os.path.join(DATABASE_DIRECTORY, "scryfall_data.db")

def create_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Create cards table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY,
        name TEXT,
        type_line TEXT,
        mana_cost TEXT,
        rarity TEXT,
        set_name TEXT,
        image_url TEXT,
        legalities TEXT,
        prices TEXT,
        purchase_uris TEXT,
        related_uris TEXT,
        tcgplayer_id INTEGER,
        set_id TEXT,
        scryfall_uri TEXT
    )
    ''')
    
    # Create card_price_history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS card_price_history (
        history_id INTEGER PRIMARY KEY,
        card_id INTEGER,
        date_recorded DATE,
        price REAL,
        FOREIGN KEY(card_id) REFERENCES cards(id)
    )
    ''')

     # Create symbols table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        svg_uri TEXT,
        loose_variant TEXT,
        english TEXT,
        transposable BOOLEAN,
        represents_mana BOOLEAN,
        appears_in_mana_costs BOOLEAN,
        cmc REAL,
        funny BOOLEAN
    )
    ''')
    
    conn.commit()
    conn.close()

def save_current_prices_to_history(conn):
    cursor = conn.cursor()
    
    # Fetch current prices from cards table
    cursor.execute('SELECT id, prices FROM cards')
    records = cursor.fetchall()
    
    prices_to_insert = []
    for record in records:
        card_id, prices = record
        price_data = eval(prices)  # Convert the string representation of dictionary to an actual dictionary
        
        # Check if at least one value in the price_data dictionary is not None
        if any(val is not None for val in price_data.values()):
            prices_to_insert.append((card_id, prices))
    
    cursor.executemany('''
    INSERT INTO card_price_history (card_id, date_recorded, price)
    VALUES (?, (CURRENT_DATE - 1), ?)
    ''', prices_to_insert)
    
    conn.commit()

def fetch_data_from_scryfall():
    response = requests.get("https://api.scryfall.com/bulk-data")
    bulk_data = response.json()
    # Change from "all_cards" to "default_cards" to only fetch default cards data
    default_cards_uri = next(item for item in bulk_data['data'] if item["type"] == "default_cards")["download_uri"]
    response = requests.get(default_cards_uri)
    return response.json()

def fetch_symbols_from_scryfall():
    response = requests.get("https://api.scryfall.com/symbology")
    symbols_data = response.json()
    return symbols_data['data']

def insert_data_into_db(conn, data):
    cursor = conn.cursor()
    
    # Truncate the cards table
    cursor.execute('DELETE FROM cards')
    
    # Check if sqlite_sequence table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    if cursor.fetchone():
        # Reset the auto-increment counter for the cards table
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='cards'")
    
    cards_to_insert = []
    for card in data:
        image_url = None  # Initialize image_url as None

        # Check if 'image_uris' exists and prioritize English images
        if 'image_uris' in card and card.get('lang', '') == 'en':
            image_url = card['image_uris'].get('normal', None)
        
        # Append the card details to the list for insertion
        cards_to_insert.append((
            card['name'], 
            card.get('type_line', ''), 
            card.get('mana_cost', ''), 
            card['rarity'], 
            card['set_name'], 
            image_url, 
            str(card.get('legalities', '')), 
            str(card.get('prices', '')), 
            str(card.get('purchase_uris', '')), 
            str(card.get('related_uris', '')), 
            card.get('tcgplayer_id', None), 
            card['set_id'], 
            card['scryfall_uri']
        ))
    
    cursor.executemany('''
    INSERT INTO cards (name, type_line, mana_cost, rarity, set_name, image_url, legalities, prices, purchase_uris, related_uris, tcgplayer_id, set_id, scryfall_uri)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', cards_to_insert)
    
    conn.commit()

def insert_symbols_into_db(conn, symbols):
    cursor = conn.cursor()
    
    # Truncate the symbols table
    cursor.execute('DELETE FROM symbols')
    
    symbols_to_insert = []
    for symbol in symbols:
        symbols_to_insert.append((
            symbol['symbol'],
            symbol.get('svg_uri', ''),
            symbol.get('loose_variant', ''),
            symbol.get('english', ''),
            symbol.get('transposable', False),
            symbol.get('represents_mana', False),
            symbol.get('appears_in_mana_costs', False),
            symbol.get('cmc', 0) if symbol.get('cmc') is not None else 0,
            symbol.get('funny', False),
        ))
    
    cursor.executemany('''
    INSERT INTO symbols (symbol, svg_uri, loose_variant, english, transposable, represents_mana, appears_in_mana_costs, cmc, funny)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', symbols_to_insert)
    
    conn.commit()

def main():
    create_database()
    conn = sqlite3.connect(DATABASE_NAME)
    
    # Handle cards data
    data = fetch_data_from_scryfall()
    insert_data_into_db(conn, data)
    
    # Handle symbols data
    symbols = fetch_symbols_from_scryfall()
    insert_symbols_into_db(conn, symbols)
    
    conn.close()
    print("Data fetching and insertion completed for default cards and symbols!")

if __name__ == "__main__":
    main()