import string
import random
from application.database import with_db
import os
from dotenv import load_dotenv

from pymongo import MongoClient

load_dotenv()
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("MONGO_DB")]
users = db[os.getenv("MONGO_USER_COLLECTION")]
codes = db[os.getenv("MONGO_CODE_COLLECTION")]

# db = with_db.get_db()


# the user data should have
# Name
# Email
# Phone
# Referral Code
#  Referred_by code
# score


def create_user(data):
    users.create_index("phone", unique=True)
    users.create_index("referral_code", unique=True)
    name = data["name"]
    email = data["email"]
    phone = data["phone"]
    referred_by = data["referred_by"]
    if referred_by == "Null":
        referred_by = ""
    referral_code = generate_referral_code()
    score = 0
    user = {
        "name": name,
        "email": email,
        "phone": phone,
        "referral_code": referral_code,
        "referred_by": referred_by,
        "score": score,
    }

    db_update = users.insert_one(user)
    if not db_update:
        return {"status": "error"}
    if db_update.acknowledged:
        response = {
            "status": "success",
            "name": name.title(),
            "referral_code": referral_code,
            "referred_by": "",
        }
        if referred_by != "":
            referee = users.find_one({"referral_code": referred_by})
            referee_score = int(referee["score"])
            referee_score += 1
            users.update_one(
                {"_id": referee["_id"]}, {"$set": {"score": referee_score}}
            )
            response["referred_by"] = referee["name"].title()
        return response
    else:
        return {"status": "error"}


def generate_referral_code(length=6):
    letters = string.ascii_uppercase + string.digits
    code = "".join(random.choices(letters, k=length))
    try:
        codes_list = codes.find({})
        codes = [code["_id"] for code in codes_list]
        if code not in codes:
            return code
        else:
            generate_referral_code()
    except:
        return code
