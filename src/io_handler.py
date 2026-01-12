import pandas as pd
from src.models import Staff, Role
from datetime import datetime, date

def load_staff_from_excel(filepath: str):
    df = pd.read_excel(filepath)
    staff_list = []
    # creates a Staff object for every row in Excel
    for index, row in df.iterrows(): # index is a auto created column starting from 0 etc, row just goes through each row in the excel file
        # Handle blackout dates and convert to set format to fit with blackout_dates variable in models.py
        raw_blackouts = str(row.get('blackout dates', ""))
        blackout_set = set() # intialise empty set
        if raw_blackouts.strip(): # if cell is not empty
            # split by comma and loop thorugh each date string
            for date_str in raw_blackouts.split(','):
                clean_date_str = date_str.strip() # remove accidental spaces
                temp_dt = datetime.strptime(clean_date_str, "%Y-%m-%d").date()
                date_obj = date(temp_dt.year, temp_dt.month, temp_dt.day)
                blackout_set.add(date_obj)
        # To default ytd points t0 0.0 if there is no points assigned to enable mathemetical operations to be performed
        raw_points = row.get('ytd_points', 0.0) # if header is missing, raw_points becomes 0.0, if cell is empty, raw_points become NaN
        clean_points = 0.0 if pd.isna(raw_points) else float(raw_points) # if raw_points is NaN, change value to 0.0
        # using classes imported from above
        new_staff = Staff(
            name = row['name'], # first name is variable name in Staff class, second name is row name in excel
            role = Role[row['role'].strip().upper()],  # assign to Role object created from role in excel 
            ytd_points = clean_points,
            blackout_dates = blackout_set
        )
        staff_list.append(new_staff)
    return staff_list

if __name__ == "__main__":
    try: 
        data = load_staff_from_excel("staff_list.xlsx")
        for person in data:
            print(f'Success! Loaded {person.name} ({person.role})')
    except Exception as e:
        print(f"Error: {e}")
