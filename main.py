from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
import httpx
import json
import os
import logging

app = FastAPI()

# Load environment variables
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "123456")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN", "your_graph_api_token")
PORT = int(os.getenv("PORT", 8000))

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Handles Meta Webhook Verification."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logging.info("Webhook verified successfully!")
        return hub_challenge  # Must be returned as raw text
    return "Invalid verification token", 403

@app.post("/webhook")
async def receive_message(request: Request):
    """Handles incoming WhatsApp messages from Meta."""
    data = await request.json()
    logging.info(f"Received Webhook Data:\n{json.dumps(data, indent=2)}")

    message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]

    if message and message.get("type") == "text":
        sender_id = message["from"]
        message_text = message["text"]["body"]
        message_id = message["id"]
        
        logging.info(f"New message from {sender_id}: {message_text}")
        
        business_phone_number_id = data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": sender_id,
                    "text": {"body": f"Echo: {message_text}"},
                    "context": {"message_id": message_id},
                },
            )
            logging.info(f"Response from WhatsApp API: {response.text}")

        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                },
            )

    return {"status": "received"}

@app.get("/")
async def root():
    return {"message": "Nothing to see here. Checkout README.md to start."}
