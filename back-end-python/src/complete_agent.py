"""
完整高级Agent实现

整合能力：
1. 对话记忆
2. 递归限制
3. 错误处理与重试
4. 自我反思
5. 工具链编排
6. 流式输出
7. 状态持久化
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from src.llm.factory import get_chat_model
from typing import List, Dict, Any, Optional, Generator
from pydantic import BaseModel
import json
import hashlib

from tools import safe_calculator, get_current_time, text_stats, unit_convert
from tools.live_env_tools import query_realtime_env_data
from tools.rag_tools import rag_qa, system_health
from tools.advanced_tools import send_email_tool
from src.config import Config
from src.state_manager import StateManager
from tools.tool_chain import ToolChain, ToolStep


# ========== 状态模型 ==========
class CompleteAgentState(BaseModel):
    """完整Agent状态"""
    session_id: str = ""
    messages: List[Dict[str, Any]] = []
    tool_history: List[Dict] = []
    reflection_history: List[str] = []
    error_count: int = 0
    iteration_count: int = 0
    max_iterations: int = 6
    max_retries: int = 3
    max_history: int = 10


# ========== 完整Agent ==========

class CompleteAdvancedAgent:
    """
    完整高级Agent

    整合所有高级能力：
    - 记忆系统
    - 错误处理
    - 自我反思
    - 工具链
    - 流式输出
    - 状态持久化
    """

    def __init__(
            self,
            max_history: int = 10,
            max_iterations: int = 6,
            max_retries: int = 3,
            enable_reflection: bool = True,
            state_dir: str = "./agent_states",
    ):
        """
        初始化完整Agent

        Args:
            max_history: 最大保存对话轮数
            max_iterations: 最大工具调用迭代次数
            max_retries: 最大重试次数
            enable_reflection: 是否启用自我反思
            state_dir: 状态存储目录
        """

        self.state = CompleteAgentState(
            max_history=max_history,
            max_iterations=max_iterations,
            max_retries=max_retries,
        )

        self.enable_reflection = enable_reflection
        self.state_manager = StateManager(state_dir)

        #LLM配置
        self.llm = get_chat_model()

        #完整工具列表
        self.tools = [
            safe_calculator,
            get_current_time,
            text_stats,
            unit_convert,
            rag_qa,
            system_health,
            send_email_tool,
            query_realtime_env_data,
        ]

        #工具映射
        self.tools_map = {t.name: t for t in self.tools}

        #工具链编排器
        self.tool_chain = ToolChain(self.tools_map)

        #高级系统提示词
        self.system_prompt = """
                            你是高级环境助手，具备以下能力：
                            1. 计算与统计（使用safe_calculator, text_stats）
                            2. 单位转换（使用unit_convert）
                            3. 知识库问答（使用rag_qa）
                            4. 系统检查（使用system_health）
                            5. 邮件通知（使用send_email）
                            6. 实时环境数据（使用query_realtime_env_data，默认只查不存）
                            
                            工作原则：
                            - 遇到计算问题必须调用工具，不要自行计算
                            - 知识问题优先使用rag_qa检索知识库
                            - 多步骤任务需要规划工具链执行顺序
                            - 工具失败时分析原因并尝试替代方案
                            - 不确定的信息要说明"不确定"，不要编造
                            - 完成任务后简要总结执行过程
                            
                            错误处理策略：
                            - 如果工具返回错误，尝试不同的参数或工具
                            - 如果多次失败，向用户说明情况并建议替代方案
                            """

    def chat(self, question: str) -> Dict[str, Any]:
            """
            完整功能对话

            Args:
                question: 用户问题

            Returns:
                包含完整执行信息的字典
            """
            # 1. 保存用户消息
            self.state.messages.append({"role": "user", "content": question})
            #2.构建完整上下文
            history_context = self._format_history()
            #3.执行agent
            result = self._execute_with_retry(question, history_context)
            #4.自我反思
            if self.enable_reflection:
                result = self._reflect_and_revise(question, result)
            #5.保存回答
            self.state.messages.append({"role": "assistant", "content": result["answer"]})
            #6.持久化状态
            self.state.session_id = self._generate_session_id()
            self.state_manager.save_state(self.state.session_id, self._get_state_dict())

            #7.返回完整结果
            return result

    def chat_stream(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        流式对话

        Args:
            question: 用户问题

        Yields:
            状态更新和回答片段
        """
        self.state.messages.append({"role": "user", "content": question})
        history_context = self._format_history()
        full_prompt = f"""
                    对话历史：
                    {history_context}
                    
                    当前问题：{question}
                    """
        # 开始执行
        yield {"type": "start", "message": "开始处理..."}
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )
        #流式执行
        for event in agent.stream(
                {"messages": [HumanMessage(content=full_prompt)]},
                {"recursion_limit": self.state.max_iterations},
                stream_mode="updates",
        ):
            if "agent" in event:
                content = event["agent"].get("content", "")
                if content:
                    yield {"type": "thinking", "content": content}
            elif "tool" in event:
                tool_name = event["tool"].get("name", "")
                yield {"type": "tool_call", "tool": tool_name}
            elif "final" in event:
                answer = event["final"].get("content", "")
                yield {"type": "answer", "content": answer}

        yield {"type": "complete", "message": "处理完成"}

    #增加一次性修订函数而不是再次调用 `chat` 全流程
    def _revise_once(self,question:str,original_answer:str,reflection_text:str)->str:
        prompt=f"""
问题：{question}
原始回答：{original_answer}
评估意见：{reflection_text}
请直接给出修正后的最终回答，不要输出评分过程。
"""
        response = self.llm.invoke(prompt)
        return getattr(response, "content", str(response))

    def _execute_with_retry(self, question: str, context: str) -> Dict[str, Any]:
            """
            带重试的执行
            """
            retries = 0
            last_error = None

            while retries < self.state.max_retries:
                try:
                    error_hint = ""
                    if last_error:
                        error_hint = f"""
    上次执行错误：{last_error}
    请尝试不同策略。
    """

                    full_prompt = f"""
    {context}
    {error_hint}

    当前问题：{question}
    """

                    agent = create_agent(
                        model=self.llm,
                        tools=self.tools,
                        system_prompt=self.system_prompt,
                    )

                    result = agent.invoke(
                        {"messages": [HumanMessage(content=full_prompt)]},
                        {"recursion_limit": self.state.max_iterations},
                    )

                    answer = result["messages"][-1].content

                    # 提取工具调用
                    tool_calls = self._extract_tool_calls(result)

                    return {
                        "answer": answer,
                        "success": True,
                        "tool_calls": tool_calls,
                        "retry_count": retries,
                    }

                except Exception as e:
                    retries += 1
                    last_error = str(e)
                    self.state.error_count += 1

            return {
                "answer": "抱歉，多次尝试后仍无法完成请求。",
                "success": False,
                "error": last_error,
                "retry_count": retries,
            }

    def _reflect_and_revise(self, question: str, result: Dict) -> Dict:
        """
        反思并修正
        """
        try:
            reflection_prompt = f"""
你是质量评估专家。请根据以下信息评估回答质量，并给出1-5分评分和改进建议。

问题：{question}
回答：{result["answer"]}
工具：{result.get("tool_calls", [])}
"""
            reflection = self.llm.invoke(reflection_prompt)
            reflection_text = getattr(reflection, "content", str(reflection))
            self.state.reflection_history.append(reflection_text)

            # 判断：是否需要修正
            needs_revision = "需要修正" in reflection_text or "评分：<3" in reflection_text

            if needs_revision:
                result["answer"] = self._revise_once(question, result["answer"], reflection_text)
                result["revised"] = True
            result["reflection"] = reflection_text
        except Exception as e:
            # 反思环节失败不影响主流程，避免接口直接 500
            result["reflection_error"] = str(e)
        return result

    def _format_history(self) -> str:
        """格式化历史"""
        formatted = []
        recent = self.state.messages[-(self.state.max_history * 2):]
        for msg in recent:
            formatted.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(formatted)

    def _extract_tool_calls(self, result: Dict) -> List[Dict]:
        """提取工具调用"""
        tool_calls = []
        for msg in result.get("messages", []):
            # 检查对象是否有某属性
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    tool_calls.append({
                        "tool": call.get("name"),
                        "args": call.get("args"),
                    })
        self.state.tool_history.extend(tool_calls)
        return tool_calls

    def _generate_session_id(self) -> str:
        content = "".join([m["content"] for m in self.state.messages[:2]])
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _get_state_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        return {
            "session_id": self.state.session_id,
            "messages": self.state.messages,
            "tool_history": self.state.tool_history,
            "reflection_history": self.state.reflection_history,
            "error_count": self.state.error_count,
        }

    def reset(self):
        """重置状态"""
        self.state = CompleteAgentState(
            max_history=self.state.max_history,
            max_iterations=self.state.max_iterations,
            max_retries=self.state.max_retries,
        )

    def restore(self, session_id: str) -> bool:
        """
        恢复历史会话

        Args:
            session_id: 会话ID

        Returns:
            是否恢复成功
        """
        saved_state = self.state_manager.get_latest_state(session_id)
        if saved_state:
            self.state.messages = saved_state.get("messages", [])
            self.state.tool_history = saved_state.get("tool_history", [])
            self.state.session_id = session_id
            return True
        return False
