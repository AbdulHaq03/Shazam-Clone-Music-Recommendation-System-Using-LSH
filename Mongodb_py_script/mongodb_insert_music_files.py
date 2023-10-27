import os
import pymongo
from mutagen.easyid3 import EasyID3

# Establish a connection to your MongoDB instance
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Music_Database"]
collection = db["All_mp3"]

# Define a function to extract the metadata from a music file
def get_metadata(file_path):
    metadata = EasyID3(file_path)
    metaData = {"title": metadata.get("title", [""])[0],
        "artist": metadata.get("artist", [""])[0],
        "album": metadata.get("album", [""])[0],
        "year": metadata.get("date", [""])[0][:4]
        }
    return metaData;

# Loop over your music files and insert them into MongoDB
for root, dirs, files in os.walk("C:/Users/ahaqu/OneDrive/Desktop/ML BASED SE PROJECT/Data"):
    for file_name in files:
        if file_name.endswith(".mp3"):
            file_path = os.path.join(root, file_name)
            metadata = get_metadata(file_path)
            with open(file_path, "rb") as f:
                file_data = f.read()
            collection.insert_one({
                "file_path": file_path,
                "file_name": file_name,
                **metadata, ## HERE I USED ** TO UNPACK DICTIONARY OF META DATA INTO KEY VALUE PAIRS
                "data": file_data
            })
