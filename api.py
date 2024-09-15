from flask import Flask, jsonify, request, render_template
import sqlite3
import random
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Rate Limiting (i know i was getting jokes at .5 from the original one but this will be hosted on a $5 a month python anywhere account and just in case people happen to use it, I don't know if i would overload my plan lol)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["60 per minute"]
)


def get_db_connection():
    conn = sqlite3.connect('jokes.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/jokes/random', methods=['GET'])
@limiter.limit("60 per minute")
def get_random_joke():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM jokes')
    total_jokes = cursor.fetchone()[0]

    if total_jokes == 0:
        return jsonify({'error': 'No jokes found in the database.'}), 404

    random_offset = random.randint(0, total_jokes - 1)
    cursor.execute('SELECT id, joke FROM jokes LIMIT 1 OFFSET ?', (random_offset,))
    joke_row = cursor.fetchone()
    conn.close()

    return jsonify({'id': joke_row['id'], 'joke': joke_row['joke']})


if __name__ == '__main__':
    app.run(debug=True)