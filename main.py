import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json

# 1. 구글 시트 연결 (최종 1줄 Secret 방식)
def connect_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # [수정] key_json 하나로 모든 정보를 읽어옵니다.
        creds_raw = st.secrets["key_json"]
        creds_info = json.loads(creds_raw) # 텍스트를 JSON으로 변환
        
        # 줄바꿈 기호 복구
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open("TKD_Data")
    except Exception as e:
        st.error(f"⚠️ 연결 실패: {e}")
        return None

def main():
    st.set_page_config(page_title="태권도 스마트 시스템", layout="wide")
    ss = connect_sheet()
    if not ss: return

    sheet_member = ss.get_worksheet(0)
    sheet_log = ss.get_worksheet(1)

    st.sidebar.title("🥋 메뉴")
    mode = st.sidebar.selectbox("선택", ["📢 출석체크", "💻 관리자"])

    if mode == "📢 출석체크":
        st.title("🥋 출석 번호 입력")
        num = st.text_input("뒷번호 4자리", max_chars=4, type="password")
        if st.button("확인", use_container_width=True):
            data = sheet_member.get_all_records()
            for row in data:
                if str(row['Phone']) == num:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sheet_log.append_row([now, row['Name'], row['ParentPhone'], "등원"])
                    st.success(f"✅ {row['Name']} 등원 완료!")
                    return
            st.error("번호를 찾을 수 없습니다.")
    else:
        st.title("💻 관리자 페이지")
        df = pd.DataFrame(sheet_member.get_all_records())
        st.data_editor(df, use_container_width=True)

if __name__ == "__main__":
    main()
