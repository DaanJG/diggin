import pandas as pd
import json

# Load the mapping data
with open("discogs_spotify_mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(mapping)

# Display the DataFrame
pd.set_option('display.max_rows', None)  # Show all rows
print(df)

# Optionally save to a CSV file for analysis
df.to_csv("discogs_spotify_full_results.csv", index=False)

