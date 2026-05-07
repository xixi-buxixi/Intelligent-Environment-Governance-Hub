"""
高级Agent演示脚本（带记忆）
运行方式: python demo_advanced_agent.py
"""

from src.advanced_agent import AdvancedAgent


def demo_memory():
    """带记忆的Agent演示"""
    agent=AdvancedAgent(max_history=5,max_iterations=6)

     # 第一轮对话
    print("\n【第一轮】")
    question1 = "帮我计算 (1+2)**3"
    result1 = agent.chat(question1)
    print(f"问题: {question1}")
    print(f"回答: {result1}")
    print(f"回答: {result1['answer']}")
    print(f"工具调用: {result1['tool_calls']}")


    # 第二轮对话（测试记忆）
    print("\n【第二轮】")
    question2 = "刚才的计算结果是多少？"
    result2 = agent.chat(question2)
    print(f"问题: {question2}")
    print(f"回答: {result2['answer']}")
    print(f"（Agent能记住之前的计算结果）")


 # 第三轮对话
    print("\n【第三轮】")
    question3 = "统计'你好世界'的字符数"
    result3 = agent.chat(question3)
    print(f"问题: {question3}")
    print(f"回答: {result3['answer']}")

    # 显示完整历史
    print("\n【对话历史】")
    for msg in result3['history']:
        print(f"[{msg['role']}]: {msg['content'][:50]}...")


def main():
    demo_memory()


if __name__ == "__main__":
    main()
















