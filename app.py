import streamlit as st
import json
import os
import time
from datetime import datetime
from openai import OpenAI

# Cấu hình trang web
st.set_page_config(page_title="Smart Study 🎓 - Web Free", layout="wide")

# File lưu dữ liệu
DATA_FILE = "study_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"users": {}, "forum": []}
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_data()

# CSS giao diện tối
st.markdown("""
<style>
    .main { background-color: #0E1117; color: white; }
    .stButton > button { width: 100%; border-radius: 8px; height: 3em; background-color: #1E90FF; color: white; font-weight: bold; }
    .user-post { padding: 18px; border-left: 5px solid #FFD700; background: #1E1E1E; border-radius: 8px; margin: 15px 0; }
</style>
""", unsafe_allow_html=True)

# Kết nối Groq AI (free tier)
client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

def ask_ai(system_prompt, user_prompt):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.45,
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Lỗi: {str(e)}\n(Có thể hết limit free hôm nay, mai thử lại nhé!)"

# Session state
if "user" not in st.session_state:
    st.session_state.user = None
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# Đăng nhập / Đăng ký
if not st.session_state.user:
    st.title("🎓 Smart Study - Đăng nhập / Đăng ký")
    tab1, tab2 = st.tabs(["🔐 Đăng nhập", "✨ Đăng ký"])

    with tab1:
        u = st.text_input("Tên đăng nhập")
        p = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Sai tên hoặc mật khẩu!")

    with tab2:
        nu = st.text_input("Tên mới")
        np = st.text_input("Mật khẩu mới", type="password")
        if st.button("Đăng ký"):
            if nu and np and nu not in db["users"]:
                db["users"][nu] = {"password": np, "total": 0, "history": {}}
                save_data(db)
                st.success("Đăng ký OK! Đăng nhập đi 🚀")
            else:
                st.error("Tên đã có hoặc thiếu info!")
    st.stop()

curr_user = st.session_state.user
user_data = db["users"][curr_user]

# Sidebar
with st.sidebar:
    st.title(f"👋 Chào {curr_user}!")
    st.metric("Tổng thời gian học", f"{user_data['total']} phút")
    if st.button("Đăng xuất"):
        st.session_state.user = None
        st.rerun()

# Tabs chính
tab_study, tab_rank, tab_forum, tab_ai = st.tabs(["⏱ Học tập", "🏆 BXH", "💬 Diễn đàn", "🤖 AI"])

with tab_study:
    st.subheader("Phiên học hôm nay")
    if st.session_state.start_time is None:
        if st.button("Bắt đầu học 🚀"):
            st.session_state.start_time = time.time()
            st.rerun()
    else:
        elapsed = int((time.time() - st.session_state.start_time) / 60)
        st.warning(f"Đã học: {elapsed} phút")
        if st.button("Kết thúc"):
            if elapsed >= 1:
                today = datetime.now().strftime("%d-%m-%Y")
                user_data["total"] += elapsed
                user_data["history"][today] = user_data["history"].get(today, 0) + elapsed
                save_data(db)
                st.balloons()
            st.session_state.start_time = None
            st.rerun()

with tab_rank:
    st.subheader("Bảng xếp hạng")
    sorted_users = sorted(db["users"].items(), key=lambda x: x[1]["total"], reverse=True)
    for i, (u, info) in enumerate(sorted_users[:10], 1):
        st.write(f"{i}. {u} - {info['total']} phút")

with tab_forum:
    st.subheader("Diễn đàn")
    with st.expander("Đăng bài mới"):
        title = st.text_input("Tiêu đề")
        content = st.text_area("Nội dung")
        if st.button("Đăng"):
            if title and content:
                new_post = {
                    "id": str(time.time()),
                    "user": curr_user,
                    "title": title,
                    "content": content,
                    "time": datetime.now().strftime("%H:%M %d-%m-%Y"),
                    "comments": []
                }
                db["forum"] = [new_post] + db["forum"]
                save_data(db)
                st.rerun()

    for post in db["forum"]:
        st.markdown(f"""<div class="user-post">
            <h4>{post['title']}</h4>
            <small>Bởi {post['user']} | {post['time']}</small>
            <p>{post['content']}</p>
        </div>""", unsafe_allow_html=True)

        for c in post.get("comments", []):
            st.caption(f"↳ {c}")

        comment = st.text_input("Bình luận...", key=f"c_{post['id']}")
        if st.button("Gửi", key=f"b_{post['id']}"):
            if comment:
                post["comments"].append(f"{curr_user}: {comment}")
                save_data(db)
                st.rerun()

with tab_ai:
    st.subheader("🤖 Gia sư AI miễn phí (Groq)")
    mode = st.selectbox("Chế độ", ["Giải thích bài học", "Chấm bài tự luận", "Tạo đề ôn tập", "Gợi ý lịch học"])
    q = st.text_area("Câu hỏi...")
    if st.button("Gửi"):
        if q:
            with st.spinner("Đang hỏi..."):
                if mode == "Giải thích bài học":
                    sys = "Bạn là gia sư dễ hiểu. Giải thích rõ ràng với ví dụ thực tế, KHÔNG làm hộ bài."
                elif mode == "Chấm bài tự luận":
                    sys = "Bạn là giáo viên. Nhận xét cấu trúc, lập luận, ngữ pháp và gợi ý cải thiện."
                elif mode == "Tạo đề ôn tập":
                    sys = "Tạo 5 câu hỏi ôn tập dựa trên nội dung (mix trắc nghiệm + tự luận). Không đưa đáp án."
                else:
                    sys = "Phân tích thói quen và gợi ý lịch học tối ưu cho tuần tới (cân bằng, khả thi)."
                ans = ask_ai(sys, q)
                st.markdown("### Phản hồi từ AI:")
                st.write(ans)
        else:
            st.warning("Nhập câu hỏi đi!")

st.caption("Smart Study - Free 2026 | Tuấn & Grok ❤️")
