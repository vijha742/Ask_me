"""Question display widget with beautiful, modern design."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Label


class QuestionView(Container):
    """Widget for displaying a question with hints - premium design."""

    def __init__(self, question_data: dict, question_num: int, total: int, show_hints: bool = False):
        """Initialize question view.
        
        Args:
            question_data: Dictionary with question, hints, category
            question_num: Current question number (1-indexed)
            total: Total number of questions
            show_hints: Whether to show hints
        """
        super().__init__(id="question-card")
        self.question_data = question_data
        self.question_num = question_num
        self.total = total
        self.show_hints = show_hints
        self.border_title = f"❓ Question {question_num} of {total}"

    def compose(self) -> ComposeResult:
        """Compose the question view with beautiful layout."""
        # Category and difficulty badges
        with Horizontal(id="question-badge"):
            category = self.question_data.get("category", "General").replace("_", " ").title()
            yield Label(f"📚 {category}", classes="category-badge")
            
            difficulty = self.question_data.get("difficulty", "intermediate")
            difficulty_emoji = {"beginner": "🌱", "intermediate": "🌿", "advanced": "🌲"}.get(difficulty, "🌿")
            yield Label(f"{difficulty_emoji} {difficulty.title()}", classes="difficulty-badge")
        
        # Question text - large and centered
        question_text = self.question_data.get("question", "")
        yield Static(question_text, id="question-text")
        
        # Hints (conditionally shown)
        if self.show_hints and "hints" in self.question_data and self.question_data["hints"]:
            with Vertical(id="hints-card"):
                yield Label("💡 Hints to Guide You", classes="hints-header")
                for i, hint in enumerate(self.question_data["hints"], 1):
                    yield Static(f"  {i}. {hint}", classes="hint-item")

    def update_hints_visibility(self, show: bool) -> None:
        """Update hint visibility."""
        self.show_hints = show
        self.refresh(recompose=True)
