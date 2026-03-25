"""Session summary screen with beautiful design."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static


class SummaryScreen(Screen):
    """Screen to display session summary and statistics with premium design."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "review", "Review Answers"),
    ]

    def __init__(self):
        """Initialize summary screen."""
        super().__init__(id="summary-screen")

    def compose(self) -> ComposeResult:
        """Compose the summary screen."""
        with ScrollableContainer(id="summary-container"):
            # Title with icon
            with Container(id="summary-title"):
                yield Static("🎊", id="summary-icon")
                yield Label("Session Complete!", id="summary-header")
            
            # Statistics card
            yield Static("📊 Statistics", classes="section-header")
            with Container(id="stats-card"):
                total_questions = len(self.app.questions)
                answered = len(self.app.answers)
                evaluations = len(self.app.evaluations)
                
                yield Static(f"Total Questions: {total_questions}", classes="stat-item")
                yield Static(f"Answered: {answered}", classes="stat-item")
                yield Static(f"Evaluated: {evaluations}", classes="stat-item")
                
                # Accuracy breakdown
                if self.app.evaluations:
                    accuracy_counts = {}
                    for e in self.app.evaluations.values():
                        acc = e.get("accuracy", "partial")
                        accuracy_counts[acc] = accuracy_counts.get(acc, 0) + 1
                    
                    yield Static("", classes="stat-item")
                    yield Static("Performance Breakdown:", classes="stat-item")
                    if "excellent" in accuracy_counts:
                        yield Static(f"  ★★★★★ Excellent: {accuracy_counts['excellent']}", classes="stat-item")
                    if "good" in accuracy_counts:
                        yield Static(f"  ★★★★☆ Good: {accuracy_counts['good']}", classes="stat-item")
                    if "partial" in accuracy_counts:
                        yield Static(f"  ★★★☆☆ Partial: {accuracy_counts['partial']}", classes="stat-item")
                    if "needs_improvement" in accuracy_counts:
                        yield Static(f"  ★★☆☆☆ Needs Improvement: {accuracy_counts['needs_improvement']}", classes="stat-item")
            
            # Topics covered
            topics = set()
            for q in self.app.questions:
                if "category" in q:
                    topics.add(q["category"])
            
            if topics:
                yield Static("📚 Topics Explored", classes="section-header")
                with Container(id="topics-card"):
                    for topic in sorted(topics):
                        topic_display = topic.replace("_", " ").title()
                        yield Static(f"  • {topic_display}", classes="topic-item")
            
            # Commit info
            yield Static("📝 Commit Summary", classes="section-header")
            with Container(id="stats-card"):
                commit_msg = self.app.commit_info.get("message", "No commit message")
                yield Static(commit_msg, classes="stat-item")
            
            # Action buttons
            with Horizontal(id="summary-actions"):
                yield Button("📖 Review Answers", id="btn-review", variant="default")
                yield Button("✓ Done", id="btn-exit", classes="-primary")
        
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-exit":
            self.action_quit()
        elif event.button.id == "btn-review":
            self.action_review()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_review(self) -> None:
        """Return to main screen to review answers."""
        # Reset to first question
        self.app.current_question_idx = 0
        
        # Pop back to main screen
        self.app.pop_screen()
        
        # Refresh main screen
        main_screen = self.app.screen_stack[0]
        if hasattr(main_screen, "refresh_screen"):
            main_screen.refresh_screen()
