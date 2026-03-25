"""Main Q&A screen with beautiful, modern design."""

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static

from ..widgets.answer_input import AnswerInput
from ..widgets.question_view import QuestionView


class MainScreen(Screen):
    """Main Q&A screen for answering questions with premium design."""

    BINDINGS = [
        Binding("ctrl+s", "submit_answer", "Submit Answer"),
        Binding("ctrl+n", "next_question", "Next Question"),
        Binding("ctrl+p", "prev_question", "Previous Question"),
        Binding("escape", "skip_question", "Skip"),
    ]

    def __init__(self):
        """Initialize main screen."""
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the main screen with beautiful layout."""
        # Custom branded header
        with Container(id="brand-header"):
            yield Static(
                "╔══════════════════════════════════════════════════════════════════════════╗\n"
                "║                    VCA  -  VibeCodeAsker                                ║\n"
                "║              🎓 Learn from Your Code, One Question at a Time             ║\n"
                "╚══════════════════════════════════════════════════════════════════════════╝",
                id="logo"
            )
        
        # Main scrollable content
        with ScrollableContainer(id="main-content"):
            # Commit info card
            with Container(id="commit-card"):
                commit_msg = self.app.commit_info.get("message", "No commit message")
                yield Label("📝 Current Commit", id="commit-icon")
                yield Label(commit_msg, id="commit-message")
                
                # Stats if available
                if "stats" in self.app.commit_info:
                    stats = self.app.commit_info["stats"]
                    stats_text = f"📊 {stats.get('files', 0)} files • +{stats.get('additions', 0)} -{stats.get('deletions', 0)} lines"
                    yield Label(stats_text, id="commit-stats")
            
            # Question card
            question_data = self.app.get_current_question()
            if question_data:
                yield QuestionView(
                    question_data=question_data,
                    question_num=self.app.current_question_idx + 1,
                    total=len(self.app.questions),
                    show_hints=self.app.hints_visible
                )
            
            # Answer input card
            yield AnswerInput()
        
        # Navigation bar
        with Horizontal(id="nav-bar"):
            yield Button("◀ Previous", id="btn-prev", variant="default")
            yield Button("⏭ Skip", id="btn-skip", variant="default")
            yield Button("✓ Submit Answer", id="btn-submit", classes="-primary")
            yield Button("Next ▶", id="btn-next", variant="default")
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus the answer input
        answer_input = self.query_one(AnswerInput)
        answer_input.focus_input()
        
        # Load previous answer if any
        prev_answer = self.app.get_answer()
        if prev_answer:
            answer_input.set_answer(prev_answer)
        
        self.update_navigation_buttons()

    def update_navigation_buttons(self) -> None:
        """Update button states based on current question."""
        prev_btn = self.query_one("#btn-prev", Button)
        next_btn = self.query_one("#btn-next", Button)
        
        prev_btn.disabled = self.app.current_question_idx == 0
        next_btn.disabled = self.app.current_question_idx >= len(self.app.questions) - 1

    def refresh_hints(self) -> None:
        """Refresh hint visibility."""
        question_view = self.query_one(QuestionView)
        question_view.update_hints_visibility(self.app.hints_visible)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-submit":
            self.action_submit_answer()
        elif event.button.id == "btn-skip":
            self.action_skip_question()
        elif event.button.id == "btn-prev":
            self.action_prev_question()
        elif event.button.id == "btn-next":
            self.action_next_question()

    def action_submit_answer(self) -> None:
        """Submit the current answer for evaluation."""
        answer_input = self.query_one(AnswerInput)
        answer = answer_input.get_answer().strip()
        
        if not answer:
            self.app.notify("Please enter an answer before submitting.", severity="warning")
            return
        
        # Save the answer
        self.app.save_answer(answer)
        
        # Start evaluation
        question = self.app.get_current_question()
        self.evaluate_answer(question, answer)

    def action_skip_question(self) -> None:
        """Skip the current question."""
        if self.app.next_question():
            self.refresh_screen()
        else:
            # Last question, show summary
            self.show_summary()

    def action_next_question(self) -> None:
        """Move to next question."""
        # Save current answer
        answer_input = self.query_one(AnswerInput)
        answer = answer_input.get_answer().strip()
        if answer:
            self.app.save_answer(answer)
        
        if self.app.next_question():
            self.refresh_screen()
        else:
            self.app.notify("Already at the last question.", severity="information")

    def action_prev_question(self) -> None:
        """Move to previous question."""
        # Save current answer
        answer_input = self.query_one(AnswerInput)
        answer = answer_input.get_answer().strip()
        if answer:
            self.app.save_answer(answer)
        
        if self.app.prev_question():
            self.refresh_screen()
        else:
            self.app.notify("Already at the first question.", severity="information")

    def refresh_screen(self) -> None:
        """Refresh the screen with current question."""
        question_data = self.app.get_current_question()
        main_content = self.query_one("#main-content")
        commit_card = self.query_one("#commit-card")
        
        # Remove all existing question views (should only be one)
        for question_view in self.query(".question-card").results(QuestionView):
            question_view.remove()
        
        # Create and add new question view
        new_question_view = QuestionView(
            question_data=question_data,
            question_num=self.app.current_question_idx + 1,
            total=len(self.app.questions),
            show_hints=self.app.hints_visible
        )
        main_content.mount(new_question_view, after=commit_card)
        
        # Update answer input with saved answer
        answer_input = self.query_one(AnswerInput)
        prev_answer = self.app.get_answer()
        answer_input.set_answer(prev_answer)
        answer_input.focus_input()
        
        # Update navigation buttons
        self.update_navigation_buttons()

    @work(exclusive=True, thread=True)
    def evaluate_answer(self, question: dict, answer: str) -> None:
        """Evaluate answer asynchronously.
        
        Args:
            question: Question data
            answer: User's answer
        """
        try:
            # Show loading notification
            self.app.call_from_thread(
                self.app.notify,
                "🤔 Evaluating your answer...",
                timeout=2
            )
            
            # Call evaluator (blocking call in thread)
            evaluation = self.app.evaluator.evaluate_answer(
                question=question,
                user_answer=answer,
                context=self.app.commit_info.get("diff", "")
            )
            
            # Save evaluation
            self.app.call_from_thread(self.app.save_evaluation, evaluation)
            
            # Show feedback screen
            self.app.call_from_thread(self.show_feedback, evaluation)
            
        except Exception as e:
            self.app.call_from_thread(
                self.app.notify,
                f"❌ Error evaluating answer: {str(e)}",
                severity="error"
            )

    def show_feedback(self, evaluation: dict) -> None:
        """Show feedback screen."""
        from .feedback import FeedbackScreen
        self.app.push_screen(FeedbackScreen(evaluation))

    def show_summary(self) -> None:
        """Show session summary screen."""
        from .summary import SummaryScreen
        self.app.push_screen(SummaryScreen())
