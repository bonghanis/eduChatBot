import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

def get_authorize():
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
    temp = {}
    gc = get_authorize()
    ws = gc.open_by_url(st.secrets["sheet_url"]).worksheet("정보")
    url = ws.acell("B1").value
    serviceOnOff = ws.acell("B2").value.lower()
    print(serviceOnOff)
    sheet = gc.open_by_url(url).worksheet("설정")
    data = sheet.col_values(2)

    temp["AI"] = data[0]
    temp["key"] = data[1]
    temp["model"] = data[2]
    temp["max_tokens"] = int(data[3])
    temp["temperature"] = float(data[4])
    temp["system"] = data[5]
    temp["stream"] = True if data[6].lower() == 'true' else False
    temp["url"] = url
    temp["serviceOnOff"] = serviceOnOff
    
    return temp

def addContent(role, content):
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
    
    return new_worksheet
    #return doc.add_worksheet(title=name, rows=100, cols=20)