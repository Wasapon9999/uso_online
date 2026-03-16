import streamlit as st
import pandas as pd
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. การตั้งค่า Font ---
def init_fonts():
    try:
        # ตรวจสอบชื่อไฟล์ฟอนต์ให้ตรงกับใน GitHub
        pdfmetrics.registerFont(TTFont('ThaiFont', 'thsarabunnew.ttf'))
        pdfmetrics.registerFont(TTFont('ThaiFontBold', 'thsarabunnew_bold.ttf'))
        return "ThaiFont", "ThaiFontBold"
    except:
        return "Helvetica", "Helvetica-Bold"

F_REG, F_BOLD = init_fonts()

# --- 2. ฟังก์ชันสร้าง PDF (คงรูปแบบเดิมที่คุณต้องการ) ---
def generate_pdf(df, center_name):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    st_title = ParagraphStyle('T', fontName=F_BOLD, fontSize=16, leading=20)
    st_normal = ParagraphStyle('N', fontName=F_REG, fontSize=14, leading=16)
    
    story = []
    story.append(Paragraph("รายงานเวลาปฏิบัติงาน USO1-Renew", st_title))
    story.append(Paragraph(f"ศูนย์ : {center_name}", st_normal))
    story.append(Spacer(1, 20))

    # ตารางสรุป
    table_data = [["ลำดับ", "วันที่", "ชื่อ - นามสกุล", "เวลาเข้า", "เวลาออก", "ตำแหน่ง"]]
    for i, row in df.iterrows():
        table_data.append([str(i+1), row['date'], row['name'], row['time_in'], row['time_out'], row['status']])

    t = Table(table_data, colWidths=[35, 85, 150, 60, 60, 90])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), F_REG),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
    ]))
    story.append(t)
    doc.build(story)
    return buffer.getvalue()

# --- 3. หน้า UI แบบใหม่ ---
st.set_page_config(page_title="USO1 Easy Report", layout="centered")

# โหลดข้อมูลเข้า Session State (เพื่อให้บันทึกการแก้ไขได้)
if 'main_df' not in st.session_state:
    try:
        st.session_state.main_df = pd.read_csv("03-2026.csv")
    except:
        st.error("ไม่พบไฟล์ 03-2026.csv")
        st.stop()

st.title("📑 ระบบรายงาน USO1")
st.write("ตรวจสอบและแก้ไขข้อมูลรายวันด้านล่างนี้")

# เลือกศูนย์
centers = st.session_state.main_df['file_name'].unique()
selected_center = st.sidebar.selectbox("เลือกศูนย์", centers)

# กรองข้อมูลเฉพาะศูนย์ที่เลือก
mask = st.session_state.main_df['file_name'] == selected_center
df_to_edit = st.session_state.main_df[mask]

# วนลูปแสดงข้อมูลเป็น Card (Expander)
for idx, row in df_to_edit.iterrows():
    with st.expander(f"📅 วันที่ {row['date']} | {row['name']}"):
        col1, col2 = st.columns(2)
        
        # ช่องกรอกข้อมูลแบบแสดงค่าเดิมไว้ให้
        new_name = col1.text_input("ชื่อ-นามสกุล", value=row['name'], key=f"name_{idx}")
        new_status = col2.text_input("ตำแหน่ง", value=row['status'], key=f"status_{idx}")
        new_in = col1.text_input("เวลาเข้า", value=row['time_in'], key=f"in_{idx}")
        new_out = col2.text_input("เวลาออก", value=row['time_out'], key=f"out_{idx}")
        
        # อัปเดตข้อมูลลงใน session_state ทันทีที่พิมพ์
        st.session_state.main_df.at[idx, 'name'] = new_name
        st.session_state.main_df.at[idx, 'status'] = new_status
        st.session_state.main_df.at[idx, 'time_in'] = new_in
        st.session_state.main_df.at[idx, 'time_out'] = new_out

st.divider()

# ปุ่มดำเนินการหลัก
col_btn1, col_btn2 = st.columns(2)

if col_btn1.button("💾 บันทึกข้อมูล", use_container_width=True):
    st.success("บันทึกการแก้ไขลงในระบบชั่วคราวแล้ว!")

if col_btn2.button("🚀 ออกรายงาน PDF", use_container_width=True, type="primary"):
    with st.spinner("กำลังสร้างไฟล์..."):
        # ส่งข้อมูลล่าสุดที่ผ่านการแก้ไขแล้วไปสร้าง PDF
        updated_center_df = st.session_state.main_df[st.session_state.main_df['file_name'] == selected_center]
        pdf_data = generate_pdf(updated_center_df, selected_center)
        
        st.download_button(
            label="📥 ดาวน์โหลด PDF",
            data=pdf_data,
            file_name=f"Report_{selected_center}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
