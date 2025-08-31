"""
Maestro Orchestrator - Deterministic AI-powered development pipeline.

A deterministic and auditable orchestrator for chaining the cycle:
Planner (Gemini) → Coder (Codex) → Integrator/Runner (Cursor) → Tester → Reporter
"""

__version__ = "0.1.0"
__author__ = "Julio Cezar"
__email__ = "julio@example.com"

from .orchestrator import Orchestrator
from .dashboard import DashboardServer

__all__ = ["Orchestrator", "DashboardServer"]