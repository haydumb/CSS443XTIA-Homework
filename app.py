from flask import Flask, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS 

app = Flask(__name__, static_url_path='', static_folder='../frontend')
CORS(app)

DATABASE_NAME = "../backend/scryfall_data.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/get_cards')
def get_cards():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cards LIMIT 50')
        cards = cursor.fetchall()
        conn.close()

        cards_list = [dict(ix) for ix in cards]
        return jsonify(cards_list)
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred fetching the card data"}), 500

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
