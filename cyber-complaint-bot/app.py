
# app.py
import os
from flask import Flask, request, jsonify
from config import VERIFY_TOKEN
from conversation import ConversationManager

app = Flask(__name__)
conv_manager = ConversationManager()

@app.route('/webhook', methods=['GET'])
def verify():
    """
    Verification endpoint for WhatsApp webhook setup.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        # Respond with the challenge token from the request
        return challenge, 200
    return 'Verification token mismatch', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handles incoming webhook events from WhatsApp.
    """
    data = request.get_json()
    # Pass data to the conversation manager for processing
    conv_manager.handle_incoming(data)
    return jsonify(status='received'), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
