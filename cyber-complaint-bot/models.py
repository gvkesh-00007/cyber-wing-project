# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    id_proof = Column(String)
    description = Column(Text, nullable=False)
    transaction_count = Column(Integer)
    sender_txn_id = Column(String)
    receiver_txn_id = Column(String)
    ifsc = Column(String)
    timestamp_evidence = Column(String)
    suspect_name = Column(String)
    suspect_details = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationState(Base):
    __tablename__ = "conversation_state"
    phone_number = Column(String, primary_key=True, index=True)
    current_step = Column(String, nullable=False)
    temp_data = Column(Text)  # JSON-encoded temporary data
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
