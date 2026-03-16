import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ตั้งค่าฟอนต์
try:
    pdfmetrics.registerFont(TTFont('ThaiFont', 'THSarabunNew.ttf'))
    pdfmetrics.registerFont(TTFont('ThaiFontBold', 'THSarabunNew Bold.ttf'))
    FONT_NAME = 'ThaiFont'
except:
    FONT_NAME = 'Helvetica'

st.set_page_config(page_title="USO1 System", layout="wide")
st.title("ระบบจัดการรายงาน USO1 ออนไลน์")

# โหลดข้อมูล


@st.cache_data
def load_data():
    return pd.read_csv("03-2026.csv")


try:
    df = load_data()
    centers = df['file_name'].unique()
    selected_center = st.sidebar.selectbox("เลือกศูนย์", centers)

    # กรองข้อมูล
    current_df = df[df['file_name'] == selected_center].copy()

    st.subheader(f"ตารางข้อมูล: {selected_center}")
    # ทีมสามารถแก้ไขข้อมูลในตารางนี้ได้เลย
    edited_df = st.data_editor(current_df, use_container_width=True)

    if st.button("สร้างไฟล์ PDF"):
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont(FONT_NAME, 16)
        c.drawString(50, 800, f"ศูนย์: {selected_center}")

        y = 750
        c.setFont(FONT_NAME, 12)
        for i, row in edited_df.iterrows():
            text = f"{row['date']} - {row['name']} ({row['time_in']} - {row['time_out']})"
            c.drawString(50, y, text)
            y -= 20

        c.save()
        st.download_button("ดาวน์โหลด PDF", buf.getvalue(),
                           f"{selected_center}.pdf")

except Exception as e:
    st.error(f"กรุณาตรวจสอบไฟล์ 03-2026.csv: {e}")
