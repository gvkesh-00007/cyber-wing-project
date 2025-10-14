# whatsapp_handler.py
import requests
from config import WHATSAPP_TOKEN, PHONE_NUMBER_ID

class WhatsAppHandler:
    def __init__(self):
        # Base URL for WhatsApp Cloud API
        self.base_url = f"https://graph.facebook.com/v16.0/{PHONE_NUMBER_ID}/messages"
        # Authorization header
        self.headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }

    def send_text(self, to: str, body: str) -> dict:
        """
        Send a simple text message.
        :param to: Recipient phone number in international format (e.g., '919876543210')
        :param body: Text content of the message
        :return: JSON response from the API
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body}
        }
        response = requests.post(self.base_url, headers=self.headers, json=payload)
        return response.json()

    def send_buttons(self, to: str, body: str, buttons: list) -> dict:
        """
        Send an interactive message with up to three buttons.
        :param to: Recipient phone number
        :param body: Body text above buttons
        :param buttons: List of dicts with keys 'type', 'title', and 'id'
        :return: JSON response
        Example button:
            {"type": "reply", "reply": {"id": "yes_btn", "title": "Yes"}}
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {"buttons": buttons}
            }
        }
        response = requests.post(self.base_url, headers=self.headers, json=payload)
        return response.json()

    def send_document(self, to: str, link: str, filename: str, caption: str = "") -> dict:
        """
        Send a document (e.g., PDF) hosted at a public URL.
        :param to: Recipient phone number
        :param link: Publicly accessible URL of the document
        :param filename: Name shown in WhatsApp
        :param caption: Optional caption text
        :return: JSON response
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": link,
                "filename": filename,
                "caption": caption
            }
        }
        response = requests.post(self.base_url, headers=self.headers, json=payload)
        return response.json()
