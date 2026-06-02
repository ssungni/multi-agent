"""Lecture 07: Tools Implementation - AskUser HITL Tool with tool_call mode.

This package contains tool implementations that leverage HITL capabilities:
- AskUserQuestionTool: Tool for asking users questions with HITL interrupts
- ExtendedHITLData: Extended HITL data supporting tool_call mode
- ExtendedBaseAgent: Base agent with tool_call mode support in _resume_hitl()
- ExtendedAgentState: Agent state with ExtendedHITLData support
- ExtendedOrchestratorState: Orchestrator state combining ExtendedAgentState with workflow fields

These tools demonstrate how to integrate human-in-the-loop functionality
into agent tool execution, allowing agents to gather user input dynamically.
"""

from lec07_02_ask_user.ask_user import AskUserQuestionTool
from lec07_02_ask_user.base import ExtendedBaseAgent
from lec07_02_ask_user.hitl import ExtendedHITLData
from lec07_02_ask_user.state import ExtendedAgentState, ExtendedOrchestratorState

__all__ = [
    "AskUserQuestionTool",
    "ExtendedBaseAgent",
    "ExtendedHITLData",
    "ExtendedAgentState",
    "ExtendedOrchestratorState",
]
