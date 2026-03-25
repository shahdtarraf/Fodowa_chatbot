"""Extract FAQ from PDF and create JSON knowledge base."""

import pypdf
import json
import re
from pathlib import Path

PDF_PATH = Path(__file__).parent / "data" / "knowledge_base.pdf"
JSON_PATH = Path(__file__).parent / "data" / "faq.json"


def extract_faq():
    """Extract Q&A from PDF."""
    
    # Read PDF
    reader = pypdf.PdfReader(str(PDF_PATH))
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # Parse Q&A pairs
    faq_list = []
    
    # Pattern: number followed by question mark or Arabic question
    # Split by question numbers (1., 2., etc.)
    lines = full_text.split('\n')
    
    current_question = None
    current_answer = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a new question (starts with number and . or Arabic numeral)
        question_match = re.match(r'^(\d+)\s*[\.、]\s*(.+)', line)
        
        if question_match:
            # Save previous Q&A if exists
            if current_question and current_answer:
                answer_text = ' '.join(current_answer).strip()
                # Clean up answer
                answer_text = re.sub(r'\s+', ' ', answer_text)
                if answer_text:
                    faq_list.append({
                        "question": current_question,
                        "answer": answer_text
                    })
            
            # Start new question
            current_question = question_match.group(2).strip()
            current_answer = []
        else:
            # This is part of the answer
            if current_question:
                current_answer.append(line)
    
    # Save last Q&A
    if current_question and current_answer:
        answer_text = ' '.join(current_answer).strip()
        answer_text = re.sub(r'\s+', ' ', answer_text)
        if answer_text:
            faq_list.append({
                "question": current_question,
                "answer": answer_text
            })
    
    # Save to JSON
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(faq_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Extracted {len(faq_list)} Q&A pairs")
    print(f"📁 Saved to: {JSON_PATH}")
    
    # Print first few for verification
    print("\n📋 Sample Q&A:")
    for i, item in enumerate(faq_list[:3]):
        print(f"\n{i+1}. {item['question']}")
        print(f"   {item['answer'][:100]}...")
    
    return faq_list


if __name__ == "__main__":
    extract_faq()
