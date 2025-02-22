from fastapi import FastAPI, Request, Query
import json
import logging

app = FastAPI()

# Set your verification token (should match the token in Meta Developer Console)
VERIFY_TOKEN = "123456"

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.get("/")
async def verify_webhook(
    hub_mode: str = Query(None),
    hub_challenge: str = Query(None),
    hub_verify_token: str = Query(None)
):
    """Handles Meta Webhook Verification."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)  # Meta expects the raw integer response

    return {"error": "Invalid verification token"}

@app.post("/")
async def receive_message(request: Request):
    """Handles incoming messages from WhatsApp."""
    data = await request.json()
    logging.info(f"Received Webhook Data:\n{json.dumps(data, indent=2)}")

    # Process WhatsApp messages
    if "entry" in data:
        for entry in data["entry"]:
            for change in entry.get("changes", []):
                if "value" in change and "messages" in change["value"]:
                    messages = change["value"]["messages"]
                    for message in messages:
                        sender_id = message["from"]
                        message_text = message["text"]["body"]
                        logging.info(f"New message from {sender_id}: {message_text}")

                        # Process message further (e.g., send a reply)

    return {"status": "received"}
