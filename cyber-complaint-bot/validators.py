
# validators.py
import re

class InputValidator:
    def validate_name(self, name: str) -> bool:
        return bool(re.match(r"^[A-Za-z ]{2,50}$", str(name).strip()))

    def validate_phone(self, phone: str) -> bool:
        return bool(re.match(r"^[0-9]{10,15}$", str(phone).strip()))

    def validate_ifsc(self, ifsc: str) -> bool:
        return bool(re.match(r"^[A-Za-z]{4}0[0-9A-Za-z]{6}$", str(ifsc).strip()))

    def validate_transaction_id(self, tid: str) -> bool:
        return len(str(tid).strip()) >= 8
