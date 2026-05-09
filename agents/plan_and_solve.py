from planner import Planner
from executor import Executor


class PlanAndSolveAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        print(f"\n--- 开始处理问题 ---\n问题: {question}")

        plan = self.planner.plan(question)

        if not plan:
            print("\n--- 任务终止 --- \n无法生成有效的行动计划。")
            return

        final_answer = self.executor.execute(question, plan)

        print(f"\n--- 任务完成 ---\n最终答案: {final_answer}")


if __name__ == '__main__':
    from llm_client import HelloAgentsLLM

    llmClient = HelloAgentsLLM()
    agent = PlanAndSolveAgent(llmClient)

    question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
    agent.run(question)
