"""Human-In-The-Loop (HITL) support for agents.

This package extends the base agent with HITL capabilities, allowing agents to:
- Pause execution when user input is needed
- Collect user responses
- Resume execution with user-provided data

Key components:
- HITLData: Data structure for HITL interrupts
- BaseAgentState: Extended with hitl_interrupts field
- ToolResult: Extended with hitl_data field
- BaseAgent: Extended with HITL-aware execution flow
- AskOutlineApprovalTool: HITL tool for outline approval
- HITLOrchestratorAgent: HITL이 통합된 Orchestrator Agent
"""

from lec06_02_hitl.agent import HITLOrchestratorAgent
from lec06_02_hitl.ask_outline_approval import AskOutlineApprovalTool
from lec06_02_hitl.base import BaseAgent
from lec06_02_hitl.hitl import HITLData
from lec06_02_hitl.state import BaseAgentState, HITLOrchestratorState, HITLPhase, TState
from lec06_02_hitl.tool import BaseTool, ToolResult

__all__ = [
    "AskOutlineApprovalTool",
    "BaseAgent",
    "BaseAgentState",
    "BaseTool",
    "HITLData",
    "HITLOrchestratorAgent",
    "HITLOrchestratorState",
    "HITLPhase",
    "TState",
    "ToolResult",
]
