"""
Answer evaluator - provides feedback on user answers using LLM
"""
from typing import Dict, Any
from .opencode_client import OpenCodeClient


class AnswerEvaluator:
    """Evaluates user answers and provides constructive feedback"""
    
    SYSTEM_PROMPT = """You are an expert programming instructor providing constructive feedback on a student's answer.

Your feedback should:
- Be encouraging and supportive
- Point out what they got right
- Gently correct misconceptions
- Provide additional context or insights
- Suggest areas for deeper exploration
- Be concise (2-4 sentences)

Focus on helping them learn, not just grading them."""

    EVALUATION_PROMPT = """A student was asked this question about their code changes:

QUESTION: {question}
CATEGORY: {category}
DIFFICULTY: {difficulty}

CONTEXT (Code changes):
{context}

STUDENT'S ANSWER:
{user_answer}

{hints_text}

Provide constructive feedback on their answer. Return ONLY a valid JSON object:
{{
  "feedback": "Your constructive feedback here (2-4 sentences)",
  "key_points": ["point 1", "point 2", "point 3"],
  "accuracy": "excellent|good|partial|needs_improvement",
  "suggestions": ["suggestion 1", "suggestion 2"]
}}

Be specific to their answer and the actual code changes shown."""

    def __init__(self, opencode_client: OpenCodeClient):
        self.client = opencode_client
    
    def evaluate_answer(
        self,
        question: Dict[str, Any],
        user_answer: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluate a user's answer to a question
        
        Args:
            question: The question dict with category, difficulty, hints
            user_answer: The user's answer text
            context: Optional code diff context
        
        Returns:
            Dict with feedback, key_points, accuracy, suggestions
        """
        # Build hints text if available
        hints_text = ""
        if question.get('hints'):
            hints_text = "HINTS PROVIDED: " + ", ".join(question['hints'])
        
        # Build the prompt
        prompt = self.EVALUATION_PROMPT.format(
            question=question.get('question', ''),
            category=question.get('category', 'general'),
            difficulty=question.get('difficulty', 'intermediate'),
            context=context[:1000] if context else "Not provided",  # Limit context size
            user_answer=user_answer,
            hints_text=hints_text
        )
        
        try:
            # Get JSON response from LLM
            response = self.client.ask_json(prompt, system_prompt=self.SYSTEM_PROMPT)
            
            # Validate and return
            return {
                'feedback': response.get('feedback', 'Thank you for your answer.'),
                'key_points': response.get('key_points', []),
                'accuracy': response.get('accuracy', 'partial'),
                'suggestions': response.get('suggestions', [])
            }
            
        except Exception as e:
            # Fallback feedback if LLM fails
            print(f"Warning: Answer evaluation failed ({e}), using fallback feedback")
            return {
                'feedback': "Thank you for your thoughtful answer. Keep exploring these concepts!",
                'key_points': [],
                'accuracy': 'partial',
                'suggestions': ["Review the code changes again", "Consider alternative approaches"]
            }
    
    def quick_feedback(self, accuracy: str) -> str:
        """Generate quick encouraging feedback based on accuracy"""
        feedback_map = {
            'excellent': "Excellent! You've demonstrated a strong understanding of this concept.",
            'good': "Good answer! You've captured the key ideas.",
            'partial': "You're on the right track. Consider exploring this topic further.",
            'needs_improvement': "This is a great learning opportunity. Let's explore this concept more."
        }
        return feedback_map.get(accuracy, "Thank you for your answer!")
