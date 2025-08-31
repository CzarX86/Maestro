#!/usr/bin/env bash
set -euo pipefail

# Development scripts for Maestro Orchestrator
# All commands use Poetry for dependency management

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Function to run commands with Poetry
poetry_run() {
    echo "🔧 Running with Poetry: $*"
    poetry run "$@"
}

# Function to show help
show_help() {
    echo "🎭 Maestro Orchestrator - Development Scripts"
    echo "=============================================="
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  install     - Install dependencies with Poetry"
    echo "  test        - Run tests with pytest"
    echo "  lint        - Run linting with ruff"
    echo "  type-check  - Run type checking with mypy"
    echo "  format      - Format code with black and isort"
    echo "  dashboard   - Start the dashboard server"
    echo "  demo        - Run the dashboard demo"
    echo "  orchestrator <task> - Run orchestrator for a task"
    echo "  shell       - Open Poetry shell"
    echo "  clean       - Clean Poetry cache and build artifacts"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 install"
    echo "  $0 test"
    echo "  $0 dashboard"
    echo "  $0 orchestrator demo"
    echo ""
}

# Main command handling
case "${1:-help}" in
    install)
        echo "📦 Installing dependencies with Poetry..."
        poetry install
        echo "✅ Dependencies installed successfully"
        ;;
        
    test)
        echo "🧪 Running tests..."
        poetry_run pytest tests/ -v --cov=src --cov-report=html --cov-report=term
        echo "✅ Tests completed"
        ;;
        
    lint)
        echo "🔍 Running linting..."
        poetry_run ruff check src/ tests/ dashboard/
        echo "✅ Linting completed"
        ;;
        
    type-check)
        echo "🔬 Running type checking..."
        poetry_run mypy src/
        echo "✅ Type checking completed"
        ;;
        
    format)
        echo "🎨 Formatting code..."
        poetry_run black src/ tests/ dashboard/
        poetry_run isort src/ tests/ dashboard/
        echo "✅ Code formatting completed"
        ;;
        
    dashboard)
        echo "🎭 Starting dashboard server..."
        poetry_run python dashboard/server.py
        ;;
        
    demo)
        echo "🎪 Running dashboard demo..."
        poetry_run python dashboard/demo.py
        ;;
        
    orchestrator)
        if [ -z "${2:-}" ]; then
            echo "❌ Error: Task ID required"
            echo "Usage: $0 orchestrator <task_id>"
            exit 1
        fi
        echo "🚀 Running orchestrator for task: $2"
        poetry_run python -m src.maestro.orchestrator "$2"
        ;;
        
    shell)
        echo "🐚 Opening Poetry shell..."
        poetry shell
        ;;
        
    clean)
        echo "🧹 Cleaning Poetry cache and build artifacts..."
        poetry cache clear --all pypi
        rm -rf dist/ build/ *.egg-info/
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        echo "✅ Cleanup completed"
        ;;
        
    help|--help|-h)
        show_help
        ;;
        
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac