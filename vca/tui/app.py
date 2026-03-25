"""Main VCA TUI Application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen


class VCAApp(App):
    """VCA TUI Application - Interactive learning companion for code changes."""

    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+h", "toggle_hints", "Toggle Hints"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(self, questions, commit_info, evaluator, generator):
        """Initialize the VCA TUI app.
        
        Args:
            questions: List of generated questions
            commit_info: Dict with commit message and diff
            evaluator: LLM evaluator instance
            generator: Question generator instance
        """
        super().__init__()
        self.questions = questions
        self.commit_info = commit_info
        self.evaluator = evaluator
        self.generator = generator
        self.current_question_idx = 0
        self.answers = {}
        self.evaluations = {}
        self.hints_visible = False

    def on_mount(self) -> None:
        """Called when app starts."""
        # Import here to avoid circular imports
        from .screens.main import MainScreen
        
        self.push_screen(MainScreen())

    def action_toggle_hints(self) -> None:
        """Toggle hint visibility."""
        self.hints_visible = not self.hints_visible
        # Broadcast to current screen
        if hasattr(self.screen, "refresh_hints"):
            self.screen.refresh_hints()

    def action_help(self) -> None:
        """Show help screen."""
        from .screens.help import HelpScreen
        self.push_screen(HelpScreen())

    def get_current_question(self):
        """Get the current question data."""
        if 0 <= self.current_question_idx < len(self.questions):
            return self.questions[self.current_question_idx]
        return None

    def next_question(self) -> bool:
        """Move to next question. Returns True if successful."""
        if self.current_question_idx < len(self.questions) - 1:
            self.current_question_idx += 1
            return True
        return False

    def prev_question(self) -> bool:
        """Move to previous question. Returns True if successful."""
        if self.current_question_idx > 0:
            self.current_question_idx -= 1
            return True
        return False

    def save_answer(self, answer: str) -> None:
        """Save answer for current question."""
        self.answers[self.current_question_idx] = answer

    def get_answer(self, idx: int = None) -> str:
        """Get saved answer for a question."""
        if idx is None:
            idx = self.current_question_idx
        return self.answers.get(idx, "")

    def save_evaluation(self, evaluation: dict) -> None:
        """Save evaluation for current question."""
        self.evaluations[self.current_question_idx] = evaluation

    def get_evaluation(self, idx: int = None) -> dict:
        """Get saved evaluation for a question."""
        if idx is None:
            idx = self.current_question_idx
        return self.evaluations.get(idx)

    def is_session_complete(self) -> bool:
        """Check if all questions have been answered."""
        return len(self.answers) == len(self.questions)
