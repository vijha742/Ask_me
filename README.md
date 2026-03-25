# vca - VibeCodeAsker

AI-powered learning companion that helps you understand your code changes.

## What is vca?

When you use AI tools to write code, `vca` helps you learn from those changes by:
- Analyzing your git commits
- Generating contextual learning questions about architectural decisions, syntax choices, and design patterns
- Providing AI-powered feedback on your answers
- Tracking your progress over time

## Installation

```bash
# Clone or navigate to this directory
cd vibeCodeAsker

# Install in development mode
pip install -e .
```

## Quick Start

```bash
# Initialize vca in your git repository
cd /path/to/your/project
vca init

# After making a commit, ask for learning questions
git commit -m "Add user authentication"
vca ask

# Configure vca settings
vca config
```

## How It Works

1. **Make code changes** (using AI assistance or manually)
2. **Commit your changes** to git
3. **Run `vca ask`** to generate learning questions
4. **Answer questions** interactively in your terminal
5. **Get feedback** from AI on your understanding
6. **Track progress** as you learn

## Commands

### TUI Mode (Default)

vca uses a modern Text User Interface by default for an interactive learning experience:

```bash
vca ask  # Launches TUI
```

**TUI Features:**
- Multi-line answer input with full text editing
- Scrollable content for long questions
- Navigate between questions (Ctrl+N/P)
- Toggle hints on/off (Ctrl+H)
- Real-time feedback display
- Session summary with statistics

**Keyboard Shortcuts:**
- `Ctrl+S` - Submit answer
- `Ctrl+H` - Toggle hints
- `Ctrl+N` / `Ctrl+P` - Next/Previous question
- `Tab` / `Shift+Tab` - Navigate widgets
- `Escape` - Skip question
- `F1` - Show help
- `Ctrl+Q` - Quit application

### CLI Mode

For scripting or simpler usage, use the classic CLI mode:

```bash
vca ask --no-tui
```

### Other Commands

- `vca init` - Initialize vca in current git repository
- `vca ask` - Generate questions for your last commit (TUI mode)
- `vca ask --no-tui` - Use classic CLI mode
- `vca ask --diff HEAD~3` - Questions for specific commit range
- `vca ask --count 10` - Generate 10 questions instead of default
- `vca --debug ask` - Enable debug logging for troubleshooting
- `vca config` - Configure OpenCode model and preferences
- `vca status` - Show vca status and configuration

## Question Types

vca generates 5-8 questions per session covering:

- **Architectural decisions**: Why did you structure it this way?
- **Syntax choices**: Why use X over Y in this context?
- **Design patterns**: What pattern is this? When would you avoid it?
- **Alternatives**: What are other ways to solve this problem?
- **Scalability**: How would this handle increased load?
- **Best practices**: What potential issues exist?

## Configuration

vca stores its data in `.vca/` directory in your repository:

```
.vca/
├── config.json          # Your preferences and settings
├── sessions/            # Q&A session history
└── logs/                # Debug logs (one per day)
    └── vca_20260324.log
```

Add `.vca/` to your `.gitignore` to keep learning sessions private.

## Debugging

If you encounter issues with question generation or rendering:

1. **Enable debug mode** to see detailed logs:
   ```bash
   vca --debug ask
   ```

2. **Check the logs** in `.vca/logs/` for detailed information:
   ```bash
   cat .vca/logs/vca_*.log
   ```

3. **Common issues**:
   - Questions not rendering: Check logs for JSON parsing errors
   - OpenCode errors: Ensure OpenCode CLI is installed and accessible
   - Timeout errors: Large diffs may take longer, check network/API status

The debug logs include:
- OpenCode CLI command execution details
- LLM request/response information
- JSON parsing attempts and errors
- Question generation and evaluation flow

## Requirements

- Python 3.8+
- Git repository
- OpenCode CLI (for AI question generation)

## Example Session

```bash
$ vca ask

🎓 Analyzing your commit: Add Redis caching layer
📝 Found changes in 3 files (+127, -45 lines)
🤖 Generating learning questions...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Question 1 of 6 [Architecture]

You implemented Redis for caching. What are two
scenarios where an in-memory cache (like LRU) 
would be better than Redis?

Your answer: > When you need low latency and data 
fits in memory, and when you don't need persistence
across restarts...

✓ Great answer! You identified the key trade-offs...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## License

MIT
