import os
import requests
import json
import time
import base64
import random
import pandas as pd
from typing import Optional

# Load environment variables for Spotify API
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
MATCH_LIMIT = os.getenv("MATCH_LIMIT")
SHUFFLE_RELEASES = os.getenv("SHUFFLE_RELEASES", "false").lower() == "true"

# Files
DISCOGS_FILE = "discogs_collection.json"
MAPPING_FILE = "discogs_spotify_mapping.json"

# Spotify API endpoints
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_SEARCH_URL = "https://api.spotify.com/v1/search"
SPOTIFY_ALBUM_URL = "https://api.spotify.com/v1/albums"
SPOTIFY_TRACK_URL = "https://api.spotify.com/v1/tracks"
SPOTIFY_AUDIO_FEATURES_URL = "https://api.spotify.com/v1/audio-features"

# Authenticate with Spotify
def authenticate_spotify():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise EnvironmentError("Missing Spotify API credentials.")

    credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    auth_response = requests.post(
        SPOTIFY_AUTH_URL,
        data={"grant_type": "client_credentials"},
        headers={
            "Authorization": f"Basic {encoded_credentials}"
        },
    )

    if auth_response.status_code != 200:
        raise Exception(f"Error authenticating with Spotify: {auth_response.text}")

    return auth_response.json()["access_token"]

# Normalize track titles for better matching
def normalize_title(title):
    # Remove text in parentheses and extra whitespace
    import re
    return re.sub(r"\(.*?\)", "", title).strip().lower()

# Search for an album on Spotify
def search_spotify_album(spotify_token, release_title, artist):
    query = f"album:{release_title} artist:{artist}"
    print(f"Searching for album: '{release_title}' by '{artist}' on Spotify.")
    response = requests.get(
        SPOTIFY_SEARCH_URL,
        headers={"Authorization": f"Bearer {spotify_token}"},
        params={"q": query, "type": "album", "limit": 1},
    )
    if response.status_code != 200:
        print(f"Error searching for album: {response.status_code}, {response.text}")
        return None

    items = response.json().get("albums", {}).get("items", [])
    if items:
        print(f"Album match found: '{items[0].get('name')}' by '{items[0].get('artists', [{}])[0].get('name')}'.")
    else:
        print("No album match found.")
    return items[0] if items else None

# Get tracks for a Spotify album
def get_album_tracks(spotify_token, album_id):
    print(f"Fetching tracks for album ID: {album_id}")
    response = requests.get(
        f"{SPOTIFY_ALBUM_URL}/{album_id}/tracks",
        headers={"Authorization": f"Bearer {spotify_token}"},
    )
    if response.status_code != 200:
        print(f"Error fetching tracks for album: {response.status_code}, {response.text}")
        return []

    tracks = response.json().get("items", [])
    print(f"Fetched {len(tracks)} tracks from album ID: {album_id}.")
    return tracks

# Get details for a single Spotify track
def get_spotify_track_details(spotify_token, track_id):
    print(f"Fetching details for track ID: {track_id}")
    response = requests.get(
        f"{SPOTIFY_TRACK_URL}/{track_id}",
        headers={"Authorization": f"Bearer {spotify_token}"},
    )
    if response.status_code == 200:
        data = response.json()
        album = data.get("album", {}).get("name", "Unknown Album")
        artist = ", ".join(artist["name"] for artist in data.get("artists", []))
        title = data.get("name", "Unknown Track")
        print(f"Fetched details: '{title}' by '{artist}' on album '{album}'.")
        return album, artist, title, track_id
    print(f"Failed to fetch details for track ID: {track_id}. {response.status_code}, {response.text}")
    return None, None, None, None

# Get audio features for a Spotify track
def get_audio_features(spotify_token, track_id):
    print(f"Fetching audio features for track ID: {track_id}")
    response = requests.get(
        f"{SPOTIFY_AUDIO_FEATURES_URL}/{track_id}",
        headers={"Authorization": f"Bearer {spotify_token}"},
    )
    if response.status_code == 200:
        return response.json()
    print(f"Failed to fetch audio features for track ID: {track_id}. {response.status_code}, {response.text}")
    return None

# Search for a single track on Spotify
def search_spotify_track(spotify_token, track_title, artist):
    query = f"track:{track_title} artist:{artist}"
    print(f"Searching for track: '{track_title}' by '{artist}' on Spotify.")
    response = requests.get(
        SPOTIFY_SEARCH_URL,
        headers={"Authorization": f"Bearer {spotify_token}"},
        params={"q": query, "type": "track", "limit": 1},
    )
    if response.status_code != 200:
        print(f"Error searching for track: {response.status_code}, {response.text}")
        return None

    items = response.json().get("tracks", {}).get("items", [])
    if items:
        print(f"Track match found: '{items[0].get('name')}' by '{items[0].get('artists', [{}])[0].get('name')}'.")
    else:
        print("No track match found.")
    return items[0] if items else None

# Enrich Discogs data with Spotify info
def match_discogs_with_spotify(limit: Optional[int] = None):
    # Load Discogs data
    if not os.path.exists(DISCOGS_FILE):
        print(f"Discogs file {DISCOGS_FILE} not found.")
        return

    with open(DISCOGS_FILE, "r", encoding="utf-8") as f:
        discogs_data = json.load(f)

    # Shuffle the releases if enabled
    if SHUFFLE_RELEASES:
        print("Shuffling releases for random order.")
        random.shuffle(discogs_data)

    spotify_token = authenticate_spotify()
    mapping = []

    # Determine limit from environment variable if not set
    if limit is None:
        limit = int(MATCH_LIMIT) if MATCH_LIMIT else None

    for i, release in enumerate(discogs_data):
        if limit and i >= limit:
            break

        release_title = release.get("title", "Unknown Release")
        artist = ", ".join(a["name"] for a in release.get("artists", []))

        print(f"Processing release: '{release_title}' by '{artist}'.")

        # Try to find the album on Spotify
        spotify_album = search_spotify_album(spotify_token, release_title, artist)
        if spotify_album:
            album_id = spotify_album["id"]
            spotify_tracks = get_album_tracks(spotify_token, album_id)

            for track in release.get("tracklist", []):
                discogs_track_id = track.get("id", f"{release.get('id')}-{track['position']}")
                discogs_track_title_normalized = normalize_title(track["title"])
                spotify_track = next((t for t in spotify_tracks if normalize_title(t["name"]) == discogs_track_title_normalized), None)

                if spotify_track:
                    spotify_album, spotify_artist, spotify_title, spotify_track_id = get_spotify_track_details(spotify_token, spotify_track["id"])
                    audio_features = get_audio_features(spotify_token, spotify_track_id)
                    mapping.append({
                        "Discogs Release Title": release_title,
                        "Discogs Track Artist": artist,
                        "Discogs Track Title": track["title"],
                        "Spotify Album": spotify_album,
                        "Spotify Track Artist": spotify_artist,
                        "Spotify Track Title": spotify_title,
                        "Spotify Track ID": spotify_track_id,
                        "Audio Features": audio_features,
                    })
                else:
                    print(f"Track '{track['title']}' not found in album '{release_title}'. Searching individually.")
                    spotify_track = search_spotify_track(spotify_token, track["title"], artist)
                    if spotify_track:
                        spotify_album, spotify_artist, spotify_title, spotify_track_id = get_spotify_track_details(spotify_token, spotify_track["id"])
                        audio_features = get_audio_features(spotify_token, spotify_track_id)
                        mapping.append({
                            "Discogs Release Title": release_title,
                            "Discogs Track Artist": artist,
                            "Discogs Track Title": track["title"],
                            "Spotify Album": spotify_album,
                            "Spotify Track Artist": spotify_artist,
                            "Spotify Track Title": spotify_title,
                            "Spotify Track ID": spotify_track_id,
                            "Audio Features": audio_features,
                        })
                    else:
                        print(f"No match found for track: '{track['title']}' by '{artist}'.")
                        mapping.append({
                            "Discogs Release Title": release_title,
                            "Discogs Track Artist": artist,
                            "Discogs Track Title": track["title"],
                            "Spotify Album": None,
                            "Spotify Track Artist": None,
                            "Spotify Track Title": None,
                            "Spotify Track ID": None,
                            "Audio Features": None,
                        })
        else:
            print(f"No Spotify album found for release: '{release_title}' by '{artist}'. Searching tracks individually.")
            for track in release.get("tracklist", []):
                discogs_track_id = track.get("id", f"{release.get('id')}-{track['position']}")
                discogs_track_title_normalized = normalize_title(track["title"])
                spotify_track = search_spotify_track(spotify_token, track["title"], artist)
                if spotify_track:
                    spotify_album, spotify_artist, spotify_title, spotify_track_id = get_spotify_track_details(spotify_token, spotify_track["id"])
                    audio_features = get_audio_features(spotify_token, spotify_track_id)
                    mapping.append({
                        "Discogs Release Title": release_title,
                        "Discogs Track Artist": artist,
                        "Discogs Track Title": track["title"],
                        "Spotify Album": spotify_album,
                        "Spotify Track Artist": spotify_artist,
                        "Spotify Track Title": spotify_title,
                        "Spotify Track ID": spotify_track_id,
                        "Audio Features": audio_features,
                    })
                else:
                    print(f"No match found for track: '{track['title']}' by '{artist}'.")
                    mapping.append({
                        "Discogs Release Title": release_title,
                        "Discogs Track Artist": artist,
                        "Discogs Track Title": track["title"],
                        "Spotify Album": None,
                        "Spotify Track Artist": None,
                        "Spotify Track Title": None,
                        "Spotify Track ID": None,
                        "Audio Features": None,
                    })

        # Respect API rate limits
        time.sleep(0.1)

    # Save mapping data
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=4, ensure_ascii=False)

    print(f"Saved Discogs-to-Spotify mapping to {MAPPING_FILE}")

if __name__ == "__main__":
    match_discogs_with_spotify()

