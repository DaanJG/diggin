import json

# Load mapping data
with open("discogs_spotify_mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

# Initialize counters
total_tracks = 0
matched_tracks = 0

# Count total and matched tracks
for entry in mapping:
    total_tracks += 1
    if entry.get("Spotify Track Title"):  # Check if a match was found
        matched_tracks += 1

# Calculate match percentage
match_percentage = (matched_tracks / total_tracks) * 100 if total_tracks > 0 else 0

# Display results
print(f"Total tracks searched: {total_tracks}")
print(f"Matched tracks: {matched_tracks}")
print(f"Match percentage: {match_percentage:.2f}%")

