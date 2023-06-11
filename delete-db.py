from application.database.with_db import get_db
import os
from dotenv import load_dotenv

# import pymongo

load_dotenv()
db = get_db()
codes_collection = db[os.getenv("MONGO_CODE_COLLECTION")]

codes_cursor = codes_collection.find({})
# get _id values into a list
codes = [code["_id"] for code in codes_cursor]

print(codes)