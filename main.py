from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import logging
import httpx
import os

app = FastAPI()

# Load environment variables
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "123456")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN", "YOUR_ACCESS_TOKEN_HERE")

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    """Handles Meta Webhook Verification."""
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logging.info("✅ Webhook verified successfully!")
        return JSONResponse(content=hub_challenge)
    return JSONResponse(content={"error": "Invalid verification token"}, status_code=403)

@app.post("/webhook")
async def receive_message(request: Request):
    """Handles incoming WhatsApp messages."""
    try:
        data = await request.json()
        logging.info(f"📩 Received Webhook Data:\n{json.dumps(data, indent=2)}")

        # Extract message details
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            for message in messages:
                sender_id = message.get("from", "Unknown")
                message_text = message.get("text", {}).get("body", "No text")
                message_id = message.get("id", "")

                logging.info(f"📨 New message from {sender_id}: {message_text}")

                # Extract business phone number ID
                business_phone_number_id = value.get("metadata", {}).get("phone_number_id")

                if business_phone_number_id:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                            headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
                            json={
                                "messaging_product": "whatsapp",
                                "to": sender_id,
                                "text": {"body": f"Echo: {message_text}"},
                                "context": {"message_id": message_id},
                            },
                        )

        return JSONResponse(content={"status": "received"}, status_code=200)

    except Exception as e:
        logging.error(f"❌ Error processing webhook: {str(e)}")
        return JSONResponse(content={"error": "Webhook processing failed"}, status_code=500)
