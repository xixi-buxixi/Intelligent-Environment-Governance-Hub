"""
高级Agent测试
"""

import pytest
from src.advanced_agent import AdvancedAgent, MemoryManager


class TestMemoryManager:
    """记忆管理器测试"""

    def test_add_message(self):
        """测试添加消息"""
        memory = MemoryManager(max_history=5)
        memory.add_message("user", "你好")
        memory.add_message("assistant", "你好！")

        history = memory.get_history()
        assert len(history) == 2

    def test_max_history_limit(self):
        """测试历史限制"""
        memory = MemoryManager(max_history=2)

        # 添加6条消息（3轮对话）
        for i in range(3):
            memory.add_message("user", f"问题{i}")
            memory.add_message("assistant", f"回答{i}")

        history = memory.get_history()
        # 应只保留最近2轮（4条）
        assert len(history) <= 4

    def test_clear(self):
        """测试清空"""
        memory = MemoryManager(max_history=5)
        memory.add_message("user", "测试")
        memory.clear()
        assert len(memory.get_history()) == 0


class TestAdvancedAgent:
    """高级Agent测试"""

    @pytest.mark.integration
    def test_chat_basic(self):
        """基础对话测试"""
        agent = AdvancedAgent(max_history=5, max_iterations=6)
        result = agent.chat("现在几点")

        assert "answer" in result
        assert result["answer"] is not None

    def test_memory_preservation(self):
        """记忆保持测试"""
        agent = AdvancedAgent(max_history=5, max_iterations=6)

        # 第一轮
        agent.chat("帮我计算 1+2")

        # 第二轮测试记忆
        result = agent.chat("刚才的结果是多少")
        history = result["history"]

        # 历史中应有第一轮对话
        assert len(history) >= 4

    def test_reset(self):
        """重置测试"""
        agent = AdvancedAgent(max_history=5, max_iterations=6)
        agent.chat("测试")
        agent.reset()

        history = agent.memory.get_history()
        assert len(history) == 0