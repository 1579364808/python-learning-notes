"""
Hello Agents — 第四章 智能体经典范式构建
=========================================
使用方法:
  1. 复制 .env.example 为 .env，填入你的 API 密钥
  2. pip install openai python-dotenv google-search-results
  3. 运行 python main.py
"""

from llm_client import HelloAgentsLLM
from tool_executor import ToolExecutor, search
from react_agent import ReActAgent
from plan_and_solve import PlanAndSolveAgent
from reflection_agent import ReflectionAgent


def demo_react():
    print("=" * 60)
    print("演示: ReAct 智能体 (思考-行动-观察)")
    print("=" * 60)

    toolExecutor = ToolExecutor()
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)

    llmClient = HelloAgentsLLM()
    agent = ReActAgent(llm_client=llmClient, tool_executor=toolExecutor, max_steps=5)

    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    agent.run(question)


def demo_reflection():
    print("\n" + "=" * 60)
    print("演示: Reflection 智能体 (执行-反思-优化)")
    print("=" * 60)

    llmClient = HelloAgentsLLM()
    agent = ReflectionAgent(llm_client=llmClient, max_iterations=3)

    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    agent.run(task)


def demo_plan_and_solve():
    print("\n" + "=" * 60)
    print("演示: Plan-and-Solve 智能体 (先规划，后执行)")
    print("=" * 60)

    llmClient = HelloAgentsLLM()
    agent = PlanAndSolveAgent(llmClient)

    question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
    agent.run(question)


if __name__ == '__main__':
    # 取消注释即可运行对应的演示
    # demo_react()
    # demo_plan_and_solve()
    demo_reflection()
