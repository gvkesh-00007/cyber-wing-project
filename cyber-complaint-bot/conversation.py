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
                temp_data={}
            )
            self.db.add(state)
            self.db.commit()

        temp = state.temp_data
        step = state.current_step

        # Route based on current step
        if step == "start":
            self.start_conversation(phone, state)
        elif step == "await_category":
            self.collect_category(phone, text, state, temp)
        elif step == "await_name":
            self.collect_name(phone, text, state, temp)
        elif step == "await_address":
            self.collect_address(phone, text, state, temp)
        elif step == "await_phone":
            self.collect_phone(phone, text, state, temp)
        elif step == "await_email":
            self.collect_email(phone, text, state, temp)
        elif step == "await_description":
            self.collect_description(phone, text, state, temp)
        elif step == "await_evidence":
            self.collect_evidence(phone, raw_msg, state, temp)
        elif step == "await_edit_choice":
            self.handle_edit_choice(phone, text, state, temp)
        elif step == "await_edit_field":
            self.handle_edit_field(phone, text, state, temp)

    def start_conversation(self, phone, state):
        # Welcome message and category selection
        buttons = [
            {"type": "reply", "reply": {"id": "cyber_fraud", "title": "Cyber Fraud"}},
            {"type": "reply", "reply": {"id": "identity_theft", "title": "Identity Theft"}},
            {"type": "reply", "reply": {"id": "online_harassment", "title": "Online Harassment"}}
        ]
        self.whatsapp.send_buttons(
            phone,
            "Welcome to Cyber Crime Complaint System. Please select your complaint category:",
            buttons
        )
        state.current_step = "await_category"
        self.db.commit()

    def collect_category(self, phone, text, state, temp):
        # Store category and ask for name
        temp["category"] = text
        state.temp_data = temp
        self.whatsapp.send_text(phone, "Please enter your full name:")
        state.current_step = "await_name"
        self.db.commit()

    def collect_name(self, phone, text, state, temp):
        # Validate and store name
        if not self.validator.validate_name(text):
            self.whatsapp.send_text(phone, "Invalid name. Please enter a valid full name:")
            return
        temp["name"] = text
        state.temp_data = temp
        
        # Check if this is an edit flow - if complaint_id exists, go to review
        if "complaint_id" in temp:
            self.prompt_review(phone, state)
        else:
            self.whatsapp.send_text(phone, "Please enter your address:")
            state.current_step = "await_address"
            self.db.commit()

    def collect_address(self, phone, text, state, temp):
        # Store address and ask for phone
        temp["address"] = text
        state.temp_data = temp
        
        # Check if this is an edit flow
        if "complaint_id" in temp:
            self.prompt_review(phone, state)
        else:
            self.whatsapp.send_text(phone, "Please enter your phone number:")
            state.current_step = "await_phone"
            self.db.commit()

    def collect_phone(self, phone, text, state, temp):
        # Validate and store phone
        if not self.validator.validate_phone(text):
            self.whatsapp.send_text(phone, "Invalid phone number. Please enter a valid phone number:")
            return
        temp["phone"] = text
        state.temp_data = temp
        
        # Check if this is an edit flow
        if "complaint_id" in temp:
            self.prompt_review(phone, state)
        else:
            self.whatsapp.send_text(phone, "Please enter your email address:")
            state.current_step = "await_email"
            self.db.commit()

    def collect_email(self, phone, text, state, temp):
        # Validate and store email
        if not self.validator.validate_email(text):
            self.whatsapp.send_text(phone, "Invalid email. Please enter a valid email address:")
            return
        temp["email"] = text
        state.temp_data = temp
        
        # Check if this is an edit flow
        if "complaint_id" in temp:
            self.prompt_review(phone, state)
        else:
            self.whatsapp.send_text(phone, "Please describe your complaint in detail:")
            state.current_step = "await_description"
            self.db.commit()

    def collect_description(self, phone, text, state, temp):
        # Store description and ask for evidence
        temp["description"] = text
        state.temp_data = temp
        
        # Check if this is an edit flow
        if "complaint_id" in temp:
            self.prompt_review(phone, state)
        else:
            self.whatsapp.send_text(phone, "Please upload any evidence (images, documents). Type 'skip' if you don't have any.")
            state.current_step = "await_evidence"
            self.db.commit()

    def collect_evidence(self, phone, raw_msg, state, temp):
        # Handle evidence upload
        if "image" in raw_msg or "document" in raw_msg:
            # Save media file
            media_url = self.get_media_url(raw_msg)
            if media_url:
                temp["evidence_url"] = media_url
                state.temp_data = temp
        
        # Generate complaint ID if not exists
        if "complaint_id" not in temp:
            temp["complaint_id"] = str(uuid.uuid4())[:8].upper()
            state.temp_data = temp
            
            # Create complaint record
            complaint = Complaint(
                complaint_id=temp["complaint_id"],
                phone_number=phone,
                category=temp.get("category"),
                name=temp.get("name"),
                address=temp.get("address"),
                phone=temp.get("phone"),
                email=temp.get("email"),
                description=temp.get("description"),
                evidence_url=temp.get("evidence_url"),
                status="draft"
            )
            self.db.add(complaint)
            self.db.commit()
        
        # Generate PDF
        pdf_path = self.pdf.generate(temp)
        pdf_url = f"{os.getenv('BASE_URL')}/uploads/{os.path.basename(pdf_path)}"
        temp["pdf_url"] = pdf_url
        state.temp_data = temp
        self.db.commit()
        
        # Send PDF and prompt for review
        self.whatsapp.send_text(phone, f"Your complaint draft has been generated. PDF: {pdf_url}")
        self.prompt_review(phone, state)

    def get_media_url(self, raw_msg):
        # Extract media URL from message
        media_id = None
        if "image" in raw_msg:
            media_id = raw_msg["image"]["id"]
        elif "document" in raw_msg:
            media_id = raw_msg["document"]["id"]
        
        if media_id:
            # Download media from WhatsApp
            headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            response = requests.get(f"https://graph.facebook.com/v17.0/{media_id}", headers=headers)
            if response.status_code == 200:
                return response.json().get("url")
        return None

    def prompt_review(self, phone, state):
        # Prompt user to review and edit
        buttons = [
            {"type": "reply", "reply": {"id": "yes_edit", "title": "Yes"}},
            {"type": "reply", "reply": {"id": "no_edit", "title": "No"}}
        ]
        self.whatsapp.send_buttons(
            phone,
            "Do you want to edit any details before final submission?",
            buttons
        )
        state.current_step = "await_edit_choice"
        self.db.commit()

    def handle_edit_choice(self, phone, text, state, temp):
        # Handle user's choice to edit or finalize
        if text.lower() in ["yes", "yes_edit"]:
            # Ask which field to edit
            options = [
                {"type": "reply", "reply": {"id": "edit_name", "title": "Name"}},
                {"type": "reply", "reply": {"id": "edit_address", "title": "Address"}},
                {"type": "reply", "reply": {"id": "edit_phone", "title": "Phone"}},
                {"type": "reply", "reply": {"id": "edit_email", "title": "Email"}},
                {"type": "reply", "reply": {"id": "edit_description", "title": "Description"}}
            ]
            self.whatsapp.send_buttons(
                phone,
                "Which section do you want to edit?",
                options
            )
            state.current_step = "await_edit_field"
            self.db.commit()
        else:
            # Final submission without SMS
            self.complete_without_sms(phone, state, temp)

    def handle_edit_field(self, phone, text, state, temp):
        # Route to appropriate field collection based on choice
        mapping = {
            "edit_name": ("await_name", "Please enter your corrected full name:"),
            "edit_address": ("await_address", "Please enter your corrected address:"),
            "edit_phone": ("await_phone", "Please enter your corrected phone number:"),
            "edit_email": ("await_email", "Please enter your corrected email address:"),
            "edit_description": ("await_description", "Please enter your corrected description:")
        }
        
        if text in mapping:
            next_step, prompt = mapping[text]
            self.whatsapp.send_text(phone, prompt)
            state.current_step = next_step
            self.db.commit()
        else:
            self.whatsapp.send_text(phone, "Invalid choice. Please select a valid section to edit.")

    def complete_without_sms(self, phone, state, temp):
        # Save final fields to Complaint record and finalize
        complaint = self.db.query(Complaint).filter_by(complaint_id=temp["complaint_id"]).first()
        if complaint:
            # Update all fields from temp data
            for key, value in temp.items():
                if hasattr(complaint, key):
                    setattr(complaint, key, value)
            complaint.status = "submitted"
            self.db.commit()

            # Inform user and end conversation
            self.whatsapp.send_text(
                phone,
                f"Your complaint (ID: {complaint.complaint_id}) has been submitted successfully. Thank you."
            )
            state.current_step = "end"
            self.db.commit()
        else:
            self.whatsapp.send_text(phone, "Error: Complaint not found. Please start again.")
            state.current_step = "start"
            self.db.commit()
