import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conversation import ConversationManager
from models import ConversationState


class TestConversationManager:
    """Test cases for ConversationManager class."""

    @pytest.fixture
    def conv_manager(self):
        """Create a ConversationManager instance for testing."""
        return ConversationManager()

    @pytest.fixture
    def mock_state(self):
        """Create a mock ConversationState."""
        state = Mock(spec=ConversationState)
        state.phone_number = '+1234567890'
        state.current_step = 'initial'
        state.name = None
        state.phone = None
        state.email = None
        state.transaction_id = None
        state.amount = None
        state.account_number = None
        state.ifsc_code = None
        state.bank_name = None
        state.incident_date = None
        state.description = None
        state.complaint_id = None
        return state

    def test_collect_name_valid(self, conv_manager, mock_state):
        """Test collecting valid name."""
        mock_state.current_step = 'await_name'
        
        with patch.object(conv_manager, 'save_state') as mock_save:
            result = conv_manager.handle_message(mock_state, 'John Doe')
            
            assert mock_state.name == 'John Doe'
            assert mock_state.current_step == 'await_phone'
            assert 'phone number' in result.lower()
            mock_save.assert_called_once()

    def test_collect_name_invalid(self, conv_manager, mock_state):
        """Test collecting invalid name (too short)."""
        mock_state.current_step = 'await_name'
        
        with patch.object(conv_manager, 'save_state') as mock_save:
            result = conv_manager.handle_message(mock_state, 'A')
            
            assert mock_state.current_step == 'await_name'
            assert 'invalid' in result.lower() or 'enter' in result.lower()
            mock_save.assert_not_called()

    def test_collect_phone_valid(self, conv_manager, mock_state):
        """Test collecting valid phone number."""
        mock_state.current_step = 'await_phone'
        
        with patch.object(conv_manager, 'save_state') as mock_save:
            result = conv_manager.handle_message(mock_state, '9876543210')
            
            assert mock_state.phone == '9876543210'
            assert mock_state.current_step == 'await_email'
            assert 'email' in result.lower()
            mock_save.assert_called_once()

    def test_collect_phone_invalid(self, conv_manager, mock_state):
        """Test collecting invalid phone number."""
        mock_state.current_step = 'await_phone'
        
        with patch.object(conv_manager, 'save_state') as mock_save:
            result = conv_manager.handle_message(mock_state, '123')
            
            assert mock_state.current_step == 'await_phone'
            assert 'invalid' in result.lower() or 'valid' in result.lower()
            mock_save.assert_not_called()

    def test_collect_ifsc_valid(self, conv_manager, mock_state):
        """Test collecting valid IFSC code."""
        mock_state.current_step = 'await_ifsc'
        
        with patch.object(conv_manager, 'save_state') as mock_save:
            result = conv_manager.handle_message(mock_state, 'SBIN0001234')
            
            assert mock_state.ifsc_code == 'SBIN0001234'
            assert mock_state.current_step != 'await_ifsc'
            mock_save.assert_called_once()

    def test_collect_ifsc_invalid(self, conv_manager, mock_state):
        """Test collecting invalid IFSC code."""
        mock_state.current_step = 'await_ifsc'
        
        with patch.object(conv_manager, 'save_state') as mock_save:
            result = conv_manager.handle_message(mock_state, 'INVALID')
            
            assert mock_state.current_step == 'await_ifsc'
            assert 'invalid' in result.lower() or 'format' in result.lower()
            mock_save.assert_not_called()

    def test_state_transition_flow(self, conv_manager, mock_state):
        """Test complete state transition flow."""
        mock_state.current_step = 'initial'
        
        # Simulate full conversation flow
        steps = [
            ('initial', 'yes', 'await_name'),
            ('await_name', 'John Doe', 'await_phone'),
            ('await_phone', '9876543210', 'await_email'),
        ]
        
        for current, message, expected_next in steps:
            mock_state.current_step = current
            with patch.object(conv_manager, 'save_state'):
                conv_manager.handle_message(mock_state, message)
                assert mock_state.current_step == expected_next

    def test_money_loss_no_redirect(self, conv_manager, mock_state):
        """Test that answering 'no' to money loss redirects user."""
        mock_state.current_step = 'await_money_loss'
        
        with patch.object(conv_manager, 'save_state') as mock_save:
            result = conv_manager.handle_message(mock_state, 'no')
            
            assert 'cyber crime' in result.lower() or 'redirect' in result.lower()
            mock_save.assert_not_called()

    @patch('conversation.PDFGenerator')
    def test_pdf_generation(self, mock_pdf_gen, conv_manager, mock_state):
        """Test PDF generation on complaint completion."""
        mock_state.current_step = 'complete'
        mock_state.name = 'John Doe'
        mock_state.complaint_id = 'CYB2025001'
        
        mock_pdf_instance = Mock()
        mock_pdf_instance.generate.return_value = '/path/to/pdf.pdf'
        mock_pdf_gen.return_value = mock_pdf_instance
        
        with patch.object(conv_manager, 'generate_pdf') as mock_gen:
            mock_gen.return_value = '/path/to/pdf.pdf'
            result = conv_manager.finalize_complaint(mock_state)
            
            mock_gen.assert_called_once()
            assert 'pdf' in result.lower() or 'generated' in result.lower()


class TestValidationFunctions:
    """Test input validation functions."""

    def test_validate_email(self):
        """Test email validation."""
        from validators import validate_email
        
        assert validate_email('test@example.com') == True
        assert validate_email('user.name@domain.co.in') == True
        assert validate_email('invalid.email') == False
        assert validate_email('@example.com') == False
        assert validate_email('test@') == False

    def test_validate_phone(self):
        """Test phone number validation."""
        from validators import validate_phone
        
        assert validate_phone('9876543210') == True
        assert validate_phone('1234567890') == True
        assert validate_phone('123') == False
        assert validate_phone('abcdefghij') == False

    def test_validate_ifsc(self):
        """Test IFSC code validation."""
        from validators import validate_ifsc
        
        assert validate_ifsc('SBIN0001234') == True
        assert validate_ifsc('HDFC0001234') == True
        assert validate_ifsc('INVALID') == False
        assert validate_ifsc('SBI123') == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
