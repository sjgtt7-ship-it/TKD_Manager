import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json

# 1. 구글 시트 연결 (Secrets 방식)
def connect_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Streamlit Secrets에서 보안 정보 가져오기
        creds_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        
        client = gspread.authorize(creds)
        return client.open("TKD_Data")
    except Exception as e:
        st.error(f"연결 실패: {e}")
        return None

def main():
    st.set_page_config(page_title="태권도 스마트 관리 시스템", layout="wide")
    ss = connect_sheet()
    if not ss:
        st.error("구글 시트 연결 실패! Secrets 설정을 확인하세요.")
        return

    sheet_member = ss.get_worksheet(0)
    sheet_log = ss.get_worksheet(1)

    st.sidebar.title("🥋 관장님 전용 메뉴")
    main_mode = st.sidebar.selectbox("모드 선택", ["📢 출석체크 모드", "💻 관리자 페이지"])

    if main_mode == "📢 출석체크 모드":
        st.title("아이들 출석용 화면")
        number = st.text_input("뒷번호 4자리 입력", max_chars=4, type="password")
        if st.button("출석 확인", use_container_width=True):
            data = sheet_member.get_all_records()
            found = False
            for row in data:
                if str(row['Phone']) == number:
                    name = row['Name']
                    p_phone = str(row['ParentPhone']).replace("-", "")
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # 매크로 발송용 신호
                    sms_signal = f"SEND_SMS|{p_phone}|[태권도] {name} 관원이 등원했습니다."
                    sheet_log.append_row([now, name, p_phone, "등원", sms_signal])
                    st.success(f"✅ {name} 관원 확인! 즐겁게 운동하자!")
                    found = True
                    break
            if not found:
                st.error("등록되지 않은 번호입니다.")

    else:
        st.title("💻 관리자 상세 제어센터")
        col1, col2, col3 = st.columns(3)
        if "admin_menu" not in st.session_state: st.session_state.admin_menu = "원생명부"
        with col1:
            if st.button("👤 원생명부/등록", use_container_width=True): st.session_state.admin_menu = "원생명부"
        with col2:
            if st.button("📊 출결 현황", use_container_width=True): st.session_state.admin_menu = "출결현황"
        with col3:
            if st.button("⚙️ 시스템 설정", use_container_width=True): st.session_state.admin_menu = "설정"
        st.divider()

        if st.session_state.admin_menu == "원생명부":
            st.subheader("📝 원생 명부 상세 관리")
            df = pd.DataFrame(sheet_member.get_all_records())
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("변경내용 시트에 저장"):
                sheet_member.clear()
                sheet_member.update([edited_df.columns.values.tolist()] + edited_df.values.tolist(), raw=False)
                st.success("명부가 업데이트되었습니다.")

        elif st.session_state.admin_menu == "출결현황":
            st.subheader("📅 전체 출결 현황")
            logs = pd.DataFrame(sheet_log.get_all_records())
            st.dataframe(logs.sort_index(ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
