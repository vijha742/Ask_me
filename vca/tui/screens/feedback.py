"""Feedback screen with beautiful, modern design."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Markdown, Static


class FeedbackScreen(Screen):
    """Screen to display evaluation feedback with premium design."""

    BINDINGS = [
        Binding("enter", "continue", "Continue"),
        Binding("escape", "back", "Back"),
    ]

    def __init__(self, evaluation: dict):
        """Initialize feedback screen.
        
        Args:
            evaluation: Evaluation result from LLM
        """
        super().__init__(id="feedback-screen")
        self.evaluation = evaluation

    def compose(self) -> ComposeResult:
        """Compose the feedback screen."""
        with ScrollableContainer(id="feedback-container"):
            # Rating display with stars
            with Container(id="feedback-rating"):
                accuracy = self.evaluation.get("accuracy", "partial")
                stars = self.get_stars(accuracy)
                quality = self.get_quality_label(accuracy)
                rating_class = f"rating-{accuracy.replace('_', '-')}"
                
                yield Static(stars, id="feedback-stars", classes=rating_class)
                yield Label(f"{quality}!", id="feedback-label", classes=rating_class)
            
            # Main feedback card
            with Container(id="feedback-card"):
                feedback_text = self.evaluation.get("feedback", "No feedback available.")
                yield Markdown(feedback_text, id="feedback-text")
            
            # Key points
            if "key_points" in self.evaluation and self.evaluation["key_points"]:
                yield Static("✨ Key Points", classes="section-header")
                with Vertical(id="points-container"):
                    for i, point in enumerate(self.evaluation["key_points"], 1):
                        yield Static(f"  {i}. {point}", classes="point-item")
            
            # Suggestions for further exploration
            if "suggestions" in self.evaluation and self.evaluation["suggestions"]:
                yield Static("🚀 Explore Further", classes="section-header")
                with Vertical(id="suggestions-container"):
                    for i, item in enumerate(self.evaluation["suggestions"], 1):
                        yield Static(f"  {i}. {item}", classes="suggestion-item")
            
            # Continue button
            with Container(id="continue-button"):
                yield Button("Continue to Next Question ▶", id="btn-continue", classes="-primary")
        
        yield Footer()

    def get_stars(self, accuracy: str) -> str:
        """Get star display based on accuracy.
        
        Args:
            accuracy: Accuracy level
            
        Returns:
            Star string
        """
        star_map = {
            "excellent": "★ ★ ★ ★ ★",
            "good": "★ ★ ★ ★ ☆",
            "partial": "★ ★ ★ ☆ ☆",
            "needs_improvement": "★ ★ ☆ ☆ ☆"
        }
        return star_map.get(accuracy, "★ ★ ★ ☆ ☆")

    def accuracy_to_score(self, accuracy: str) -> int:
        """Convert accuracy string to score.
        
        Args:
            accuracy: Accuracy level (excellent, good, partial, needs_improvement)
            
        Returns:
            Score from 1-5
        """
        score_map = {
            "excellent": 5,
            "good": 4,
            "partial": 3,
            "needs_improvement": 2
        }
        return score_map.get(accuracy, 3)

    def get_quality_label(self, accuracy: str) -> str:
        """Get quality label based on accuracy.
        
        Args:
            accuracy: Accuracy level string
            
        Returns:
            Quality label string
        """
        label_map = {
            "excellent": "🎉 Excellent Work",
            "good": "👏 Great Job",
            "partial": "👍 Good Effort",
            "needs_improvement": "💪 Keep Learning"
        }
        return label_map.get(accuracy, "👍 Good Effort")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-continue":
            self.action_continue()

    def action_continue(self) -> None:
        """Continue to next question or summary."""
        # Pop this screen
        self.app.pop_screen()
        
        # Move to next question
        if self.app.next_question():
            # Refresh the main screen
            main_screen = self.app.screen_stack[0]
            if hasattr(main_screen, "refresh_screen"):
                main_screen.refresh_screen()
        else:
            # Show summary
            from .summary import SummaryScreen
            self.app.push_screen(SummaryScreen())

    def action_back(self) -> None:
        """Go back to main screen without advancing."""
        self.app.pop_screen()
