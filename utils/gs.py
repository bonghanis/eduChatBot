import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

def get_authorize():
    """
    Google Sheets API에 접근하기 위한 인증된 gspread 클라이언트를 생성하는 함수입니다.

    Returns:
        gspread.Client: 인증된 gspread 클라이언트 객체

    이 함수는 다음과 같은 작업을 수행합니다:
    1. Streamlit의 secrets에서 서비스 계정 키 정보를 가져옵니다.
    2. 가져온 정보를 사용하여 Credentials 객체를 생성합니다.
    3. 생성된 Credentials를 사용하여 인증된 gspread 클라이언트를 반환합니다.

    Note:
    - 이 함수는 Streamlit의 st.secrets를 사용하여 민감한 인증 정보를 안전하게 관리합니다.
    - Google Sheets API에 대한 접근 범위는 'https://www.googleapis.com/auth/spreadsheets'로 설정됩니다.
    """
    
    # 서비스 계정 key 정보를 딕셔너리 형태로 정의합니다.
    service_account_info = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    }

    # Credentials 객체 생성
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

    # gspread 클라이언트 생성
    return gspread.authorize(creds)

def getSetupInfo():
    """
    Google Sheets에서 설정 정보를 가져오는 함수입니다.

    Returns:
        dict: 다음 키를 포함하는 설정 정보 딕셔너리
            - url: 수업할 시트의 URL
            - serviceOnOff: 서비스 활성화 여부
            - AI: 사용할 생성형 AI 서비스 이름
            - key: API 키
            - model: 사용할 AI 모델
            - max_tokens: 최대 토큰 수 (정수)
            - temperature: 온도 설정 (부동소수점)
            - select: 선택 옵션
            - system: 시스템 프롬프트
            - a_p: 종합 평가 프롬프트
            - e_p: 평어 프롬프트
            - stream: 스트리밍 모드 사용 여부 (불리언)

    Note:
    - 이 함수는 st.secrets["sheet_url"]에 저장된 URL의 Google Sheets에서 정보를 가져옵니다.
    - "정보" 워크시트의 2번째 열에서 데이터를 읽어옵니다.
    - 데이터는 0부터 11까지의 인덱스로 구성되며, 각 인덱스는 주석에 설명된 정보를 나타냅니다.
    0 수업할 시트
    1 서비스 여부
    2 생성형AI
    3 API KEY
    4 model
    5 max_tokens
    6 temperature
    7 select
    8 system
    9 a_p
    10 e_p
    11 stream
    """

    gc = get_authorize()
    ws = gc.open_by_url(st.secrets["sheet_url"]).worksheet("정보")
    
    # 정보 데이터 가져오기
    data = ws.col_values(2)
    temp = {}
    temp["url"] = data[0]
    temp["serviceOnOff"] = data[1].lower()
    temp["AI"] = data[2]
    temp["key"] = data[3]
    temp["model"] = data[4]
    temp["max_tokens"] = int(data[5])
    temp["temperature"] = float(data[6])
    temp["select"] = data[7]
    temp["system"] = data[8]
    temp["a_p"] = data[9]
    temp["e_p"] = data[10]
    temp["stream"] = True if data[11].lower() == 'true' else False   
    
    return temp

def add_Content(role, content):
    """
    대화 내용을 Google Sheets에 추가하는 함수입니다.

    Parameters:
        role (str): 메시지 작성자의 역할. "user" 또는 "assistant" 중 하나여야 합니다.
        content (str): 추가할 메시지 내용

    이 함수는 현재 시간, 역할, 그리고 메시지 내용을 포함하는 새로운 행을
    세션 상태에 저장된 Google Sheets 워크시트에 추가합니다.
    """
    contents = [get_timestamp()]

    if role == "user":
        contents += ["USER", content]
    elif role == "assistant":
        contents +=["ASSISTANT", content]

    st.session_state["sheet"].append_row(contents)

def get_timestamp():
    """
    현재 시간을 아시아/서울 시간대 기준으로 "시:분" 형식의 문자열로 반환합니다.

    Returns:
        str: "HH:MM" 형식의 현재 시간 문자열
    """
    return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H:%M")

def get_worksheet(doc, name):
    """
    Google Sheets 문서에서 특정 이름의 워크시트를 찾거나 생성하는 함수입니다.

    Parameters:
        doc (gspread.Spreadsheet): 워크시트를 찾을 Google Sheets 문서 객체
        name (str): 찾거나 생성할 워크시트의 이름

    Returns:
        gspread.Worksheet: 기본 워크시트 또는 새로 생성한 워크시트 객체

    이 함수는 먼저 주어진 이름의 워크시트를 찾습니다. 
    없으면 '템플릿' 시트를 복사하여 새 워크시트를 생성하고, 
    생성된 시트로의 하이퍼링크를 '수업요약' 시트에 추가합니다.
    """
    for sheet in doc.worksheets():
        if sheet.title == name:
            print("시트 찾음")
            return sheet

    # 복사할 원본 시트 선택
    source_worksheet = doc.worksheet('템플릿')
    # 새 시트 생성 (원본 시트 복사)
    new_worksheet = doc.duplicate_sheet(
        source_worksheet.id, 
        insert_sheet_index = 100, 
        new_sheet_name = name
    )

    add_Hyperlink(doc, new_worksheet.id, name)

    return new_worksheet

def add_Hyperlink(doc, id, nick_name):
    """
    Google Sheets 문서에 하이퍼링크를 추가하는 함수입니다.

    Parameters:
        doc (gspread.Spreadsheet): 하이퍼링크를 추가할 Google Sheets 문서 객체
        id (str): 링크의 대상이 될 시트의 gid
        nick_name (str): 하이퍼링크에 표시될 텍스트

    이 함수는 "수업요약" 시트의 A열 다음 빈 행에 하이퍼링크를 추가합니다.
    하이퍼링크는 같은 문서 내의 다른 시트로 연결됩니다.
    """

    
    sheet = doc.worksheet("수업요약")
    next_row = len(sheet.col_values(2)) + 1
    content = f'=HYPERLINK("#gid={id}", "{nick_name}")'
    sheet.update("A" + str(next_row), [[False]])
    sheet.update_acell("B" + str(next_row), content)

def delete_message():
    """
    대화 기록 중 마지막 대화를 삭제하는 함수입니다.

    이 함수는 다음과 같은 작업을 수행합니다:
    1. 세션 상태에서 현재 활성화된 워크시트를 가져옵니다.
    2. 워크시트의 첫 번째 열에서 데이터가 있는 마지막 행의 번호를 찾습니다.
    3. 해당 행을 삭제합니다(마지막 대화 삭제).
    """
    target = st.session_state["sheet"]
    target_row = len(target.col_values(1))
    target.delete_rows(target_row)

def get_summary_sheet(doc):
    """
    Returns:
        '수업요약' 시트를 리턴
    """
    return doc.worksheet("수업요약")