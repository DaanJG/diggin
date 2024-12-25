import os
import requests
import time
import json
from requests_oauthlib import OAuth1

# Read credentials and username from environment variables
consumer_key = os.getenv("DISCOGS_CONSUMER_KEY")
consumer_secret = os.getenv("DISCOGS_CONSUMER_SECRET")
access_token = os.getenv("DISCOGS_ACCESS_TOKEN")  # Optional
access_secret = os.getenv("DISCOGS_ACCESS_SECRET")  # Optional
username = os.getenv("DISCOGS_USERNAME")

# Check if required environment variables are set
if not consumer_key or not consumer_secret or not username:
    raise EnvironmentError("Missing required environment variables.")

# OAuth1 authentication
auth = OAuth1(consumer_key, consumer_secret, access_token, access_secret)

# Function to get release details including tracklist
def fetch_release_details(release_id):
    url = f"https://api.discogs.com/releases/{release_id}"
    while True:
        response = requests.get(url, auth=auth)
        if response.status_code == 429:
            print("Rate limit exceeded. Waiting 10 seconds...")
            time.sleep(10)  # Wait for 10 seconds
            continue
        elif response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching release {release_id}: {response.status_code}")
            return None

# Fetch the full collection
base_url = f"https://api.discogs.com/users/{username}/collection/folders/0/releases"
page = 1
per_page = 50
full_releases = []

while True:
    url = f"{base_url}?page={page}&per_page={per_page}"
    response = requests.get(url, auth=auth)
    if response.status_code == 429:
        print("Rate limit exceeded. Waiting 10 seconds...")
        time.sleep(10)
        continue
    elif response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        break

    data = response.json()
    releases = data['releases']
    
    for release in releases:
        release_id = release['id']
        release_details = fetch_release_details(release_id)
        if release_details:
            full_releases.append(release_details)

    if len(releases) < per_page:
        break
    page += 1

    # Respect rate limits with a small delay
    time.sleep(1)

# Save all data to a JSON file
output_file = "discogs_collection.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(full_releases, f, indent=4, ensure_ascii=False)

print(f"Saved {len(full_releases)} releases to {output_file}.")

