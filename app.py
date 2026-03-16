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

# --- 1. Font Setup (ตรวจสอบชื่อไฟล์ฟอนต์บน GitHub ของคุณด้วยนะครับ) ---
def init_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ThaiFont', 'thsarabunnew.ttf'))
        pdfmetrics.registerFont(TTFont('ThaiFontBold', 'thsarabunnew_bold.ttf'))
        return "ThaiFont", "ThaiFontBold"
    except:
        return "Helvetica", "Helvetica-Bold"

F_REG, F_BOLD = init_fonts()

# --- 2. PDF Engine (ปรับปรุงการจัดวางรูปภาพ) ---
def generate_exact_pdf(df, center_name, uploaded_imgs):
    buffer = BytesIO()
    # ปรับขอบกระดาษให้สมดุล
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    st_title = ParagraphStyle('T', fontName=F_BOLD, fontSize=16, leading=20, alignment=0)
    st_normal = ParagraphStyle('N', fontName=F_REG, fontSize=14, leading=16)
    st_bold = ParagraphStyle('B', fontName=F_BOLD, fontSize=14, leading=16)
    
    story = []

    # --- หน้า 1: ตารางสรุป ---
    story.append(Paragraph("รายงานเวลาปฏิบัติงาน USO1-Renew", st_title))
    story.append(Paragraph(f"ศูนย์ : {center_name}", st_normal))
    staff_name = df.iloc[0]['name'] if not df.empty else "-"
    story.append(Paragraph(f"เจ้าหน้าที่ดูแลประจำศูนย์ : {staff_name}", st_normal))
    story.append(Spacer(1, 15))

    table_data = [["ลำดับ", "วันที่", "ชื่อ - นามสกุล", "เวลาเข้า", "เวลาออก", "ตำแหน่ง", "หมายเหตุ"]]
    for i, row in df.iterrows():
        table_data.append([str(i+1), row['date'], row['name'], row['time_in'], row['time_out'], row['status'], ""])

    t = Table(table_data, colWidths=[30, 80, 120, 50, 50, 90, 65])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), F_REG),
        ('FONTNAME', (0,0), (-1,0), F_BOLD),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
    ]))
    story.append(t)
    story.append(PageBreak())

    # --- หน้า 2 เป็นต้นไป: รูปภาพ (หน้าละ 1 วัน 2 รูป) ---
    for i, row in df.iterrows():
        day_content = []
        day_content.append(Paragraph(f"วันที่ : {row['date']}", st_bold))
        day_content.append(Paragraph(f"ชื่อ : {row['name']}  ตำแหน่ง : {row['status']}", st_normal))
        day_content.append(Spacer(1, 15))

        # ตรวจสอบรูปภาพ
        for label, col_name, upload_key in [("เวลาเข้า (เช้า)", "img_in1", f"in_{i}"), ("เวลาออก (เย็น)", "img_out1", f"out_{i}")]:
            img_to_use = None
            if upload_key in uploaded_imgs and uploaded_imgs[upload_key] is not None:
                img_to_use = uploaded_imgs[upload_key]
            else:
                photo_path = f"photos/{row[col_name]}"
                if os.path.exists(photo_path):
                    img_to_use = photo_path

            if img_to_use:
                try:
                    img = Image.open(img_to_use)
                    w, h = img.size
                    aspect = h / float(w)
                    # ล็อคความกว้างที่ 330 เพื่อให้ 2 รูปพอดีใน 1 หน้า A4
                    day_content.append(RLImage(img_to_use, width=330, height=330*aspect))
                    day_content.append(Spacer(1, 5))
                    day_content.append(Paragraph(f"{label} : {row['time_in'] if 'เข้า' in label else row['time_out']}", st_normal))
                    day_content.append(Spacer(1, 15))
                except:
                    day_content.append(Paragraph(f"[ ไฟล์รูปภาพชำรุด: {label} ]", st_normal))
            else:
                day_content.append(Paragraph(f"[ ไม่พบรูปภาพ: {label} ]", st_normal))
                day_content.append(Spacer(1, 50))
        
        # ใช้ KeepTogether เพื่อให้ข้อมูลของ 1 วันอยู่หน้าเดียวกันเสมอ
        story.append(KeepTogether(day_content))
        story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()

# --- ส่วน UI (เหมือนเดิมแต่ปรับการแสดงผล Preview ให้ชัดขึ้น) ---
st.set_page_config(page_title="USO1 Master System", layout="wide")
st.title("🚀 ระบบตรวจและแก้ไขรายงาน USO1")

if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv("03-2026.csv")

centers = st.session_state.df['file_name'].unique()
target = st.sidebar.selectbox("เลือกศูนย์", centers)
current_df = st.session_state.df[st.session_state.df['file_name'] == target].copy()

st.subheader(f"📍 ศูนย์: {target}")
edited_df = st.data_editor(current_df, use_container_width=True)

uploaded_files = {}
st.write("---")
st.subheader("🖼️ ตรวจสอบรูปภาพ (Preview)")

for idx, row in edited_df.iterrows():
    with st.expander(f"📅 วันที่ {row['date']} - {row['name']}"):
        c1, c2 = st.columns(2)
        for i, (col_img, label, key) in enumerate([("img_in1", "รูปเช้า", "in"), ("img_out1", "รูปเย็น", "out")]):
            target_col = c1 if i == 0 else c2
            up_key = f"{key}_{idx}"
            
            # แสดง Preview รูปเดิม
            photo_path = f"photos/{row[col_img]}"
            if os.path.exists(photo_path):
                target_col.image(photo_path, caption=f"รูปเดิม: {label}", width=250)
            
            # ช่องอัปโหลดรูปใหม่
            new_file = target_col.file_uploader(f"อัปโหลด{label}ใหม่เพื่อแทนที่", type=['jpg','png'], key=up_key)
            if new_file:
                uploaded_files[up_key] = new_file
                target_col.image(new_file, caption=f"✅ รูปใหม่ที่จะใช้: {label}", width=250)

st.divider()
if st.button("🖨️ Export PDF (Final Report)", use_container_width=True):
    with st.spinner("กำลังคำนวณหน้ากระดาษ..."):
        pdf_out = generate_exact_pdf(edited_df, target, uploaded_files)
        st.download_button(f"📥 ดาวน์โหลด PDF: {target}", pdf_out, f"{target}.pdf", "application/pdf")
