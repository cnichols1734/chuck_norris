import requests
import sqlite3
import time

# chucknorris.io api joke getter 3000!

conn = sqlite3.connect('chuck_norris_jokes.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS jokes (
    internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    joke_id TEXT UNIQUE,
    joke TEXT,
    categories TEXT
)
''')
conn.commit()

# URL
api_url = 'https://api.chucknorris.io/jokes/random'

#duplicate counter
duplicate_count = 0
consecutive_duplicate_limit = 40 # gonna try 40, seems like a lot but when we get to the end we could get a lot of dupes. This is probably not the best way to do this but it's what i will try
unique_jokes_count = 0

while duplicate_count < consecutive_duplicate_limit:
    try:
        response = requests.get(api_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
        time.sleep(60) # my attempt at error handling lol
        continue

    data = response.json()
    joke_id = data.get('id')
    joke_text = data.get('value')
    categories = data.get('categories', [])
    categories_str = ','.join(categories) if categories else 'None'

    if not joke_text or not joke_id:
        continue

    # dupe check in my db
    cursor.execute('SELECT joke_id FROM jokes WHERE joke_id = ?', (joke_id,))
    result = cursor.fetchone()

    if result:
        # if jke already exists in my db, increment and print the total
        duplicate_count += 1
        print(f"Duplicate joke found. Consecutive duplicates: {duplicate_count}")
    else:
        cursor.execute('''
            INSERT INTO jokes (joke_id, joke, categories) VALUES (?, ?, ?)
        ''', (joke_id, joke_text, categories_str))
        conn.commit()
        unique_jokes_count += 1
        duplicate_count = 0  # if a new joke is found, we reest the counter to start back from the top
        print(f"New joke inserted! Total unique jokes: {unique_jokes_count}")

    # me trying to be nicce and not overload this free api so waiting half a second
    time.sleep(0.5)

print(f"Reached {consecutive_duplicate_limit} consecutive duplicates. Exiting, hopefully we get a nice amount of jokes!.")
conn.close()
