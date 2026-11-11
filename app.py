import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime
import json
import os
import time

# 1. Cấu hình giao diện trang web
st.set_page_config(
    page_title="AI Chấm Speaking THCS",
    page_icon="🎙️",
    layout="wide"
)

# 2. Quản lý lưu trữ tệp lịch sử dùng chung trên máy chủ
HISTORY_FILE = "history_data.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_entry(entry):
    current_data = load_history()
    current_data.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)

st.title("🎙️ Hệ Thống Chấm Chữa Speaking Tiếng Anh THCS")
st.caption("Ứng dụng phân tích phát âm, ngữ pháp và chấm điểm bài nói từ tệp âm thanh hoặc ghi âm trực tiếp.")

# 3. Quản lý API Key & Thông tin học sinh ở thanh bên
raw_keys = st.secrets.get("GEMINI_API_KEY", "")
api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]

with st.sidebar:
    st.header("⚙️ Cấu Hình")
    if not api_keys:
        single_key = st.text_input(
            "Nhập Gemini API Key:", 
            type="password", 
            help="Lấy khóa API từ aistudio.google.com"
        )
        if single_key:
            api_keys = [single_key.strip()]
    else:
        st.success(f"✅ Đã kết nối ({len(api_keys)} API Key)")

    st.divider()
    st.subheader("📋 Thông Tin Học Sinh")
    student_name = st.text_input("Tên học sinh *:", placeholder="Ví dụ: Nguyễn Minh Anh")
    class_name = st.text_input("Lớp *:", placeholder="Ví dụ: 7A6")
    grade_level = st.selectbox("Khối lớp:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"], index=2)
    topic = st.text_input("Chủ đề bài nói:", placeholder="Ví dụ: Unit 3 - Teenagers")

# 4. Phân chia 2 Tab
tab_grade, tab_history = st.tabs(["📝 Chấm Bài Mới", "🔒 Lịch Sử Đã Chấm (Giáo Viên)"])

# ================= TAB 1: DÀNH CHO HỌC SINH NỘP VÀ CHẤM BÀI =================
with tab_grade:
    st.subheader("1. Chọn phương thức nộp bài:")
    input_method = st.radio(
        "Hình thức nộp âm thanh:",
        ["🎙️ Ghi âm trực tiếp trên web", "📁 Tải lên tệp ghi âm (.mp3, .wav, .m4a)"],
        horizontal=True
    )

    audio_source = None
    if input_method == "🎙️ Ghi âm trực tiếp trên web":
        audio_source = st.audio_input("Nhấn nút tròn để bắt đầu ghi âm:")
    else:
        audio_source = st.file_uploader("Chọn tệp âm thanh từ thiết bị:", type=["mp3", "wav", "m4a"])

    if audio_source is not None:
        st.audio(audio_source)

    if st.button("🚀 Bắt đầu chấm bài", type="primary"):
        if not api_keys:
            st.error("⚠️ Vui lòng cung cấp Gemini API Key để thực hiện chấm bài.")
        elif not student_name.strip():
            st.warning("⚠️ Vui lòng nhập Tên học sinh ở thanh bên trái trước khi bắt đầu chấm.")
        elif audio_source is None:
            st.warning("⚠️ Vui lòng ghi âm hoặc tải tệp âm thanh lên trước.")
        else:
            with st.spinner("AI đang lắng nghe và phân tích bài nói của học sinh... Vui lòng chờ vài giây!"):
                try:
                    audio_bytes = audio_source.read()

                    system_instruction = (
                        "Bạn là một giám khảo sư phạm chuyên chấm kỹ năng Speaking Tiếng Anh cấp THCS tại Việt Nam "
                        "(bám sát chương trình phổ thông và khung CEFR A1 - B1).\n"
                        "Hãy lắng nghe trực tiếp tệp âm thanh và đánh giá chi tiết theo cấu trúc Markdown sau:\n\n"
                        "### 1. BẢN GHI LẠI (Transcript)\n"
                        "Ghi lại chính xác từng câu học sinh đã nói trong file.\n\n"
                        "### 2. PHÂN TÍCH PHÁT ÂM (Pronunciation)\n"
                        "Chỉ rõ các từ phát âm chưa chuẩn, đặc biệt chú ý lỗi thiếu âm cuối "
                        "(ending sounds: /s/, /z/, /ed/, /t/, /d/) hoặc sai trọng âm từ. "
                        "Trình bày dạng bảng Markdown gồm các cột: | Từ học sinh nói | Phiên âm chuẩn | Nhận xét lỗi cụ thể |\n\n"
                        "### 3. SỬA LỖI NGỮ PHÁP & TỪ VỰNG\n"
                        "- Câu gốc của học sinh -> Câu sửa lại tự nhiên, chuẩn xác hơn (Better version).\n\n"
                        "### 4. BẢNG ĐIỂM (Thang điểm 10)\n"
                        "- **Pronunciation & Clarity**: ... / 4.0 điểm\n"
                        "- **Grammar & Lexical Resource**: ... / 3.0 điểm\n"
                        "- **Fluency & Coherence**: ... / 3.0 điểm\n"
                        "- **TỔNG ĐIỂM**: ... / 10 điểm\n\n"
                        "### 5. LỜI KHUYÊN & ĐỘNG VIÊN\n"
                        "Nhận xét khích lệ, thân thiện phù hợp với lứa tuổi học sinh THCS."
                    )

                    user_prompt = f"Chấm bài nói của học sinh: {student_name.strip()} ({grade_level}), Đề tài: {topic.strip() or 'Tự do'}."

                    candidate_models = ["gemini-3.8-flash"]
                    response = None
                    last_error = None

                    # Duyệt qua từng Key và Model
                    for key in api_keys:
                        try:
                            client = genai.Client(api_key=key)
                            for current_model in candidate_models:
                                for attempt in range(2):
                                    try:
                                        response = client.models.generate_content(
                                            model=current_model,
                                            contents=[
                                                types.Part.from_bytes(
                                                    data=audio_bytes,
                                                    mime_type=getattr(audio_source, "type", "audio/wav") or "audio/mp3",
                                                ),
                                                user_prompt
                                            ],
                                            config=types.GenerateContentConfig(
                                                system_instruction=system_instruction,
                                                temperature=0.2,
                                            )
                                        )
                                        break
                                    except Exception as err:
                                        last_error = err
                                        if "503" in str(err):
                                            time.sleep(2)
                                            continue
                                        elif "404" in str(err):
                                            break
                                        else:
                                            raise err
                                if response is not None:
                                    break
                            if response is not None:
                                break
                        except Exception as err:
                            last_error = err
                            if "429" in str(err):
                                continue
                            else:
                                raise err

                    if response is None:
                        raise last_error

                    result_text = response.text
                    timestamp_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                    entry_data = {
                        "student": student_name.strip(),
                        "grade": grade_level,
                        "topic": topic.strip() if topic else "Chủ đề tự do",
                        "time": timestamp_str,
                        "result": result_text
                    }
                    save_entry(entry_data)

                    st.success("🎉 Đã hoàn tất việc chấm chữa bài và lưu lại kết quả!")
                    st.markdown("---")
                    st.markdown(result_text)

                except Exception as e:
                    if "429" in str(e):
                        st.error("⚠️ Hệ thống chấm bài hôm nay đã đạt giới hạn lượt gọi miễn phí của máy chủ AI. Học sinh vui lòng thử lại sau hoặc gửi file qua cho cô giáo nhé!")
                    elif "503" in str(e):
                        st.error("⏳ Máy chủ AI đang tạm thời có lượng truy cập cao. Em hãy chờ khoảng 10-15 giây rồi bấm lại nút chấm bài nhé!")
                    else:
                        st.error(f"Đã xảy ra lỗi khi kết nối AI: {e}")

# ================= TAB 2: KHU VỰC QUẢN TRỊ DÀNH CHO GIÁO VIÊN =================
with tab_history:
    st.subheader("🔒 Khu Vực Quản Lý Của Giáo Viên")

    teacher_pass = st.secrets.get("TEACHER_PASSWORD", "123456")

    if "is_teacher" not in st.session_state:
        st.session_state.is_teacher = False

    if not st.session_state.is_teacher:
        st.info("Nhập mật mã quản trị để mở khóa xem toàn bộ bài nộp của học sinh.")
        col_pwd, col_btn = st.columns([3, 1])
        with col_pwd:
            input_pwd = st.text_input("Mật khẩu giáo viên:", type="password", key="teacher_pwd_input")
        with col_btn:
            st.write("")
            if st.button("Mở khóa", type="primary"):
                if input_pwd == teacher_pass:
                    st.session_state.is_teacher = True
                    st.rerun()
                else:
                    st.error("Mật khẩu không chính xác!")
    else:
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.success("✅ Đã xác thực quyền Giáo viên")
        with col_logout:
            if st.button("Đăng xuất 🔒"):
                st.session_state.is_teacher = False
                st.rerun()

        st.markdown("---")

        shared_history = load_history()

        if not shared_history:
            st.info("Hiện chưa có học sinh nào nộp bài.")
        else:
            all_students = sorted(list(set(item["student"] for item in shared_history)))
            selected_filter = st.selectbox("🔍 Lọc xem theo tên học sinh:", ["Tất cả học sinh"] + all_students)

            filtered_history = [
                item for item in shared_history 
                if selected_filter == "Tất cả học sinh" or item["student"] == selected_filter
            ]

            col_export, _ = st.columns([2, 2])
            with col_export:
                json_data = json.dumps(filtered_history, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 Tải toàn bộ lịch sử (.json)",
                    data=json_data,
                    file_name=f"lich_su_cham_speaking_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

            st.markdown(f"**Tổng số bài ghi nhận:** {len(filtered_history)}")

            for idx, item in enumerate(reversed(filtered_history)):
                header = f"👤 {item['student']} - {item['grade']} | Chủ đề: {item['topic']} ({item['time']})"
                with st.expander(header, expanded=(idx == 0)):
                    st.markdown(item["result"])
