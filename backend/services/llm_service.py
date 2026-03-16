"""
NYAYA AI — LLM Service
Handles: Query translation, LLM generation, response translation, document generation
"""
import time
import asyncio
from typing import Optional, List, Tuple
from loguru import logger
from groq import AsyncGroq
from langdetect import detect
from deep_translator import GoogleTranslator

from config import settings
from rag.pipeline import rag_pipeline, LegalDocument
from models import QueryCategory, Language


SYSTEM_PROMPT = """You are NYAYA AI, India's most trusted legal rights assistant. 
You help ordinary Indian citizens understand their legal rights and take action.

CORE RULES:
1. ALWAYS cite the exact Act name and Section number for every legal claim
2. Give STEP-BY-STEP actionable advice, not just theory
3. Mention relevant helpline numbers when applicable
4. If the issue requires a lawyer, say so clearly but also give immediate steps they can take themselves
5. NEVER give information you are not certain about - say "I need to verify this" if unsure
6. Keep language simple - explain as if talking to a class 8 student
7. Always end with: what to do RIGHT NOW (immediate steps)
8. If the question is about violence, abuse, or emergency - lead with helpline numbers FIRST

RESPONSE FORMAT:
- Start with the core answer
- Then: "Your Rights:" (bullet points with Act/Section citations)
- Then: "Step-by-step what to do:"
- Then: "Helplines:" (if relevant)
- Keep response under 400 words unless the topic demands more detail

LANGUAGE: Respond in the same language the question was asked in.
"""

INTENT_CATEGORIES = {
    "criminal": ["FIR", "arrest", "bail", "murder", "theft", "police", "complaint", "gir", "गिरफ्तार", "FIR"],
    "labour": ["salary", "wage", "job", "fire", "dismiss", "PF", "ESI", "तनख्वाह", "नौकरी"],
    "property": ["land", "eviction", "rent", "tenant", "zameen", "किराया", "ज़मीन"],
    "family": ["divorce", "domestic violence", "dowry", "custody", "तलाक", "दहेज"],
    "consumer": ["refund", "fraud", "defective", "cheating", "धोखा", "वापसी"],
    "rti": ["RTI", "information", "government file", "सूचना का अधिकार"],
    "scheme": ["scheme", "yojana", "benefit", "subsidy", "योजना", "लाभ"],
    "constitutional": ["rights", "fundamental", "constitution", "मौलिक अधिकार"],
}


class NyayaLLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            lang = detect(text)
            # Map to our supported languages
            lang_map = {
                "hi": "hi", "bn": "bn", "te": "te", "mr": "mr",
                "ta": "ta", "gu": "gu", "ur": "ur", "kn": "kn",
                "ml": "ml", "pa": "pa", "or": "or", "en": "en",
            }
            return lang_map.get(lang, "hi")
        except Exception:
            return "hi"

    def translate_to_english(self, text: str, source_lang: str) -> str:
        """Translate query to English for RAG retrieval"""
        if source_lang == "en":
            return text
        try:
            translated = GoogleTranslator(source=source_lang, target="en").translate(text)
            return translated
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return text

    def translate_response(self, text: str, target_lang: str) -> str:
        """Translate LLM response back to user's language"""
        if target_lang == "en":
            return text
        try:
            # Split into chunks for translation (API limits)
            if len(text) > 4500:
                chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
                translated_chunks = []
                for chunk in chunks:
                    t = GoogleTranslator(source="en", target=target_lang).translate(chunk)
                    translated_chunks.append(t)
                return " ".join(translated_chunks)
            return GoogleTranslator(source="en", target=target_lang).translate(text)
        except Exception as e:
            logger.warning(f"Response translation failed: {e}")
            return text

    def detect_category(self, text: str) -> QueryCategory:
        """Classify query into legal category"""
        text_lower = text.lower()
        for category, keywords in INTENT_CATEGORIES.items():
            if any(kw.lower() in text_lower for kw in keywords):
                try:
                    return QueryCategory(category)
                except Exception:
                    pass
        return QueryCategory.OTHER

    def build_context(self, results: List[Tuple[LegalDocument, float]]) -> str:
        """Build context string from RAG results"""
        if not results:
            return "No specific legal provisions found. Providing general guidance."

        context_parts = []
        for doc, score in results:
            source_info = f"[{doc.act}"
            if doc.section:
                source_info += f", {doc.section}"
            source_info += "]"
            context_parts.append(f"{source_info}\n{doc.content}")

        return "\n\n---\n\n".join(context_parts)

    def extract_helplines(self, response: str) -> List[str]:
        """Extract helpline numbers mentioned in response"""
        import re
        helplines = []
        patterns = [
            r'\b1\d{3,4}\b',  # Short codes like 112, 1098, 15100
            r'\b[7-9]\d{9}\b',  # Mobile numbers
            r'\b0\d{2,4}[-\s]?\d{6,8}\b',  # Landlines
        ]
        for pattern in patterns:
            matches = re.findall(pattern, response)
            helplines.extend(matches)
        return list(set(helplines))[:5]

    async def process_query(
        self,
        query: str,
        session_id: str,
        conversation_history: List[dict] = None,
        channel: str = "web",
    ) -> dict:
        """
        Main query processing pipeline:
        1. Detect language
        2. Translate to English
        3. Classify intent
        4. RAG retrieval
        5. LLM generation
        6. Translate response back
        7. Return structured result
        """
        start_time = time.time()

        # Step 1: Detect language
        detected_lang = self.detect_language(query)
        logger.info(f"Detected language: {detected_lang}")

        # Step 2: Translate to English for RAG
        english_query = self.translate_to_english(query, detected_lang)
        logger.info(f"English query: {english_query[:100]}")

        # Step 3: Classify category
        category = self.detect_category(english_query + " " + query)
        logger.info(f"Category: {category}")

        # Step 4: RAG retrieval
        rag_results = await rag_pipeline.retrieve(
            query=english_query,
            top_k=settings.TOP_K_RESULTS,
            category_filter=category.value if category != QueryCategory.OTHER else None,
        )
        logger.info(f"Retrieved {len(rag_results)} relevant chunks")

        # Step 5: Build context
        context = self.build_context(rag_results)

        # Step 6: Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history (last 4 turns)
        if conversation_history:
            for turn in conversation_history[-4:]:
                messages.append({
                    "role": turn["role"],
                    "content": turn["content"]
                })

        # Add RAG context + query
        user_message = f"""LEGAL KNOWLEDGE BASE (cite from this):
{context}

USER QUESTION: {english_query}

(Original language: {detected_lang}. Please respond in {detected_lang} if it's not English, otherwise in English.)"""

        messages.append({"role": "user", "content": user_message})

        # Step 7: LLM generation
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024,
            temperature=0.3,  # Low temp for legal accuracy
            top_p=0.9,
        )

        llm_response = response.choices[0].message.content
        logger.info(f"LLM response generated: {len(llm_response)} chars")

        # Step 8: Translate back if needed
        final_response = llm_response
        if detected_lang not in ["en", "hi"] and detected_lang:
            # LLM handles Hindi well, for other languages translate
            final_response = self.translate_response(llm_response, detected_lang)

        # Step 9: Check if lawyer needed
        needs_lawyer = any(kw in llm_response.lower() for kw in [
            "consult a lawyer", "legal representation", "sessions court",
            "high court", "supreme court", "criminal trial", "advocate"
        ])

        # Step 10: Extract sources for citation
        sources = []
        for doc, score in rag_results[:5]:
            sources.append({
                "act": doc.act,
                "section": doc.section,
                "title": doc.section_title or "",
                "excerpt": doc.content[:200] + "...",
                "relevance_score": round(float(score), 3),
            })

        processing_time = int((time.time() - start_time) * 1000)

        return {
            "response": final_response,
            "detected_language": detected_lang,
            "category": category.value,
            "sources": sources,
            "needs_lawyer": needs_lawyer,
            "suggested_helplines": self.extract_helplines(final_response),
            "confidence_score": float(rag_results[0][1]) if rag_results else 0.0,
            "processing_time_ms": processing_time,
        }

    async def generate_document(
        self,
        doc_type: str,
        user_details: dict,
        case_details: dict,
        language: str = "en",
    ) -> str:
        """Generate legal documents (RTI, notices, complaints)"""

        doc_prompts = {
            "rti_application": f"""Generate a complete, legally proper RTI Application under the Right to Information Act 2005.

User Details:
- Name: {user_details.get('name')}
- Address: {user_details.get('address')}
- Phone: {user_details.get('phone')}

Information Requested:
- Public Authority: {case_details.get('authority')}
- Department: {case_details.get('department')}
- Information Needed: {case_details.get('information_needed')}
- Time Period: {case_details.get('time_period', 'Last 3 years')}
- State: {case_details.get('state', 'India')}

Generate a formal RTI application with:
1. Proper addressing to PIO
2. Application number placeholder
3. Date placeholder
4. Specific information requests numbered
5. Section 6(1) RTI Act citation
6. Fee mention (₹10 by postal order/court fee stamp)
7. Proper closing and signature block
8. Appeal rights reminder""",

            "legal_notice": f"""Generate a formal Legal Notice under the Code of Civil Procedure.

From:
- Name: {user_details.get('name')}
- Address: {user_details.get('address')}

To:
- Name: {case_details.get('respondent_name')}
- Address: {case_details.get('respondent_address')}

Issue: {case_details.get('issue')}
Relief Sought: {case_details.get('relief')}
Notice Period: {case_details.get('notice_period', '15 days')}

Generate complete legal notice with proper legal language, sections cited, consequences of non-compliance, and demand for relief.""",

            "consumer_complaint": f"""Generate a Consumer Complaint for filing before the District Consumer Commission.

Complainant: {user_details.get('name')}, {user_details.get('address')}
Opposite Party: {case_details.get('company_name')}, {case_details.get('company_address')}

Product/Service: {case_details.get('product')}
Date of Purchase: {case_details.get('purchase_date')}
Amount Paid: {case_details.get('amount')}
Problem: {case_details.get('problem')}
Previous Communication: {case_details.get('previous_communication', 'Written complaint sent, no response')}

Generate complete consumer complaint with:
1. Jurisdictional statement
2. Facts of the case numbered
3. Grounds for complaint (Consumer Protection Act 2019 sections)
4. Relief sought (refund + compensation + litigation cost)
5. Verification clause
6. List of documents to attach""",

            "police_complaint": f"""Generate a Police Complaint/FIR draft.

Complainant: {user_details.get('name')}, {user_details.get('address')}, Phone: {user_details.get('phone')}
Date of Incident: {case_details.get('incident_date')}
Place of Incident: {case_details.get('incident_place')}
Accused: {case_details.get('accused', 'Unknown')}
Incident Details: {case_details.get('incident_details')}
Witnesses: {case_details.get('witnesses', 'None')}
Evidence: {case_details.get('evidence', 'None')}

Generate complete police complaint with proper FIR format, relevant IPC/BNS sections cited, clear narration of facts, and prayer for action.""",
        }

        prompt = doc_prompts.get(doc_type, f"Generate a {doc_type} legal document based on: {case_details}")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Indian lawyer generating legal documents. Generate complete, legally accurate, properly formatted documents. Use formal legal language. Include all necessary legal citations."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2048,
            temperature=0.2,
        )

        document_content = response.choices[0].message.content

        # Translate if needed
        if language not in ["en"]:
            document_content = self.translate_response(document_content, language)

        return document_content


# Singleton
llm_service = NyayaLLMService()
