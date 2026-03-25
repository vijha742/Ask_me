"""Multi-line answer input widget with beautiful design."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, TextArea


class AnswerInput(Container):
    """Widget for multi-line answer input with text editing support."""

    def __init__(self):
        """Initialize answer input."""
        super().__init__(id="answer-card")
        self.border_title = "✍️  Your Answer"

    def compose(self) -> ComposeResult:
        """Compose the answer input."""
        yield Static("Press Ctrl+S when ready to submit • Use Ctrl+H to toggle hints", id="input-hint")
        yield TextArea(
            text="",
            language="markdown",
            theme="monokai",
            id="answer-textarea",
            soft_wrap=True,
            show_line_numbers=False,
        )

    def get_answer(self) -> str:
        """Get the current answer text."""
        textarea = self.query_one("#answer-textarea", TextArea)
        return textarea.text

    def set_answer(self, text: str) -> None:
        """Set the answer text."""
        textarea = self.query_one("#answer-textarea", TextArea)
        textarea.text = text

    def clear(self) -> None:
        """Clear the answer input."""
        textarea = self.query_one("#answer-textarea", TextArea)
        textarea.clear()

    def focus_input(self) -> None:
        """Focus the text area."""
        textarea = self.query_one("#answer-textarea", TextArea)
        textarea.focus()
