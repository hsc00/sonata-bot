# List commands
default:
    @just --list

# Run the Discord bot
run:
    python bot/bot.py

# Install dependencies
[group("dependencies")]
install:
    pip install -r requirements.txt

# Run linting checks
[group("lint")]
lint:
    ruff check .

# Run linting and auto-fix issues
[group("lint")]
lint-fix:
    ruff check --fix .

# Run type checking
type-check:
    PYTHONPATH=bot ty check --exclude "tests/*"

# Format code with ruff
[group("format")]
format:
    ruff format .

# Check formatting without making changes
[group("format")]
format-check:
    ruff format --check .

# Run all checks 
check: lint format-check type-check
    @echo "All checks passed!"

# Build documentation
[group("docs")]
docs-build:
    mkdocs build

# Serve documentation locally
[group("docs")]
docs-serve:
    mkdocs serve

# Deploy documentation to GitHub Pages
[group("docs")]
docs-deploy:
    mkdocs gh-deploy 

# Run tests
test:
    pytest tests/

# Setup development environment
setup: install
    @echo "Development environment setup complete!"
    @echo "Run 'just run' to start the bot"