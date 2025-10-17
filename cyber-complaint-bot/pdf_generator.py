# pdf_generator.py
import os

class PDFGenerator:
    def __init__(self):
        self._ready = False
        self._err = None
        self._use_fallback = False
        
        # Try to import WeasyPrint dependencies
        try:
            from jinja2 import Environment, FileSystemLoader
            from weasyprint import HTML
            self.os = os
            self.Environment = Environment
            self.FileSystemLoader = FileSystemLoader
            self.HTML = HTML
            self._ready = True
        except Exception as e:
            self._err = e
            # Try fallback to ReportLab
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import LETTER
                self.canvas = canvas
                self.LETTER = LETTER
                self._use_fallback = True
                self._ready = True
            except Exception as fallback_err:
                self._err = f"WeasyPrint error: {e}\nReportLab fallback error: {fallback_err}"

    def generate(self, complaint):
        """
        Render HTML template with complaint data and output a PDF file.
        Falls back to ReportLab if WeasyPrint is unavailable.
        Returns the local file path.
        """
        if not self._ready:
            raise RuntimeError(
                f"PDF generation not available on this system. "
                f"Install WeasyPrint dependencies (GTK/Pango/Cairo on Windows) "
                f"or ReportLab for fallback support.\n\nError details: {self._err}"
            )
        
        # Ensure uploads directory exists
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Unique filename
        filename = f"{complaint.complaint_id}.pdf"
        output_path = os.path.join(uploads_dir, filename)
        
        if self._use_fallback:
            # Use ReportLab fallback
            return self._generate_with_reportlab(complaint, output_path)
        else:
            # Use WeasyPrint with HTML template
            return self._generate_with_weasyprint(complaint, output_path)
    
    def _generate_with_weasyprint(self, complaint, output_path):
        """Generate PDF using WeasyPrint with HTML template."""
        templates_dir = self.os.path.join(self.os.path.dirname(__file__), "templates")
        env = self.Environment(loader=self.FileSystemLoader(templates_dir))
        template = env.get_template("complaint_template.html")
        html_content = template.render(complaint=complaint)
        self.HTML(string=html_content).write_pdf(output_path)
        return output_path
    
    def _generate_with_reportlab(self, complaint, output_path):
        """Generate PDF using ReportLab fallback (simple text-based PDF)."""
        c = self.canvas.Canvas(output_path, pagesize=self.LETTER)
        width, height = self.LETTER
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - 72, "Cyber Crime Complaint Report")
        
        # Complaint details
        c.setFont("Helvetica", 11)
        y = height - 120
        line_height = 20
        
        fields = [
            ("Complaint ID:", complaint.complaint_id),
            ("Name:", complaint.name),
            ("Phone Number:", complaint.phone_number),
            ("Email:", complaint.email),
            ("Address:", complaint.address),
            ("Transaction ID:", complaint.transaction_id),
            ("Amount Lost:", f"₹{complaint.amount_lost}"),
            ("Account Number:", complaint.account_number),
            ("IFSC Code:", complaint.ifsc),
            ("Bank Name:", complaint.bank_name),
            ("Incident Date:", complaint.incident_date),
            ("Timestamp:", complaint.timestamp_evidence),
        ]
        
        for label, value in fields:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(72, y, label)
            c.setFont("Helvetica", 11)
            c.drawString(200, y, str(value))
            y -= line_height
            
            # New page if needed
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 72
        
        # Description section
        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(72, y, "Incident Description:")
        y -= line_height
        
        # Wrap description text
        c.setFont("Helvetica", 10)
        description = complaint.description
        max_width = width - 144  # margins
        words = description.split()
        line = ""
        
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, "Helvetica", 10) < max_width:
                line = test_line
            else:
                c.drawString(72, y, line.strip())
                y -= 15
                line = word + " "
                
                if y < 72:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - 72
        
        if line:
            c.drawString(72, y, line.strip())
        
        # Footer note
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(72, 50, "Note: This PDF was generated using fallback mode (ReportLab). Install WeasyPrint for enhanced formatting.")
        
        c.showPage()
        c.save()
        return output_path
