import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# 1. 구글 시트 연결
def connect_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', scope)
        client = gspread.authorize(creds)
        return client.open("TKD_Data")
    except:
        return None

def main():
    st.set_page_config(page_title="태권도 통합 관리 시스템", layout="wide")
    ss = connect_sheet()
    if not ss:
        st.error("구글 시트 연결 실패! key.json을 확인하세요.")
        return

    sheet_member = ss.get_worksheet(0) # 관원 명부 (이름, Phone, ParentPhone)
    sheet_log = ss.get_worksheet(1)    # 출결 기록 (시간, 이름, 연락처, 상태, SMS신호)

    st.sidebar.title("🥋 TKD 관리 시스템")
    mode = st.sidebar.radio("모드 선택", ["📢 출석체크(공기계용)", "💻 상세 관리자 페이지(PC용)"])

    # --- [모드 1: 출석체크] ---
    if mode == "📢 출석체크(공기계용)":
        st.title("출석 번호를 입력하세요")
        number = st.text_input("뒷번호 4자리", max_chars=4, type="password")
        
        if st.button("출석 확인", use_container_width=True):
            data = sheet_member.get_all_records()
            found = False
            for row in data:
                if str(row['Phone']) == number:
                    name = row['Name']
                    p_phone = str(row['ParentPhone']).replace("-", "")
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # [SMS 발송용 신호] 관장님 폰의 매크로가 읽을 텍스트
                    sms_signal = f"SEND_SMS|{p_phone}|[OO태권도] {name} 관원이 등원했습니다."
                    sheet_log.append_row([now, name, p_phone, "등원", sms_signal])
                    
                    st.success(f"✅ {name} 관원 확인! 즐겁게 운동하자!")
                    found = True
                    break
            if not found:
                st.error("등록되지 않은 번호입니다.")

    # --- [모드 2: 상세 관리자] ---
    else:
        st.title("💻 PC 전용 상세 관리 페이지")
        tab1, tab2, tab3 = st.tabs(["📝 원생 정보 수정", "📅 전체 출결 통계", "⚙️ 시스템 설정"])

        with tab1:
            st.subheader("원생 명부 상세 편집 (엑셀 방식)")
            df = pd.DataFrame(sheet_member.get_all_records())
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("수정사항 시트에 저장하기"):
                sheet_member.clear()
                sheet_member.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())
                st.success("명부가 업데이트되었습니다!")

        with tab2:
            st.subheader("출결 기록 조회")
            logs = pd.DataFrame(sheet_log.get_all_records())
            st.dataframe(logs.sort_index(ascending=False), use_container_width=True)

        with tab3:
            st.subheader("시스템 정보")
            st.info("이 프로그램은 구글 시트와 연동되어 작동합니다.")

if __name__ == "__main__":
    main()