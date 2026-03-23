"""
Terminal UI components using Rich library
"""
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich import box


class TerminalUI:
    """Rich terminal interface for vca"""
    
    def __init__(self):
        self.console = Console()
    
    def print_header(self, title: str, subtitle: str = ""):
        """Print a header banner"""
        text = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            text += f"\n[dim]{subtitle}[/dim]"
        
        self.console.print(Panel(text, box=box.DOUBLE, border_style="cyan"))
    
    def print_info(self, message: str, emoji: str = "ℹ️"):
        """Print an info message"""
        self.console.print(f"{emoji}  {message}")
    
    def print_success(self, message: str):
        """Print a success message"""
        self.console.print(f"[green]✓[/green] {message}")
    
    def print_error(self, message: str):
        """Print an error message"""
        self.console.print(f"[red]✗[/red] {message}", style="red")
    
    def print_warning(self, message: str):
        """Print a warning message"""
        self.console.print(f"[yellow]⚠[/yellow]  {message}", style="yellow")
    
    def show_commit_info(self, commit_message: str, analysis: Dict[str, Any]):
        """Display commit information"""
        self.console.print()
        self.console.print(f"[bold]📝 Commit:[/bold] {commit_message}")
        self.console.print(
            f"[dim]Files changed: {analysis['file_count']} | "
            f"+{analysis['additions']} -{analysis['deletions']} lines | "
            f"Type: {analysis['change_type']}[/dim]"
        )
        self.console.print()
    
    def show_question(
        self,
        question: Dict[str, Any],
        current: int,
        total: int,
        show_hints: bool = False
    ):
        """Display a question"""
        # Question header
        category_colors = {
            'architecture': 'blue',
            'syntax': 'green',
            'design_patterns': 'magenta',
            'alternatives': 'yellow',
            'scalability': 'cyan',
            'best_practices': 'red'
        }
        
        category = question.get('category', 'general')
        color = category_colors.get(category, 'white')
        
        self.console.print("━" * 60, style="dim")
        self.console.print(
            f"[bold]Question {current} of {total}[/bold] "
            f"[{color}][{category.replace('_', ' ').title()}][/{color}]"
        )
        self.console.print()
        
        # Question text
        self.console.print(question['question'])
        self.console.print()
        
        # Hints if requested
        if show_hints and question.get('hints'):
            self.console.print("[dim]💡 Hints:[/dim]")
            for hint in question['hints']:
                self.console.print(f"[dim]  • {hint}[/dim]")
            self.console.print()
    
    def get_answer(self, allow_skip: bool = True) -> Optional[str]:
        """Get user's answer input"""
        prompt_text = "Your answer"
        if allow_skip:
            prompt_text += " (or 'skip' to skip, 'hints' for hints)"
        
        answer = Prompt.ask(f"[cyan]{prompt_text}[/cyan]")
        
        if answer.lower() == 'skip' and allow_skip:
            return None
        
        return answer
    
    def show_feedback(self, evaluation: Dict[str, Any]):
        """Display feedback on an answer"""
        accuracy = evaluation.get('accuracy', 'partial')
        
        # Accuracy indicator
        accuracy_symbols = {
            'excellent': '[green]★★★[/green]',
            'good': '[green]★★[/green][dim]★[/dim]',
            'partial': '[yellow]★[/yellow][dim]★★[/dim]',
            'needs_improvement': '[dim]★★★[/dim]'
        }
        
        symbol = accuracy_symbols.get(accuracy, '[dim]★★★[/dim]')
        
        self.console.print()
        self.console.print(f"{symbol}  [bold]Feedback:[/bold]")
        self.console.print(f"[dim]{evaluation.get('feedback', 'Thank you for your answer.')}[/dim]")
        
        # Key points
        if evaluation.get('key_points'):
            self.console.print()
            self.console.print("[bold]Key Points:[/bold]")
            for point in evaluation['key_points']:
                self.console.print(f"  • {point}")
        
        # Suggestions
        if evaluation.get('suggestions'):
            self.console.print()
            self.console.print("[bold]To Explore Further:[/bold]")
            for suggestion in evaluation['suggestions']:
                self.console.print(f"  → {suggestion}")
        
        self.console.print()
    
    def show_session_summary(self, questions: List[Dict[str, Any]]):
        """Display session summary"""
        answered = sum(1 for q in questions if q.get('answered'))
        
        self.console.print()
        self.console.print("━" * 60, style="cyan")
        self.console.print("[bold cyan]Session Complete![/bold cyan]")
        self.console.print()
        self.console.print(f"Questions answered: {answered}/{len(questions)}")
        
        # Category breakdown
        categories = {}
        for q in questions:
            if q.get('answered'):
                cat = q.get('category', 'general')
                categories[cat] = categories.get(cat, 0) + 1
        
        if categories:
            self.console.print()
            self.console.print("[bold]Topics covered:[/bold]")
            for cat, count in categories.items():
                self.console.print(f"  • {cat.replace('_', ' ').title()}: {count}")
        
        self.console.print()
        self.console.print("[dim]Session saved to .vca/sessions/[/dim]")
        self.console.print("━" * 60, style="cyan")
        self.console.print()
    
    def show_config(self, config: Dict[str, Any]):
        """Display current configuration"""
        table = Table(title="vca Configuration", box=box.SIMPLE)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            table.add_row(key, str(value))
        
        self.console.print(table)
    
    def confirm(self, question: str, default: bool = True) -> bool:
        """Ask for confirmation"""
        return Confirm.ask(question, default=default)
    
    def spinner(self, message: str):
        """Return a spinner context manager"""
        return self.console.status(f"[cyan]{message}...", spinner="dots")
