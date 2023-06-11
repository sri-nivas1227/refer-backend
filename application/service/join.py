from twilio.rest import Client
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("MONGO_DB")]
pending_user_collection = db["pending"]

# vid_cache = Redis(os.getenv("REDIS_HOST"), os.getenv("REDIS_PORT"), db=0)

try:
    twilio_client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
    )
except Exception as e:
    print(e)
    print("unable to create twilio client")


def send(phone):
    try:
        resend_data = pending_user_collection.find_one({"_id": phone})
        if resend_data is not None:
            vsid = resend_data["verification_details"]["vsid"]
            (
                twilio_client.verify.v2.services(os.getenv("TWILIO_VERIFY_SERVICE_SID"))
                .verifications(vsid)
                .update(status="canceled")
            )
            pending_user_collection.delete_one({"_id": phone})
        verification = twilio_client.verify.v2.services(
            os.getenv("TWILIO_VERIFY_SERVICE_SID")
        ).verifications.create(to=phone, channel="sms")
        if verification.status == "pending":
            map_value = {
                "status": verification.status,
                "tries": 0,
                "vsid": verification.sid,
                "time_of_request": str(verification.date_created),
            }
            pending_user_collection.insert_one(
                {"_id": phone, "verification_details": map_value}
            )
            # add logs
            return True
        # add logs
        return False
    except Exception as e:
        print(e)
        # add logs
        print("unable to send sms")
        return False


def verify(phone, otp):
    try:
        # Check the number of tries made to verify the otp
        tries = int(
            pending_user_collection.find_one({"_id": phone})["verification_details"][
                "tries"
            ]
        )
        if tries >= 3:
            vsid = pending_user_collection.find_one({"_id": phone})[
                "verification_details"
            ]["vsid"]
            expire_verification = (
                twilio_client.verify.v2.services(os.getenv("TWILIO_VERIFY_SERVICE_SID"))
                .verifications(vsid)
                .update(status="canceled")
            )
            # logger.info("Multiple wrong otp submissions")
            pending_user_collection.delete_one({"_id": phone})
            return {"status": "canceled", "message": "max tries exceeded"}
        verification_check = twilio_client.verify.v2.services(
            os.getenv("TWILIO_VERIFY_SERVICE_SID")
        ).verification_checks.create(to=phone, code=otp)

        # OTP  is verified
        if verification_check.status == "approved":
            pending_user_collection.delete_one({"_id": phone})
            return {"status": "approved", "message": "OTP verified successfully"}
        elif verification_check.status == "pending":
            pending_user_collection.update_one(
                {"_id": phone}, {"$set": {"verification_details.tries": tries + 1}}
            )
            # logger.info("wrong OTP")
            return {
                "status": "pending",
                "message": "wrong OTP",
            }
    except Exception as e:
        # add logs
        print("unable to verify the OTP", e)
        return False
