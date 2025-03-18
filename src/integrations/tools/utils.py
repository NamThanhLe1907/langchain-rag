from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.runnables import RunnableLambda

from langgraph.prebuilt import ToolNode


def handle_tool_error(state: dict) -> dict:
    error = state.get("error")
    tool_call_id = state.get("tool_call_id")
    return {
        "messages": [
            ToolMessage(
                tool_call_id=tool_call_id,
                content=f"Tool error: {str(error)}"
            )
        ]
    }

def create_tool_node_with_fallback(tools: list):
    def _get_tool_call_id(state: dict):
        # Lấy tool_call_id từ message AI cuối cùng
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                return msg.tool_calls[0]["id"]
        return None

    return ToolNode(tools).with_fallbacks(
        [
            RunnableLambda(lambda x: {
                "error": x["error"],
                "tool_call_id": _get_tool_call_id(x)
            }) | RunnableLambda(handle_tool_error)
        ],
        exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)