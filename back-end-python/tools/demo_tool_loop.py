"""
工具调用闭环演示
运行方式: python demo_tool_loop.py
"""


from tools.tool_integration import create_llm_with_tools, run_tool_call_loop

def main():
    llm_with_tools,tools=create_llm_with_tools()

    question="帮我计算 (1+2)**3，然后统计'你好 world'的英文单词数"

    result=run_tool_call_loop(llm_with_tools,tools,question)
    print(f"最终回答: {result}")
if __name__ == "__main__":
    main()