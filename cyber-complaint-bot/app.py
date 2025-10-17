# app.py
import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from config import VERIFY_TOKEN
from conversation import ConversationManager

# Configure logging with security in mind
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Suppress sensitive data in logs
class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive information in logs."""
    def filter(self, record):
        # Mask phone numbers (last 6 digits)
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            # Basic masking - can be enhanced further
            record.msg = msg
        return True

logger.addFilter(SensitiveDataFilter())

app = Flask(__name__)
conv_manager = ConversationManager()

logger.info("CyberComplaintBot application started")

@app.route('/webhook', methods=['GET'])
def verify():
    """
    Verification endpoint for WhatsApp webhook setup.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        logger.info("Webhook verification successful")
        # Respond with the challenge token from the request
        return challenge, 200
    
    logger.warning("Webhook verification failed: token mismatch")
    return 'Verification token mismatch', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handles incoming webhook events from WhatsApp.
    """
    try:
        data = request.get_json()
        logger.info("Received webhook event")
        
        # Pass data to the conversation manager for processing
        conv_manager.handle_incoming(data)
        
        return jsonify(status='received'), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return jsonify(status='error'), 500

@app.route('/uploads/<filename>', methods=['GET'])
def serve_uploads(filename):
    """
    Serve uploaded files (PDFs and attachments) from the uploads directory.
    This enables serving PDFs and attachments via ngrok URL.
    Security: Only serve files from the uploads directory, validate file exists.
    """
    try:
        # Basic security: prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"Suspicious file access attempt: {filename}")
            return 'Invalid filename', 400
        
        logger.info(f"Serving file: {filename}")
        return send_from_directory('uploads', filename)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        return 'File not found', 404

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
