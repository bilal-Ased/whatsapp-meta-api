import httpx
import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

# Load environment variables
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "123456")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN", "EAAPscODv25cBO9wHI2sB0XnMh15iln7W4hWzPwY3GozzzHMytsjTKp7o9ZAuVDVf3hZCuXNLt7WVlv5RNCYoSHnw8UFu1AYPISwpD36lBPhHjROrX3h6OSolrbWd9PAyOWqt2LYrAoZBFXnzY8Qh3NH1op6j46bNtjYjUAH3gqaMrx8RZCWOpDh2NZC87r2ZBpjAZDZD")

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.post("/webhook")
async def receive_message(request: Request):
    """Handles incoming WhatsApp messages from Meta."""
    try:
        data = await request.json()
        logging.info(f"📩 Received Webhook Data:\n{json.dumps(data, indent=2)}")

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

                        # Log full API response
                        logging.info(f"🚀 Meta API Response: {response.status_code}")
                        logging.info(f"📄 Response Body: {response.text}")

        return {"status": "received"}

    except Exception as e:
        logging.error(f"❌ Error processing webhook: {str(e)}")
        return {"error": "Webhook processing failed"}, 500
