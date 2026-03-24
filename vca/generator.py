"""
Question generator - creates learning questions from code diffs using LLM
"""
from typing import Dict, List, Any
from .opencode_client import OpenCodeClient
from .logger import get_logger

logger = get_logger()


class QuestionGenerator:
    """Generates contextual learning questions from code changes"""
    
    SYSTEM_PROMPT = """You are an expert programming instructor helping developers learn from their code changes.
Your task is to generate thoughtful, educational questions that help developers understand:
- Architectural decisions and trade-offs
- Syntax and language-specific features
- Design patterns and best practices
- Alternative approaches and when to use them
- Scalability and performance considerations
- Potential issues and improvements

Generate questions that encourage critical thinking, not just recall."""

    QUESTION_GENERATION_PROMPT = """Based on the following code changes, generate {question_count} learning questions.

COMMIT MESSAGE:
{commit_message}

CHANGE SUMMARY:
- Files changed: {file_count}
- Lines added: {additions}
- Lines deleted: {deletions}
- Change type: {change_type}
- File types: {file_types}

CODE DIFF:
{diff}

Generate {question_count} questions covering these categories (distribute evenly):
1. Architecture - Why this structure? What are the trade-offs?
2. Syntax/Language - Why use this syntax/feature over alternatives?
3. Design Patterns - What patterns are used? When to avoid them?
4. Alternatives - What are other ways to solve this? When would you use them?
5. Scalability - How does this handle growth? What are the limits?
6. Best Practices - What could be improved? What risks exist?

CRITICAL: You MUST respond with ONLY a valid JSON object. Do not include any explanatory text before or after the JSON.

Expected output structure (return EXACTLY this format):
{{
  "questions": [
    {{
      "id": 1,
      "category": "architecture",
      "question": "Why was this particular architectural approach chosen for the changes?",
      "difficulty": "intermediate",
      "hints": ["Consider the project structure", "Think about maintainability"]
    }},
    {{
      "id": 2,
      "category": "syntax",
      "question": "What language-specific feature is being used here and why?",
      "difficulty": "beginner",
      "hints": ["Look at the new syntax introduced", "Consider readability"]
    }},
    {{
      "id": 3,
      "category": "design_patterns",
      "question": "Which design pattern is applied in this implementation?",
      "difficulty": "advanced",
      "hints": ["Look for common patterns", "Consider object relationships"]
    }}
  ]
}}

Valid category values: "architecture", "syntax", "design_patterns", "alternatives", "scalability", "best_practices"
Valid difficulty values: "beginner", "intermediate", "advanced"

Make questions specific to the actual code changes shown, not generic. Focus on the most important learning opportunities.
Return ONLY the JSON object, nothing else."""

    def __init__(self, opencode_client: OpenCodeClient):
        self.client = opencode_client
    
    def generate_questions(
        self,
        diff: str,
        commit_message: str,
        analysis: Dict[str, Any],
        question_count: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Generate learning questions from a code diff
        
        Args:
            diff: The git diff text
            commit_message: Commit message for context
            analysis: Diff analysis metadata
            question_count: Number of questions to generate
        
        Returns:
            List of question dicts with id, category, question, difficulty, hints
        """
        logger.info(f"Generating {question_count} questions for commit: {commit_message[:50]}...")
        logger.debug(f"Analysis: {analysis}")
        
        # Build the prompt
        prompt = self.QUESTION_GENERATION_PROMPT.format(
            question_count=question_count,
            commit_message=commit_message,
            file_count=analysis.get('file_count', 0),
            additions=analysis.get('additions', 0),
            deletions=analysis.get('deletions', 0),
            change_type=analysis.get('change_type', 'modification'),
            file_types=', '.join(analysis.get('file_types', [])) or 'unknown',
            diff=diff
        )
        
        logger.debug(f"Generated prompt length: {len(prompt)} characters")
        
        try:
            # Get JSON response from LLM
            logger.info("Requesting questions from LLM...")
            response = self.client.ask_json(prompt, system_prompt=self.SYSTEM_PROMPT)
            
            logger.debug(f"Received response: {response}")
            
            if 'questions' in response and isinstance(response['questions'], list):
                questions = response['questions']
                logger.info(f"LLM returned {len(questions)} questions")
                
                # Validate and clean questions
                validated_questions = []
                for i, q in enumerate(questions[:question_count]):
                    if not isinstance(q, dict):
                        logger.warning(f"Question {i+1} is not a dict, skipping: {q}")
                        continue
                    
                    validated_q = {
                        'id': i + 1,
                        'category': q.get('category', 'general'),
                        'question': q.get('question', '').strip(),
                        'difficulty': q.get('difficulty', 'intermediate'),
                        'hints': q.get('hints', []),
                        'answered': False,
                        'user_answer': None,
                        'feedback': None
                    }
                    
                    # Only include if question text exists
                    if validated_q['question']:
                        validated_questions.append(validated_q)
                        logger.debug(f"Validated question {i+1}: {validated_q['question'][:60]}...")
                    else:
                        logger.warning(f"Question {i+1} has no text, skipping")
                
                logger.info(f"Successfully validated {len(validated_questions)} questions")
                return validated_questions
            else:
                logger.error(f"Invalid response format from LLM: {response}")
                raise ValueError("Invalid response format from LLM")
                
        except Exception as e:
            # Fallback: return generic questions if LLM fails
            logger.error(f"Question generation failed: {e}", exc_info=True)
            logger.warning("Using fallback questions")
            print(f"Warning: Question generation failed ({e}), using fallback questions")
            return self._get_fallback_questions(analysis, question_count)
    
    def _get_fallback_questions(self, analysis: Dict[str, Any], count: int = 6) -> List[Dict[str, Any]]:
        """Generate basic fallback questions if LLM fails"""
        logger.info(f"Generating {count} fallback questions")
        
        questions = [
            {
                'id': 1,
                'category': 'architecture',
                'question': 'What was the main architectural goal of this change?',
                'difficulty': 'intermediate',
                'hints': ['Think about the overall structure', 'Consider the change type'],
                'answered': False,
                'user_answer': None,
                'feedback': None
            },
            {
                'id': 2,
                'category': 'alternatives',
                'question': 'What alternative approaches could you have taken to solve this problem?',
                'difficulty': 'intermediate',
                'hints': ['Consider different design patterns', 'Think about language features'],
                'answered': False,
                'user_answer': None,
                'feedback': None
            },
            {
                'id': 3,
                'category': 'best_practices',
                'question': 'What potential issues or risks exist in this implementation?',
                'difficulty': 'intermediate',
                'hints': ['Consider edge cases', 'Think about error handling'],
                'answered': False,
                'user_answer': None,
                'feedback': None
            }
        ]
        
        return questions[:count]
