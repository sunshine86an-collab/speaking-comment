import streamlit as st
from google import genai
from google.genai import types

# 1. Cấu hình tiêu đề và giao diện trang web
st.set_page_config(
    page_title="AI Chấm Speaking THCS",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ Hệ Thống Chấm Chữa Speaking Tiếng Anh THCS")
st.caption("Ứng dụng phân tích phát âm, ngữ pháp và chấm điểm bài nói từ tệp MP3 bằng Google Gemini.")

# 2. Xử lý API Key tự động từ cấu hình Secrets hoặc nhập tay trên web
api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ Cấu Hình")
    if not api_key:
        api_key = st.text_input(
            "Nhập Gemini API Key:", 
            type="password", 
            help="Lấy khóa API miễn phí từ aistudio.google.com"
        )
    else:
        st.success("✅ Đã kết nối Gemini API tự động.")

    st.divider()
    student_name = st.text_input("Tên học sinh:", placeholder="Ví dụ: Minh Anh")
    grade_level = st.selectbox("Khối lớp:", ["Lớp 6", "Lớp 7", "Lớp 8", "Lớp 9"], index=2)
    topic = st.text_input("Chủ đề bài nói:", placeholder="Ví dụ: Unit 3 - Teenagers")

# 3. Khu vực tải tệp âm thanh
uploaded_file = st.file_uploader("Tải lên tệp ghi âm bài nói (.mp3):", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/mp3")

# 4. Nút bấm kích hoạt AI chấm bài
if st.button("🚀 Bắt đầu chấm bài", type="primary"):
    if not api_key:
        st.error("⚠️ Vui lòng cung cấp Gemini API Key để thực hiện chấm bài.")
    elif uploaded_file is None:
        st.warning("⚠️ Vui lòng tải lên một tệp âm thanh (.mp3) trước.")
    else:
        with st.spinner("AI đang lắng nghe và phân tích bài nói của học sinh... Vui lòng chờ vài giây!"):
            try:
                # Kết nối tới dịch vụ Gemini
                client = genai.Client(api_key=api_key)

                # Đọc tệp MP3
                audio_bytes = uploaded_file.read()

                # Bộ tiêu chí sư phạm chi tiết cho cấp THCS
                system_instruction = (
                    "Bạn là một giám khảo chuyên nghiệp chấm kỹ năng Speaking Tiếng Anh cấp THCS tại Việt Nam "
                    "(bám sát chương trình phổ thông và khung CEFR A1 - B1).\n"
                    "Hãy lắng nghe trực tiếp tệp âm thanh và nhận xét chi tiết theo đúng cấu trúc Markdown sau:\n\n"
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

                user_prompt = f"Chấm bài nói của học sinh: {student_name or 'Học sinh'} ({grade_level}), Đề tài: {topic or 'Tự do'}."

                # Gửi trực tiếp âm thanh và chỉ dẫn tới mô hình Gemini
                response = client.models.generate_content(
                   model="gemini-3.8-flash",
                    contents=[
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type=uploaded_file.type or "audio/mp3",
                        ),
                        user_prompt
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    )
                )

                # Xuất kết quả ra màn hình web
                st.success("🎉 Đã hoàn tất việc chấm chữa bài!")
                st.markdown("---")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Đã xảy ra lỗi khi kết nối AI: {e}")
