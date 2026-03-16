"""
NYAYA AI — WhatsApp Bot Service via Twilio
Handles incoming WhatsApp messages and sends responses
"""
import uuid
from typing import Optional
from loguru import logger
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from config import settings
from services.llm_service import llm_service
from models import Session, ConversationTurn, Language
from datetime import datetime


class WhatsAppService:
    def __init__(self):
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        else:
            self.client = None
            logger.warning("Twilio not configured — WhatsApp disabled")

    async def handle_incoming(self, form_data: dict) -> str:
        """
        Process incoming WhatsApp message and return TwiML response
        """
        from_number = form_data.get("From", "")
        body = form_data.get("Body", "").strip()
        profile_name = form_data.get("ProfileName", "User")

        logger.info(f"WhatsApp from {from_number}: {body[:80]}")

        if not body:
            return self._twiml_response("Namaste! 🙏 I am NYAYA AI. Ask me any question about your legal rights in India. / नमस्ते! मुझसे अपने कानूनी अधिकारों के बारे में कोई भी सवाल पूछें।")

        # Get or create session
        session = await self._get_or_create_session(from_number)

        # Handle menu commands
        if body.lower() in ["hi", "hello", "start", "help", "नमस्ते", "शुरू"]:
            welcome = self._get_welcome_message()
            return self._twiml_response(welcome)

        if body == "1" or body.lower() == "rti":
            return self._twiml_response(
                "RTI (Right to Information) Help:\n\n"
                "Send me your question like:\n"
                "'How do I file RTI for my ration card status?'\n"
                "'RTI against police station'\n\n"
                "Or just describe your problem and I'll help you!"
            )

        if body == "0" or body.lower() == "lawyer":
            return self._twiml_response(
                "🆓 FREE LEGAL AID:\n\n"
                "📞 NALSA Helpline: *15100* (24/7)\n"
                "Available in all languages\n\n"
                "Or visit your nearest:\n"
                "• District Legal Services Authority (at District Court)\n"
                "• Taluk Legal Services Committee\n\n"
                "All services are 100% FREE for eligible persons."
            )

        # Process with LLM
        try:
            # Add to conversation
            session.conversation.append(ConversationTurn(
                role="user",
                content=body,
            ))

            # Get conversation history
            history = [
                {"role": t.role, "content": t.content}
                for t in session.conversation[-6:]
            ]

            result = await llm_service.process_query(
                query=body,
                session_id=session.session_id,
                conversation_history=history,
                channel="whatsapp",
            )

            response_text = result["response"]

            # Format for WhatsApp (shorter)
            whatsapp_response = self._format_for_whatsapp(response_text)

            # Add helplines if not present
            if result["needs_lawyer"] and "15100" not in whatsapp_response:
                whatsapp_response += "\n\n🆓 Free Lawyer: *15100* (NALSA)"

            # Save assistant response
            session.conversation.append(ConversationTurn(
                role="assistant",
                content=whatsapp_response,
            ))
            session.updated_at = datetime.utcnow()
            await session.save()

            return self._twiml_response(whatsapp_response)

        except Exception as e:
            logger.error(f"WhatsApp processing error: {e}")
            return self._twiml_response(
                "Sorry, I couldn't process your message. Please try again.\n\n"
                "For immediate help:\n"
                "🆓 Legal Aid: 15100\n"
                "👮 Police: 100\n"
                "👩 Women Helpline: 181"
            )

    def _format_for_whatsapp(self, text: str, max_length: int = 1500) -> str:
        """Format response for WhatsApp display"""
        # WhatsApp markdown
        text = text.replace("**", "*")  # Bold
        text = text.replace("##", "")
        text = text.replace("#", "")

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length - 100]
            text += "\n\n_(Reply 'more' for details or call NALSA: 15100)_"

        return text

    def _get_welcome_message(self) -> str:
        return """🏛️ *NYAYA AI* - आपका कानूनी सहायक

नमस्ते! मैं आपकी किसी भी कानूनी समस्या में मदद करूँगा।

*आप मुझसे पूछ सकते हैं:*
⚖️ अपने कानूनी अधिकार
🚔 FIR और पुलिस मामले
💼 नौकरी और मजदूरी के अधिकार
🏠 किराया और ज़मीन के मवाले
👩 महिला अधिकार
🏥 सरकारी योजनाएं
📋 RTI कैसे दाखिल करें

*Important Helplines:*
🆘 Emergency: 112
👩 Women: 181
👶 Child: 1098
⚖️ Free Legal Aid: 15100

बस अपना सवाल हिंदी या English में लिखें!"""

    def _twiml_response(self, message: str) -> str:
        """Generate TwiML XML response"""
        resp = MessagingResponse()
        resp.message(message)
        return str(resp)

    async def _get_or_create_session(self, phone: str) -> Session:
        """Get existing session or create new one"""
        # Clean phone number for session ID
        session_id = f"wa_{phone.replace('+', '').replace(':', '_')}"

        session = await Session.find_one(Session.session_id == session_id)
        if not session:
            session = Session(
                session_id=session_id,
                channel="whatsapp",
                language=Language.HINDI,
            )
            await session.insert()
        return session

    async def send_proactive_message(self, to: str, message: str):
        """Send outbound WhatsApp message (for notifications)"""
        if not self.client:
            logger.warning("Twilio not configured")
            return

        try:
            self.client.messages.create(
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                to=f"whatsapp:{to}",
                body=message,
            )
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")


whatsapp_service = WhatsAppService()
