"""Main Entry Point for Duty Roster Application"""
import streamlit as st
import pandas as pd
import io
from src.io_handler import load_staff_from_excel 
from src.engine import assign_staff_to_shifts_csp, generate_month_shifts
from datetime import date
import calendar

# 1. Setup the page
st.set_page_config(page_title="Staff Scheduler", layout="wide")

# 2. Add a Header
st.title("Duty Roster Planner")
st.markdown("Upload your staff Excel file to generate a balanced monthly roster.")

# 3. Sidebar for settings
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload Staff Excel", type=["xlsx"])


    month_options = [
        "January", "February", "March", "April", "May", "June", 
        "July", "August", "September", "October", "November", "December"
    ]
    month = st.selectbox("Select Month", month_options)
    year = st.number_input("Select Year", min_value=2024, max_value=2030, value=2026)

    month_map = {name: i+1 for i, name in enumerate(month_options)}
    month_int = month_map[month]

    st.divider()
    st.header("Public Holidays")
    
    # Calculate all possible days in the selected month to populate the dropdown
    _, num_days = calendar.monthrange(year, month_int)
    all_days_in_month = [date(year, month_int, d) for d in range(1, num_days + 1)]
    
    # Multi-select for holidays
    ph_dates = st.multiselect(
        "Select Public Holidays",
        options=all_days_in_month,
        format_func=lambda x: x.strftime("%d %b (%a)"),
        help="These days will be assigned PUBLIC_HOL shifts (3.0 points)"
    )

    st.divider()
    # Reset Button: Clears points in memory without re-uploading the file
    if st.button("Reset All YTD Points", use_container_width=True):
        if "staff_list" in st.session_state:
            for staff in st.session_state.staff_list:
                staff.ytd_points = 0.0
            st.rerun()
    

# 4. Main Logic
if uploaded_file is not None:
    # --- SESSION STATE MANAGEMENT ---
    # This ensures we don't lose point updates when the app refreshes
    if "staff_list" not in st.session_state:
        st.session_state.staff_list = load_staff_from_excel(uploaded_file)

    # Map month string to integer
    month_map = {name: i+1 for i, name in enumerate(month_options)}
    month_int = month_map[month]
    
    current_shifts = generate_month_shifts(year, month_int, holidays=ph_dates)

    # Dashboard Metrics
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Staff Loaded", len(st.session_state.staff_list))
    col2.metric("Total Shifts", len(current_shifts))
    col3.metric("Target Month", f"{month} {year}")

    # 5. The Action Button
    if st.button("Generate Optimized Roster", type="primary", use_container_width=True):
        with st.spinner(f"AI is calculating the best schedule for {month}..."):
            # Pass the persistent staff list from session state
            assignments = assign_staff_to_shifts_csp(current_shifts, st.session_state.staff_list)
            
            # Store assignments so they persist during downloads
            st.session_state.last_assignments = assignments

    # 6. Display Results
    if "last_assignments" in st.session_state and st.session_state.last_assignments:
        assignments = st.session_state.last_assignments
        
        # --- TAB 1: THE CALENDAR ---
        st.subheader(f"Final Schedule: {month} {year}")
        df = pd.DataFrame(assignments)
        calendar_view = df.pivot(index="Date", columns="Shift", values="Staff")
        
        preferred_order = ["WEEKDAY_PM", "WEEKEND_AM", "WEEKEND_PM", "PUBLIC_HOL"]
        existing_cols = [c for c in preferred_order if c in calendar_view.columns]
        calendar_view = calendar_view.reindex(columns=existing_cols).fillna("-")
        
        calendar_view.index = [d.strftime("%a, %b %d") for d in calendar_view.index]
        st.table(calendar_view)

        # --- TAB 2: POINTS UPDATE ---
        st.divider()
        st.subheader("Updated Year-to-Date Points")
        
        points_data = []
        for s in st.session_state.staff_list:
            points_data.append({
                "Staff Name": s.name,
                "Role": s.role.name,
                "Updated YTD Total": s.ytd_points
            })
        
        points_df = pd.DataFrame(points_data)
        st.bar_chart(points_df.set_index("Staff Name")["Updated YTD Total"])
        st.dataframe(points_df, use_container_width=True)

        # --- DOWNLOADS ---
        st.divider()
        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            csv_roster = calendar_view.to_csv().encode('utf-8')
            st.download_button("Download Roster (CSV)", csv_roster, f"roster_{month}.csv", "text/csv")

        with dl_col2:
            updated_staff_df = pd.DataFrame([
                {"name": s.name, "role": s.role.name, "ytd_points": s.ytd_points} 
                for s in st.session_state.staff_list
            ])
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                updated_staff_df.to_excel(writer, index=False)
            
            st.download_button(
                label="Download Updated Staff List",
                data=buffer.getvalue(),
                file_name="staff_list_updated.xlsx",
                mime="application/vnd.ms-excel"
            )
    elif "last_assignments" in st.session_state:
        st.error("No valid roster found! Try reducing the number of blackout dates.")

else:
    # Clear memory if the file is removed
    if "staff_list" in st.session_state:
        del st.session_state.staff_list
    if "last_assignments" in st.session_state:
        del st.session_state.last_assignments
    st.info("👈 Please upload an Excel file in the sidebar to begin.")