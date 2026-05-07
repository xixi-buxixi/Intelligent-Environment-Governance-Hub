
"""
Agent演示脚本
运行方式: python demo_agent.py
"""

from src.agent import run_agent

def main():
    question = "帮我算 (1+2)**3，统计'你好 world'的英文单词数，告诉我现在时间。"

    result = run_agent(question)

    print("=" * 50)
    print("最终回答:")
    print(result["messages"][-1].content)
    print("=" * 50)

    print("过程回放（messages）:")
    for msg in result["messages"]:
        # 只做简单展示：打印消息类型 + 内容
        print(f"[{msg.__class__.__name__}] {getattr(msg, 'content', '')}")


if __name__ == "__main__":
    main()