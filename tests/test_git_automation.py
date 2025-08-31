#!/usr/bin/env python3
"""
Tests for Git Automation and CI/CD Agents
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

# Import the agents
from src.maestro.git_agent import GitAgent
from src.maestro.ci_cd_agent import CICDAgent


class TestGitAgent(unittest.TestCase):
    """Test cases for Git Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_data = {
            "git": {
                "auto_commit": True,
                "auto_push": True,
                "auto_pr": True,
                "branch_prefix": "feature/",
                "commit_message_template": "feat: {task_id} - {description}",
                "max_commit_size": 200,
                "allowed_paths": ["src/maestro/**", ".github/workflows/**", "config/**"],
                "exclude_patterns": ["*.env", "secrets/*", "*.key", "*.log", "*.tmp"]
            },
            "ci_cd": {
                "auto_deploy_staging": True,
                "auto_deploy_production": False,
                "staging_environment": "staging",
                "production_environment": "production",
                "rollback_on_failure": True,
                "deploy_timeout": 300,
                "github_actions_workflow": "maestro-automation.yml"
            },
            "security": {
                "require_manual_approval": True,
                "exclude_secrets": True,
                "exclude_patterns": ["*.env", "secrets/*", "*.key"],
                "max_diff_lines": 1000,
                "require_qa_pass": True
            },
            "logging": {
                "log_level": "INFO",
                "log_file": "logs/git-automation.log",
                "structured_logging": True,
                "retention_days": 30
            }
        }
        
        # Create temporary config file
        self.config_file = os.path.join(self.temp_dir, "git-automation.json")
        with open(self.config_file, 'w') as f:
            json.dump(self.config_data, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_check_qa_status_pass(self, mock_run):
        """Test checking QA status when it passes"""
        # Mock QA report
        qa_report = {"status": "pass", "elapsed_sec": 120}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(qa_report))):
            with patch('os.path.exists', return_value=True):
                agent = GitAgent(self.config_file)
                status = agent.check_qa_status("test-task")
                self.assertEqual(status, "pass")
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_check_qa_status_fail(self, mock_run):
        """Test checking QA status when it fails"""
        # Mock QA report
        qa_report = {"status": "fail", "elapsed_sec": 60}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(qa_report))):
            with patch('os.path.exists', return_value=True):
                agent = GitAgent(self.config_file)
                status = agent.check_qa_status("test-task")
                self.assertEqual(status, "fail")
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_create_feature_branch_new(self, mock_run):
        """Test creating a new feature branch"""
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=1),  # Branch doesn't exist
            Mock(returncode=0)   # Checkout successful
        ]
        
        agent = GitAgent(self.config_file)
        branch_name = agent.create_feature_branch("test-task")
        self.assertEqual(branch_name, "feature/test-task")
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_create_feature_branch_existing(self, mock_run):
        """Test switching to existing feature branch"""
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0),  # Branch exists
            Mock(returncode=0)   # Checkout successful
        ]
        
        agent = GitAgent(self.config_file)
        branch_name = agent.create_feature_branch("test-task")
        self.assertEqual(branch_name, "feature/test-task")
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_validate_changes_success(self, mock_run):
        """Test validating changes successfully"""
        # Mock git diff output
        mock_run.side_effect = [
            Mock(returncode=0, stdout="src/maestro/test.py\nconfig/test.json"),
            Mock(returncode=0, stdout="src/maestro/test.py | 10 +++++-----\n")
        ]
        
        agent = GitAgent(self.config_file)
        result = agent.validate_changes("test-task")
        self.assertTrue(result)
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_validate_changes_excluded_pattern(self, mock_run):
        """Test validating changes with excluded pattern"""
        # Mock git diff output with excluded file
        mock_run.side_effect = [
            Mock(returncode=0, stdout="src/maestro/test.py\nsecrets/api.key"),
            Mock(returncode=0, stdout="")
        ]
        
        agent = GitAgent(self.config_file)
        result = agent.validate_changes("test-task")
        self.assertFalse(result)
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_commit_changes_success(self, mock_run):
        """Test committing changes successfully"""
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0),  # git add
            Mock(returncode=1),   # git diff --cached --quiet (has changes)
            Mock(returncode=0),   # git commit
            Mock(returncode=0, stdout="abc123")  # git rev-parse
        ]
        
        agent = GitAgent(self.config_file)
        result = agent.commit_changes("test-task", "feat: test commit")
        self.assertTrue(result)
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_push_branch_success(self, mock_run):
        """Test pushing branch successfully"""
        # Mock git push
        mock_run.return_value = Mock(returncode=0)
        
        agent = GitAgent(self.config_file)
        result = agent.push_branch("feature/test-task")
        self.assertTrue(result)
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_create_pull_request_success(self, mock_run):
        """Test creating pull request successfully"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0, stdout="https://github.com/repo/pull/123")  # gh pr create
        ]
        
        agent = GitAgent(self.config_file)
        pr_url = agent.create_pull_request("test-task", "feature/test-task")
        self.assertEqual(pr_url, "https://github.com/repo/pull/123")
    
    @patch('src.maestro.git_agent.subprocess.run')
    def test_rollback_changes_success(self, mock_run):
        """Test rolling back changes successfully"""
        # Mock git commands
        mock_run.side_effect = [
            Mock(returncode=0),  # git reset
            Mock(returncode=0)   # git clean
        ]
        
        agent = GitAgent(self.config_file)
        result = agent.rollback_changes("test-task")
        self.assertTrue(result)


class TestCICDAgent(unittest.TestCase):
    """Test cases for CI/CD Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_data = {
            "git": {
                "auto_commit": True,
                "auto_push": True,
                "auto_pr": True,
                "branch_prefix": "feature/",
                "commit_message_template": "feat: {task_id} - {description}",
                "max_commit_size": 200,
                "allowed_paths": ["src/maestro/**", ".github/workflows/**", "config/**"],
                "exclude_patterns": ["*.env", "secrets/*", "*.key", "*.log", "*.tmp"]
            },
            "ci_cd": {
                "auto_deploy_staging": True,
                "auto_deploy_production": False,
                "staging_environment": "staging",
                "production_environment": "production",
                "rollback_on_failure": True,
                "deploy_timeout": 300,
                "github_actions_workflow": "maestro-automation.yml"
            },
            "security": {
                "require_manual_approval": True,
                "exclude_secrets": True,
                "exclude_patterns": ["*.env", "secrets/*", "*.key"],
                "max_diff_lines": 1000,
                "require_qa_pass": True
            },
            "logging": {
                "log_level": "INFO",
                "log_file": "logs/ci-cd-automation.log",
                "structured_logging": True,
                "retention_days": 30
            }
        }
        
        # Create temporary config file
        self.config_file = os.path.join(self.temp_dir, "git-automation.json")
        with open(self.config_file, 'w') as f:
            json.dump(self.config_data, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_deploy_staging_success(self, mock_run):
        """Test deploying to staging successfully"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0)   # gh workflow run
        ]
        
        agent = CICDAgent(self.config_file)
        result = agent.deploy_staging("test-task", "feature/test-task")
        self.assertTrue(result)
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_deploy_staging_disabled(self, mock_run):
        """Test staging deployment when disabled"""
        # Disable auto deploy staging
        self.config_data["ci_cd"]["auto_deploy_staging"] = False
        with open(self.config_file, 'w') as f:
            json.dump(self.config_data, f)
        
        agent = CICDAgent(self.config_file)
        result = agent.deploy_staging("test-task", "feature/test-task")
        self.assertTrue(result)  # Should return True when disabled
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_check_deploy_status_success(self, mock_run):
        """Test checking deployment status successfully"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0, stdout=json.dumps([{
                "status": "completed",
                "conclusion": "success"
            }]))  # gh run list
        ]
        
        agent = CICDAgent(self.config_file)
        status = agent.check_deploy_status("test-task")
        self.assertEqual(status, "success")
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_check_deploy_status_failed(self, mock_run):
        """Test checking deployment status when failed"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0, stdout=json.dumps([{
                "status": "completed",
                "conclusion": "failure"
            }]))  # gh run list
        ]
        
        agent = CICDAgent(self.config_file)
        status = agent.check_deploy_status("test-task")
        self.assertEqual(status, "failed")
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_rollback_deploy_success(self, mock_run):
        """Test rolling back deployment successfully"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0)   # gh workflow run
        ]
        
        agent = CICDAgent(self.config_file)
        result = agent.rollback_deploy("test-task")
        self.assertTrue(result)
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_trigger_production_deploy_manual_approval(self, mock_run):
        """Test production deployment with manual approval required"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0)   # gh workflow run
        ]
        
        agent = CICDAgent(self.config_file)
        result = agent.trigger_production_deploy("test-task")
        self.assertTrue(result)  # Should return True when manual approval is required
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_handle_qa_failure_success(self, mock_run):
        """Test handling QA failure successfully"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0)   # gh workflow run
        ]
        
        agent = CICDAgent(self.config_file)
        result = agent.handle_qa_failure("test-task")
        self.assertTrue(result)
    
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    @patch('src.maestro.ci_cd_agent.time.sleep')
    def test_auto_deploy_and_monitor_success(self, mock_sleep, mock_run):
        """Test automatic deployment and monitoring successfully"""
        # Mock GitHub CLI
        mock_run.side_effect = [
            Mock(returncode=0),  # gh --version (deploy_staging)
            Mock(returncode=0),  # gh workflow run (deploy_staging)
            Mock(returncode=0),  # gh --version (check_deploy_status)
            Mock(returncode=0, stdout=json.dumps([{
                "status": "completed",
                "conclusion": "success"
            }]))  # gh run list
        ]
        
        agent = CICDAgent(self.config_file)
        result = agent.auto_deploy_and_monitor("test-task", "feature/test-task")
        self.assertTrue(result)


class TestIntegration(unittest.TestCase):
    """Integration tests for Git and CI/CD agents"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_data = {
            "git": {
                "auto_commit": True,
                "auto_push": True,
                "auto_pr": True,
                "branch_prefix": "feature/",
                "commit_message_template": "feat: {task_id} - {description}",
                "max_commit_size": 200,
                "allowed_paths": ["src/maestro/**", ".github/workflows/**", "config/**"],
                "exclude_patterns": ["*.env", "secrets/*", "*.key", "*.log", "*.tmp"]
            },
            "ci_cd": {
                "auto_deploy_staging": True,
                "auto_deploy_production": False,
                "staging_environment": "staging",
                "production_environment": "production",
                "rollback_on_failure": True,
                "deploy_timeout": 300,
                "github_actions_workflow": "maestro-automation.yml"
            },
            "security": {
                "require_manual_approval": True,
                "exclude_secrets": True,
                "exclude_patterns": ["*.env", "secrets/*", "*.key"],
                "max_diff_lines": 1000,
                "require_qa_pass": True
            },
            "logging": {
                "log_level": "INFO",
                "log_file": "logs/git-automation.log",
                "structured_logging": True,
                "retention_days": 30
            }
        }
        
        # Create temporary config file
        self.config_file = os.path.join(self.temp_dir, "git-automation.json")
        with open(self.config_file, 'w') as f:
            json.dump(self.config_data, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('src.maestro.git_agent.subprocess.run')
    @patch('src.maestro.ci_cd_agent.subprocess.run')
    def test_full_automation_flow_success(self, mock_cicd_run, mock_git_run):
        """Test full automation flow when QA passes"""
        # Mock QA report
        qa_report = {"status": "pass", "elapsed_sec": 120}
        
        # Mock git operations
        mock_git_run.side_effect = [
            Mock(returncode=0, stdout="src/maestro/test.py\nconfig/test.json"),  # git diff --cached --name-only
            Mock(returncode=0, stdout="src/maestro/test.py | 10 +++++-----\n"),  # git diff --cached --stat
            Mock(returncode=1),  # git rev-parse --verify (branch doesn't exist)
            Mock(returncode=0),  # git checkout -b
            Mock(returncode=0),  # git add
            Mock(returncode=1),  # git diff --cached --quiet (has changes)
            Mock(returncode=0),  # git commit
            Mock(returncode=0, stdout="abc123"),  # git rev-parse HEAD
            Mock(returncode=0),  # git push
            Mock(returncode=0),  # gh --version
            Mock(returncode=0, stdout="https://github.com/repo/pull/123")  # gh pr create
        ]
        
        # Mock CI/CD operations
        mock_cicd_run.side_effect = [
            Mock(returncode=0),  # gh --version
            Mock(returncode=0),  # gh workflow run
            Mock(returncode=0),  # gh --version
            Mock(returncode=0, stdout=json.dumps([{
                "status": "completed",
                "conclusion": "success"
            }]))  # gh run list
        ]
        
        with patch('builtins.open', mock_open(read_data=json.dumps(qa_report))):
            with patch('os.path.exists', return_value=True):
                # Test Git Agent
                git_agent = GitAgent(self.config_file)
                git_success = git_agent.auto_commit_and_push("test-task")
                self.assertTrue(git_success)
                
                # Test CI/CD Agent
                cicd_agent = CICDAgent(self.config_file)
                cicd_success = cicd_agent.auto_deploy_and_monitor("test-task", "feature/test-task")
                self.assertTrue(cicd_success)


if __name__ == '__main__':
    unittest.main()
