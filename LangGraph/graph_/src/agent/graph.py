"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph


class Configuration(TypedDict):
    """Configurable parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    my_configurable_param: str


@dataclass
class State:
    """Input state for the agent.

    Defines the initial structure of incoming data.
    See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
    """

    changeme: str = "example"


async def call_model(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """Process input and returns output.

    Can use runtime configuration to alter behavior.
    """
    configuration = config["configurable"]# 获取配置
    return {
        "changeme": "output from call_model. "
        f'Configured with {configuration.get("my_configurable_param")}'# 获取具体参数值
    }


# Define the graph
graph = (
    StateGraph(State, config_schema=Configuration)
    #config_schema参数接受一个TypedDict类型，用于声明图形运行时可以动态配置的参数
    #这些参数可以在创建或调用图形时动态传入，用于改变图形行为
    .add_node(call_model)
    .add_edge("__start__", "call_model")
    .compile(name="New Graph")
)


