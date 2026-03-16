import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

# --- 1. ตั้งค่าฟอนต์ ---
def init_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ThaiFont', 'THSarabunNew.ttf'))
        pdfmetrics.registerFont(TTFont('ThaiFontBold', 'THSarabunNew Bold.ttf'))
        return "ThaiFont", "ThaiFontBold"
    except:
        return "Helvetica", "Helvetica-Bold"

FONT_REG, FONT_BOLD = init_fonts()

# --- 2. ฟังก์ชันสร้าง PDF ตามตัวอย่าง ---
def generate_custom_pdf(df, center_name, uploaded_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # สร้าง Styles ภาษาไทย
    style_header = ParagraphStyle('Header', fontName=FONT_BOLD, fontSize=18, alignment=1, leading=22)
    style_normal = ParagraphStyle('Normal', fontName=FONT_REG, fontSize=14, leading=18)
    style_table = ParagraphStyle('TableText', fontName=FONT_REG, fontSize=12, alignment=1)

    story = []

    # --- หน้า 1: ตารางสรุป ---
    story.append(Paragraph("รายงานเวลาปฏิบัติงาน USO1-Renew", style_header))
    story.append(Paragraph(f"ศูนย์ : {center_name}", style_header))
    story.append(Paragraph("เดือน : มีนาคม 2569", style_header)) # ปรับตามต้องการ
    story.append(Spacer(1, 20))

    # เตรียมข้อมูลตาราง
    table_data = [["ลำดับ", "วันที่", "ชื่อ - นามสกุล", "เวลาเข้า", "เวลาออก", "ตำแหน่ง", "หมายเหตุ"]]
    for i, row in df.iterrows():
        table_data.append([str(i+1), row['date'], row['name'], row['time_in'], row['time_out'], row['status'], ""])

    # ตั้งค่าความกว้างคอลัมน์
    t = Table(table_data, colWidths=[30, 80, 130, 50, 50, 100, 70])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_REG),
        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    story.append(t)
    story.append(PageBreak())

    # --- หน้าถัดไป: รูปภาพรายวัน ---
    for i, row in df.iterrows():
        story.append(Paragraph(f"วันที่ : {row['date']}", style_normal))
        story.append(Paragraph(f"ชื่อ : {row['name']}  ตำแหน่ง : {row['status']}", style_normal))
        story.append(Spacer(1, 10))

        # ตารางใส่รูป (2 รูปซ้ายขวา หรือ บนล่าง ตามต้องการ)
        # ในที่นี้ใส่รูปใหญ่ตามลำดับ
        img_key_in = f"img_in_{i}"
        img_key_out = f"img_out_{i}"

        for key, label in [(img_key_in, "เวลาเข้า"), (img_key_out, "เวลาออก")]:
            if key in uploaded_imgs and uploaded_imgs[key] is not None:
                img = Image.open(uploaded_imgs[key])
                # จัดการขนาดรูปให้พอดีหน้า PDF
                w, h = img.size
                aspect = h / float(w)
                story.append(RLImage(uploaded_imgs[key], width=350, height=350*aspect))
                story.append(Paragraph(f"{label} : {row['time_in'] if 'in' in label else row['time_out']}", style_normal))
                story.append(Spacer(1, 15))
        
        story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()

# --- 3. ส่วน UI ของหน้าเว็บ ---
st.set_page_config(page_title="USO1 Report Editor", layout="wide")
st.markdown("""<style> .main { background-color: #f5f7f9; } </style>""", unsafe_allow_html=True)

st.title("📄 USO1 Report Management System")

if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv("03-2026.csv")

# แถบควบคุมด้านข้าง
st.sidebar.header("เมนูตั้งค่า")
centers = st.session_state.df['file_name'].unique()
target_center = st.sidebar.selectbox("เลือกศูนย์ที่ต้องการตรวจ", centers)

# กรองข้อมูลศูนย์ที่เลือก
current_df = st.session_state.df[st.session_state.df['file_name'] == target_center].copy()

# แบ่ง Tab การทำงาน
tab1, tab2 = st.tabs(["📝 แก้ไขข้อมูลตาราง", "📸 อัปโหลดรูปภาพ"])

uploaded_images = {}

with tab1:
    st.info("คุณสามารถแก้ไข วันที่, ชื่อ, และเวลา ได้โดยการคลิกที่ช่องในตารางด้านล่าง")
    edited_df = st.data_editor(current_df, use_container_width=True, num_rows="dynamic")
    if st.button("💾 บันทึกการแก้ไขตาราง"):
        st.session_state.df.update(edited_df)
        st.success("บันทึกข้อมูลเรียบร้อยแล้ว!")

with tab2:
    st.warning("กรุณาอัปโหลดรูปภาพแยกตามรายวัน (รูปจะถูกนำไปใส่ใน PDF ตามลำดับวันที่)")
    cols = st.columns(2)
    for idx, row in edited_df.iterrows():
        with st.expander(f"📅 ข้อมูลวันที่ {row['date']}"):
            c1, c2 = st.columns(2)
            uploaded_images[f"img_in_{idx}"] = c1.file_uploader(f"รูปเวลาเข้า ({row['date']})", type=['jpg','png'], key=f"in_{idx}")
            uploaded_images[f"img_out_{idx}"] = c2.file_uploader(f"รูปเวลาออก ({row['date']})", type=['jpg','png'], key=f"out_{idx}")

# ปุ่มสร้าง PDF (แสดงตลอด)
st.divider()
if st.button("🚀 สร้างไฟล์ PDF และดาวน์โหลด (Final Report)", use_container_width=True):
    with st.spinner("กำลังจัดหน้า PDF..."):
        pdf_data = generate_custom_pdf(edited_df, target_center, uploaded_images)
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์ PDF ของ " + target_center,
            data=pdf_data,
            file_name=f"{target_center}.pdf",
            mime="application/pdf"
        )
