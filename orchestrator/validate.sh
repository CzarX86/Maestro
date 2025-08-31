#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting environment validation..."

# --- Helper Functions ---
check_file_exists() {
    if [ ! -f "$1" ]; then
        echo "❌ ERROR: Required file not found: $1"
        exit 1
    fi
    echo "✅ File exists: $1"
}

check_command_exists() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ ERROR: Required command not found in PATH: '$1'. Please install it."
        exit 1
    fi
    echo "✅ Command exists: $1"
}

# --- Main Validation Logic ---

# 1. Check for essential tools for the validator itself
check_command_exists "jq"

# 2. Check for required project files
check_file_exists "secrets/.env"
check_file_exists "orchestrator/config.json"

# 3. Validate JSON structure
if ! jq -e . orchestrator/config.json > /dev/null; then
    echo "❌ ERROR: 'orchestrator/config.json' is not a valid JSON file."
    exit 1
fi
echo "✅ JSON is valid: orchestrator/config.json"

# 4. Check for required CLI tools from config.json
PLANNER_CMD=$(jq -r '.clis.planner.command' orchestrator/config.json)
CODER_CMD=$(jq -r '.clis.coder.command' orchestrator/config.json)
INTEGRATOR_CMD=$(jq -r '.clis.integrator.command' orchestrator/config.json)

check_command_exists "$PLANNER_CMD"
check_command_exists "$CODER_CMD"
check_command_exists "$INTEGRATOR_CMD"

echo "🎉 Validation successful! Environment is configured correctly."
exit 0
