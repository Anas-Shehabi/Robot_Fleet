# #
# # import requests
# # import json
# #
# # # Odoo API Endpoint
# # ODOO_URL = 'http://localhost:8069/api/robot/update'  # Replace with your Odoo URL
# #
# # # Data to send (JSON payload)
# # data = {
# #     'name': 'Volvo Robot VV001',  # Robot name (must exist in Odoo)
# #     'status': 'active',     # New status (e.g., 'active', 'idle', 'charging')
# #     'location_id': 6 ,       # Odoo location ID (must exist in Odoo)
# #     'task_ref' : 'TSK00047',
# #     'task_status' : 'in_progress',  # New State(e.g.,'new','in_progress','done')
# #
# # }
# #
# # # Headers for JSON request
# # headers = {
# #     'Content-Type': 'application/json',
# #     'Accept': 'application/json'
# # }
# #
# # try:
# #     # Send POST request to Odoo
# #     response = requests.post(
# #         ODOO_URL,
# #         headers=headers,
# #         json=data  # Automatically converts dict to JSON
# #     )
# #
# #     # Print response details
# #     print("Status Code:", response.status_code)  # Should be 200 (success)
# #     print("Response:", response.json())  # Odoo's JSON response
# #
# # except requests.exceptions.RequestException as e:
# #     print("Request failed:", str(e))  # Network/connection error
# # except json.JSONDecodeError as e:
# #     print("Failed to decode JSON response:", str(e))  # Invalid JSON response
# # except Exception as e:
# #     print("Unexpected error:", str(e))  # Other errors'
# import json
# from flask import Flask, request, jsonify
#
# app = Flask(__name__)
#
# # -------------------------
# # Endpoint that receives task from Odoo
# # -------------------------
# @app.post("/receive_task")
# def receive_task():
#     data = request.json
#     print("\n=== NEW TASK RECEIVED FROM ODOO ===")
#     print(json.dumps(data, indent=4))
#     print("====================================\n")
#
#     return jsonify({
#         "status": "ok",
#         "message": "Task received successfully"
#     })
#
# @app.get("/")
# def home():
#     return "Robot is running"
# # -------------------------
# # Run the robot server
# # -------------------------
# def start_server():
#     print("Robot server is running at: http://127.0.0.1:5005")
#     print("Waiting for Odoo to send tasks...\n")
#     app.run(host="0.0.0.0", port=5005)
#
# if __name__ == "__main__":
#     try:
#         start_server()
#     except KeyboardInterrupt:
#         pass
#
#     input("Press ENTER to exit robot server...")

import json
import sys
import time

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Odoo base URL for retrieving task details
ODOO_TASK_URL = "http://127.0.0.1:8069/v1/task"


# -------------------------
# Endpoint that receives task from Odoo
# -------------------------
@app.post("/receive_task")
def receive_task():
    data = request.json

    print("\n=== 📥 NEW TASK RECEIVED FROM ODOO ===")
    print(json.dumps(data, indent=4))
    print("====================================\n")

    # Extract task_id
    task_id = data.get("task_id")
    task_ref = data.get("task_ref")

    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400

    print(f"➡ Fetching full task details from Odoo for Task ID: {task_id} ...")

    # -----------------------------------------
    # STEP 2: CALL ODOO TO GET FULL TASK DETAILS
    # -----------------------------------------
    try:
        url = f"{ODOO_TASK_URL}/{task_id}"
        response = requests.get(url)

        if response.status_code != 200:
            print("Failed to fetch full task data:", response.text)
            return jsonify({
                "status": "failed",
                "message": "Could not fetch task details from Odoo"
            }), 500

        task_details = response.json()

        print("\n=== 📦 FULL TASK DATA FROM ODOO ===")
        print(json.dumps(task_details, indent=4))
        print("====================================\n")

        print("🤖 Executing task...\n")

        total_steps = 25
        for step in range(total_steps + 1):
            percent = int((step / total_steps) * 100)
            bar = "█" * step + "-" * (total_steps - step)

            # Print progress on the same line
            sys.stdout.write(f"\r[{bar}] {percent}%")
            sys.stdout.flush()

            time.sleep(1)  # Adjust speed of progress

        print("\n\n✅ Task execution complete!\n")

        return jsonify({
            "status": "ok",
            "message": "Task received and fetched successfully",
            "task_details": task_details
        }), 200

    except Exception as e:
        print(f"❌ Error connecting to Odoo: {str(e)}")
        return jsonify({"error": "Robot internal error"}), 500


# -------------------------
# Simple Home Route
# -------------------------
@app.get("/")
def home():
    return "Robot is running"


# -------------------------
# Run the robot server
# -------------------------
def start_server():
    print("Robot server is running at: http://127.0.0.1:5005")
    print("Waiting for Odoo to send tasks...\n")
    app.run(host="0.0.0.0", port=5005)


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        pass

    input("Press ENTER to exit robot server...")
