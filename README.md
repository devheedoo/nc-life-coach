# Life Coach: Web Search

- Streamlit UI와 웹 검색 기능을 갖춘 Life Coach Agent의 기초를 구축하세요!
- Life Coach가 갖춰야 할 기능:
  - Streamlit으로 구축된 채팅 인터페이스
  - OpenAI Agents SDK 사용 (Agent + Runner)
  - 동기부여 콘텐츠, 자기 개발 팁, 습관 형성 조언을 검색하는 웹 검색 도구

## Requirements

- [x] Streamlit으로 UI를 구현하세요 (st.chat_input, st.chat_message).
- [x] 코치가 대화를 기억하도록 세션 메모리를 구현하세요.
- [x] 에이전트가 관련 조언을 검색할 수 있는 웹 검색 도구를 추가하세요.
- [x] 에이전트는 유저를 격려하는 라이프 코치처럼 행동해야 합니다.

## Example

```
User: 아침에 일찍 일어나고 싶은데 자꾸 알람을 끄게 돼
Coach: [웹 검색: "아침에 일찍 일어나는 팁"]
Coach: 좋은 목표네요! 효과가 검증된 방법들을 알려드릴게요: 1. 알람을 침대에서 먼 곳에 두세요...

User: 좋은 습관을 만들려면 어떻게 해야 해?
Coach: [웹 검색: "습관 만들기 기술"]
Coach: 가장 효과적인 방법은 "습관 쌓기(habit stacking)" 기법입니다...
```
