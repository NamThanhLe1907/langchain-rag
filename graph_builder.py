import json
from typing import Optional,Type,Any
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition
from assistants import Assistant, State
from tools.tool_util import create_tool_node_with_fallback
from dotenv import load_dotenv
load_dotenv() 
from langsmith import Client
# Giả sử bạn đã có part_1_assistant_runnable và part_1_tools được định nghĩa (danh sách các tool của bạn)
# Ví dụ: (bạn có thể tái sử dụng primary_assistant_prompt và llm từ code AIAgentFAQ cũ)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from tools.exec_tools import (fetch_user_flight_information, search_flights, lookup_policy,
                               update_ticket_to_new_flight, cancel_ticket,
                               search_car_rentals, book_car_rental, update_car_rental, cancel_car_rental,
                               search_hotels, book_hotel, update_hotel, cancel_hotel,
                               search_trip_recommendations, book_excursion, update_excursion, cancel_excursion)
from datetime import datetime

llm = ChatOpenAI(model="gpt-4o-mini")

# Xây dựng prompt cho assistant
primary_assistant_prompt = ChatPromptTemplate.from_messages(
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

part_2_tools = [
    # TavilySearchResults(max_results=1, tavily_api_key="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"),
    fetch_user_flight_information,
    search_flights,
    lookup_policy,
    update_ticket_to_new_flight,
    cancel_ticket,
    search_car_rentals,
    book_car_rental,
    update_car_rental,
    cancel_car_rental,
    search_hotels,
    book_hotel,
    update_hotel,
    cancel_hotel,
    search_trip_recommendations,
    book_excursion,
    update_excursion,
    cancel_excursion,
]

part_2_assistant_runnable = primary_assistant_prompt | llm.bind_tools(part_2_tools)



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



# ✅ Thêm các node vào Graph
builder.add_node("fetch_user_info", user_info)
builder.add_edge(START, "fetch_user_info")
builder.add_node("assistant", Assistant(part_2_assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(part_2_tools))
builder.add_edge("fetch_user_info", "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

# ✅ Khởi tạo LangGraph
memory = MemorySaver()


log_to_langsmith("init_graph", {"status": "Graph initialized"})