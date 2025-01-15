import os
import pandas as pd
import streamlit as st
from datetime import datetime

# Constants
UPLOAD_FOLDER = "uploads"
DATA_FILE = "health_insurance_data.xlsx"
BACKGROUND_IMAGE = "https://silverlinecrm.com/wp-content/uploads/2021/03/iStock-881499528.jpg"

# Ensure directories and files exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FILE):
    pd.DataFrame(
        columns=[
            "FIELD OFFICER DISTRICT",
            "HOSPITAL NAME",
            "HOSPITAL ID",
            "CASE ID",
            "PROCEDURE DISP ID",
            "PMJAY CARD NUMBER",
            "DATE OF ADMISSION",
            "TOTAL OUT OF POCKET EXPENDITURE",
            "TYPE OF FRAUD",
            "PHOTO FILE"
        ]
    ).to_excel(DATA_FILE, index=False)

# Inject custom CSS for background image
st.markdown(
    f"""
    <style>
    body {{
        background-image: url('{BACKGROUND_IMAGE}');
        background-size: cover;
        background-attachment: fixed;
    }}
    .stApp {{
        background-color: rgba(0, 0, 0, 0.8);

        border-radius: 10px;
        padding: 20px;
        max-width: 800px;
        margin: auto;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App
st.title("Health Insurance Census Form")

# Form Input
with st.form("health_form", clear_on_submit=True):
    field_officer_district = st.text_input("Field Officer District").upper()
    hospital_name = st.text_input("Hospital Name").upper()
    hospital_id = st.text_input("Hospital ID").upper()
    case_id = st.text_input("Case ID").upper()
    procedure_disp_id = st.text_input("Procedure Disp ID").upper()
    pmyaj_card_number = st.text_input("PMJAY Card Number").upper()
    date_of_admission = st.date_input("Date of Admission")
    total_out_of_pocket_expenditure = st.number_input(
        "Total Out-of-Pocket Expenditure", min_value=0.0, step=0.01
    )
    fraud_type = st.selectbox("Type of Fraud", ["MONEY COLLECTION", "PACKAGE UPCODING", "BOTH"])
    uploaded_photo = st.file_uploader("Upload Photo", type=["jpg", "png", "jpeg"])

    submit_button = st.form_submit_button("Submit")

if submit_button:
    # Save uploaded photo
    photo_filename = None
    if uploaded_photo:
        photo_filename = os.path.join(UPLOAD_FOLDER, uploaded_photo.name)
        with open(photo_filename, "wb") as f:
            f.write(uploaded_photo.read())

    # Append data to Excel
    new_data = {
        "FIELD OFFICER DISTRICT": field_officer_district,
        "HOSPITAL NAME": hospital_name,
        "HOSPITAL ID": hospital_id,
        "CASE ID": case_id,
        "PROCEDURE DISP ID": procedure_disp_id,
        "PMJAY CARD NUMBER": pmyaj_card_number,
        "DATE OF ADMISSION": date_of_admission,
        "TOTAL OUT OF POCKET EXPENDITURE": total_out_of_pocket_expenditure,
        "TYPE OF FRAUD": fraud_type,
        "PHOTO FILE": photo_filename,
    }

    df = pd.read_excel(DATA_FILE)
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_excel(DATA_FILE, index=False)
    st.success("Form submitted successfully!")

# View Data
if st.button("View Data"):
    df = pd.read_excel(DATA_FILE)
    st.dataframe(df)

# Download Data
if st.button("Download Data"):
    with open(DATA_FILE, "rb") as f:
        st.download_button(
            label="Download Excel File",
            data=f,
            file_name="health_insurance_data.xlsx",
            mime="application/vnd.ms-excel",
        )
