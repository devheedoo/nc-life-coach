import asyncio
import base64
import os

import streamlit as st
from dotenv import load_dotenv
from agents import Agent, FileSearchTool, Runner, WebSearchTool, ImageGenerationTool
from openai import OpenAI

from session_store import SESSION_STORE_VERSION, LifeCoachSQLiteSession

load_dotenv()
vector_store_id = os.getenv("VECTOR_STORE_ID")

st.title("Life Coach: Web Search")

client = OpenAI()

# 에이전트 초기화
if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach",
        instructions="""
        You are a life coach that helps users achieve their goals. You are friendly and encouraging.
        Always behave like a life coach whose role is to encourage and uplift the user.

        답변 언어: 사용자에게 보이는 최종 답변과 설명은 항상 한국어로 작성한다. 사용자가 다른 언어를 명시적으로 요청한 경우만 예외로 한다.

        Image generation (Image Generation Tool) — use proactively when it helps motivation or clarity:
            - Goal-based vision board: Collage-style boards that represent the user's themes (e.g. health, learning, travel). When goals live in uploaded documents, call File Search first to ground themes and wording, then Web Search as required by workflow, then generate the image with a rich, specific prompt (themes, colors, mood, layout).
            - Motivational poster: Short, customized headline-style message plus supportive visuals. Align copy with what you know from the conversation or files.
            - Progress visualization: Charts, timelines, milestone ribbons, or infographic-style images that make progress tangible (e.g. books read, streaks, phases completed).
            - Weave tools in one turn when appropriate: e.g. retrieve goals with File Search, satisfy Web Search obligation if applicable, acknowledge goals briefly in Korean, then generate the image—so File Search + Web Search + Image Generation feel like one coaching moment, not separate steps.
            - Celebrations & wins: When the user shares an achievement, offer genuine praise in Korean and offer to generate a congratulations image; use Image Generation with a prompt that names their win clearly.
            - Image prompts: Prefer vivid, concrete descriptions (scene, composition, text on image if any). Keep user-visible coaching in Korean; image-generation prompts may be in English or Korean depending on what produces the best result.

        Mandatory tool workflow (same user turn):
            - If you call File Search for the user's message, you MUST also call Web Search before you write your final answer—every time—using 1-3 focused queries informed by the file excerpts and the user's question (e.g., evidence-based tips, exercise ideas, progression or safety notes aligned with their stated goal). For vision boards grounded in files, queries can include composition/motivation/visual-planning angles that still integrate with their goals.
            - Do not end your turn with only File Search. Do not give coaching, tips, or progress commentary based solely on retrieved files without a Web Search pass in that same turn.
            - Exceptions (rare): the user explicitly asks for file-only content, or the question is purely verbatim extraction from a document with no sensible external angle.
            - Merge results into one unified reply: weave file-grounded personalization with web-sourced guidance in a single coherent narrative. Avoid a pile of generic tips that ignore web findings; avoid bolting web content on as an unrelated appendix—integrate them so the answer reads as one coach response.

        You have access to the following tools:
            - Web Search Tool: Use for anything not fully covered by training data, current/future events, and unknowns—search first when unsure. After File Search, Web Search is required in the same turn (see workflow above). For workout or fitness goals, prioritize evidence-informed ideas, programming patterns, and safety; tie them to the user's goals and constraints from files and conversation.
            - File Search Tool: Use when the question depends on facts about the user or content they uploaded. It never replaces Web Search in the same turn: always pair with Web Search and produce the integrated answer described above.
            - Image Generation Tool: For vision boards, motivational posters, progress visuals, and celebration images. Combine naturally with coaching text and, when personalization from files matters, with File Search + Web Search as above.
        """,
        model="gpt-4o-mini",
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[vector_store_id],
                max_num_results=3,
            ),
            ImageGenerationTool(
                tool_config={
                    "type": "image_generation",
                    "quality": "low",
                    "output_format": "jpeg",
                    "model": "gpt-image-1",
                    "partial_images": 1,
                }
            ),
        ],
    )
agent = st.session_state["agent"]

# 세션 메모리 초기화
if (
    "session" not in st.session_state
    or st.session_state.get("_session_store_version") != SESSION_STORE_VERSION
):
    st.session_state["session"] = LifeCoachSQLiteSession(
        session_id="life-coach",
        db_path="life-coach.db",
    )
    st.session_state["_session_store_version"] = SESSION_STORE_VERSION
session = st.session_state["session"]

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
            elif msg["type"] == "file_search_call":
                with st.chat_message("assistant"):
                    st.write("[목표 문서 검색]")
            elif msg["type"] == "image_generation_call":
                image = base64.b64decode(msg["result"])
                with st.chat_message("assistant"):
                    st.image(image)

asyncio.run(paint_history())

def update_status(status_container, event):
    status_messages = {
        "response.web_search_call.in_progress": ("🔍 Start web search...", "running"),
        "response.web_search_call.searching": ("🔍 Continue web search...", "running"),
        "response.web_search_call.completed": ("✅ Completed web search.", "complete"),

        "response.file_search_call.in_progress": ("🔍 Start file search...", "running"),
        "response.file_search_call.searching": ("🔍 Continue file search...", "running"),
        "response.file_search_call.completed": ("✅ Completed file search.", "complete"),

        "response.image_generation_call.in_progress": ("🔍 Start image generation...", "running"),
        "response.image_generation_call.generating": ("🔍 Continue image generation...", "running"),
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)

# 에이전트 실행
async def run_agent(message):
    with st.chat_message("assistant"):
        status_container = st.status("⌛️", expanded=False)
        text_placeholder = st.empty()
        image_placeholder = st.empty()
        stream = Runner.run_streamed(
            agent,
            message,
            session=session,
        )

        response = ""
        async for event in stream.stream_events():
            if event.type == "raw_response_event":
                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)
                elif event.data.type == "response.image_generation_call.partial_image":
                    image = base64.b64decode(event.data.partial_image_b64)
                    image_placeholder.image(image)
                elif event.data.type == "response.completed":
                    image_placeholder.empty()
                    text_placeholder.empty()

# 메시지 입력
prompt = st.chat_input(
    "메시지를 입력하세요...",
    accept_file=True,
    file_type=["txt"]
)

if prompt:
    for file in prompt.files:
        with st.chat_message("assistant"):
            with st.status("⌛️ Uploading file...") as status:
                uploaded_file = client.files.create(
                    file=(file.name, file.getvalue()),
                    purpose="user_data",
                )
                status.update(label="⌛️ Attaching file...")
                client.vector_stores.files.create(
                    vector_store_id=vector_store_id,
                    file_id=uploaded_file.id,
                )
                status.update(label="✅ File uploaded.", state="complete")
    if prompt.text:
        with st.chat_message("user"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))
        st.rerun()

# 사이드바: 세션 초기화
with st.sidebar:
    if st.button("Reset Session"):
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
