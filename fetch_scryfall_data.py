import requests
import sqlite3

DATABASE_NAME = "scryfall_data.db"

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
    all_cards_uri = next(item for item in bulk_data['data'] if item["type"] == "all_cards")["download_uri"]
    response = requests.get(all_cards_uri)
    return response.json()

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
        image_url = card['image_uris']['normal'] if 'image_uris' in card else None
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

def main():
    create_database()
    conn = sqlite3.connect(DATABASE_NAME)
    
    # Save current prices to history before fetching new data
    save_current_prices_to_history(conn)
    
    data = fetch_data_from_scryfall()
    insert_data_into_db(conn, data)
    conn.close()
    print("Data fetching completed!")

if __name__ == "__main__":
    main()
