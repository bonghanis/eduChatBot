import streamlit as st
from openai import OpenAI
import json

def toText(messages):
    """주고 받은 메세지를 텍스트로 변환하는 함수"""
    text = ''
    
    for conversation in st.session_state.messages:
        if conversation['role'] == 'user':
        # 유저 발언 추가
            text += f"유저: {conversation['content']}\n"
        elif conversation['role'] == 'assistant':
        # 챗봇 발언 추가
            text += f"친구봇: {conversation['content']}\n"
    
    # with open(st.session_state["user_name_1"] + '.txt', "w", encoding="utf-8") as f:
    #     f.write(text)
    return text

def download_text(text, filename):
    """텍스트를 파일로 다운로드하는 함수"""
    binary = text.encode()
    mime = "text/plain;charset=utf-8"
    st.download_button(
        label="텍스트 다운로드",
        data=binary,
        file_name=filename,
        mime=mime,
    )

def main():
    # 사이드바 
    user_name = ''

    with st.sidebar:
        # 페이지 제목 설정
        st.title("교육용 챗봇")

        # # api key 입력
        # api_key = st.text_input("API 키를 입력하세요:", type = "password")
        
        # if api_key:
        #     st.session_state["api_key"] = api_key

        st.session_state["api_key"] = st.secrets["API_KEY"]
        
        # user name 입력
        if user_name := st.text_input("대화명을 입력하세요:"):
            st.session_state["user_name_1"] = user_name


        # 대화 다운로드 버튼
        if st.button("대화 내용 저장"):
            download_text(toText(st.session_state.messages), st.session_state["user_name_1"] + ".txt")
    

    

    # API 클라이언트 초기화
    if "api_key" in st.session_state:
        client = OpenAI(api_key=st.session_state["api_key"])

    system_message = '''
    너의 이름은 친구봇이야.
    너는 항상 반말을 하는 챗봇이야. 다나까나 요 같은 높임말로 절대로 끝내지 마
    항상 반말로 친근하게 대답해줘.
    영어로 질문을 받아도 무조건 한글로 답변해줘.
    한글이 아닌 답변일 때는 다시 생각해서 꼭 한글로 만들어줘
    모든 답변 끝에 답변에 맞는 이모티콘도 추가해줘
    '''

    # 시스템 메시지 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_message}]

    # 챗 메시지 출력
    for idx, message in enumerate(st.session_state.messages):
        if idx > 0:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("대와 내용을 입력해 주세요."):
        if not user_name:
            st.warning('대화명을 입력해 주세요!', icon='⚠️')
            return

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)


        # OpenAI 모델 호출
        if "api_key" in st.session_state:
            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
