import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random
import string
import pandas as pd

# --- 1. DATABASE CONNECTION ---
# def connect_to_sheet():
    # Make sure this matches your Google Sheet name exactly
    # SHEET_NAME = "School_Maintenance_DB"
    # scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    #try:
    #   creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    #   client = gspread.authorize(creds)
    #   return client.open(SHEET_NAME).sheet1
    #except Exception as e:
    #   st.error(f"Connection Error: Ensure 'creds.json' exists and Sheet name is correct. {e}")
    #   return None

#----- 1. UPDATE connection ------
def connect_to_sheet():
    SHEET_NAME = "School_Maintenance_DB"
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    try:
        # This line changes to use Streamlit Secrets instead of the json file
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

def generate_ticket():
    return "TIC-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# --- 2. PAGE CONFIG & SIDEBAR MANUAL ---
st.set_page_config(page_title="PTES BMO Portal", layout="wide")

with st.sidebar:
    st.title("📖 User Guide")
    st.markdown("""
    ### 📝 Reporting a Fault
    1. Fill in the **New Complaint** form.
    2. Click **Submit**. 
    3. **Important:** Copy the **Ticket Number** (e.g., TIC-A1B2C3) provided at the end.

    ### 🔍 Checking Progress
    1. Go to the **Submitted List** tab to see all reports.
    2. Or use the **Admin & Action** tab search box to see your specific updates.

    ### 🛠️ Admin Instructions
    1. Go to **Admin & Action**.
    2. Enter the Admin's password.
    3. Enter the Ticket Number provided by the user.
    4. Set the 'Authority Date' and add your 'Remarks'.
    5. Click **Update Database**.
    """)
    st.divider()
    st.info("System Online")

st.title("🏫 PTES Maintenance Portal")

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["📝 New Complaint", "📋 Submitted List", "🔐 Admin & Action"])

# --- 3. TAB 1: NEW COMPLAINT FORM ---
with tab1:
    st.subheader("Submit Maintenance Request")
    with st.form("complaint_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            dept = st.text_input("Department/Section")
            name = st.text_input("Your Full Name")
            phone = st.text_input("Contact Number (WhatsApp)")
        with c2:
            designation = st.selectbox("Designation",["BMS", "Teaching Staff", "Support Officer", "Security", "Non-Teaching Staff", "Administrator", "Others"])
            date_today = st.date_input("Today's Date", datetime.now())
            area = st.selectbox("Building Area",
                                ["Classroom", "Science Building", "Library", "Green Area", "SA Area", "Parking Area", "Admin Block", "Theatre",
                                 "SA Staffroom", "Admin Foyer", "Canteen", "Admin Garage", "Water Tank / Pump", "Security Post", "Others"])

        room_name = st.selectbox("Room Name",
                                 ["LT1", "LT2", "MPH", "MMT", "Surau", "Staffroom 1", "Staffroom 2", "HODs Room", "Kitchen", "Washroom", "Science Lab",
                                  "Examination", "Sick Bay", "Registration", "Store Room", "Computer Lab 1", "SMART Lab / ICT 2", "Admin Office", "Others"])
        level = st.select_slider("Level/Floor",
                                 options=["Ground", "Level 1", "Level 2", "Level 3", "Level 4", "Level 5"])
        room_no = st.text_input("Room Number or Not Available")

        details = st.text_area("Complaint Details (Explain fully)", height=100)
        duration = st.selectbox("Duration of fault",
                                ["less than 2 days", "more than 5 days", "more than 2 week", "more than a month"])

        if st.form_submit_button("SUBMIT COMPLAINT"):
            sheet = connect_to_sheet()
            if sheet:
                ticket = generate_ticket()
                # Row structure for Google Sheets
                new_row = [str(datetime.now()), dept, name, phone, designation, str(date_today),
                           area, room_name, level, room_no, details, duration, ticket, "Pending", "Waiting for update"]
                sheet.append_row(new_row)
                st.success(f"SUCCESS!! Keep Your Complain Ticket Number : {ticket}")
                st.balloons()

# --- 4. TAB 2: PUBLIC VIEW ---
with tab2:
    st.subheader("Current Complaint Status")
    sheet = connect_to_sheet()
    if sheet:
        data = sheet.get_all_records()
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No records found in the database.")

# --- 5. TAB 3: ADMIN MANAGEMENT & ACTION SEARCH ---
#----- use secret to hide the password of admin ---

with tab3:
    col_admin, col_search = st.columns([1, 1])

    with col_admin:
        st.subheader("🛠️ Admin Transaction")
        password_input = st.text_input("Enter Admin Password", type="password")

        # Pull the password from Streamlit Secrets instead of quoting it here
        if password_input == st.secrets["admin_credentials"]["password"]:
            st.write("---")
            t_id = st.text_input("Search Ticket to Update (e.g. TIC-XXXXXX)")

            if t_id:
                sheet = connect_to_sheet()
                records = sheet.get_all_records()

                row_idx = None
                found_data = None
                for i, r in enumerate(records):
                    if str(r.get('Ticket Number')) == t_id:
                        row_idx = i + 2
                        found_data = r
                        break

                if row_idx:
                    st.write(f"**Updating:** {found_data['Name of Complainer']} - {found_data['Room Name']}")
                    auth_date = st.date_input("Date Forwarded to Authority")
                    admin_remarks = st.text_area("Admin Remarks / Authority Reply")

                    if st.button("UPDATE DATABASE"):
                        # Column 14 = Authority Date, Column 15 = Remarks
                        sheet.update_cell(row_idx, 14, str(auth_date))
                        sheet.update_cell(row_idx, 15, admin_remarks)
                        st.success(f"Ticket {t_id} has been updated!")
                else:
                    st.error("Ticket ID not found.")
        else:
            st.warning("Enter Admin Password to access update controls.")

    with col_search:
        st.subheader("🔍 Check Action Status")
        user_query = st.text_input("Enter your Ticket Number to see progress")
        if user_query:
            sheet = connect_to_sheet()
            records = sheet.get_all_records()
            match = next((r for r in records if str(r.get('Ticket Number')) == user_query), None)

            if match:
                st.info(f"**Status/Date:** {match['Authority Date']}")
                st.success(f"**Latest Remark:** {match['Remarks']}")
            else:
                st.error("No record found for that Ticket Number.")
