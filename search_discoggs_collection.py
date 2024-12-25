import json
import os

# Load the JSON data
DATA_FILE = "discogs_collection.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file '{DATA_FILE}' not found.")
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Search for a track
def search_track(data, query):
    results = []
    for release in data:
        release_title = release.get("title", "Unknown Release")
        year = release.get("year", "Unknown Year")
        genres = release.get("genres", [])
        styles = release.get("styles", [])
        artists = ", ".join(artist["name"] for artist in release.get("artists", []))
        
        for track in release.get("tracklist", []):
            if query.lower() in track["title"].lower():
                results.append({
                    "track_title": track["title"],
                    "release_title": release_title,
                    "artist": artists,
                    "year": year,
                    "genres": genres,
                    "styles": styles
                })
    return results

# Display search results
def display_results(results):
    if not results:
        print("No tracks found matching your query.")
        return

    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Artist: {result['artist']}")
        print(f"  Track Title: {result['track_title']}")
        print(f"  Release Title: {result['release_title']}")
        print(f"  Year: {result['year']}")
        print(f"  Genre(s): {', '.join(result['genres']) if result['genres'] else 'Unknown'}")
        print(f"  Style(s): {', '.join(result['styles']) if result['styles'] else 'Unknown'}")
        print("-" * 40)

# CLI Main Function
def main():
    print("Welcome to Diggin Search!")
    data = load_data()
    if not data:
        return

    while True:
        query = input("Enter a track title to search (or 'exit' to quit): ").strip()
        if query.lower() == "exit":
            print("Goodbye!")
            break

        results = search_track(data, query)
        display_results(results)

if __name__ == "__main__":
    main()

