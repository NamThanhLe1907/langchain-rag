from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition
from assistants import Assistant, State
from tools.tool_util import create_tool_node_with_fallback
from dotenv import load_dotenv
load_dotenv() 
# Giả sử bạn đã có part_1_assistant_runnable và part_1_tools được định nghĩa (danh sách các tool của bạn)
# Ví dụ: (bạn có thể tái sử dụng primary_assistant_prompt và llm từ code AIAgentFAQ cũ)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.config import RunnableConfig
from langchain_community.tools.tavily_search import TavilySearchResults
from tools.exec_tools import (fetch_user_flight_information, search_flights, lookup_policy,
                               update_ticket_to_new_flight, cancel_ticket,
                               search_car_rentals, book_car_rental, update_car_rental, cancel_car_rental,
                               search_hotels, book_hotel, update_hotel, cancel_hotel,
                               search_trip_recommendations, book_excursion, update_excursion, cancel_excursion)
from datetime import datetime

from langsmith import Client

llm = ChatOpenAI(model="gpt-4o-mini")

# Xây dựng prompt cho assistant
assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Swiss Airlines. "
            "Use the provided tools to search for flights, company policies, and other information to assist the user's queries. "
            "When searching, be persistent. Expand your query bounds if the first search returns no results. "
            "If a search comes up empty, expand your search before giving up."
            "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
            "\nCurrent time: {time}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

part_3_safe_tools = [
    TavilySearchResults(max_results=1, tavily_api_key="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"),
    fetch_user_flight_information,
    search_flights,
    lookup_policy,
    search_car_rentals,
    search_hotels,
    search_trip_recommendations,
]

part_3_sensitive_tools = [
    update_ticket_to_new_flight,
    cancel_ticket,
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
    book_hotel,
    update_hotel,
    cancel_hotel,
    book_excursion,
    update_excursion,
    cancel_excursion,

]
sensitive_tool_names = {t.name for t in part_3_sensitive_tools}
part_3_assistant_runnable = assistant_prompt | llm.bind_tools(part_3_safe_tools+part_3_sensitive_tools)

#
# ✅ Dùng State từ Assistant
builder = StateGraph(State)

client = Client()

def log_to_langsmith(run_name, state: State):
    """Ghi logs vào LangSmith để theo dõi quá trình chạy của LangGraph."""
    client.create_run(
        name=run_name,
        inputs=state,
        run_type="chain",
    )

def user_info(state: State, config: RunnableConfig):
    """✅ Truyền `config` để đảm bảo `passenger_id` tồn tại."""
    return {"user_info": fetch_user_flight_information.invoke(config)}

def route_tools(state: State):
    next_node = tools_condition(state)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in sensitive_tool_names:
        return "sensitive_tools"
    return "safe_tools"

# ✅ Thêm các node vào Graph
builder.add_node("fetch_user_info", user_info)
builder.add_edge(START, "fetch_user_info")
builder.add_node("assistant", Assistant(part_3_assistant_runnable))
builder.add_node("safe_tools", create_tool_node_with_fallback(part_3_safe_tools))
builder.add_node(
    "sensitive_tools", create_tool_node_with_fallback(part_3_sensitive_tools)
)
# Define logic
builder.add_edge("fetch_user_info", "assistant")
builder.add_conditional_edges(
    "assistant", route_tools, ["safe_tools", "sensitive_tools", END]
)
builder.add_edge("safe_tools", "assistant")
builder.add_edge("sensitive_tools", "assistant")

memory = MemorySaver()
part_3_graph = builder.compile(
    checkpointer=memory,
    # NEW: The graph will always halt before executing the "tools" node.
    # The user can approve or reject (or even alter the request) before
    # the assistant continues
    interrupt_before=["sensitive_tools"],
)


#log_to_langsmith("init_graph", {"status": "Graph initialized"})
