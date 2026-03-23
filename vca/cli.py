"""
CLI interface for vca
"""
import sys
import click
from pathlib import Path

from .analyzer import DiffAnalyzer
from .opencode_client import OpenCodeClient
from .generator import QuestionGenerator
from .evaluator import AnswerEvaluator
from .storage import VCAStorage
from .ui import TerminalUI


@click.group()
@click.version_option(version="0.1.0")
def main():
    """vca - AI-powered learning companion for code changes"""
    pass


@main.command()
def init():
    """Initialize vca in the current git repository"""
    ui = TerminalUI()
    
    try:
        # Check if we're in a git repo
        analyzer = DiffAnalyzer()
        
        # Initialize storage
        storage = VCAStorage(str(analyzer.repo_root))
        
        if storage.is_initialized():
            ui.print_warning("vca is already initialized in this repository")
            
            if not ui.confirm("Reinitialize?", default=False):
                return
        
        # Initialize
        if storage.initialize():
            ui.print_success(f"Initialized vca in {analyzer.repo_root}")
            ui.print_info("Configuration saved to .vca/config.json")
            ui.print_info("Run 'vca ask' after your next commit to start learning!")
            
            # Suggest adding to .gitignore
            gitignore = Path(analyzer.repo_root) / ".gitignore"
            if gitignore.exists():
                with open(gitignore, 'r') as f:
                    content = f.read()
                
                if '.vca' not in content:
                    ui.print_info("")
                    if ui.confirm("Add .vca/ to .gitignore?", default=True):
                        with open(gitignore, 'a') as f:
                            f.write("\n# vca learning sessions\n.vca/\n")
                        ui.print_success("Added .vca/ to .gitignore")
        else:
            ui.print_error("Failed to initialize vca")
            sys.exit(1)
            
    except ValueError as e:
        ui.print_error(str(e))
        ui.print_info("Make sure you're in a git repository")
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Unexpected error: {e}")
        sys.exit(1)


@main.command()
@click.option('--diff', default='HEAD', help='Commit reference to analyze (default: HEAD)')
@click.option('--count', default=None, type=int, help='Number of questions to generate')
def ask(diff, count):
    """Generate learning questions for a commit"""
    ui = TerminalUI()
    
    try:
        # Initialize components
        analyzer = DiffAnalyzer()
        storage = VCAStorage(str(analyzer.repo_root))
        
        # Check if initialized
        if not storage.is_initialized():
            ui.print_error("vca not initialized in this repository")
            ui.print_info("Run 'vca init' first")
            sys.exit(1)
        
        # Load config
        config = storage.load_config()
        question_count = count or config.get('question_count', 6)
        model = config.get('model', 'auto')
        
        # Show header
        ui.print_header("vca - Learn from your code", "Analyzing your changes...")
        
        # Get commit info
        with ui.spinner("Analyzing commit"):
            commit_hash = analyzer.get_last_commit_hash()
            commit_message = analyzer.get_commit_message(diff)
            diff_text = analyzer.get_diff(diff)
            analysis = analyzer.analyze_diff(diff_text)
        
        # Check if session already exists
        existing_session = storage.load_session(commit_hash)
        if existing_session:
            ui.print_warning(f"You already completed a session for this commit ({commit_hash})")
            if not ui.confirm("Start a new session?", default=False):
                return
        
        # Show commit info
        ui.show_commit_info(commit_message, analysis)
        
        # Check if change is too trivial
        if analyzer.is_trivial_change(analysis):
            ui.print_warning("This change seems too small to generate meaningful questions")
            if not ui.confirm("Continue anyway?", default=False):
                return
        
        # Initialize OpenCode client
        try:
            opencode = OpenCodeClient(model=model)
        except RuntimeError as e:
            ui.print_error(str(e))
            sys.exit(1)
        
        # Generate questions
        with ui.spinner("Generating learning questions"):
            generator = QuestionGenerator(opencode)
            relevant_diff = analyzer.get_relevant_diff_context(diff_text)
            questions = generator.generate_questions(
                relevant_diff,
                commit_message,
                analysis,
                question_count
            )
        
        if not questions:
            ui.print_error("Failed to generate questions")
            sys.exit(1)
        
        ui.print_success(f"Generated {len(questions)} questions")
        ui.console.print()
        
        # Interactive Q&A session
        evaluator = AnswerEvaluator(opencode)
        
        for i, question in enumerate(questions, 1):
            # Show question
            ui.show_question(question, i, len(questions))
            
            # Get answer
            show_hints = False
            while True:
                answer = ui.get_answer(allow_skip=True)
                
                if answer is None:
                    # Skipped
                    ui.print_info("Skipped")
                    ui.console.print()
                    break
                
                if answer.lower() == 'hints':
                    show_hints = True
                    ui.show_question(question, i, len(questions), show_hints=True)
                    continue
                
                # Valid answer
                question['answered'] = True
                question['user_answer'] = answer
                
                # Evaluate answer
                with ui.spinner("Evaluating your answer"):
                    evaluation = evaluator.evaluate_answer(
                        question,
                        answer,
                        relevant_diff
                    )
                
                question['feedback'] = evaluation
                
                # Show feedback
                ui.show_feedback(evaluation)
                break
        
        # Save session
        session_data = {
            'commit_hash': commit_hash,
            'commit_message': commit_message,
            'analysis': analysis,
            'questions': questions,
            'model': model
        }
        
        storage.save_session(commit_hash, session_data)
        
        # Show summary
        ui.show_session_summary(questions)
        
    except ValueError as e:
        ui.print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        ui.console.print()
        ui.print_warning("Session interrupted")
        ui.print_info("Progress not saved")
        sys.exit(0)
    except Exception as e:
        ui.print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@main.command()
@click.option('--model', help='Set the LLM model to use')
@click.option('--count', type=int, help='Set default question count')
@click.option('--show', is_flag=True, help='Show current configuration')
def config(model, count, show):
    """Configure vca settings"""
    ui = TerminalUI()
    
    try:
        analyzer = DiffAnalyzer()
        storage = VCAStorage(str(analyzer.repo_root))
        
        if not storage.is_initialized():
            ui.print_error("vca not initialized in this repository")
            ui.print_info("Run 'vca init' first")
            sys.exit(1)
        
        current_config = storage.load_config()
        
        if show:
            ui.show_config(current_config)
            return
        
        # Update config
        updated = False
        
        if model is not None:
            current_config['model'] = model
            updated = True
            ui.print_success(f"Model set to: {model}")
        
        if count is not None:
            current_config['question_count'] = count
            updated = True
            ui.print_success(f"Question count set to: {count}")
        
        if updated:
            storage.save_config(current_config)
            ui.print_info("Configuration saved")
        else:
            # Interactive config
            ui.show_config(current_config)
            ui.console.print()
            
            if ui.confirm("Update configuration?", default=False):
                # Ask for model
                current_model = current_config.get('model', 'auto')
                new_model = click.prompt(
                    "LLM model (auto, gpt-4o-mini, claude-sonnet, etc.)",
                    default=current_model
                )
                current_config['model'] = new_model
                
                # Ask for question count
                current_count = current_config.get('question_count', 6)
                new_count = click.prompt(
                    "Default question count",
                    type=int,
                    default=current_count
                )
                current_config['question_count'] = new_count
                
                storage.save_config(current_config)
                ui.print_success("Configuration updated")
        
    except ValueError as e:
        ui.print_error(str(e))
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Unexpected error: {e}")
        sys.exit(1)


@main.command()
def status():
    """Show vca status and statistics"""
    ui = TerminalUI()
    
    try:
        analyzer = DiffAnalyzer()
        storage = VCAStorage(str(analyzer.repo_root))
        
        if not storage.is_initialized():
            ui.print_error("vca not initialized in this repository")
            ui.print_info("Run 'vca init' first")
            sys.exit(1)
        
        ui.print_header("vca Status")
        
        # Show config
        config = storage.load_config()
        ui.console.print("[bold]Configuration:[/bold]")
        ui.console.print(f"  Model: {config.get('model', 'auto')}")
        ui.console.print(f"  Questions per session: {config.get('question_count', 6)}")
        ui.console.print()
        
        # Show stats
        stats = storage.get_stats()
        ui.console.print("[bold]Learning Statistics:[/bold]")
        ui.console.print(f"  Total sessions: {stats['total_sessions']}")
        ui.console.print(f"  Total questions: {stats['total_questions']}")
        ui.console.print(f"  Questions answered: {stats['total_answered']}")
        
        if stats['total_questions'] > 0:
            answer_rate = stats['answer_rate'] * 100
            ui.console.print(f"  Answer rate: {answer_rate:.1f}%")
        
        # Category breakdown
        if stats['category_stats']:
            ui.console.print()
            ui.console.print("[bold]Topics explored:[/bold]")
            for category, cat_stats in stats['category_stats'].items():
                ui.console.print(
                    f"  • {category.replace('_', ' ').title()}: "
                    f"{cat_stats['answered']}/{cat_stats['total']}"
                )
        
        ui.console.print()
        
    except ValueError as e:
        ui.print_error(str(e))
        sys.exit(1)
    except Exception as e:
        ui.print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
