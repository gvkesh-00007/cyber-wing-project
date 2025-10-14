# conversation.py
import json
import uuid
import requests
import os
from whatsapp_handler import WhatsAppHandler
from database import SessionLocal
from models import Complaint, ConversationState
from pdf_generator import PDFGenerator
from validators import InputValidator
from config import WHATSAPP_TOKEN

class ConversationManager:
    def __init__(self):
        self.whatsapp = WhatsAppHandler()
        self.db = SessionLocal()
        self.pdf = PDFGenerator()
        self.validator = InputValidator()

    def handle_incoming(self, data):
        # Process each message event
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                if "messages" in change["value"]:
                    msg = change["value"]["messages"][0]
                    from_number = msg["from"]
                    text = msg.get("text", {}).get("body")
                    self.process_message(from_number, text, msg)

    def process_message(self, phone, text, raw_msg):
        # Retrieve or create conversation state
        state = self.db.query(ConversationState).get(phone)
        if not state:
            state = ConversationState(
                phone_number=phone,
                current_step="start",
                temp_data="{}"
            )
            self.db.add(state)
            self.db.commit()
        
        # Load temp data
        temp = json.loads(state.temp_data)
        
        # Handle file attachments (document or image)
        if raw_msg.get("type") in ["document", "image"]:
            media_id = raw_msg[raw_msg["type"]]["id"]
            media_url = self.get_media_url(media_id)
            file_path = self.download_media(media_url, temp.get("complaint_id", "temp"))
            temp["id_proof"] = file_path
            self.whatsapp.send_text(phone, "Thank you for uploading your ID proof. Please continue...")
        
        # Route based on current_step
        step = state.current_step
        if step == "start":
            self.ask_money_loss(phone, state)
        elif step == "await_money_loss":
            self.handle_money_loss(phone, text, state, temp)
        elif step == "await_name":
            self.collect_name(phone, text, state, temp)
        elif step == "await_phone":
            self.collect_phone(phone, text, state, temp)
        elif step == "await_address":
            self.collect_address(phone, text, state, temp)
        elif step == "await_idproof":
            self.collect_id_proof(phone, text, state, temp)
        elif step == "await_description":
            self.collect_description(phone, text, state, temp)
        elif step == "await_txncount":
            self.collect_transaction_count(phone, text, state, temp)
        # Add more steps as needed...
        
        # Commit state updates
        state.temp_data = json.dumps(temp)
        self.db.commit()

    def get_media_url(self, media_id):
        """Get media URL from WhatsApp API"""
        url = f"https://graph.facebook.com/v16.0/{media_id}"
        params = {"access_token": WHATSAPP_TOKEN}
        res = requests.get(url, params=params).json()
        return res.get("url")

    def download_media(self, url, complaint_id):
        """Download media file and save to uploads directory"""
        res = requests.get(url, headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"})
        ext = res.headers.get("Content-Type", "application/octet-stream").split("/")[-1]
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, f"{complaint_id}_proof.{ext}")
        with open(file_path, "wb") as f:
            f.write(res.content)
        return file_path

    # Step implementations:
    def ask_money_loss(self, phone, state):
        buttons = [
            {"type": "reply", "reply": {"id": "yes", "title": "Yes"}},
            {"type": "reply", "reply": {"id": "no", "title": "No"}}
        ]
        self.whatsapp.send_buttons(phone, "Hello! Did you suffer a money loss case?", buttons)
        state.current_step = "await_money_loss"

    def handle_money_loss(self, phone, text, state, temp):
        if text.lower() == "yes":
            # Initialize new Complaint
            complaint = Complaint(
                complaint_id=str(uuid.uuid4()),
                phone_number=phone,
                status="pending"
            )
            self.db.add(complaint)
            self.db.commit()
            temp["complaint_id"] = complaint.complaint_id
            self.whatsapp.send_text(phone, "Please enter your full name:")
            state.current_step = "await_name"
        else:
            # Redirect to NCRP for tracking
            self.whatsapp.send_text(
                phone,
                "To track an existing complaint, please visit: https://cybercrime.gov.in"
            )
            state.current_step = "end"

    def collect_name(self, phone, text, state, temp):
        if self.validator.validate_name(text):
            temp["name"] = text
            self.whatsapp.send_text(phone, "Enter your registered phone number:")
            state.current_step = "await_phone"
        else:
            self.whatsapp.send_text(phone, "Invalid name format. Please enter alphabetic characters only:")

    def collect_phone(self, phone, text, state, temp):
        if self.validator.validate_phone(text):
            temp["user_phone"] = text
            self.whatsapp.send_text(phone, "Enter your address:")
            state.current_step = "await_address"
        else:
            self.whatsapp.send_text(phone, "Invalid phone number. Please enter digits only (10–15 chars):")

    def collect_address(self, phone, text, state, temp):
        temp["address"] = text
        self.whatsapp.send_text(phone, "Please upload your ID proof (document or image):")
        state.current_step = "await_idproof"

    def collect_id_proof(self, phone, text, state, temp):
        # This method handles text response while file attachment is handled in process_message
        if "id_proof" in temp:
            self.whatsapp.send_text(phone, "Please describe the incident:")
            state.current_step = "await_description"
        else:
            self.whatsapp.send_text(phone, "Please upload your ID proof as a document or image.")

    def collect_description(self, phone, text, state, temp):
        temp["description"] = text
        self.whatsapp.send_text(phone, "How many transactions were involved?")
        state.current_step = "await_txncount"

    def collect_transaction_count(self, phone, text, state, temp):
        if text.isdigit():
            temp["transaction_count"] = int(text)
            # Move to final step for this example
            self.finalize_complaint(phone, state, temp)
        else:
            self.whatsapp.send_text(phone, "Please enter a valid number of transactions:")

    # At final step:
    def finalize_complaint(self, phone, state, temp):
        # Load complaint, update fields from temp, generate PDF, and send back
        complaint = (
            self.db.query(Complaint)
            .filter_by(complaint_id=temp["complaint_id"])
            .first()
        )
        for key, value in temp.items():
            if hasattr(complaint, key):
                setattr(complaint, key, value)
        self.db.commit()
        
        pdf_path = self.pdf.generate(complaint)
        # Upload pdf_path to a public URL or serve via ngrok tunnel
        public_link = f"https://<your-ngrok-id>.ngrok.io/uploads/{complaint.complaint_id}.pdf"
        self.whatsapp.send_document(phone, public_link, "ComplaintReport.pdf", "Here is your complaint PDF.")
        self.whatsapp.send_text(phone, f"Your complaint ID is {complaint.complaint_id}. We will send SMS confirmation shortly.")
        state.current_step = "end"
