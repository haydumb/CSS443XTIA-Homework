from flask import Flask, jsonify, request, send_from_directory
import sqlite3

app = Flask(__name__, static_url_path='', static_folder='C:/xampp/htdocs/scryfall_project/frontend')

DATABASE_NAME = "C:/xampp/htdocs/scryfall_project/backend/scryfall_data.db"

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
        cursor.execute('SELECT * FROM cards LIMIT 10')
        cards = cursor.fetchall()
        conn.close()

        cards_list = [dict(ix) for ix in cards]
        return jsonify(cards_list)
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred fetching the card data"}), 500

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

if __name__ == "__main__":
    app.run(debug=True, port=8000)
