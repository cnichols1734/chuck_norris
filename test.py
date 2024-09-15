import requests
import json


def fetch_and_print_chuck_norris_joke():
    api_url = 'https://api.chucknorris.io/jokes/random'

    try:
        # Fetch a joke from the API
        response = requests.get(api_url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Pretty print the entire response
            print("Full API Response:")
            print(json.dumps(data, indent=2))

        else:
            print(f"Error fetching joke: HTTP Status Code {response.status_code}")

    except requests.RequestException as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    fetch_and_print_chuck_norris_joke()