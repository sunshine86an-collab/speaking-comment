import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime
import json

# 1. Cấu hình giao diện trang web
st.set_page_config(
    page_title="AI Chấm Speaking THCS",
    page_icon="🎙️",
    layout="wide"
)

# Khởi tạo bộ nhớ lưu trữ lịch sử chấm bài (st.session_state)
if "history" not in st.session_state:
    st.session_state.history = []

st.title("🎙️ Hệ Thống Chấm Chữa Speaking Tiếng Anh THCS")
st.caption("Ứng dụng chấm bài nói qua Micro trực tiếp hoặc tệp âm thanh với Gemini 3.8 Flash.")

# 2. Xử lý API Key & Thông tin học sinh ở thanh bên (Sidebar)
api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ Cấu Hình")
    if not api_key:
        api_key = st.text_input(
            "Nhập Gemini API Key:", 
            type="password", 
            help="Lấy API Key từ aistudio.google.com"
        )
    else:
        st.success("✅ Đã kết nối Gemini API")

    st.divider()
    st.subheader("📋 Thông Tin Học Sinh")
    student_name = st.text_input("Tên học sinh *:", placeholder="Ví dụ: Nguyễn Minh Anh")
    grade_level = st.selectbox("Khối lớp:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"], index=2)
    topic = st.text_input("Chủ đề bài nói:", placeholder="Ví dụ: Unit 3 - Teenagers")

# 3. Phân chia 2 Tab chính: [Chấm Bài] và [Lịch Sử Chấm]
tab_grade, tab_history = st.tabs(["📝 Chấm Bài Mới", "📚 Lịch Sử Đã Chấm"])

with tab_grade:
    st.subheader("1. Chọn phương thức nộp bài:")
    input_method = st.radio(
        "Hình thức nộp âm thanh:",
        ["🎙️ Ghi âm trực tiếp trên web", "📁 Tải lên tệp ghi âm (.mp3, .wav, .m4a)"],
        horizontal=True
    )

    audio_source = None
    if input_method == "🎙️ Ghi âm trực tiếp trên web":
        # Widget ghi âm trực tiếp của Streamlit
        audio_source = st.audio_input("Nhấn nút tròn để bắt đầu ghi âm:")
    else:
        # Widget tải tệp có sẵn
        audio_source = st.file_uploader("Chọn tệp âm thanh từ máy tính/điện thoại:", type=["mp3", "wav", "m4a"])

    if audio_source is not None:
        st.audio(audio_source)

    # Nút bấm bắt đầu chấm
    if st.button("🚀 Bắt đầu chấm bài", type="primary"):
        if not api_key:
            st.error("⚠️ Vui lòng cung cấp Gemini API Key để thực hiện chấm bài.")
        elif not student_name.strip():
            st.warning("⚠️ Vui lòng nhập Tên học sinh ở thanh bên trái trước khi chấm để lưu lịch sử.")
        elif audio_source is None:
            st.warning("⚠️ Vui lòng ghi âm hoặc tải tệp âm thanh lên trước.")
        else:
            with st.spinner("AI đang nghe và phân tích bài nói của học sinh... Vui lòng chờ vài giây!"):
                try:
                    client = genai.Client(api_key=api_key)
                    audio_bytes = audio_source.read()

                    system_instruction = (
                        "Bạn là một giám khảo sư phạm chuyên chấm kỹ năng Speaking Tiếng Anh cấp THCS tại Việt Nam "
                        "(bám sát chương trình phổ thông hiện hành và khung CEFR A1 - B1).\n"
                        "Hãy lắng nghe trực tiếp tệp âm thanh và đánh giá chi tiết theo cấu trúc Markdown sau:\n\n"
                        "### 1. BẢN GHI LẠI (Transcript)\n"
                        "Ghi lại chính xác từng câu học sinh đã nói trong bài.\n\n"
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
                        "Nhận xét ngắn gọn, mang tính khích lệ lứa tuổi học sinh THCS."
                    )

                    user_prompt = f"Chấm bài nói của học sinh: {student_name} ({grade_level}), Đề tài: {topic or 'Tự do'}."

                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
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

                    result_text = response.text
                    timestamp_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                    # Lưu bài chấm vào danh sách lịch sử trong phiên làm việc
                    st.session_state.history.append({
                        "student": student_name.strip(),
                        "grade": grade_level,
                        "topic": topic.strip() if topic else "Chủ đề tự do",
                        "time": timestamp_str,
                        "result": result_text
                    })

                    st.success("🎉 Đã hoàn tất việc chấm chữa bài và lưu vào lịch sử!")
                    st.markdown("---")
                    st.markdown(result_text)

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi kết nối AI: {e}")

# 4. Tab Lịch Sử: Quản lý theo tên từng học sinh
with tab_history:
    st.subheader("📚 Danh sách các bài đã chấm")
    
    if not st.session_state.history:
        st.info("Chưa có bài chấm nào trong phiên làm việc hiện tại.")
    else:
        # Bộ lọc tìm kiếm theo học sinh
        all_students = sorted(list(set(item["student"] for item in st.session_state.history)))
        selected_filter = st.selectbox("🔍 Lọc xem theo tên học sinh:", ["Tất cả học sinh"] + all_students)

        filtered_history = [
            item for item in st.session_state.history 
            if selected_filter == "Tất cả học sinh" or item["student"] == selected_filter
        ]

        # Nút xuất file tải về máy cho giáo viên
        col_export, _ = st.columns([1, 3])
        with col_export:
            json_data = json.dumps(filtered_history, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Tải lịch sử chấm (.json)",
                data=json_data,
                file_name=f"lich_su_cham_speaking_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

        st.markdown(f"**Tổng số bài ghi nhận:** {len(filtered_history)}")
        
        # Hiển thị từng bài dạng thẻ mở rộng (expander)
        for idx, item in enumerate(reversed(filtered_history)):
            header = f"👤 {item['student']} - {item['grade']} | Chủ đề: {item['topic']} ({item['time']})"
            with st.expander(header, expanded=(idx == 0)):
                st.markdown(item["result"])
