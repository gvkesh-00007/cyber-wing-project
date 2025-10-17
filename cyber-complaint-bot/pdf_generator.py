# pdf_generator.py (ReportLab)
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

class PDFGenerator:
    def generate(self, complaint):
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        path = os.path.join(uploads_dir, f"{complaint.complaint_id}.pdf")
        c = canvas.Canvas(path, pagesize=LETTER)
        y = 750
        lines = [
            f"Complaint ID: {complaint.complaint_id}",
            f"Name: {complaint.name}",
            f"Phone: {complaint.phone_number}",
            f"Address: {complaint.address}",
            f"Description: {complaint.description}",
            f"Transactions: {complaint.transaction_count}",
            f"Sender TXN ID: {complaint.sender_txn_id}",
            f"Receiver TXN ID: {complaint.receiver_txn_id}",
            f"IFSC: {complaint.ifsc}",
            f"Timestamp: {complaint.timestamp_evidence}",
            f"Suspect Name: {getattr(complaint, 'suspect_name', '')}",
        ]
        for line in lines:
            c.drawString(72, y, line or "")
            y -= 16
        c.showPage()
        c.save()
        return path
