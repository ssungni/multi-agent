"""BaseAgent 구조를 검증하는 테스트 스크립트 (LLM 호출 없음)."""

import inspect

from lec04_01_base_agent.base import BaseAgent, MaxIterationError
from lec04_01_base_agent.state import BaseAgentState
from lec04_01_base_agent.tool import BaseTool, ToolResult


def test_base_agent_structure() -> None:
    """BaseAgent에 필요한 모든 메서드가 있는지 검증합니다."""
    print("Testing BaseAgent structure...")

    required_methods = [
        "__init__",
        "setup",
        "run",
        "_should_stop",
        "_execute_single_step",
        "_hook_pre_llm_call",
        "_call_llm",
        "_call_llm_non_streaming",
        "_call_llm_streaming",
        "_build_llm_params",
        "_merge_delta_thinking_blocks",
        "_merge_delta_tool_calls",
        "_hook_post_llm_call",
        "_execute_tool_calls",
        "_find_tool_by_name",
        "_tool_call",
        "_build_tool_message",
        "_hook_post_step",
        "_append_message",
        "_extend_messages",
    ]

    for method_name in required_methods:
        assert hasattr(BaseAgent, method_name), f"Missing method: {method_name}"
        _ = getattr(BaseAgent, method_name)
        print(f"  ✓ {method_name}")

    # 특정 메서드가 추상인지 확인
    assert inspect.isabstract(BaseAgent), "BaseAgent should be abstract"

    # MaxIterationError 확인
    assert issubclass(MaxIterationError, Exception)
    print("  ✓ MaxIterationError exception")

    print("\n✓ All required methods found!")


def test_base_agent_state() -> None:
    """BaseAgentState 구조를 검증합니다."""
    print("\nTesting BaseAgentState structure...")

    state = BaseAgentState()
    assert hasattr(state, "model")
    assert hasattr(state, "messages")
    assert hasattr(state, "iteration_count")
    assert hasattr(state, "working_messages")

    print("  ✓ model attribute")
    print("  ✓ messages attribute")
    print("  ✓ iteration_count attribute")
    print("  ✓ working_messages property")
    print("\n✓ BaseAgentState structure verified!")


def test_base_tool() -> None:
    """BaseTool 구조를 검증합니다."""
    print("\nTesting BaseTool structure...")

    required_methods = [
        "to_chat_completion_tool",
        "call",
        "_execute",
    ]

    for method_name in required_methods:
        assert hasattr(BaseTool, method_name), f"Missing method: {method_name}"
        print(f"  ✓ {method_name}")

    assert inspect.isabstract(BaseTool), "BaseTool should be abstract"
    print("\n✓ BaseTool structure verified!")


def test_tool_result() -> None:
    """ToolResult 구조를 검증합니다."""
    print("\nTesting ToolResult structure...")

    result = ToolResult(content="test content")
    assert result.content == "test content"
    assert result.artifact is None

    result_with_artifact = ToolResult(content="test", artifact={"key": "value"})
    assert result_with_artifact.artifact == {"key": "value"}

    print("  ✓ content field")
    print("  ✓ artifact field")
    print("\n✓ ToolResult structure verified!")


def main() -> None:
    """모든 테스트를 실행합니다."""
    print("=" * 80)
    print("BaseAgent Implementation Structure Test")
    print("=" * 80)

    test_base_agent_structure()
    test_base_agent_state()
    test_base_tool()
    test_tool_result()

    print("\n" + "=" * 80)
    print("✓ All structure tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
