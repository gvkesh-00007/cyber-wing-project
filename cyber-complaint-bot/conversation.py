
# conversation.py
import json
import uuid
from whatsapp_handler import WhatsAppHandler
from database import SessionLocal
from models import Complaint, ConversationState
from pdf_generator import PDFGenerator
from validators import InputValidator

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
        # Continue for each step...
        # E.g., await_address, await_idproof, await_description, await_txncount, etc.

        # Commit state updates
        state.temp_data = json.dumps(temp)
        self.db.commit()

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

    # Define similar methods for address, ID proof (ask for document), description,
    # transaction count, txn IDs, IFSC, timestamp, suspect info, PDF generation, and edit flow.

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
