import asyncio

import streamlit as st
from dotenv import load_dotenv
from agents import Agent, Runner, SQLiteSession, WebSearchTool
from openai import OpenAI

load_dotenv()

st.title("Life Coach: Web Search")

client = OpenAI()

# 에이전트 초기화
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach",
        instructions="""
        You are a life coach that helps users achieve their goals. You are friendly and encouraging.
        Always behave like a life coach whose role is to encourage and uplift the user.

        You have access to the following tools:
            - Web Search Tool: Use this when the user asks a questions that isn't in your training data. Use this tool when the users asks about current or future events, when you think you don't know the answer, try searching for it in the web first.
        """,
        model="gpt-4o-mini",
        tools=[WebSearchTool()],
    )
agent = st.session_state["agent"]

# 세션 메모리 초기화
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        session_id="life-coach",
        db_path="life-coach.db",
    )
session = st.session_state["session"]

# 사이드바: 세션 초기화
with st.sidebar:
    if st.button("Reset Session"):
        asyncio.run(session.clear_session())

# 메시지 표시
async def paint_history():
    messages = await session.get_items()
    for msg in messages:
        if "role" in msg:
            with st.chat_message(msg["role"]):
                if msg["role"] == "user":
                    st.write(msg["content"])
                else:
                    st.write(msg["content"][0]["text"])
        if "type" in msg:
            if msg["type"] == "web_search_call":
                with st.chat_message("assistant"):
                    st.write(f'[웹 검색: "{msg["action"]["query"]}"]')
asyncio.run(paint_history())

# 에이전트 실행
async def run_agent(message):
    with st.chat_message("assistant"):
        placeholder = st.empty()
        stream = Runner.run_streamed(
            agent,
            message,
            session=session
        )

        response = ""
        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    placeholder.write(response)

# 메시지 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    asyncio.run(run_agent(prompt))

with st.sidebar:
    st.write(asyncio.run(session.get_items()))
