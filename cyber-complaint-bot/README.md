# CyberComplaintBot - WhatsApp Cyber Crime Complaint System

A fully local WhatsApp chatbot for filing cyber crime complaints with integrated PDF generation and secure data storage.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Testing](#testing)
- [Security](#security)
- [Deployment](#deployment)
- [Maintenance](#maintenance)
- [Future Scaling](#future-scaling)

## Features

- **WhatsApp Integration**: Seamless conversation flow via WhatsApp Business API
- **Interactive Complaint Filing**: Step-by-step guided complaint submission
- **PDF Generation**: Professional complaint reports with HTML templates
- **Edit/Review Flow**: Users can review and edit information before submission
- **File Upload Support**: Attach evidence (screenshots, documents)
- **Local Data Storage**: SQLite database - all data stays on your machine
- **Secure**: Input validation, sanitization, and logging with sensitive data masking

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows OS (for backup script) or adapt for Linux/Mac
- WhatsApp Business API credentials
- ngrok (for development webhook tunneling)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/gvkesh-00007/cyber-wing-project.git
   cd cyber-wing-project/cyber-complaint-bot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   
   **Windows:**
   ```bash
   .\venv\Scripts\activate
   ```
   
   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create a `.env` file in the project root (already included, update with your credentials):
   ```env
   WHATSAPP_TOKEN=your_whatsapp_api_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
   VERIFY_TOKEN=your_verify_token
   PORT=3000
   ```
   
   **⚠️ IMPORTANT**: Never commit `.env` to version control! It's already in `.gitignore`.

6. **Initialize database**
   ```bash
   python init_db.py
   ```

## Testing

### Unit and Integration Tests

The project includes comprehensive tests using `pytest`.

**Run all tests:**
```bash
pytest tests/ -v
```

**Run with coverage:**
```bash
pytest tests/ -v --cov=. --cov-report=html
```

**Test files included:**
- `tests/test_conversation.py`: Tests for conversation flow, state management, validation

**Test coverage includes:**
- Valid/invalid user inputs (name, phone, email, IFSC code)
- State transitions in ConversationManager
- PDF generation verification
- Money loss redirect flow
- Input validation functions

### Manual End-to-End Testing

Follow these steps to test the complete bot workflow:

1. **Activate virtual environment** (if not already active)
   ```bash
   .\venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   ```

2. **Start Flask application**
   ```bash
   python app.py
   ```
   
   You should see:
   ```
   * Running on http://0.0.0.0:3000
   ```

3. **Start ngrok tunnel** (in a new terminal)
   ```bash
   ngrok http 3000
   ```
   
   Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`)

4. **Configure Meta webhook**
   - Go to Meta Developer Dashboard
   - Navigate to your WhatsApp app
   - Set webhook URL: `https://abc123.ngrok.io/webhook`
   - Set verify token (same as in `.env`)
   - Subscribe to messages

5. **Test on WhatsApp**
   - Send "Hello" to your WhatsApp Business number
   - Bot responds with welcome and "Yes/No" buttons
   - Select "Yes" to start filing complaint
   - Follow prompts:
     - Enter name
     - Enter phone number
     - Enter email
     - Enter transaction ID
     - Enter amount lost
     - Enter account number
     - Enter IFSC code
     - Enter bank name
     - Enter incident date
     - Describe incident
     - Upload evidence (optional)
   - Review and edit if needed
   - Confirm to generate PDF

6. **Verify logs and debugging**
   - Check console output for incoming messages
   - Check `bot.log` for detailed logging
   - Verify database entries: open `complaints.db` with SQLite browser
   - Check `uploads/` for uploaded files
   - Verify PDF generation in `uploads/`

## Security

### Security Best Practices Implemented

#### 1. Input Sanitization
- **SQLAlchemy ORM**: All database queries use prepared statements to prevent SQL injection
- **Strict validation**: Name, phone, email, IFSC, account numbers validated before storage
- **File type restrictions**: Only PDF, JPG, JPEG, PNG allowed for uploads
- **Directory traversal prevention**: File serving validates filenames to prevent `../` attacks

#### 2. Sensitive Data Protection
- **Environment variables**: All credentials stored in `.env` (excluded from Git)
- **Logging filter**: Sensitive data masked in log files
- **No raw data logging**: User inputs are not logged in plain text

#### 3. Secure File Handling
- **Restricted upload types**: Validated by extension and MIME type
- **Unpredictable filenames**: Files saved with complaint ID prefix to prevent guessing
- **Isolated storage**: Uploads stored in dedicated directory

#### 4. HTTPS Enforcement
- **Development**: ngrok provides HTTPS tunneling
- **Production**: Use SSL/TLS certificates (Let's Encrypt, etc.)

### Security Checklist

- [x] `.env` file excluded from version control
- [x] Input validation on all user inputs
- [x] SQLAlchemy prepared statements for DB queries
- [x] Logging with sensitive data masking
- [x] File upload type and content validation
- [x] Directory traversal prevention
- [x] HTTPS for webhook endpoints

## Deployment

### Local Development Deployment

1. **Activate virtual environment**
   ```bash
   .\venv\Scripts\activate  # Windows
   ```

2. **Start Flask server**
   ```bash
   python app.py
   ```
   
   Server runs on `http://0.0.0.0:3000`

3. **Run ngrok tunnel**
   ```bash
   ngrok http 3000
   ```
   
   Use the HTTPS URL for your WhatsApp webhook

### Production Deployment Considerations

For production deployment, consider:

- **Process Manager**: Use `gunicorn` or `waitress` instead of Flask dev server
- **Reverse Proxy**: nginx or Apache for SSL/TLS termination
- **Systemd Service**: Auto-start on server boot
- **Firewall**: Restrict access to necessary ports only

## Maintenance

### Database Backups

#### Automated Nightly Backups (Windows)

1. **Backup script provided**: `backup_db.bat`
   - Creates timestamped backups in `backups/` directory
   - Automatically removes backups older than 30 days

2. **Schedule with Windows Task Scheduler**:
   - Open Task Scheduler
   - Create Basic Task
   - Name: "CyberBot DB Backup"
   - Trigger: Daily at 2:00 AM
   - Action: Start a program
   - Program: `C:\path\to\cyber-complaint-bot\backup_db.bat`
   - Finish

#### Manual Backup

```bash
copy complaints.db backups\complaints_manual.db
```

### Log Rotation

**Logging configuration**: Logs are written to `bot.log`

**Weekly log rotation** (manual):
```bash
# Archive old log
move bot.log logs\bot_%date%.log

# New log file will be created automatically on next app start
```

**Automated log rotation** (Linux with logrotate):
```bash
# /etc/logrotate.d/cybercomplaintbot
/path/to/cyber-complaint-bot/bot.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    create 0644 user group
}
```

### Monitoring

- **Check logs regularly**: `tail -f bot.log` (Linux) or open in text editor
- **Database size**: Monitor `complaints.db` file size
- **Disk space**: Ensure sufficient space for uploads and backups
- **ngrok session**: Restart if tunnel disconnects

## Future Scaling

### When Your Bot Grows

As usage increases, consider these upgrades:

#### 1. Database Migration
- **Current**: SQLite (file-based, single-user)
- **Upgrade to**: PostgreSQL or MySQL
  - Better concurrency handling
  - ACID compliance
  - Support for multiple connections
  - Built-in replication and backups

**Migration steps**:
```bash
pip install psycopg2-binary  # for PostgreSQL
# Update database.py to use PostgreSQL connection string
```

#### 2. Hosting Migration
- **Current**: Local machine with ngrok
- **Upgrade to**: VPS or Cloud VM
  - AWS EC2, DigitalOcean, Linode, or Azure VM
  - Static IP address
  - 24/7 uptime
  - Professional SSL certificates
  - Still fully controlled by you (no third-party data access)

#### 3. Containerization with Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

**Benefits**:
- Consistent deployment across environments
- Easy scaling with Docker Compose or Kubernetes
- Simplified dependency management

#### 4. CI/CD with GitHub Actions

Create `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

**Benefits**:
- Automated testing on every commit
- Catch bugs before deployment
- Automated deployment to production

#### 5. Additional Features

- **Redis caching**: Speed up frequent queries
- **Celery task queue**: Background PDF generation
- **Admin dashboard**: Web interface for viewing complaints
- **Multi-language support**: i18n for regional languages
- **SMS/Email notifications**: Notify users of complaint status

## Project Structure

```
cyber-complaint-bot/
├── templates/           # HTML templates for PDF generation
├── tests/              # Unit and integration tests
├── uploads/            # User uploaded files and generated PDFs
├── backups/            # Database backups (created by backup script)
├── venv/               # Virtual environment (not in Git)
├── .env                # Environment variables (not in Git)
├── .gitignore          # Git ignore rules
├── app.py              # Main Flask application with logging
├── backup_db.bat       # Windows backup script
├── bot.log             # Application logs
├── config.py           # Configuration loader
├── conversation.py     # Conversation state management
├── database.py         # Database connection and session
├── init_db.py          # Database initialization script
├── models.py           # SQLAlchemy models
├── pdf_generator.py    # PDF generation logic
├── requirements.txt    # Python dependencies
├── validators.py       # Input validation functions
└── whatsapp_handler.py # WhatsApp API integration
```

## Troubleshooting

### Common Issues

**1. Webhook verification fails**
- Ensure `VERIFY_TOKEN` in `.env` matches Meta dashboard
- Check ngrok is running and URL is correct
- Verify Flask app is running on port 3000

**2. Database errors**
- Run `python init_db.py` to initialize/recreate database
- Check file permissions on `complaints.db`

**3. PDF generation fails**
- Ensure WeasyPrint dependencies installed (Cairo, Pango)
- Check `templates/` directory exists
- Verify sufficient disk space

**4. File uploads not working**
- Check `uploads/` directory exists and is writable
- Verify file size within limits
- Check MIME type is allowed (PDF, JPG, PNG)

## License

This project is developed for educational and governmental use.

## Support

For issues or questions:
- Open an issue on GitHub
- Check logs in `bot.log` for error details
- Review test cases for expected behavior

---

**Step 9 Completion**: This README covers all aspects of Testing, Security, and Deployment as specified in Step 9 requirements. The bot is production-ready for local deployment with comprehensive testing, security measures, and maintenance tools.
