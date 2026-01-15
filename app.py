# """Main Entry Point for Duty Roster Application"""
# import streamlit as st
# import pandas as pd
# import io
# from src.io_handler import load_staff_from_excel 
# from src.engine import assign_staff_to_shifts_csp, generate_month_shifts
# from datetime import date
# import calendar

# # 1. Setup the page
# st.set_page_config(page_title="Staff Scheduler", layout="wide")

# # 2. Add a Header
# st.title("Duty Roster Planner")
# st.markdown("Upload your staff Excel file to generate a balanced monthly roster.")

# # 3. Sidebar for settings
# with st.sidebar:
#     st.header("Settings")
#     uploaded_file = st.file_uploader("Upload Staff Excel", type=["xlsx"])


#     month_options = [
#         "January", "February", "March", "April", "May", "June", 
#         "July", "August", "September", "October", "November", "December"
#     ]
#     month = st.selectbox("Select Month", month_options)
#     #year = st.number_input("Select Year", min_value=2024, max_value=2030, value=2026)

#     month_map = {name: i+1 for i, name in enumerate(month_options)}
#     month_int = month_map[month]

#     st.divider()
#     st.header("Public Holidays")
    
#     # Calculate all possible days in the selected month to populate the dropdown
#     _, num_days = calendar.dutyrange(year, month_int)
#     all_days_in_month = [date(year, month_int, d) for d in range(1, num_days + 1)]
    
#     # Multi-select for holidays
#     ph_dates = st.multiselect(
#         "Select Public Holidays",
#         options=all_days_in_month,
#         format_func=lambda x: x.strftime("%d %b (%a)"),
#         help="These days will be assigned PUBLIC_HOL shifts (3.0 points)"
#     )

#     st.divider()
#     # Reset Button: Clears points in memory without re-uploading the file
#     if st.button("Reset All YTD Points", use_container_width=True):
#         if "staff_list" in st.session_state:
#             for staff in st.session_state.staff_list:
#                 staff.ytd_points = 0.0
#             st.rerun()
    

# # 4. Main Logic
# if uploaded_file is not None:
#     # --- SESSION STATE MANAGEMENT ---
#     # This ensures we don't lose point updates when the app refreshes
#     if "staff_list" not in st.session_state:
#         st.session_state.staff_list = load_staff_from_excel(uploaded_file)

#     # Map month string to integer
#     month_map = {name: i+1 for i, name in enumerate(month_options)}
#     month_int = month_map[month]
    
#     current_shifts = generate_month_shifts(year, month_int, holidays=ph_dates)

#     # Dashboard Metrics
#     st.divider()
#     col1, col2, col3 = st.columns(3)
#     col1.metric("Staff Loaded", len(st.session_state.staff_list))
#     col2.metric("Total Shifts", len(current_shifts))
#     col3.metric("Target Month", f"{month} {year}")

#     # 5. The Action Button
#     if st.button("Generate Optimized Roster", type="primary", use_container_width=True):
#         with st.spinner(f"AI is calculating the best schedule for {month}..."):
#             # Pass the persistent staff list from session state
#             assignments = assign_staff_to_shifts_csp(current_shifts, st.session_state.staff_list)
            
#             # Store assignments so they persist during downloads
#             st.session_state.last_assignments = assignments

#     # 6. Display Results
#     if "last_assignments" in st.session_state and st.session_state.last_assignments:
#         assignments = st.session_state.last_assignments
        
#         # --- TAB 1: THE CALENDAR ---
#         st.subheader(f"Final Schedule: {month} {year}")
#         df = pd.DataFrame(assignments)
#         calendar_view = df.pivot(index="Date", columns="Shift", values="Staff")
        
#         preferred_order = ["WEEKDAY_PM", "WEEKEND_AM", "WEEKEND_PM", "PUBLIC_HOL"]
#         existing_cols = [c for c in preferred_order if c in calendar_view.columns]
#         calendar_view = calendar_view.reindex(columns=existing_cols).fillna("-")
        
#         calendar_view.index = [d.strftime("%a, %b %d") for d in calendar_view.index]
#         st.table(calendar_view)

#         # --- TAB 2: POINTS UPDATE ---
#         st.divider()
#         st.subheader("Updated Year-to-Date Points")
        
#         points_data = []
#         for s in st.session_state.staff_list:
#             points_data.append({
#                 "Staff Name": s.name,
#                 "Role": s.role.name,
#                 "Updated YTD Total": s.ytd_points
#             })
        
#         points_df = pd.DataFrame(points_data)
#         st.bar_chart(points_df.set_index("Staff Name")["Updated YTD Total"])
#         st.dataframe(points_df, use_container_width=True)

#         # --- DOWNLOADS ---
#         st.divider()
#         dl_col1, dl_col2 = st.columns(2)

#         with dl_col1:
#             csv_roster = calendar_view.to_csv().encode('utf-8')
#             st.download_button("Download Roster (CSV)", csv_roster, f"roster_{month}.csv", "text/csv")

#         with dl_col2:
#             updated_staff_df = pd.DataFrame([
#                 {"name": s.name, "role": s.role.name, "ytd_points": s.ytd_points} 
#                 for s in st.session_state.staff_list
#             ])
            
#             buffer = io.BytesIO()
#             with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
#                 updated_staff_df.to_excel(writer, index=False)
            
#             st.download_button(
#                 label="Download Updated Staff List",
#                 data=buffer.getvalue(),
#                 file_name="staff_list_updated.xlsx",
#                 mime="application/vnd.ms-excel"
#             )
#     elif "last_assignments" in st.session_state:
#         st.error("No valid roster found! Try reducing the number of blackout dates.")

# else:
#     # Clear memory if the file is removed
#     if "staff_list" in st.session_state:
#         del st.session_state.staff_list
#     if "last_assignments" in st.session_state:
#         del st.session_state.last_assignments
#     st.info("👈 Please upload an Excel file in the sidebar to begin.")



# """Main Entry Point for Duty Roster Application"""
# import streamlit as st
# import pandas as pd
# import io
# from src.io_handler import load_staff_from_excel 
# from src.engine import assign_staff_to_shifts_csp
# from src.models import Shift, ShiftType
# from datetime import date, timedelta

# # 1. Setup the page
# st.set_page_config(page_title="Staff Scheduler", layout="wide")

# # 2. Add a Header
# st.title("🏥 AI Duty Roster Planner")

# # 3. Sidebar for settings
# with st.sidebar:
#     st.header("1. Data Upload")
#     uploaded_file = st.file_uploader("Upload Staff Excel", type=["xlsx"])

#     if uploaded_file is not None:
#         if "staff_list" not in st.session_state:
#             st.session_state.staff_list = load_staff_from_excel(uploaded_file)
#             # Store initial points to show comparison later
#             st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}
        
#         st.divider()
#         st.header("2. Date Range")
#         start_date = st.date_input("Start Date", value=date(2026, 1, 1))
#         end_date = st.date_input("End Date", value=date(2026, 1, 31))

#         delta = end_date - start_date
#         all_dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
        
#         st.header("3. Public Holidays")
#         ph_dates = st.multiselect("Select Public Holidays", options=all_dates, format_func=lambda x: x.strftime("%d %b (%a)"))

#     if st.button("Reset All YTD Points", use_container_width=True):
#         if "staff_list" in st.session_state:
#             for staff in st.session_state.staff_list:
#                 staff.ytd_points = 0.0
#             st.session_state.initial_points = {s.name: 0.0 for s in st.session_state.staff_list}
#             st.rerun()

# # 4. Main Logic
# if uploaded_file is not None and start_date <= end_date:
    
#     # Generate shifts for the custom range
#     current_shifts = []
#     for d in all_dates:
#         if d in ph_dates:
#             current_shifts.append(Shift(date=d, type=ShiftType.PUBLIC_HOL))
#         elif d.weekday() >= 5:
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_AM))
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_PM))
#         else:
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKDAY_PM))

#     if st.button("🚀 Generate Optimized Roster", type="primary", use_container_width=True):
#         # Capture points BEFORE assignment
#         st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}
        
#         with st.spinner("AI is calculating shifts..."):
#             assignments = assign_staff_to_shifts_csp(current_shifts, st.session_state.staff_list)
#             st.session_state.last_assignments = assignments

#     # 5. Display Results
#     if "last_assignments" in st.session_state and st.session_state.last_assignments:
        
#         # --- ROSTER TABLE (Clean & Styled) ---
#         st.subheader("📅 Finalized Roster")
#         df_roster = pd.DataFrame(st.session_state.last_assignments)
#         pivot_df = df_roster.pivot(index="Date", columns="Shift", values="Staff")
        
#         # Ensure all shift types exist as columns for consistency
#         cols = ["WEEKDAY_PM", "WEEKEND_AM", "WEEKEND_PM", "PUBLIC_HOL"]
#         pivot_df = pivot_df.reindex(columns=[c for c in cols if c in pivot_df.columns]).fillna("-")
#         pivot_df.index = [d.strftime("%a, %b %d") for d in pivot_df.index]

#         # Displaying with a styled dataframe for better readability
#         st.dataframe(pivot_df.style.highlight_null(color="transparent").set_properties(**{'text-align': 'center'}), use_container_width=True)

#         # --- POINTS COMPARISON TABLE ---
#         st.divider()
#         st.subheader("📈 Points Reconciliation (Before vs. After)")
        
#         comparison_data = []
#         for s in st.session_state.staff_list:
#             before = st.session_state.initial_points.get(s.name, 0.0)
#             after = s.ytd_points
#             diff = after - before
#             comparison_data.append({
#                 "Staff Name": s.name,
#                 "Role": s.role.name,
#                 "Starting YTD": before,
#                 "Points Earned This Run": diff,
#                 "Final YTD Total": after
#             })
        
#         comp_df = pd.DataFrame(comparison_data)
        
#         # Style the comparison: Highlight the "Points Earned" column
#         def highlight_changes(val):
#             color = '#b7e4c7' if val > 0 else 'transparent'
#             return f'background-color: {color}'

#         st.dataframe(
#             comp_df.style.map(highlight_changes, subset=['Points Earned This Run']),
#             use_container_width=True,
#             hide_index=True
#         )


# else:
#     st.info("👈 Please upload the Staff Excel file and select your dates in the sidebar.")





# """Main Entry Point for Duty Roster Application"""
# import streamlit as st
# import pandas as pd
# import io
# from src.io_handler import load_staff_from_excel 
# from src.engine import assign_staff_to_shifts_csp
# from src.models import Shift, ShiftType
# from datetime import date, timedelta

# # 1. Setup the page
# st.set_page_config(page_title="Staff Scheduler", layout="wide")

# # 2. Add a Header
# st.title("🏥 AI Duty Roster Planner")

# # 3. Sidebar for settings
# with st.sidebar:
#     st.header("1. Define Date Range")
#     start_date = st.date_input("Start Date", value=date(2026, 1, 1))
#     end_date = st.date_input("End Date", value=date(2026, 1, 31))
    
#     delta = end_date - start_date
#     all_dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]

#     st.divider()
#     st.header("2. Public Holidays")
#     ph_dates = st.multiselect(
#             "Select Public Holidays", 
#             options=all_dates, 
#             format_func=lambda x: x.strftime("%d %b (%a)")
#         )

#     st.divider()
#     st.header("3. Data Upload")
#     uploaded_file = st.file_uploader("Upload Staff Excel", type=["xlsx"])

#     if uploaded_file is not None:
#         # Load the full dataframe for display purposes
#         raw_df = pd.read_excel(uploaded_file)
        
#         if "staff_list" not in st.session_state:
#             st.session_state.staff_list = load_staff_from_excel(uploaded_file)
#             st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}
#             st.session_state.raw_staff_df = raw_df

#     if st.button("Reset All YTD Points", use_container_width=True):
#         if "staff_list" in st.session_state:
#             for staff in st.session_state.staff_list:
#                 staff.ytd_points = 0.0
#             st.session_state.initial_points = {s.name: 0.0 for s in st.session_state.staff_list}
#             st.rerun()

# # 4. Main Logic
# if uploaded_file is not None and start_date <= end_date:
    
#     # --- NEW: STAFF INFORMATION TABLE ---
#     with st.expander("📋 View Staff Directory & Availability", expanded=True):
#         st.write("This table shows the current staff constraints and bidding preferences.")
#         # Display the uploaded data directly
#         st.dataframe(
#             st.session_state.raw_staff_df,
#             use_container_width=True,
#             hide_index=True
#         )
    
#     # Create the shift objects for the requested period
#     current_shifts = []
#     for d in all_dates:
#         if d in ph_dates:
#             current_shifts.append(Shift(date=d, type=ShiftType.PUBLIC_HOL))
#         elif d.weekday() >= 5: # Saturday=5, Sunday=6
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_AM))
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_PM))
#         else:
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKDAY_PM))

#     if st.button("🚀 Generate Optimized Roster", type="primary", use_container_width=True):
#         st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}
        
#         with st.spinner("AI is calculating the best shifts..."):
#             assignments = assign_staff_to_shifts_csp(current_shifts, st.session_state.staff_list)
#             if assignments:
#                 st.session_state.last_assignments = assignments
#             else:
#                 st.error("Constraint Error: No valid solution found. Please check blackout dates.")

#     # 5. Display Results
#     if "last_assignments" in st.session_state and st.session_state.last_assignments:
        
#         # --- TAB 1: ROSTER TABLE ---
#         st.subheader("📅 Finalized Roster")
#         df_roster = pd.DataFrame(st.session_state.last_assignments)
#         pivot_df = df_roster.pivot(index="Date", columns="Shift", values="Staff")
        
#         cols = ["WEEKDAY_PM", "WEEKEND_AM", "WEEKEND_PM", "PUBLIC_HOL"]
#         pivot_df = pivot_df.reindex(columns=[c for c in cols if c in pivot_df.columns]).fillna("-")
        
#         display_roster = pivot_df.copy()
#         display_roster.index = [d.strftime("%a, %b %d") for d in display_roster.index]
        
#         st.dataframe(
#             display_roster.style.set_properties(**{'text-align': 'center', 'border': '1px solid #dee2e6'}), 
#             use_container_width=True
#         )

#         # --- TAB 2: POINTS RECONCILIATION ---
#         st.divider()
#         st.subheader("📈 Points Reconciliation")
        
#         comparison_data = []
#         for s in st.session_state.staff_list:
#             before = st.session_state.initial_points.get(s.name, 0.0)
#             comparison_data.append({
#                 "Staff Name": s.name,
#                 "Role": s.role.name,
#                 "Starting YTD": round(before, 1),
#                 "Points Earned": round(s.ytd_points - before, 1),
#                 "Final YTD Total": round(s.ytd_points, 1)
#             })
        
#         comp_df = pd.DataFrame(comparison_data)

#         def highlight_earned(val):
#             return 'background-color: #b7e4c7' if val > 0 else ''

#         styled_comp_df = comp_df.style.map(
#             highlight_earned, subset=['Points Earned']
#         ).format({
#             'Starting YTD': "{:.1f}",
#             'Points Earned': "{:.1f}",
#             'Final YTD Total': "{:.1f}"
#         })

#         st.dataframe(styled_comp_df, use_container_width=True, hide_index=True)

#         # --- DOWNLOADS ---
#         st.divider()
#         output = io.BytesIO()
#         with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#             pivot_df.to_excel(writer, sheet_name='Roster')
#             comp_df.to_excel(writer, sheet_name='Updated_Points', index=False)
        
#         st.download_button(
#             label="📥 Download Updated Excel",
#             data=output.getvalue(),
#             file_name=f"Roster_{start_date}_to_{end_date}.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             use_container_width=True
#         )

# else:
#     st.info("👈 Set your Date Range and upload the Staff Excel file to begin.")


# """Main Entry Point for Duty Roster Application"""
# import streamlit as st
# import pandas as pd
# import io
# from src.io_handler import load_staff_from_excel 
# from src.engine import assign_staff_to_shifts_csp
# from src.models import Shift, ShiftType
# from datetime import date, timedelta

# st.set_page_config(page_title="Staff Scheduler", layout="wide")
# st.title("🏥 AI Duty Roster Planner")

# with st.sidebar:
#     st.header("1. Define Date Range")
#     start_date = st.date_input("Start Date", value=date(2026, 1, 1))
#     end_date = st.date_input("End Date", value=date(2026, 1, 31))
#     delta = end_date - start_date
#     all_dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]

#     st.divider()
#     st.header("2. Public Holidays")
#     ph_dates = st.multiselect("Select Public Holidays", options=all_dates, format_func=lambda x: x.strftime("%d %b (%a)"))

#     st.divider()
#     st.header("3. Data Upload")
#     uploaded_file = st.file_uploader("Upload Staff Excel", type=["xlsx"])

#     if uploaded_file is not None:
#         if "staff_list" not in st.session_state:
#             # We load the raw DF for the nice display
#             st.session_state.raw_staff_df = pd.read_excel(uploaded_file)
#             st.session_state.staff_list = load_staff_from_excel(uploaded_file)
#             st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}

# # Main Logic
# if uploaded_file is not None:
    
#     # --- STAFF DIRECTORY WITH NICE FORMATTING ---
#     with st.expander("📋 View Staff Directory & Availability", expanded=True):
#         st.write("Current staff constraints and PH bidding preferences:")
        
#         # Clean up the display: Format blackout dates to be more readable
#         display_df = st.session_state.raw_staff_df.copy()
        
#         # We use st.dataframe's column configuration to make "Blackout_Dates" look better
#         st.dataframe(
#             display_df,
#             column_config={
#                 "Blackout_Dates": st.column_config.TextColumn(
#                     "Blackout Dates",
#                     help="List of dates this staff member is unavailable",
#                     width="large",
#                 ),
#                 "PH_Bidding": st.column_config.TextColumn("PH Bids", width="medium")
#             },
#             use_container_width=True,
#             hide_index=True
#         )
    
#     # Shift Generation Logic
#     current_shifts = []
#     for d in all_dates:
#         if d in ph_dates:
#             current_shifts.append(Shift(date=d, type=ShiftType.PUBLIC_HOL))
#         elif d.weekday() >= 5:
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_AM))
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_PM))
#         else:
#             current_shifts.append(Shift(date=d, type=ShiftType.WEEKDAY_PM))

#     if st.button("🚀 Generate Optimized Roster", type="primary", use_container_width=True):
#         st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}
#         with st.spinner("AI is calculating shifts..."):
#             assignments = assign_staff_to_shifts_csp(current_shifts, st.session_state.staff_list)
#             if assignments:
#                 st.session_state.last_assignments = assignments
#             else:
#                 st.error("No valid solution found.")

#     # Results Display
#     if "last_assignments" in st.session_state and st.session_state.last_assignments:
#         st.subheader("📅 Finalized Roster")
#         df_roster = pd.DataFrame(st.session_state.last_assignments)
#         pivot_df = df_roster.pivot(index="Date", columns="Shift", values="Staff")
#         cols = ["WEEKDAY_PM", "WEEKEND_AM", "WEEKEND_PM", "PUBLIC_HOL"]
#         pivot_df = pivot_df.reindex(columns=[c for c in cols if c in pivot_df.columns]).fillna("-")
        
#         # Visual Table
#         view_df = pivot_df.copy()
#         view_df.index = [d.strftime("%a, %b %d") for d in view_df.index]
#         st.dataframe(view_df, use_container_width=True)

#         # Points Table
#         st.divider()
#         st.subheader("📈 Points Reconciliation")
#         comparison_data = []
#         for s in st.session_state.staff_list:
#             before = st.session_state.initial_points.get(s.name, 0.0)
#             comparison_data.append({
#                 "Staff Name": s.name, "Role": s.role.name,
#                 "Starting YTD": round(before, 1),
#                 "Points Earned": round(s.ytd_points - before, 1),
#                 "Final YTD Total": round(s.ytd_points, 1)
#             })
        
#         comp_df = pd.DataFrame(comparison_data)
#         st.dataframe(comp_df.style.map(lambda x: 'background-color: #b7e4c7' if isinstance(x, (int, float)) and x > 0 else '', subset=['Points Earned']).format(precision=1), use_container_width=True, hide_index=True)

#         # Export
#         output = io.BytesIO()
#         with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#             pivot_df.to_excel(writer, sheet_name='Roster')
#             comp_df.to_excel(writer, sheet_name='Points', index=False)
#         st.download_button("📥 Download Excel", output.getvalue(), f"Roster_{start_date}.xlsx", use_container_width=True)


"""Main Entry Point for Duty Roster Application"""
import streamlit as st
import pandas as pd
import io
from src.io_handler import load_staff_from_excel 
from src.engine import assign_staff_to_shifts_csp
from src.models import Shift, ShiftType
from datetime import date, timedelta

# 1. Setup the page
st.set_page_config(page_title="AI Staff Scheduler", layout="wide", page_icon="🏥")

# 2. Header
st.title("🏥 AI Duty Roster Planner")

# 3. Sidebar for settings
with st.sidebar:
    st.header("1. Define Date Range")
    start_date = st.date_input("Start Date", value=date(2026, 1, 1))
    end_date = st.date_input("End Date", value=date(2026, 1, 31))
    
    delta = end_date - start_date
    all_dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]

    # st.divider()
    # st.header("2. Public Holidays")
    # ph_dates = st.multiselect(
    #     "Select Public Holidays", 
    #     options=all_dates, 
    #     format_func=lambda x: x.strftime("%d %b (%a)")
    # )

    st.divider()
    st.header("3. Data Upload")
    uploaded_file = st.file_uploader("Upload Staff Excel", type=["xlsx"])

    if uploaded_file is not None:
        if "staff_list" not in st.session_state:
            # We load the data once and keep it in session state
            st.session_state.staff_list = load_staff_from_excel(uploaded_file)
            st.session_state.raw_staff_df = pd.read_excel(uploaded_file)
            # Snapshot of points before the engine runs
            st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}

    if st.button("Reset All YTD Points", use_container_width=True):
        if "staff_list" in st.session_state:
            for staff in st.session_state.staff_list:
                staff.ytd_points = 0.0
            st.session_state.initial_points = {s.name: 0.0 for s in st.session_state.staff_list}
            st.rerun()

# 4. Main Logic
if uploaded_file is not None and start_date <= end_date:
    # --- Generate Shift Objects ---
    current_shifts = []
    ph_dates = [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 2, 17),
        date(2026, 2, 18),
        date(2026, 4, 3),
        date(2026, 5, 1),
        date(2026, 5, 21),
        date(2026, 8, 9),
        date(2026, 12, 25),
    ]

    for d in all_dates:
        if d in ph_dates:
            current_shifts.append(Shift(date=d, type=ShiftType.PUBLIC_HOL_AM))
            current_shifts.append(Shift(date=d, type=ShiftType.PUBLIC_HOL_PM))
        elif d.weekday() >= 5:  # Weekend
            current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_AM))
            current_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_PM))
        else: # Normal Weekday - ONLY generate if NOT a PH
            current_shifts.append(Shift(date=d, type=ShiftType.WEEKDAY_PM))

    # --- UI: Staff Preview ---
    with st.expander("📋 View Staff Directory & Constraints", expanded=False):
        st.dataframe(st.session_state.raw_staff_df, use_container_width=True, hide_index=True)

    # --- ROSTER GENERATION ---
    if st.button("🚀 Generate Optimized Roster", type="primary", use_container_width=True):
        # Refresh initial points before running
        st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}
        
        with st.spinner("AI is calculating the best shifts..."):
            assignments = assign_staff_to_shifts_csp(current_shifts, st.session_state.staff_list)
            
            if assignments:
                st.session_state.last_assignments = assignments
                st.success("Roster generated successfully!")
            else:
                st.error("❌ No valid solution found! This usually happens if blackout dates or rest rules make coverage impossible.")

    # 5. Display Results
    if "last_assignments" in st.session_state and st.session_state.last_assignments:
        
        # --- ROSTER TABLE ---
        st.subheader("📅 Finalized Roster")
        df_roster = pd.DataFrame(st.session_state.last_assignments)
        
        # Pivot the data so Dates are rows and Shift Types are columns
        pivot_df = df_roster.pivot(index="Date", columns="Shift", values="Staff")
        
        # FIXED: Corrected column names to match ShiftType Enum names exactly
        cols_priority = ["WEEKDAY_PM", "WEEKEND_AM", "WEEKEND_PM", "PUBLIC_HOL_AM", "PUBLIC_HOL_PM"]
        existing_cols = [c for c in cols_priority if c in pivot_df.columns]
        pivot_df = pivot_df.reindex(columns=existing_cols).fillna("-")
        
        # Format dates for display
        display_roster = pivot_df.copy()
        display_roster.index = [d.strftime("%a, %d %b") for d in display_roster.index]
        
        st.dataframe(display_roster, use_container_width=True)

        # --- POINTS RECONCILIATION ---
        st.divider()
        st.subheader("📈 Points Reconciliation")
        
        recon_data = []
        for s in st.session_state.staff_list:
            start_pts = st.session_state.initial_points.get(s.name, 0.0)
            recon_data.append({
                "Staff Name": s.name,
                "Role": s.role.name,
                "Starting YTD": start_pts,
                "Points Earned": round(s.ytd_points - start_pts, 1),
                "Final Total": round(s.ytd_points, 1)
            })
        
        st.table(pd.DataFrame(recon_data))

        # --- DOWNLOAD ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pivot_df.to_excel(writer, sheet_name='Roster')
            pd.DataFrame(recon_data).to_excel(writer, sheet_name='Points', index=False)
        
        st.download_button(
            "📥 Download Roster (Excel)",
            data=output.getvalue(),
            file_name=f"Roster_{start_date}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )

else:
    st.info("👈 Upload the Staff Excel file and set the dates in the sidebar to begin.")