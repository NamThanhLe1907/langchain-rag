from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import HumanMessage, AIMessage


class State(TypedDict):
    messages: Annotated[list[HumanMessage | AIMessage], add_messages]
