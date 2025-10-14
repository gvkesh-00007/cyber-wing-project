# pdf_generator.py
import os
import uuid
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

class PDFGenerator:
    def __init__(self):
        # Set up Jinja2 environment
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate(self, complaint):
        """
        Render HTML template with complaint data and output a PDF file.
        Returns the local file path.
        """
        template = self.env.get_template("complaint_template.html")
        html_content = template.render(complaint=complaint)

        # Ensure uploads directory exists
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        # Unique filename
        filename = f"{complaint.complaint_id}.pdf"
        output_path = os.path.join(uploads_dir, filename)

        # Generate PDF
        HTML(string=html_content).write_pdf(output_path)
        return output_path
