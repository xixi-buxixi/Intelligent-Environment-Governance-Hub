"""
高级Agent实现 - 记忆系统增强
"""

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage
from src.llm.factory import get_chat_model
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel

from tools import safe_calculator, get_current_time, text_stats, unit_convert
from tools.rag_tools import rag_qa, system_health
from src.config import Config

from src.parsers.robust_parser import RobustJSONParser
from src.reflection import REFLECTION_PROMPT, get_reflection_format_instructions, ReflectionResult


# ========== 状态定义（记忆核心） ==========

class AgentState(BaseModel):
    """Agent状态模型 - 包含对话历史"""
    messages:List[Dict[str,Any]]=[]# 对话历史
    current_question:str="" # 当前问题
    tool_calls:List[Dict]=[] #工具调用记录
    reflection_result:Optional[str]=None # 反思结果
    error_count:int=0 # 错误次数
    max_iterations:int=5 # 最大迭代次数
    iteration_count:int=0 # 当前迭代次数

class MemoryManager:
    """
    记忆管理器

    功能：
    1. 保存对话历史
    2. 提取最近N轮对话
    3. 清空历史
    """
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.history.append({"role":role,"content":content})
        # 如果历史长度超过最大长度*2，则删除最旧的消息
        if len(self.history)>self.max_history*2:
            self.history=self.history[-(self.max_history*2)]
    
    def get_history(self)->List[Dict]:
        """获取完整历史"""
        return self.history
    
    def get_recent(self,n:int=3)->List[Dict]:
        """获取最近N轮对话"""
        return self.history[-(n*2):]

    def clear(self):
        """清空历史"""
        self.history=[]

    def format_for_llm(self)->str:
        """格式化历史为LLM输入"""
        formatted=[]
        for msg in self.history:
            role=msg["role"]
            content=msg["content"]
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

# ========== 带记忆的Agent ==========

class AdvancedAgent:
    """
    高级Agent类

    核心能力：
    1. 对话记忆
    2. 递归限制
    3. 错误处理
    """
    def __init__(self,max_history:int=10,max_iterations:int=6):
        """
        初始化高级Agent

        Args:
            max_history: 最大保存对话轮数
            max_iterations: 最大工具调用迭代次数
        """
        self.memory=MemoryManager(max_history=max_history)
        self.max_iterations=max_iterations

        #LLM配置
        self.llm = get_chat_model()
        
        #工具列表（整合所有工具）
        self.tools=[
            safe_calculator,
            get_current_time,
            text_stats,
            unit_convert,
            rag_qa,
            system_health
        ]

        #系统提示词（增强版）
        self.system_prompt="""
        你是高级环境助手，具备以下能力：
        1. 计算与统计（使用safe_calculator, text_stats）
        2. 单位转换（使用unit_convert）
        3. 知识库问答（使用rag_qa）
        4. 系统检查（使用system_health）

        工作原则：
        - 遇到计算问题必须调用工具，不要自行计算
        - 知识问题优先使用rag_qa检索知识库
        - 不确定的信息要说明"不确定"，不要编造
        - 工具失败时要分析原因并重试或换策略
        """


    def chat(self,question:str)->Dict[str,Any]:
        """
        带记忆的对话

        Args:
            question: 用户问题

        Returns:
            包含回答和执行信息的字典
        """
        # 1. 保存用户问题到记忆
        self.memory.add_message("user",question)

        # 2. 构建完整消息（历史 + 当前问题）
        history_context=self.memory.format_for_llm()
        full_prompt=f"""
                    对话历史：
                    {history_context}

                    当前问题：{question}

                    请根据对话历史回答当前问题，如果问题与之前对话相关，请引用之前的上下文。
                    """
        # 3. 创建Agent并执行
        agent=create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt
        )
        # 4. 执行并限制迭代次数
        result=agent.invoke(
            {"messages":[HumanMessage(content=full_prompt)]},
            {"recursion_limit":self.max_iterations}
        )
        # 5. 提取回答
        answer=result["messages"][-1].content
        # 6. 保存回答到记忆
        self.memory.add_message("assistant",answer)
        # 7. 返回结果
        return{
            "answer": answer,
            "history": self.memory.get_history(),
            "tool_calls": self._extract_tool_calls(result),
        }
    
    def _extract_tool_calls(self,result:Dict)->List[Dict]:
        """提取工具调用"""
        tool_calls=[]
        for msg in result.get("messages",[]):
            if hasattr(msg,"tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    tool_calls.append({
                        "tool": call.get("name"),
                        "args": call.get("args"),
                    })
        return tool_calls
    
    def reset(self):
        """重置对话"""
        self.memory.clear()

# 带错误重试的Agent
    def chat_with_retry(self,question:str,max_retries:int=3)->Dict[str,Any]:
        """
        带错误重试的对话

        Args:
            question: 用户问题
            max_retries: 每个工具的最大重试次数

        Returns:
            包含回答和错误信息的字典
        """

        self.memory.add_message("user",question)

        retry_count=0
        last_error=None

        while retry_count<max_retries:
            try:
                #构建完整提示
                history_context=self.memory.format_for_llm()

                #如果之前有错误，加入错误提示
                error_hint=""
                if last_error:
                    error_hint = f"""
            注意：上一次执行出现错误：{last_error}
            请尝试不同的方法或工具来解决这个问题。
            """
                full_prompt = f"""
            对话历史：
            {history_context}
            {error_hint}

            当前问题：{question}
            """
                agent=create_agent(
                    model=self.llm,
                    tools=self.tools,
                    system_prompt=self.system_prompt,
                )
                result=agent.invoke(
                    {"messages":[HumanMessage(content=full_prompt)]},
                    {"recursion_limit":self.max_iterations}
                )
                answer=result["messages"][-1].content
                self.memory.add_message("assistant",answer)

                return {
                    "answer": answer,
                    "success": True,
                    "retry_count": retry_count,
                    "history": self.memory.get_history(),
                }
            except Exception as e:
                retry_count += 1
                last_error = str(e)

                # 记录错误到记忆
                self.memory.add_message("system", f"执行错误：{e}（重试 {retry_count}/{max_retries}）")

        # 所有重试都失败
        return {
            "answer": "抱歉，多次尝试后仍无法完成您的请求。",
            "success": False,
            "error": last_error,
            "retry_count": retry_count,
        }
# 反思
    def chat_with_reflection(self,question:str)->Dict[str,Any]:
        """
        带自我反思的对话

        Args:
            question: 用户问题

        Returns:
            包含回答和反思结果的字典
        """
        # 1. 首次回答
        initial_result=self.chat(question)
        initial_answer=initial_result["answer"]
        tool_calls=initial_result["tool_calls"]

        # 2. 反思评估
        reflection_prompt = f"""
        原始问题：{question}
        给出的回答：{initial_answer}
        使用的工具：{tool_calls}

        {get_reflection_format_instructions()}
        """

        # reflection_result=self.llm.invoke([
        #     {"role": "system", "content": REFLECTION_PROMPT},
        #     {"role": "user", "content": reflection_prompt},
        # ])
        # reflection_text=reflection_result.content

        # 3. 解析反思结果（简化版）
        # .lower()：把这段文本全部变成小写字母。这样做是为了防止AI写了Needs_Revision: True
        # 或者NEEDS_REVISION: TRUE导致程序识别不到。统一变小写就稳妥了。
        # 3. 调用LLM生成反思
        response = self.llm.invoke([
            {"role": "system", "content": "你是质量评估专家，严格按JSON格式输出。"},
            {"role": "user", "content": reflection_prompt},
        ])
        # 4. 使用多层级解析器解析（关键改进）
        parser = RobustJSONParser(Type[ReflectionResult], self.llm)
        reflection_result = parser.parse(response.content)
        # 5. 根据反思结果决定是否修正
        final_answer = initial_answer
        revised = False
        if reflection_result and reflection_result.needs_revision:
            # 提取修正建议
            revision_prompt = f"""
                    根据评估建议修正回答：

                    发现的问题：{reflection_result.issues}
                    改进建议：{reflection_result.suggestions}

                    原始回答：{initial_answer}

                    请给出修正后的回答。
                    """
            revision_result=self.chat(revision_prompt)
            final_answer=revision_result["answer"]
            revised=True
            # 记录修正到记忆
            self.memory.add_message("system", f"回答已根据反思修正")

            # 6. 返回完整结果
        return {
            "answer": final_answer,
            "initial_answer": initial_answer,
            "reflection": reflection_result.model_dump() if reflection_result else None,
            "needs_revision": reflection_result.needs_revision if reflection_result else False,
            "revised": revised,
            "tool_calls": tool_calls,
            "history": self.memory.get_history(),
        }


    def analyze_and_plan(self,question:str)->List[Dict]:
        """
        分析问题并规划工具链

        Args:
            question: 用户问题

        Returns:
            工具执行计划
        """

        planning_prompt = f"""
        用户问题：{question}

        可用工具：
        - safe_calculator: 数学计算
        - text_stats: 文本统计
        - unit_convert: 单位转换
        - rag_qa: 知识库问答
        - system_health: 系统检查

        请分析问题，决定需要使用哪些工具，以及执行顺序。

        输出格式（JSON）：
        {
        "tools_needed": ["tool1", "tool2"],
            "execution_order": ["tool1", "tool2"],
            "reasoning": "为什么需要这些工具"
        }
        """

        result=self.llm.invoke([
            {"role": "system", "content": "你是一个工具规划专家。"},
            {"role": "user", "content": planning_prompt},
        ])
        return result.content

    def chat_stream(self,question:str):
        """
        流式对话输出

        Args:
            question: 用户问题

        Yields:
            回答片段和状态更新
        """
        self.memory.add_message("user",question)

        history_context=self.memory.format_for_llm()
        full_prompt=f"""
        对话历史：
        {history_context}
        
        当前问题：{question}
        """
        agent=create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

        for event in agent.stream(
                {"messages": [HumanMessage(content=full_prompt)]},
                {"recursion_limit": self.max_iterations},
                stream_mode="updates",
        ):
            if "agent" in event:
                # Agent思考/输出
                yield {
                    "type": "agent",
                    "content": event["agent"].get("content", ""),
                }
            elif "tool" in event:
                # 工具执行
                yield {
                    "type": "tool",
                    "tool_name": event["tool"].get("name", ""),
                    "result": event["tool"].get("result", ""),
                }
            elif "final" in event:
                # 最终回答
                answer = event["final"].get("content", "")
                self.memory.add_message("assistant", answer)
                yield {
                    "type": "final",
                    "content": answer,
                }



























