import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('jokes.db')
cursor = conn.cursor()

# Task 1: Remove duplicate jokes based on the joke string
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

    # For each duplicate joke, delete all but the one with the smallest ID
    for joke_text, min_id in duplicates:
        # Count how many duplicates there are for this joke
        cursor.execute('SELECT COUNT(*) FROM jokes WHERE joke = ?', (joke_text,))
        count = cursor.fetchone()[0]
        duplicates_for_joke = count - 1  # since one record (with min_id) is kept

        # Delete duplicates
        cursor.execute('''
            DELETE FROM jokes
            WHERE joke = ? AND id != ?
        ''', (joke_text, min_id))

        total_duplicates_removed += duplicates_for_joke
        print(f"Removed {duplicates_for_joke} duplicate(s) for joke ID {min_id}")

    conn.commit()
    print(f"\nTotal duplicate jokes found: {duplicate_groups}")
    print(f"Total duplicates removed: {total_duplicates_removed}")

# Task 2: Ensure each category has a value or is set to NULL
def clean_categories():
    # Set 'categories' to NULL where it's an empty string or whitespace
    cursor.execute('''
        UPDATE jokes
        SET categories = NULL
        WHERE TRIM(categories) = ''
    ''')
    conn.commit()
    print("\nEmpty 'categories' fields have been set to NULL.")

    # Trim leading/trailing whitespace from 'categories' fields
    cursor.execute('''
        UPDATE jokes
        SET categories = TRIM(categories)
        WHERE categories IS NOT NULL
    ''')
    conn.commit()
    print("'Categories' fields have been trimmed of whitespace.")

# Execute the tasks
remove_duplicate_jokes()
clean_categories()

# Close the database connection
conn.close()
