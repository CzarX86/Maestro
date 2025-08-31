#!/bin/bash

# Watcher script to automatically trigger the orchestrator for new issues.

ISSUES_DIR="issues"
PROCESSED_FILE=".processed_issues"
SLEEP_INTERVAL=10 # seconds

# Ensure the processed file exists
touch $PROCESSED_FILE

echo "🕵️  Starting watcher on directory: $ISSUES_DIR"

# Start documentation watcher in background if available
if [ -x "./orchestrator/documentation_watcher.sh" ]; then
    if ! pgrep -f "orchestrator/documentation_watcher.sh" >/dev/null 2>&1; then
        echo "📝 Starting documentation watcher (qa.json changes)"
        nohup ./orchestrator/documentation_watcher.sh >/dev/null 2>&1 &
    fi
fi

while true; do
    # Find all markdown files in the issues directory
    for issue_file in "$ISSUES_DIR"/*.md; do
        # Check if the file exists and is a regular file
        if [ -f "$issue_file" ]; then
            task_id=$(basename "$issue_file" .md)

            # Check if the task_id has already been processed
            if ! grep -q "^$task_id$" "$PROCESSED_FILE"; then
                echo "✨ New issue found: $task_id. Triggering orchestrator..."
                
                # Run the main orchestrator script
                # Using ./orchestrator/orchestrate.sh directly
                if [ -x "./orchestrator/orchestrate.sh" ]; then
                    ./orchestrator/orchestrate.sh "$task_id"
                    
                    # On success, record the task_id as processed
                    if [ $? -eq 0 ]; then
                        echo "✅ Orchestrator finished successfully for $task_id."
                        echo "$task_id" >> "$PROCESSED_FILE"
                    else
                        echo "❌ Orchestrator failed for $task_id. It will be retried on next cycle." >&2
                    fi
                else
                    echo "❌ ERROR: orchestrator/orchestrate.sh is not executable or not found." >&2
                fi
                echo "-------------------------------------------------"
            fi
        fi
    done
    
    # Wait for the next cycle
    # echo "...waiting for new issues..."
    sleep $SLEEP_INTERVAL
done
