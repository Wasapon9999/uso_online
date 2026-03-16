import streamlit as st
import pandas as pd
import os
import re
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

# --- 1. ฟังก์ชันแปลงลิงก์ Google Drive ให้แสดงผลได้ (Direct Link) ---
def format_gd_link(link):
    if 'drive.google.com' in str(link):
        # ดึง ID ของไฟล์ออกมาจากลิงก์
        file_id = re.search(r'[-\w]{25,}', str(link))
        if file_id:
            return f'https://dr.saveig.com/p?id={file_id.group()}' # หรือใช้คลังรูปภาพตรงของ Google
    return link

# --- 2. Font Setup ---
def init_fonts():
    try:
        pdfmetrics.registerFont(TTFont('ThaiFont', 'thsarabunnew.ttf'))
        pdfmetrics.registerFont(TTFont('ThaiFontBold', 'thsarabunnew_bold.ttf'))
        return "ThaiFont", "ThaiFontBold"
    except: return "Helvetica", "Helvetica-Bold"

F_REG, F_BOLD = init_fonts()

# --- 3. หน้า UI ---
st.set_page_config(page_title="USO1 Drive System", layout="wide")

# โหลดข้อมูล CSV
if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.read_csv("03-2026.csv")

# ตัวจำการอัปโหลดรูป (Session Storage)
if 'temp_photos' not in st.session_state:
    st.session_state.temp_photos = {}

st.title("🚀 ระบบ USO1 (รองรับ Google Drive & Auto-Save)")

# แถบเลือกศูนย์
centers = st.session_state.main_df['file_name'].unique()
selected_center = st.sidebar.selectbox("เลือกศูนย์", centers)
df_to_edit = st.session_state.main_df[st.session_state.main_df['file_name'] == selected_center]

st.subheader(f"📍 ศูนย์: {selected_center}")

for idx, row in df_to_edit.iterrows():
    with st.expander(f"📅 {row['date']} - {row['name']}"):
        # แก้ไขข้อความ
        c_text = st.columns([2, 2, 1, 1])
        st.session_state.main_df.at[idx, 'name'] = c_text[0].text_input("ชื่อ", value=row['name'], key=f"n_{idx}")
        st.session_state.main_df.at[idx, 'status'] = c_text[1].text_input("ตำแหน่ง", value=row['status'], key=f"s_{idx}")
        st.session_state.main_df.at[idx, 'time_in'] = c_text[2].text_input("เข้า", value=row['time_in'], key=f"i_{idx}")
        st.session_state.main_df.at[idx, 'time_out'] = c_text[3].text_input("ออก", value=row['time_out'], key=f"o_{idx}")
        
        st.divider()
        
        c_img = st.columns(2)
        for i, (col_name, label, key_type) in enumerate([("img_in1", "รูปเช้า", "in"), ("img_out1", "รูปเย็น", "out")]):
            target_col = c_img[i]
            photo_key = f"{key_type}_{idx}"
            
            # 1. เช็คว่ามีรูปใน Session (ที่เพิ่งอัปโหลด) ไหม
            if photo_key in st.session_state.temp_photos:
                target_col.image(st.session_state.temp_photos[photo_key], caption=f"✨ รูปใหม่ที่บันทึกไว้ ({label})", width=250)
            
            # 2. ถ้าไม่มี ให้เช็คลิงก์ใน CSV (รองรับ Google Drive)
            else:
                img_path_or_link = row[col_name]
                if 'drive.google.com' in str(img_path_or_link):
                    display_link = format_gd_link(img_path_or_link)
                    target_col.image(display_link, caption=f"🔗 จาก Google Drive ({label})", width=250)
                elif os.path.exists(f"photos/{img_path_or_link}"):
                    target_col.image(f"photos/{img_path_or_link}", caption=f"🖼️ รูปเดิม ({label})", width=250)

            # ช่องอัปโหลดใหม่ (จะบันทึกเข้า Session อัตโนมัติ)
            new_file = target_col.file_uploader(f"เปลี่ยน{label}", type=['jpg','png'], key=f"up_{photo_key}")
            if new_file:
                st.session_state.temp_photos[photo_key] = new_file
                st.rerun() # สั่งรันใหม่เพื่อแสดงรูปที่เพิ่งอัปโหลดทันที

st.divider()

# ปุ่มสร้าง PDF
if st.button("🖨️ ออกรายงาน PDF (รวมรูปจาก Drive และที่อัปโหลดใหม่)", use_container_width=True, type="primary"):
    # (หมายเหตุ: ฟังก์ชันสร้าง PDF จะต้องปรับให้รองรับการดึงรูปจาก Link URL ด้วย ซึ่งใช้คลัง requests เพิ่มเติมได้ครับ)
    st.success("กำลังประมวลผล PDF...")
    # ... (โค้ด PDF เดิมที่ปรับปรุงให้รับ st.session_state.temp_photos)
