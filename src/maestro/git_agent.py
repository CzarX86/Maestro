#!/usr/bin/env python3
"""
Git Agent for Maestro Orchestrator

Automatically handles git operations when QA passes:
- Creates feature branches
- Commits changes
- Pushes to remote
- Creates Pull Requests
- Handles rollback on failure
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict = {
    "git": {
        "auto_commit": True,
        "auto_push": True,
        "auto_pr": True,
        "branch_prefix": "feature/",
        "commit_message_template": "feat: {task_id} - {description}",
    },
    "ci_cd": {
        "auto_deploy_staging": True,
        "auto_deploy_production": False,
        "rollback_on_failure": True,
        "deploy_timeout": 300,
        "github_actions_workflow": "maestro-automation.yml",
    },
    "security": {
        "exclude_patterns": ["*.env", "secrets/*", "*.key", "*.log", "*.tmp"],
        "max_diff_lines": 1000,
    },
    "logging": {
        "log_file": "logs/git-automation.log",
    },
}


class GitAgent:
    """Agent for automated git operations in Maestro pipeline"""
    
    def __init__(self, config_path: str = "config/git-automation.json"):
        """Initialize Git Agent with configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        def merge_defaults(cfg: Dict) -> Dict:
            # Merge missing top-level sections and keys
            merged = {}
            for key, defaults in DEFAULT_CONFIG.items():
                val = cfg.get(key)
                if not isinstance(val, dict):
                    merged[key] = defaults.copy()
                else:
                    section = defaults.copy()
                    for k2, v2 in defaults.items():
                        section.setdefault(k2, v2)
                    # preserve provided keys
                    section.update(val)
                    merged[key] = section
            # include any extra keys present in cfg
            for k in cfg.keys():
                if k not in merged:
                    merged[k] = cfg[k]
            return merged

        try:
            with open(self.config_path, 'r') as f:
                cfg = json.load(f)
                if not isinstance(cfg, dict):
                    logger.warning("Config content is not a dict; using defaults")
                    return DEFAULT_CONFIG.copy()
                return merge_defaults(cfg)
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Using default config due to error reading {self.config_path}: {e}")
            return DEFAULT_CONFIG.copy()
    
    def _setup_logging(self):
        """Setup structured logging"""
        log_config = self.config.get('logging', {})
        log_file = log_config.get('log_file', 'logs/git-automation.log')
        
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    
    def _log_operation(self, operation: str, task_id: str, status: str, **kwargs):
        """Log structured operation data"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "operation": operation,
            "status": status,
            **kwargs
        }
        logger.info(f"Git operation: {json.dumps(log_data)}")
    
    def check_qa_status(self, task_id: str) -> str:
        """Check QA status from reports/qa.json"""
        qa_file = f"reports/qa.json"
        
        if not os.path.exists(qa_file):
            logger.warning(f"QA report not found: {qa_file}")
            return "unknown"
        
        try:
            with open(qa_file, 'r') as f:
                qa_data = json.load(f)
                status = qa_data.get('status', 'unknown')
                logger.info(f"QA status for {task_id}: {status}")
                return status
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error reading QA report: {e}")
            return "unknown"
    
    def validate_changes(self, task_id: str) -> bool:
        """Validate changes before committing"""
        try:
            # Check for secrets in staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                logger.error("Failed to get staged files")
                return False
            
            staged_files = result.stdout.strip().split('\n') if result.stdout else []
            
            # Check for excluded patterns
            exclude_patterns = self.config['security']['exclude_patterns']
            if staged_files:
                import fnmatch
                for file_path in staged_files:
                    # Support glob-style patterns like secrets/*, *.key, etc.
                    if any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns):
                        logger.error(f"File matches excluded pattern: {file_path}")
                        return False
            
            # Check diff size
            result = subprocess.run(
                ['git', 'diff', '--cached', '--stat'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Count lines in diff
                lines_added = 0
                for line in result.stdout.split('\n'):
                    if '|' in line and 'insertions' in line:
                        parts = line.split('|')
                        if len(parts) > 1:
                            try:
                                lines_added = int(parts[1].strip().split()[0])
                            except (ValueError, IndexError):
                                pass
                
                max_lines = self.config['security']['max_diff_lines']
                if lines_added > max_lines:
                    logger.error(f"Diff too large: {lines_added} lines (max: {max_lines})")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating changes: {e}")
            return False
    
    def create_feature_branch(self, task_id: str) -> str:
        """Create feature branch for task"""
        branch_prefix = self.config['git']['branch_prefix']
        branch_name = f"{branch_prefix}{task_id}"
        
        try:
            # Check if branch already exists
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', branch_name],
                capture_output=True
            )
            
            if result.returncode == 0:
                logger.info(f"Branch {branch_name} already exists, switching to it")
                subprocess.run(['git', 'checkout', branch_name], check=True)
            else:
                logger.info(f"Creating new branch: {branch_name}")
                subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            
            self._log_operation("create_branch", task_id, "success", branch=branch_name)
            return branch_name
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            self._log_operation("create_branch", task_id, "error", error=str(e))
            raise
    
    def commit_changes(self, task_id: str, message: str) -> bool:
        """Commit changes with validation"""
        try:
            # Stage all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(
                ['git', 'diff', '--cached', '--quiet'],
                capture_output=True
            )
            
            if result.returncode == 0:
                logger.info("No changes to commit")
                return True
            
            # Commit changes
            subprocess.run(['git', 'commit', '-m', message], check=True)
            
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True
            )
            commit_hash = result.stdout.strip()
            
            self._log_operation(
                "commit", task_id, "success", 
                commit_hash=commit_hash, message=message
            )
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e}")
            self._log_operation("commit", task_id, "error", error=str(e))
            return False
    
    def push_branch(self, branch_name: str) -> bool:
        """Push branch to remote repository"""
        try:
            logger.info(f"Pushing branch {branch_name} to remote")
            subprocess.run(['git', 'push', 'origin', branch_name], check=True)
            
            self._log_operation("push", "unknown", "success", branch=branch_name)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push branch {branch_name}: {e}")
            self._log_operation("push", "unknown", "error", branch=branch_name, error=str(e))
            return False
    
    def create_pull_request(self, task_id: str, branch_name: str) -> Optional[str]:
        """Create Pull Request using GitHub CLI"""
        try:
            # Check if gh CLI is available
            result = subprocess.run(['gh', '--version'], capture_output=True)
            if result.returncode != 0:
                logger.warning("GitHub CLI not available, skipping PR creation")
                return None
            
            # Create PR
            title = f"feat: {task_id} - Automated PR from Maestro"
            body = f"""
Automated Pull Request created by Maestro Git Agent

**Task ID:** {task_id}
**Branch:** {branch_name}
**Status:** QA Passed ✅

This PR was automatically created after successful QA validation.
            """.strip()
            
            result = subprocess.run([
                'gh', 'pr', 'create',
                '--title', title,
                '--body', body,
                '--base', 'main'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                logger.info(f"Created PR: {pr_url}")
                self._log_operation("create_pr", task_id, "success", pr_url=pr_url)
                return pr_url
            else:
                logger.error(f"Failed to create PR: {result.stderr}")
                self._log_operation("create_pr", task_id, "error", error=result.stderr)
                return None
                
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            self._log_operation("create_pr", task_id, "error", error=str(e))
            return None
    
    def rollback_changes(self, task_id: str) -> bool:
        """Rollback changes on QA failure"""
        try:
            logger.info(f"Rolling back changes for task {task_id}")
            
            # Reset to last commit
            subprocess.run(['git', 'reset', '--hard', 'HEAD'], check=True)
            
            # Clean untracked files
            subprocess.run(['git', 'clean', '-fd'], check=True)
            
            self._log_operation("rollback", task_id, "success")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to rollback changes: {e}")
            self._log_operation("rollback", task_id, "error", error=str(e))
            return False
    
    def auto_commit_and_push(self, task_id: str) -> bool:
        """Main method to handle automatic commit and push"""
        try:
            # Check QA status
            qa_status = self.check_qa_status(task_id)
            
            if qa_status != "pass":
                logger.info(f"QA status is {qa_status}, skipping git automation")
                return False

            # Validate changes before proceeding
            if not self.validate_changes(task_id):
                logger.error("Changes validation failed")
                return False
            
            # Create feature branch
            branch_name = self.create_feature_branch(task_id)
            
            # Generate commit message
            message_template = self.config['git']['commit_message_template']
            message = message_template.format(
                task_id=task_id,
                description=f"Automated commit from Maestro pipeline"
            )
            
            # Commit changes
            if not self.commit_changes(task_id, message):
                return False
            
            # Push branch
            if not self.push_branch(branch_name):
                return False
            
            # Create PR if enabled
            if self.config['git']['auto_pr']:
                self.create_pull_request(task_id, branch_name)
            
            logger.info(f"Git automation completed successfully for {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Git automation failed for {task_id}: {e}")
            return False


def main():
    """Main entry point for Git Agent"""
    if len(sys.argv) != 2:
        print("Usage: python git_agent.py <task_id>")
        sys.exit(1)
    
    task_id = sys.argv[1]
    
    try:
        agent = GitAgent()
        success = agent.auto_commit_and_push(task_id)
        
        if success:
            print(f"✅ Git automation completed for {task_id}")
            sys.exit(0)
        else:
            print(f"❌ Git automation failed for {task_id}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Git Agent error: {e}")
        print(f"❌ Git Agent error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
