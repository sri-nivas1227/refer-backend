from flask import jsonify, request
from application import app
import os
from dotenv import load_dotenv
import re
from application.service.join import send, verify
from application.service.user import create_user

load_dotenv()


@app.route("/")
def index():
    return "Hello world! the app is running"


@app.route("/api/v1/signup/send", methods=["POST"])
def send_otp():
    data = request.json
    phone = data["phone"]
    phone_pattern = re.compile(r"^\+\d{2}\d{10}$")
    if not phone_pattern.match(phone):
        # add logs
        data = {"phone": phone, "message": "invalid phone number", "status": "error"}
        return jsonify(data), 400
    status = send(phone)
    if not status:
        # add logs
        data = {"status": "error", "message": "error sending otp"}
        return jsonify(data), 500
    # add logs
    data = {"phone": phone, "message": "success sending otp", "status": "success"}
    return jsonify(data), 200


@app.route("/api/v1/signup/verify", methods=["POST"])
def verify_otp():
    data = request.json
    otp = data["otp"]
    phone = data["phone"]
    verify_status = verify(phone, otp)
    if not verify_status:
        # add logs
        data = {"message": "error verifying otp", "status": "error"}
        return jsonify(data), 500
    if verify_status["status"] == "canceled":
        data = {"phone": phone, "message": "max tries exceeded", "status": "error"}
        return jsonify(data), 400
    elif verify_status["status"] == "pending":
        # add logs
        data = {"phone": phone, "message": "wrong otp", "status": "error"}
        return jsonify(data), 400
    elif verify_status["status"] == "approved":
        # add logs
        data = {"phone": phone, "message": "OTP verified", "status": "success"}
        return jsonify(data), 200


@app.route("/api/v1/users/user", methods=["POST"])
def update_user():
    data = request.json
    res = create_user(data)
    if res["status"] == "success":
        # add logs
        return jsonify(res), 200
    else:
        # add logs
        return jsonify(res), 400
