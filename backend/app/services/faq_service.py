"""
FAQ Chatbot Service - Lightweight matching without ML models.

Uses difflib for text similarity matching - no external APIs, no models.
Memory efficient: loads FAQ once, serves instantly.
"""

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, List, Dict, Any

# FAQ data path
FAQ_PATH = Path(__file__).parent.parent.parent / "data" / "faq.json"

# Module-level cache
_faq_data: List[Dict[str, str]] = []


def load_faq() -> List[Dict[str, str]]:
    """Load FAQ data from JSON file."""
    global _faq_data
    
    if _faq_data:
        return _faq_data
    
    try:
        with open(FAQ_PATH, 'r', encoding='utf-8') as f:
            _faq_data = json.load(f)
        return _faq_data
    except Exception as e:
        print(f"❌ Failed to load FAQ: {e}")
        return []


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for better matching."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize Arabic characters
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    
    # Remove diacritics
    text = re.sub(r'[\u064B-\u065F]', '', text)
    
    # Lowercase English
    text = text.lower()
    
    return text.strip()


def similarity_score(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using SequenceMatcher."""
    return SequenceMatcher(None, normalize_arabic(text1), normalize_arabic(text2)).ratio()


def find_best_match(query: str, threshold: float = 0.3) -> Optional[Dict[str, Any]]:
    """
    Find the best matching FAQ for a query.
    
    Args:
        query: User's question
        threshold: Minimum similarity score (0.0 to 1.0)
    
    Returns:
        Best matching FAQ item with score, or None if no match
    """
    faq = load_faq()
    
    if not faq:
        return None
    
    best_match = None
    best_score = 0.0
    
    query_normalized = normalize_arabic(query)
    
    for item in faq:
        question = item.get('question', '')
        score = similarity_score(query, question)
        
        # Also check if query words appear in question
        query_words = set(query_normalized.split())
        question_words = set(normalize_arabic(question).split())
        word_overlap = len(query_words & question_words) / max(len(query_words), 1)
        
        # Combine scores
        combined_score = (score * 0.6) + (word_overlap * 0.4)
        
        if combined_score > best_score:
            best_score = combined_score
            best_match = item
    
    if best_score >= threshold:
        return {
            "question": best_match['question'],
            "answer": best_match['answer'],
            "score": best_score
        }
    
    return None


def get_chat_response(message: str) -> str:
    """
    Get chatbot response for user message.
    
    Args:
        message: User's message
    
    Returns:
        Chatbot's response
    """
    # Try to find FAQ match
    match = find_best_match(message)
    
    if match:
        return match['answer']
    
    # No match found - return helpful default
    return "عذراً، لم أتمكن من العثور على إجابة لسؤالك. يمكنك تصفح الأسئلة الشائعة في ملفك الشخصي أو التواصل مع الدعم للمساعدة."


def get_all_questions() -> List[str]:
    """Get all FAQ questions."""
    faq = load_faq()
    return [item.get('question', '') for item in faq]


def search_faq(keyword: str, limit: int = 5) -> List[Dict[str, str]]:
    """Search FAQ by keyword."""
    faq = load_faq()
    keyword_normalized = normalize_arabic(keyword)
    
    results = []
    for item in faq:
        question = item.get('question', '')
        answer = item.get('answer', '')
        
        if keyword_normalized in normalize_arabic(question) or keyword_normalized in normalize_arabic(answer):
            results.append(item)
            if len(results) >= limit:
                break
    
    return results
