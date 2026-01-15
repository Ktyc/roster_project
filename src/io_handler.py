# import pandas as pd
# from src.models import Staff, Role
# from datetime import datetime, date
# from typing import List, Union
# import io

# def load_staff_from_excel(file_source: Union[str, io.BytesIO]) -> List[Staff]: # str is for name of file while io.BytesIO is for file in memory, st.file_uploader returns a BytesIO object
#     """
#     GOOGLE STYLE FORMAT 

#     A brief summary of what the function does. (The 'Headline')

#     Args:
#         parameter_name: A description of what this input should be.

#     Returns:
#         A description of what the function hands back to you.
#     """
    
#     """
#     Loads staff data from an Excel file path or a file-like object.
    
#     Args:
#         file_source: The path to the Excel file or a BytesIO stream from Streamlit.
        
#     Returns:
#         List[Staff]: A list of validated Staff objects.
#     """

#     df = pd.read_excel(file_source)
#     staff_list = []

#     # creates a Staff object for every row in Excel
#     for index, row in df.iterrows(): # index is a auto created column starting from 0 etc, row just goes through each row in the excel file
#         # Handle blackout dates and convert to set format to fit with blackout_dates variable in models.py
#         raw_blackouts = str(row.get('Blackout_Dates', ""))
#         blackout_set = set() # intialise empty set
#         if raw_blackouts.strip(): # if cell is not empty
#             # split by comma and loop thorugh each date string
#             for date_str in raw_blackouts.split(','):
#                 clean_date_str = date_str.strip() # remove accidental spaces
#                 temp_dt = datetime.strptime(clean_date_str, "%Y-%m-%d").date()
#                 date_obj = date(temp_dt.year, temp_dt.month, temp_dt.day)
#                 blackout_set.add(date_obj)
#         # To default ytd points t0 0.0 if there is no points assigned to enable mathemetical operations to be performed
#         raw_points = row.get('Ytd_Points', 0.0) # if header is missing, raw_points becomes 0.0, if cell is empty, raw_points become NaN
#         clean_points = 0.0 if pd.isna(raw_points) else float(raw_points) # if raw_points is NaN, change value to 0.0
#         # using classes imported from above
#         new_staff = Staff(
#             name = row['Name'], # first name is variable name in Staff class, second name is row name in excel
#             role = Role[row['Role'].strip().upper()],  # assign to Role object created from role in excel 
#             ytd_points = clean_points,
#             blackout_dates = blackout_set
#         )
#         staff_list.append(new_staff)
#     return staff_list


import pandas as pd
from datetime import datetime, date
from src.models import Staff, Role

def load_staff_from_excel(file_path):
    df = pd.read_excel(file_path)
    staff_list = []
    
    for _, row in df.iterrows():
        def clean_date_input(val):
            if pd.isna(val) or str(val).strip().upper() in ["N/A", "NONE", ""]:
                return []
            
            # If Excel already made it a datetime/Timestamp, convert to list
            if isinstance(val, (datetime, date, pd.Timestamp)):
                return [val.date() if hasattr(val, 'date') else val]
            
            # If it's a string, split and parse
            date_list = []
            for part in str(val).split(','):
                try:
                    # Remove time if present (e.g., 2026-01-01 00:00:00 -> 2026-01-01)
                    clean_str = str(part).strip().split(' ')[0]
                    date_list.append(datetime.strptime(clean_str, "%Y-%m-%d").date())
                except:
                    continue
            return date_list

        staff = Staff(
            name=str(row['Name']),
            role=Role[row['Role'].strip()],
            ytd_points=float(row['Ytd_Points']),
            blackout_dates=clean_date_input(row.get('Blackout_Dates', ""))
        )
        # Force the attribute creation
        staff.bidding_dates = clean_date_input(row.get('PH_Bidding', ""))
        staff_list.append(staff)
        
    return staff_list