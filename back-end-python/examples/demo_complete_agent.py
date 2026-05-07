"""
完整高级Agent演示
运行方式: python demo_complete_agent.py
"""

from src.complete_agent import CompleteAdvancedAgent


def main():
    print("=" * 70)
    print("完整高级Agent演示")
    print("=" * 70)

    #创建agent
    agent = CompleteAdvancedAgent(
        max_history=10,
        max_iterations=6,
        max_retries=3,
        enable_reflection=True,
    )

    #演示多轮对话
    questions = [
        "帮我计算 (1+2)**3",
        "刚才的结果是多少？（测试记忆）",
        "统计'你好世界'的字符数",
        "从知识库查询环境保护知识",
    ]
    for i, question in enumerate(questions):
        print(f"\n【第{i + 1}轮】问题：{question}")
        print("-" * 50)

        result = agent.chat(question)

        print(f"回答：{result['answer']}")
        print(f"工具调用：{result.get('tool_calls', [])}")
        print(f"反思评分：{result.get('reflection', 'N/A')[:100]}...")
        print(f"成功：{result['success']}")

    # 演示流式输出
    print("\n" + "=" * 70)
    print("流式输出演示")
    print("=" * 70)

    agent.reset()
    question = "计算 25*4，然后统计结果字符数"

    print(f"\n问题：{question}")
    print("-" * 50)

    for event in agent.chat_stream(question):
        if event["type"] == "thinking":
            print(f"[思考] {event['content'][:30]}...")
        elif event["type"] == "tool_call":
            print(f"[工具] 调用 {event['tool']}")
        elif event["type"] == "answer":
            print(f"[回答] {event['content']}")
        elif event["type"] == "complete":
            print(f"[完成] {event['message']}")


if __name__ == "__main__":
    main()
