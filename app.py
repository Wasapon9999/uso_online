import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

# --- 1. การตั้งค่า Font แบบเข้มงวด ---
def init_fonts():
    # ตรวจสอบว่าไฟล์ฟอนต์มีอยู่ในระบบจริงไหม
    reg_font_path = 'THSarabunNew.ttf'
    bold_font_path = 'THSarabunNew_bold.ttf'
    
    if os.path.exists(reg_font_path) and os.path.exists(bold_font_path):
        try:
            pdfmetrics.registerFont(TTFont('ThaiFont', reg_font_path))
            pdfmetrics.registerFont(TTFont('ThaiFontBold', bold_font_path))
            return "ThaiFont", "ThaiFontBold"
        except Exception as e:
            st.error(f"Error registering fonts: {e}")
            return "Helvetica", "Helvetica-Bold"
    else:
        st.error("❌ ไม่พบไฟล์ฟอนต์บน GitHub (ตรวจสอบว่าชื่อไฟล์เป็นตัวเล็กทั้งหมดหรือยัง)")
        return "Helvetica", "Helvetica-Bold"

F_REG, F_BOLD = init_fonts()

# --- 2. ฟังก์ชันสร้าง PDF (เน้นการใช้ฟอนต์ไทยในทุกจุด) ---
def generate_exact_pdf(df, center_name, uploaded_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    # กำหนดสไตล์ที่ใช้ฟอนต์ไทยแน่นอน
    st_title = ParagraphStyle('T', fontName=F_BOLD, fontSize=18, leading=22, alignment=0)
    st_normal = ParagraphStyle('N', fontName=F_REG, fontSize=15, leading=18)
    st_bold = ParagraphStyle('B', fontName=F_BOLD, fontSize=15, leading=18)
    
    story = []

    # --- หน้า 1: ตารางสรุป ---
    story.append(Paragraph("รายงานเวลาปฏิบัติงาน USO1-Renew", st_title))
    story.append(Paragraph(f"ศูนย์ : {center_name}", st_normal))
    staff_name = df.iloc[0]['name'] if not df.empty else "-"
    story.append(Paragraph(f"เจ้าหน้าที่ดูแลประจำศูนย์ : {staff_name}", st_normal))
    story.append(Spacer(1, 15))

    # หัวตารางภาษาไทย
    table_data = [["ลำดับ", "วันที่", "ชื่อ - นามสกุล", "เวลาเข้า", "เวลาออก", "ตำแหน่ง", "หมายเหตุ"]]
    for i, row in df.iterrows():
        table_data.append([str(i+1), row['date'], row['name'], row['time_in'], row['time_out'], row['status'], ""])

    t = Table(table_data, colWidths=[30, 85, 125, 50, 50, 85, 60])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), F_REG),       # ใช้ฟอนต์ไทยทั้งตาราง
        ('FONTNAME', (0,0), (-1,0), F_BOLD),      # หัวตารางตัวหนา
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
    ]))
    story.append(t)
    story.append(PageBreak())

    # --- หน้า 2 เป็นต้นไป: รูปภาพ (เน้นฟอนต์ไทยใต้รูป) ---
    for i, row in df.iterrows():
        day_content = []
        day_content.append(Paragraph(f"วันที่ : {row['date']}", st_bold))
        day_content.append(Paragraph(f"ชื่อ : {row['name']}  ตำแหน่ง : {row['status']}", st_normal))
        day_content.append(Spacer(1, 15))

        for label, col_name, upload_key in [("เวลาเข้า (เช้า)", "img_in1", f"in_{i}"), ("เวลาออก (เย็น)", "img_out1", f"out_{i}")]:
            img_to_use = None
            if upload_key in uploaded_imgs and uploaded_imgs[upload_key] is not None:
                img_to_use = uploaded_imgs[upload_key]
            else:
                photo_path = f"photos/{row[col_name]}"
                if os.path.exists(photo_path):
                    img_to_use = photo_path

            if img_to_use:
                img = Image.open(img_to_use)
                w, h = img.size
                aspect = h / float(w)
                day_content.append(RLImage(img_to_use, width=340, height=340*aspect))
                day_content.append(Spacer(1, 8))
                # จุดสำคัญ: บังคับใช้ Paragraph สไตล์ภาษาไทยใต้รูป
                time_val = row['time_in'] if 'เข้า' in label else row['time_out']
                day_content.append(Paragraph(f"{label} : {time_val}", st_normal))
                day_content.append(Spacer(1, 20))
        
        story.append(KeepTogether(day_content))
        story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()

# --- ส่วน UI ---
st.set_page_config(page_title="USO1 Master System", layout="wide")
st.title("🚀 ระบบจัดการรายงาน USO1 (แก้ปัญหาฟอนต์เพี้ยน)")

if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv("03-2026.csv")

centers = st.session_state.df['file_name'].unique()
target = st.sidebar.selectbox("เลือกศูนย์", centers)
current_df = st.session_state.df[st.session_state.df['file_name'] == target].copy()

# ตารางแก้ไข
edited_df = st.data_editor(current_df, use_container_width=True)

# อัปโหลด/Preview
uploaded_files = {}
st.write("---")
for idx, row in edited_df.iterrows():
    with st.expander(f"📅 วันที่ {row['date']} - {row['name']}"):
        c1, c2 = st.columns(2)
        for i, (col_img, label, key) in enumerate([("img_in1", "รูปเช้า", "in"), ("img_out1", "รูปเย็น", "out")]):
            target_col = c1 if i == 0 else c2
            up_key = f"{key}_{idx}"
            photo_path = f"photos/{row[col_img]}"
            if os.path.exists(photo_path):
                target_col.image(photo_path, caption=f"รูปเดิม: {label}", width=250)
            new_file = target_col.file_uploader(f"อัปโหลด{label}ใหม่", type=['jpg','png'], key=up_key)
            if new_file:
                uploaded_files[up_key] = new_file

if st.button("🖨️ Export PDF", use_container_width=True):
    pdf_out = generate_exact_pdf(edited_df, target, uploaded_files)
    st.download_button(f"📥 ดาวน์โหลด PDF", pdf_out, f"{target}.pdf", "application/pdf")
