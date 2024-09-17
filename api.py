import os
from flask import Flask, jsonify, request, render_template, url_for
import sqlite3
import random
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)
limiter.init_app(app)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jokes.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pretty-joke')
def pretty_joke():
    return render_template('pretty-joke.html')

@app.route('/jokes/random', methods=['GET'])
@limiter.limit("60 per minute")
def get_random_joke():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM jokes')
    total_jokes = cursor.fetchone()[0]

    if total_jokes == 0:
        conn.close()
        return jsonify({'error': 'No jokes found in the database.'}), 404

    random_offset = random.randint(0, total_jokes - 1)
    cursor.execute('SELECT id, joke FROM jokes LIMIT 1 OFFSET ?', (random_offset,))
    joke_row = cursor.fetchone()
    conn.close()

    return jsonify({'id': joke_row['id'], 'joke': joke_row['joke']})

if __name__ == '__main__':
    app.run(debug=True)
