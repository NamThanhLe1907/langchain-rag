from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition
from data.state import State
from assistants import Assistant
from tools.tool_util import create_tool_node_with_fallback
from dotenv import load_dotenv
load_dotenv() 
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

part_1_tools = [
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

part_1_assistant_runnable = primary_assistant_prompt | llm.bind_tools(part_1_tools)

# Xây dựng graph
builder = StateGraph(State)
builder.add_node("assistant", Assistant(part_1_assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(part_1_tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")
memory = MemorySaver()
part_1_graph = builder.compile(checkpointer=memory)

# part_1_graph bây giờ là graph hoàn chỉnh với state, assistant và tools.
