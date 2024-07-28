import streamlit as st
from streamlit import logger
import anthropic
from utils import gs
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

def initialize(api_key, nick_name):
    if "bot" and "sheet" in st.session_state:
        return
    
    logger.get_logger(__name__).info("초기화")
    # Anthropic
    st.session_state["api_key"] = api_key
    st.session_state["bot"] = anthropic.Anthropic(api_key = api_key)
    st.session_state["user_name_1"] = nick_name

    # Google Spread Sheet
    gc = gs.get_authorize()
    sheet_url = st.session_state["setupInfo"]["url"]
    doc = gc.open_by_url(sheet_url)
    st.session_state["sheet"] = gs.get_worksheet(doc, nick_name)

def setClassInfo():
    st.session_state['setupInfo'] = gs.getSetupInfo()

@st.experimental_dialog("출입문")
def key():
    password = st.text_input("비밀번호")

def main():
    if "setupInfo" not in st.session_state:
        logger.get_logger(__name__).info("클래스 정보 설정")
        setClassInfo()
    
    if st.session_state["setupInfo"]["serviceOnOff"] == "off":
        st.title("❤🥰지금은 휴식중입니다.🥰❤")
        return

    # 사이드바 
    # user_name = ''

    with st.sidebar:
        # 페이지 제목 설정
        st.title("교육용 챗봇")

        # api key 입력
        api_key = st.text_input("API 키를 입력하세요:", type = "password")
        api_key = st.session_state["setupInfo"]["key"]
        
        user_name = st.text_input("대화명을 입력하세요:")

        if api_key and user_name:
            initialize(api_key, user_name)
            client = st.session_state["bot"]

        # 대화 다운로드 버튼
        if st.button("대화 내용 저장"):
            download_text(toText(st.session_state.messages), st.session_state["user_name_1"] + ".txt")
    
    # if api_key and user_name:
    #     client = anthropic.Anthropic(api_key = api_key)

    # 시스템 메시지 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": st.session_state["setupInfo"]['system']}]

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
        
        gs.addContent("user", prompt)

        # OpenAI 모델 호출
        if "api_key" in st.session_state:
            full_response = ""
            setupInfo = st.session_state['setupInfo']

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.write("......")
                stream = client.messages.create(
                    model=setupInfo['model'],
                    max_tokens=setupInfo['max_tokens'],
                    temperature=setupInfo['temperature'],
                    system = setupInfo['system'],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[1:]],
                    stream = setupInfo['stream']
                )

                for chunk in stream:
                    if chunk.type == "content_block_delta":
                        full_response += chunk.delta.text
                    elif chunk.type == "message_start":
                        # 메시지 시작 이벤트 처리 (필요한 경우)
                        pass
                    elif chunk.type == "message_delta":
                        # 메시지 델타 이벤트 처리 (필요한 경우)
                        pass
                    elif chunk.type == "message_stop":
                        # 메시지 종료 이벤트 처리 (필요한 경우)
                        break
                    message_placeholder.write(full_response + "▌")

                message_placeholder.write(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})
            gs.addContent("assistant", full_response)

if __name__ == "__main__":
    main()
