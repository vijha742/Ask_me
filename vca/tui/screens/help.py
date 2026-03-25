"""Help screen with beautiful design showing keyboard shortcuts."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, Static


class HelpScreen(Screen):
    """Screen to display help and keyboard shortcuts with premium design."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def __init__(self):
        """Initialize help screen."""
        super().__init__(id="help-screen")

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with ScrollableContainer(id="help-container"):
            with Container(id="help-title"):
                yield Label("VCA - Keyboard Shortcuts & Help", id="help-header")
            
            yield Static("🎮 Navigation", classes="help-category")
            with Container(classes="help-section"):
                yield Static("  Ctrl+N / Ctrl+P    Next/Previous question", classes="help-item")
                yield Static("  Tab / Shift+Tab    Navigate between widgets", classes="help-item")
                yield Static("  ← / →              Navigate within text", classes="help-item")
            
            yield Static("⚡ Actions", classes="help-category")
            with Container(classes="help-section"):
                yield Static("  Ctrl+S             Submit your answer", classes="help-item")
                yield Static("  Ctrl+H             Toggle hints on/off", classes="help-item")
                yield Static("  Escape             Skip current question", classes="help-item")
                yield Static("  Enter              Press focused button", classes="help-item")
            
            yield Static("🎯 General", classes="help-category")
            with Container(classes="help-section"):
                yield Static("  Ctrl+Q             Quit application", classes="help-item")
                yield Static("  F1                 Show this help screen", classes="help-item")
                yield Static("  Ctrl+C             Copy selected text", classes="help-item")
                yield Static("  Ctrl+V             Paste text", classes="help-item")
            
            yield Static("✏️  Text Editing", classes="help-category")
            with Container(classes="help-section"):
                yield Static("  Ctrl+Z / Ctrl+Y    Undo/Redo", classes="help-item")
                yield Static("  Ctrl+A             Select all", classes="help-item")
                yield Static("  Home / End         Start/End of line", classes="help-item")
                yield Static("  Ctrl+Home/End      Start/End of text", classes="help-item")
            
            yield Static("💡 Tips", classes="help-category")
            with Container(classes="help-section"):
                yield Static("  • Take your time to think through answers", classes="help-item")
                yield Static("  • Use hints if you're stuck (Ctrl+H)", classes="help-item")
                yield Static("  • You can navigate back to review/edit answers", classes="help-item")
                yield Static("  • Multi-line answers are supported!", classes="help-item")
            
            with Container(id="continue-button"):
                yield Button("Got it! ✓", id="btn-close", classes="-primary")
        
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-close":
            self.action_close()

    def action_close(self) -> None:
        """Close the help screen."""
        self.app.pop_screen()
