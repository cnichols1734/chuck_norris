import sqlite3

conn = sqlite3.connect('jokes.db')
cursor = conn.cursor()

def remove_duplicate_jokes():
    # Find duplicate jokes
    cursor.execute('''
        SELECT joke, MIN(id) as min_id
        FROM jokes
        GROUP BY joke
        HAVING COUNT(*) > 1
    ''')
    duplicates = cursor.fetchall()

    duplicate_groups = len(duplicates)
    total_duplicates_removed = 0

    for joke_text, min_id in duplicates:
        cursor.execute('SELECT COUNT(*) FROM jokes WHERE joke = ?', (joke_text,))
        count = cursor.fetchone()[0]
        duplicates_for_joke = count - 1  # since one record (with min_id) is kept

        # delete duplicates
        cursor.execute('''
            DELETE FROM jokes
            WHERE joke = ? AND id != ?
        ''', (joke_text, min_id))

        total_duplicates_removed += duplicates_for_joke
        print(f"Removed {duplicates_for_joke} duplicate(s) for joke ID {min_id}")

    conn.commit()
    print(f"\nTotal duplicate jokes found: {duplicate_groups}")
    print(f"Total duplicates removed: {total_duplicates_removed}")

def clean_categories():
    cursor.execute('''
        UPDATE jokes
        SET categories = NULL
        WHERE TRIM(categories) = ''
    ''')
    conn.commit()
    print("\nEmpty 'categories' fields have been set to NULL.")

    cursor.execute('''
        UPDATE jokes
        SET categories = TRIM(categories)
        WHERE categories IS NOT NULL
    ''')
    conn.commit()
    print("'Categories' fields have been trimmed of whitespace.")

remove_duplicate_jokes()
clean_categories()

conn.close()
