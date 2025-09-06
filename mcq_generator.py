import spacy
import random
import re
from collections import Counter
from typing import List, Dict, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except OSError:
    logger.error("spaCy English model not found. Please install it with: python -m spacy download en_core_web_sm")
    nlp = None


class MCQGenerator:
    def __init__(self):
        self.min_sentence_length = 10
        self.max_options = 4

    def extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract named entities from the document"""
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],  # Geopolitical entities
            'DATE': [],
            'MONEY': [],
            'PERCENT': [],
            'CARDINAL': [],  # Numbers
            'EVENT': [],
            'PRODUCT': [],
            'WORK_OF_ART': [],
            'LAW': [],
            'LANGUAGE': [],
        }
        
        for ent in doc.ents:
            if ent.label_ in entities and len(ent.text.strip()) > 1:
                clean_text = ent.text.strip()
                if len(clean_text) <= 50 and not re.search(r'[^\w\s\-\.\,\']', clean_text):
                    entities[ent.label_].append(clean_text)
        
        # Remove duplicates while preserving order
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))
        
        return entities

    def extract_key_phrases(self, doc) -> List[str]:
        """Extract key noun phrases and important terms"""
        key_phrases = []
        
        # Extract noun chunks
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if 2 <= len(chunk_text.split()) <= 5 and len(chunk_text) > 3:
                if not chunk.root.pos_ in ['PRON', 'DET']:
                    key_phrases.append(chunk_text)
        
        # Extract important single words
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                len(token.text) > 3 and 
                not token.is_stop and 
                token.is_alpha and 
                not token.text.lower() in ['said', 'says', 'according', 'including']):
                key_phrases.append(token.text)
        
        # Extract verb phrases for action-based questions
        for token in doc:
            if (token.pos_ == 'VERB' and 
                len(token.text) > 3 and 
                not token.is_stop and 
                token.text.lower() not in ['is', 'are', 'was', 'were', 'have', 'has', 'had']):
                key_phrases.append(token.text)
        
        phrase_counts = Counter(key_phrases)
        return [phrase for phrase, count in phrase_counts.most_common(100)]

    def generate_distractors(self, correct_answer: str, answer_type: str, 
                           all_entities: Dict, key_phrases: List[str]) -> List[str]:
        """Generate plausible wrong answers"""
        distractors = []
        
        # Use entities of the same type
        if answer_type in all_entities and all_entities[answer_type]:
            candidates = [ent for ent in all_entities[answer_type] 
                         if ent != correct_answer and ent.lower() != correct_answer.lower()]
            if candidates:
                num_to_take = min(len(candidates), 3)
                distractors.extend(random.sample(candidates, num_to_take))
        
        # Use key phrases if needed
        if len(distractors) < 3:
            phrase_candidates = [phrase for phrase in key_phrases 
                               if phrase != correct_answer and 
                               phrase.lower() != correct_answer.lower() and 
                               phrase not in distractors and 
                               len(phrase.split()) <= 3]  # Prefer shorter phrases
            needed = 3 - len(distractors)
            if phrase_candidates:
                num_to_take = min(len(phrase_candidates), needed)
                distractors.extend(random.sample(phrase_candidates, num_to_take))
        
        # Enhanced generic distractors
        generic_distractors = {
            'PERSON': ['Albert Einstein', 'Marie Curie', 'Isaac Newton', 'Charles Darwin', 'Leonardo da Vinci'],
            'ORG': ['Harvard University', 'Stanford University', 'MIT', 'Oxford University', 'Cambridge University'],
            'GPE': ['United States', 'United Kingdom', 'Germany', 'France', 'Japan', 'China', 'India'],
            'DATE': ['1990', '2000', '2010', '1985', '1995', '2005', '2015'],
            'MONEY': ['$1,000', '$5,000', '$10,000', '$500', '$2,000'],
            'PERCENT': ['25%', '50%', '75%', '10%', '30%', '60%', '90%'],
            'CARDINAL': ['100', '500', '1000', '50', '200', '300', '750'],
            'EVENT': ['World War II', 'Industrial Revolution', 'Renaissance', 'Cold War'],
            'PRODUCT': ['iPhone', 'Windows', 'Android', 'MacBook'],
            'WORK_OF_ART': ['Mona Lisa', 'The Starry Night', 'The Scream', 'Guernica'],
        }
        
        if len(distractors) < 3 and answer_type in generic_distractors:
            generic_options = [opt for opt in generic_distractors[answer_type] 
                             if opt != correct_answer and opt not in distractors]
            needed = 3 - len(distractors)
            if generic_options:
                num_to_take = min(len(generic_options), needed)
                distractors.extend(random.sample(generic_options, num_to_take))
        
        return distractors[:3]

    def create_fill_in_blank_question(self, sentence: str, answer: str, answer_type: str,
                                    all_entities: Dict, key_phrases: List[str]) -> Dict[str, Any]:
        """Create a fill-in-the-blank question"""
        # Create question by replacing the answer with blank
        question_text = re.sub(re.escape(answer), "______", sentence, count=1, flags=re.IGNORECASE)
        
        if question_text == sentence:
            return None
        
        distractors = self.generate_distractors(answer, answer_type, all_entities, key_phrases)
        if len(distractors) < 2:
            return None
        
        options = [answer] + distractors
        random.shuffle(options)
        
        return {
            'question': f"Fill in the blank: {question_text}",
            'options': options,
            'answer': answer,
            'type': answer_type.lower(),
            'difficulty': self._assess_difficulty(answer, answer_type)
        }

    def create_direct_question(self, sentence: str, answer: str, answer_type: str,
                             all_entities: Dict, key_phrases: List[str]) -> Dict[str, Any]:
        """Create a direct question about the content"""
        question_templates = {
            'PERSON': [
                f"Who is mentioned in the following context: '{sentence[:100]}...'?",
                f"Which person is associated with the described situation?",
                f"Who is the key individual mentioned?"
            ],
            'ORG': [
                f"Which organization is mentioned in this context?",
                f"What company or institution is referenced?",
                f"Which organization is being discussed?"
            ],
            'GPE': [
                f"Which location is mentioned in this context?",
                f"What place is being referenced?",
                f"Which geographical location is discussed?"
            ],
            'DATE': [
                f"When did this event occur?",
                f"What is the time period mentioned?",
                f"Which date is referenced?"
            ]
        }
        
        if answer_type not in question_templates:
            return None
        
        question_text = random.choice(question_templates[answer_type])
        distractors = self.generate_distractors(answer, answer_type, all_entities, key_phrases)
        
        if len(distractors) < 2:
            return None
        
        options = [answer] + distractors
        random.shuffle(options)
        
        return {
            'question': question_text,
            'options': options,
            'answer': answer,
            'type': answer_type.lower(),
            'difficulty': self._assess_difficulty(answer, answer_type)
        }

    def _assess_difficulty(self, answer: str, answer_type: str) -> str:
        """Assess the difficulty level of a question"""
        if answer_type in ['DATE', 'CARDINAL', 'PERCENT', 'MONEY']:
            return 'easy'
        elif answer_type in ['PERSON', 'GPE']:
            return 'medium'
        else:
            return 'hard'

    def generate_mcqs_from_text(self, text: str, num_questions: int = 5) -> List[Dict[str, Any]]:
        """Generate MCQs from the given text"""
        try:
            if not nlp:
                logger.error("spaCy model not loaded")
                return []
            
            # Clean and preprocess text
            text = re.sub(r'\s+', ' ', text.strip())
            text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\$\[\]\"\'\/]', '', text)
            
            # Process with spaCy in chunks to handle large texts
            max_chunk_size = 1000000  # 1MB chunks
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
            
            all_entities = {}
            all_key_phrases = []
            potential_questions = []
            
            for chunk in chunks:
                try:
                    doc = nlp(chunk)
                    
                    # Extract entities and phrases from this chunk
                    chunk_entities = self.extract_entities(doc)
                    chunk_key_phrases = self.extract_key_phrases(doc)
                    
                    # Merge entities
                    for entity_type, entities in chunk_entities.items():
                        if entity_type not in all_entities:
                            all_entities[entity_type] = []
                        all_entities[entity_type].extend(entities)
                    
                    all_key_phrases.extend(chunk_key_phrases)
                    
                    # Find potential questions in this chunk
                    for sent in doc.sents:
                        sent_text = sent.text.strip()
                        if len(sent_text) < self.min_sentence_length:
                            continue
                        
                        sent_doc = nlp(sent_text)
                        for ent in sent_doc.ents:
                            if (ent.label_ in all_entities and 
                                len(ent.text.strip()) > 1 and 
                                len(sent_text) <= 300):  # Reasonable sentence length
                                potential_questions.append({
                                    'sentence': sent_text,
                                    'answer': ent.text.strip(),
                                    'type': ent.label_
                                })
                
                except Exception as e:
                    logger.warning(f"Error processing chunk: {str(e)}")
                    continue
            
            # Remove duplicate entities
            for entity_type in all_entities:
                all_entities[entity_type] = list(dict.fromkeys(all_entities[entity_type]))
            
            all_key_phrases = list(dict.fromkeys(all_key_phrases))
            
            logger.info(f"Extracted entities: {sum(len(v) for v in all_entities.values())}")
            logger.info(f"Found {len(potential_questions)} potential questions")
            
            # Generate MCQs
            mcqs = []
            used_answers = set()
            random.shuffle(potential_questions)
            
            # Prioritize different entity types for variety
            entity_priority = ['PERSON', 'ORG', 'GPE', 'DATE', 'EVENT', 'PRODUCT', 'MONEY', 'PERCENT']
            
            for entity_type in entity_priority:
                if len(mcqs) >= num_questions:
                    break
                
                type_questions = [q for q in potential_questions if q['type'] == entity_type]
                for item in type_questions:
                    if len(mcqs) >= num_questions:
                        break
                    
                    if item['answer'].lower() in used_answers:
                        continue
                    
                    # Try both question types
                    mcq = self.create_fill_in_blank_question(
                        item['sentence'], item['answer'], item['type'],
                        all_entities, all_key_phrases
                    )
                    
                    if not mcq:
                        mcq = self.create_direct_question(
                            item['sentence'], item['answer'], item['type'],
                            all_entities, all_key_phrases
                        )
                    
                    if mcq:
                        mcqs.append(mcq)
                        used_answers.add(item['answer'].lower())
            
            # Fill remaining slots with any available questions
            remaining_questions = [q for q in potential_questions 
                                 if q['answer'].lower() not in used_answers]
            
            for item in remaining_questions:
                if len(mcqs) >= num_questions:
                    break
                
                mcq = self.create_fill_in_blank_question(
                    item['sentence'], item['answer'], item['type'],
                    all_entities, all_key_phrases
                )
                
                if mcq:
                    mcqs.append(mcq)
                    used_answers.add(item['answer'].lower())
            
            logger.info(f"Generated {len(mcqs)} MCQs")
            return mcqs
            
        except Exception as e:
            logger.error(f"Error generating MCQs: {str(e)}")
            return []


# Global generator instance
generator = MCQGenerator()


def generate_mcqs(text: str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """Main function to generate MCQs from text"""
    if not text or not text.strip():
        return []
    return generator.generate_mcqs_from_text(text, num_questions)


def is_spacy_available() -> bool:
    """Check if spaCy model is available"""
    return nlp is not None


# Example usage
if __name__ == "__main__":
    # Test the MCQ generator
    sample_text = """
    Albert Einstein was a German-born theoretical physicist who developed the theory of relativity.
    He was born in 1879 in Ulm, Germany. Einstein won the Nobel Prize in Physics in 1921.
    He worked at Princeton University from 1933 until his death in 1955.
    """
    
    print("Testing MCQ Generator...")
    mcqs = generate_mcqs(sample_text, 3)
    
    for i, mcq in enumerate(mcqs, 1):
        print(f"\nQuestion {i}: {mcq['question']}")
        for j, option in enumerate(mcq['options'], 1):
            print(f"  {j}. {option}")
        print(f"Correct Answer: {mcq['answer']}")
        print(f"Difficulty: {mcq['difficulty']}")
