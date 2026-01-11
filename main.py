import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import json

# 1. 구글 시트 연결 함수 (인터넷 배포용)
def connect_sheet():
    try:
        # 보안 연결을 위한 범위 설정
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Streamlit Secrets(금고)에서 보안 정보 가져오기
        creds_info = st.secrets["gcp_service_account"].to_dict()
        
        # 줄바꿈 기호(\n)를 실제 줄바꿈으로 변환 (보안 연결 필수 과정)
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # 구글 시트 이름 열기 (TKD_Data)
        return client.open("TKD_Data")
    except Exception as e:
        st.error(f"⚠️ 연결 실패: {e}")
        return None

def main():
    # 페이지 제목 및 넓게 보기 설정
    st.set_page_config(page_title="태권도 스마트 관리 시스템", layout="wide")
    
    # 시트 연결 시도
    ss = connect_sheet()
    if not ss:
        st.warning("구글 시트 연결 대기 중... Secrets 설정을 확인해 주세요.")
        return

    # 각 시트 탭 가져오기
    try:
        sheet_member = ss.get_worksheet(0) # 관원 명부 탭
        sheet_log = ss.get_worksheet(1)    # 출결 기록 탭
    except:
        st.error("시트 탭을 불러오지 못했습니다. 탭 순서를 확인하세요.")
        return

    # 사이드바 메뉴 구성
    st.sidebar.title("🥋 관장님 메뉴")
    main_mode = st.sidebar.selectbox("기능 선택", ["📢 출석체크 모드", "💻 관리자 페이지"])

    # --- [모드 1: 출석체크 모드] ---
    if main_mode == "📢 출석체크 모드":
        st.title("🥋 등원 번호를 입력하세요")
        number = st.text_input("뒷번호 4자리", max_chars=4, type="password")
        
        if st.button("출석 확인", use_container_width=True):
            data = sheet_member.get_all_records()
            found = False
            for row in data:
                # 엑셀의 Phone 열과 입력번호 비교
                if str(row['Phone']) == number:
                    name = row['Name']
                    p_phone = str(row['ParentPhone']).replace("-", "")
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 매크로 발송용 신호 (나중에 폰에서 읽을 데이터)
                    sms_signal = f"SEND_SMS|{p_phone}|[태권도] {name} 관원이 등원했습니다."
                    sheet_log.append_row([now, name, p_phone, "등원", sms_signal])
                    
                    st.success(f"✅ {name} 관원 확인! 어서와!")
                    st.balloons() # 축하 풍선
                    found = True
                    break
            if not found:
                st.error("등록되지 않은 번호입니다.")

    # --- [모드 2: 관리자 페이지] ---
    else:
        st.title("💻 관리자 상세 제어센터")
        
        # 클릭할 수 있는 상단 버튼 메뉴
        col1, col2, col3 = st.columns(3)
        if "admin_menu" not in st.session_state:
            st.session_state.admin_menu = "원생명부"

        with col1:
            if st.button("👤 원생명부/등록", use_container_width=True):
                st.session_state.admin_menu = "원생명부"
        with col2:
            if st.button("📊 출결 현황/조회", use_container_width=True):
                st.session_state.admin_menu = "출결현황"
        with col3:
            if st.button("⚙️ 시스템 설정", use_container_width=True):
                st.session_state.admin_menu = "설정"

        st.divider() # 구분선

        # 버튼 클릭에 따른 화면 전환
        if st.session_state.admin_menu == "원생명부":
            st.subheader("📝 원생 명부 상세 관리 (엑셀 방식)")
            df = pd.DataFrame(sheet_member.get_all_records())
            # 엑셀처럼 직접 수정 가능한 표
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            
            if st.button("수정사항 시트에 반영하기"):
                with st.spinner('업데이트 중...'):
                    sheet_member.clear()
                    sheet_member.update([edited_df.columns.values.tolist()] + edited_df.values.tolist(), raw=False)
                    st.success("구글 시트에 성공적으로 저장되었습니다!")

        elif st.session_state.admin_menu == "출결현황":
            st.subheader("📅 전체 출결 현황 조회")
            logs = pd.DataFrame(sheet_log.get_all_records())
            # 최신 기록이 위로 오게 정렬하여 표시
            st.dataframe(logs.sort_index(ascending=False), use_container_width=True)

        elif st.session_state.admin_menu == "설정":
            st.subheader("⚙️ 시스템 정보")
            st.info("현재 구글 시트 'TKD_Data'와 정상 연동 중입니다.")
            st.write("발신 전화번호: 010-XXXX-XXXX")
            if st.button("시스템 로그 초기화 (주의)"):
                st.warning("이 기능은 관리자 전용입니다.")

if __name__ == "__main__":
    main()
