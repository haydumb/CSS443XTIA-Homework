from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS  # Import CORS
import sqlite3
import os

# Define the base directory based on this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATABASE_PATH = os.path.join(BASE_DIR, 'backend', 'scryfall_data.db')

app = Flask(__name__, static_url_path='', static_folder=FRONTEND_DIR)
CORS(app)  # Enable CORS for all domains on all routes

DATABASE_NAME = "scryfall_data.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/get_cards')
def get_cards():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cards LIMIT 10')
    cards = cursor.fetchall()
    conn.close()

    # Convert the row objects to dictionaries for JSON response
    cards_list = [dict(card) for card in cards]
    return jsonify(cards_list)

@app.route('/search')
def search():
    query = request.args.get('query')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards WHERE name LIKE ?', ('%' + query + '%',))
        cards = cursor.fetchall()
        conn.close()

        cards_list = [dict(ix) for ix in cards]
        return jsonify(cards_list)
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred searching the cards"}), 500

@app.route('/mana-symbols')
def mana_symbols():
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, svg_uri FROM symbols")
        symbols = {symbol: svg_uri for symbol, svg_uri in cursor.fetchall()}
        conn.close()
        return jsonify(symbols)
    except Exception as e:
        app.logger.error(f"Error accessing database: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
def get_mana_symbol_image(symbol):
    """Retrieve a mana symbol image from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT svg_uri FROM symbols WHERE symbol = ?", (symbol,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        return None

if __name__ == '__main__':
    app.run(debug=True)