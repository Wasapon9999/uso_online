import streamlit as st
import pandas as pd
import os
import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

# --- ตั้งค่า Google Drive Folder ID ของคุณ ---
GD_FOLDER_ID = "1YACVXpINnadQpX6DaOaBZsiMscGv9ERg"

# --- 1. ฟังก์ชันดึงรูปจาก Google Drive (ระบุ ID ไฟล์โดยตรง) ---
def get_image_from_gd(filename):
    # หมายเหตุ: วิธีนี้จะได้ประสิทธิภาพสูงสุดถ้าใน CSV ของคุณเก็บเป็น Direct Link 
    # แต่ถ้าเป็นชื่อไฟล์ ระบบจะต้องใช้ API หรือใช้ URL รูปแบบ UC
    # ในที่นี้จะสร้าง Link เพื่อดึงรูปมาแสดง (คุณสามารถประยุกต์ใช้ ID รูปภาพรายตัวจะแม่นยำที่สุด)
    pass

# --- 2. Font Setup ---
def init_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ThaiFont', 'thsarabunnew.ttf'))
        pdfmetrics.registerFont(TTFont('ThaiFontBold', 'thsarabunnew_bold.ttf'))
        return "ThaiFont", "ThaiFontBold"
    except: return "Helvetica", "Helvetica-Bold"

F_REG, F_BOLD = init_fonts()

# --- 3. ฟังก์ชันสร้าง PDF ---
def generate_final_pdf(df, center_name, temp_photos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    st_title = ParagraphStyle('T', fontName=F_BOLD, fontSize=16, leading=20)
    st_normal = ParagraphStyle('N', fontName=F_REG, fontSize=14, leading=16)
    
    story = []
    # หน้า 1: ตารางสรุป
    story.append(Paragraph("รายงานเวลาปฏิบัติงาน USO1-Renew", st_title))
    story.append(Paragraph(f"ศูนย์ : {center_name}", st_normal))
    story.append(Spacer(1, 20))
    # ... (ส่วนตารางสรุปเหมือนเดิม) ...
    story.append(PageBreak())

    # หน้า 2+: รูปภาพ
    for idx, row in df.iterrows():
        day_content = []
        day_content.append(Paragraph(f"วันที่ : {row['date']} | {row['name']}", st_title))
        
        for label, col_name, key_type in [("เวลาเข้า", "img_in1", "in"), ("เวลาออก", "img_out1", "out")]:
            img_data = None
            photo_key = f"{key_type}_{idx}"
            
            if photo_key in temp_photos:
                img_data = temp_photos[photo_key]
            else:
                # กรณีเป็นลิงก์ Google Drive ใน CSV
                val = str(row[col_name])
                if 'http' in val:
                    # แปลงเป็น Direct Link สำหรับแสดงผล
                    if 'id=' in val:
                        fid = val.split('id=')[-1]
                        img_data = f'https://drive.google.com/uc?export=view&id={fid}'
                elif os.path.exists(f"photos/{val}"):
                    img_data = f"photos/{val}"

            if img_data:
                try:
                    day_content.append(RLImage(img_data, width=330, height=250)) # ปรับความสูงตามความเหมาะสม
                    day_content.append(Paragraph(f"{label}: {row['time_in' if key_type=='in' else 'time_out']}", st_normal))
                    day_content.append(Spacer(1, 15))
                except: pass
        
        story.append(KeepTogether(day_content))
        story.append(PageBreak())

    doc.build(story)
    return buffer.getvalue()

# --- 4. หน้า UI ---
st.set_page_config(page_title="USO1 Smart Report", layout="wide")

if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.read_csv("03-2026.csv")
if 'temp_photos' not in st.session_state:
    st.session_state.temp_photos = {}

st.title("🚀 ระบบ USO1: จัดการรายงานและรูปภาพ")

# เลือกศูนย์
centers = st.session_state.main_df['file_name'].unique()
selected_center = st.sidebar.selectbox("เลือกศูนย์", centers)
df_to_edit = st.session_state.main_df[st.session_state.main_df['file_name'] == selected_center]

# แสดงข้อมูลรายวัน (Card UI)
for idx, row in df_to_edit.iterrows():
    with st.expander(f"📅 {row['date']} - {row['name']}"):
        # แก้ไขข้อความ (ชื่อ, เวลา)
        c_edit = st.columns([2, 1, 1])
        st.session_state.main_df.at[idx, 'name'] = c_edit[0].text_input("ชื่อ", value=row['name'], key=f"n_{idx}")
        st.session_state.main_df.at[idx, 'time_in'] = c_edit[1].text_input("เวลาเข้า", value=row['time_in'], key=f"i_{idx}")
        st.session_state.main_df.at[idx, 'time_out'] = c_edit[2].text_input("เวลาออก", value=row['time_out'], key=f"o_{idx}")
        
        # แสดงรูปภาพ
        c_img = st.columns(2)
        for i, (col_name, label, key_type) in enumerate([("img_in1", "รูปเช้า", "in"), ("img_out1", "รูปเย็น", "out")]):
            photo_key = f"{key_type}_{idx}"
            
            # ลำดับการโชว์: อัปโหลดใหม่ > ลิงก์ Drive ใน CSV > รูปเดิมในเครื่อง
            display_img = None
            if photo_key in st.session_state.temp_photos:
                display_img = st.session_state.temp_photos[photo_key]
            elif 'http' in str(row[col_name]):
                display_img = str(row[col_name])
            
            if display_img:
                c_img[i].image(display_img, caption=label, width=300)
            
            # ปุ่มอัปโหลดทับ
            new_f = c_img[i].file_uploader(f"เปลี่ยน{label}", type=['jpg','png'], key=f"up_{photo_key}")
            if new_f:
                st.session_state.temp_photos[photo_key] = new_f
                st.rerun()

st.divider()
if st.button("🖨️ ออกรายงาน PDF (บันทึกการเปลี่ยนแปลงทั้งหมด)", use_container_width=True, type="primary"):
    current_data = st.session_state.main_df[st.session_state.main_df['file_name'] == selected_center]
    pdf_out = generate_final_pdf(current_data, selected_center, st.session_state.temp_photos)
    st.download_button("📥 ดาวน์โหลด PDF", pdf_out, f"Report_{selected_center}.pdf", "application/pdf", use_container_width=True)
