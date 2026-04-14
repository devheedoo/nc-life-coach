import streamlit as st

def main():
    st.title("Life Coach: Web Search")

    # 메시지 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = list()

    # 메시지 표시
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 메시지 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": prompt})


if __name__ == "__main__":
    main()
