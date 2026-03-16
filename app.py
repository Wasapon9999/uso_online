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

# --- 1. Font Setup ---
def init_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ThaiFont', 'THSarabunNew.ttf'))
        pdfmetrics.registerFont(TTFont('ThaiFontBold', 'THSarabunNew Bold.ttf'))
        return "ThaiFont", "ThaiFontBold"
    except:
        return "Helvetica", "Helvetica-Bold"

F_REG, F_BOLD = init_fonts()

# --- 2. PDF Engine (เหมือนต้นฉบับเป๊ะ) ---
def generate_exact_pdf(df, center_name, uploaded_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    st_title = ParagraphStyle('T', fontName=F_BOLD, fontSize=16, leading=20)
    st_normal = ParagraphStyle('N', fontName=F_REG, fontSize=14, leading=16)
    st_bold = ParagraphStyle('B', fontName=F_BOLD, fontSize=14, leading=16)
    
    story = []
    # หน้า 1: ตารางสรุป
    story.append(Paragraph("รายงานเวลาปฏิบัติงาน USO1-Renew", st_title))
    story.append(Paragraph(f"ศูนย์ : {center_name}", st_normal))
    staff_name = df.iloc[0]['name'] if not df.empty else "-"
    story.append(Paragraph(f"เจ้าหน้าที่ดูแลประจำศูนย์ : {staff_name}", st_normal))
    story.append(Spacer(1, 20))

    table_data = [["ลำดับ", "วันที่", "ชื่อ - นามสกุล", "เวลาเข้า", "เวลาออก", "ตำแหน่ง", "หมายเหตุ"]]
    for i, row in df.iterrows():
        table_data.append([str(i+1), row['date'], row['name'], row['time_in'], row['time_out'], row['status'], ""])

    t = Table(table_data, colWidths=[35, 85, 120, 50, 50, 90, 60])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), F_REG),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
    ]))
    story.append(t)
    story.append(PageBreak())

    # หน้า 2+: รูปภาพ
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
                if os.path.exists(photo_path): img_to_use = photo_path

            if img_to_use:
                img_pil = Image.open(img_to_use)
                w, h = img_pil.size
                aspect = h / float(w)
                day_content.append(RLImage(img_to_use, width=320, height=320*aspect))
                day_content.append(Spacer(1, 5))
                day_content.append(Paragraph(f"{label} : {row['time_in'] if 'เข้า' in label else row['time_out']}", st_normal))
                day_content.append(Spacer(1, 20))
        
        story.append(KeepTogether(day_content))
        story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()

# --- 3. หน้า UI แบบ Card + Image Preview ---
st.set_page_config(page_title="USO1 Master System", layout="wide")

if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.read_csv("03-2026.csv")

st.title("🚀 ระบบตรวจและแก้ไขรายงาน USO1")

# แถบควบคุมข้าง
centers = st.session_state.main_df['file_name'].unique()
selected_center = st.sidebar.selectbox("เลือกศูนย์", centers)
df_to_edit = st.session_state.main_df[st.session_state.main_df['file_name'] == selected_center]

uploaded_files = {}

st.subheader(f"📍 กำลังตรวจสอบศูนย์: {selected_center}")
st.info("แก้ไขข้อมูลและอัปโหลดรูปภาพใหม่ได้ในแต่ละวันที่")

# แสดงข้อมูลเป็น Card รายวัน
for idx, row in df_to_edit.iterrows():
    with st.expander(f"📅 {row['date']} - {row['name']}"):
        # ส่วนแก้ไขข้อความ
        c_text1, c_text2, c_text3, c_text4 = st.columns([2, 2, 1, 1])
        st.session_state.main_df.at[idx, 'name'] = c_text1.text_input("ชื่อ-นามสกุล", value=row['name'], key=f"n_{idx}")
        st.session_state.main_df.at[idx, 'status'] = c_text2.text_input("ตำแหน่ง", value=row['status'], key=f"s_{idx}")
        st.session_state.main_df.at[idx, 'time_in'] = c_text3.text_input("เวลาเข้า", value=row['time_in'], key=f"i_{idx}")
        st.session_state.main_df.at[idx, 'time_out'] = c_text4.text_input("เวลาออก", value=row['time_out'], key=f"o_{idx}")
        
        st.divider()
        
        # ส่วนแสดงรูปภาพเดิม และปุ่มอัปโหลดใหม่
        c_img1, c_img2 = st.columns(2)
        for i, (col_img, label, key) in enumerate([("img_in1", "รูปเช้า", "in"), ("img_out1", "รูปเย็น", "out")]):
            target_col = c_img1 if i == 0 else c_img2
            up_key = f"{key}_{idx}"
            
            # เช็คและแสดงรูปเดิม
            photo_path = f"photos/{row[col_img]}"
            if os.path.exists(photo_path):
                target_col.image(photo_path, caption=f"🖼️ {label} (เดิม)", width=250)
            
            # ช่องอัปโหลดรูปใหม่
            new_file = target_col.file_uploader(f"อัปโหลด {label} ใหม่", type=['jpg','png'], key=up_key)
            if new_file:
                uploaded_files[up_key] = new_file
                target_col.image(new_file, caption=f"✨ {label} (ที่อัปโหลดใหม่)", width=250)

st.divider()

# ปุ่ม Export PDF
if st.button("🖨️ ยืนยันข้อมูลและออกรายงาน PDF", use_container_width=True, type="primary"):
    with st.spinner("กำลังสร้าง PDF ตามข้อมูลล่าสุด..."):
        current_data = st.session_state.main_df[st.session_state.main_df['file_name'] == selected_center]
        pdf_out = generate_exact_pdf(current_data, selected_center, uploaded_files)
        st.download_button(f"📥 ดาวน์โหลด PDF: {selected_center}", pdf_out, f"{selected_center}.pdf", "application/pdf", use_container_width=True)
