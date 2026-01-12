from datetime import date
import calendar 
from typing import List # clarify
from src.models import Shift, ShiftType, Staff, Role
from src.io_handler import load_staff_from_excel
from ortools.sat.python import cp_model

def generate_month_shifts(year: int, month:int): # generates a shift for every day in the month of that particular year
    shifts = []
    # calendar.monthrange(year, month) returns tuple (first_day_of_week, num_days_in_month)
    _, num_days = calendar.monthrange(year, month) # _, num_days shows that I understand that 2 field will be generated, first_day_of_week and num_days_in_month, however I dont intend to use first one and hence _ is used
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        if current_date.weekday() >= 5: # if weekend: (Satuday=5, Sunday=6)
            shifts.append(Shift(date=current_date, type=ShiftType.WEEKEND_AM))
            shifts.append(Shift(date=current_date, type=ShiftType.WEEKEND_PM))
        else: # current_date is a weekday
            shifts.append(Shift(date=current_date, type=ShiftType.WEEKDAY_PM))
    return shifts

'''
    1. Account for Shift Types and Roles (DONE)
    2. Account for YTD scores (DONE)
    3. Account for PM Shifts where Staff do not need to work the next day
    4. Account for voluntary basis
    5. Account for PHs
    6. Account for blackout dates
'''
# def assign_staff_to_shifts(shifts, staff_list):
#     for shift in shifts:
#         eligible_staff = [] # list to track every eligible staff for each shift
        
        
#         for staff in staff_list:
#             # Account for blackout dates
#             if shift.date not in staff.blackout_dates: 
                
#                 # Account for shift types 
#                 # staff is eligible for any shifts
#                 if staff.role == Role.STANDARD:
#                     eligible_staff.append(staff)
#                 # staff is only eligible for AM shifts
#                 elif staff.role == Role.NO_PM and shift.type == ShiftType.WEEKEND_AM:
#                     eligible_staff.append(staff)
#                 # staff is only eligible for weekend shifts
#                 elif staff.role == Role.WEEKEND_ONLY and (shift.type == ShiftType.WEEKEND_AM or shift.type == ShiftType.WEEKEND_PM):
#                     eligible_staff.append(staff)
#                 else:
#                     continue
#             else:
#                 continue
#         # Account for YTD points
#         if eligible_staff != 0: # there are eligible staffs
#             eligible_staff.sort(key=lambda s: s.ytd_points) # use annonymous function to sort Staffs in ascending order based on their YTD points 
#             # Account for PM shifts (Additional attributes in Staff?)
#             # Account for voluntary basis
#             # Account for PHs

#             # Assignment of staff
#             chosen_staff = eligible_staff[0]
#             shift.assigned_staff = chosen_staff # Took it as always assign to staff with lowest points in the meantime

#             # Addition of points
#             chosen_staff.ytd_points += shift.type.points

#         else: #  no eligible staff
#             print(f"⚠️ WARNING: No one available for {shift.date} ({shift.type.name})") # Although ShiftType dont have name attribute, due to enum, there is a .name and .value assigned to each attribute already. 
#             continue # assigned_staff will just remain None

def assign_staff_to_shifts_csp(shifts: List[Shift], staff_list: List[Staff]):
    model = cp_model.CpModel()
    assignments = {} # (staff_name, shift_index) -> bit variable 

    # 1. Create Variables
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:   
            # It creates a special Google OR-Tools variable that can only be 0 or 1. It’s not a number yet; it’s a "decision" the computer has to make.
            assignments[(staff.name, s_idx)] = model.NewBoolVar(f"s{s_idx}_{staff.name}")

    # 2. Hard Constraint: Coverage
    # Every shift must have EXACTLY one person
    for s_idx in range(len(shifts)):
        # Looks at every staff member's "light switch" for that specific shift, and ensure sum is 1 (1 person working shift)
        model.Add(sum(assignments[(staff.name, s_idx)] for staff in staff_list) == 1)

    # 3. Hard Constraint: Blackout 
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            if shift.date in staff.blackout_dates:
                model.Add(assignments[(staff.name, s_idx)] == 0)  

    # 4. Hard Constraint: The Rest Rule
    for s_idx, current_shift in enumerate(shifts):
        if current_shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_PM]:

            # Now, look for any shift that happens "tomorrow"
            for next_s_idx, next_shift in enumerate(shifts):
                # Check if next_shift is exactly 1 day after current_shift
                days_diff = (next_shift.date - current_shift.date).days

                if days_diff == 1:
                    # for every staff member...
                    for staff in staff_list:
                        # Law: Alice_Today_PM + Alice_Tomorrow_Any <= 1
                        today_pm_var = assignments[(staff.name, s_idx)]
                        tomorrow_var = assignments[(staff.name, next_s_idx)]

                        model.Add(today_pm_var + tomorrow_var <= 1)
    # Hard Constraint: NO_PM Role
    for s_idx, shift in enumerate(shifts):
        if shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_PM]:
            for staff in staff_list:
                if staff.role == Role.NO_PM:
                    model.Add(assignments[(staff.name, s_idx)] == 0)
    
    for s_idx, shift in enumerate(shifts):
        if shift.date.weekday() in [0,1,2,3,4]: # if shift is on weekend
            for staff in staff_list:
                if staff.role == Role.WEEKEND_ONLY:
                    model.Add(assignments[(staff.name, s_idx)] == 0)
                


if __name__ == "__main__":
    # 1. Setup
    staff_members = load_staff_from_excel("staff_list.xlsx")
    feb_shifts = generate_month_shifts(2026, 2)
    
    # 2. Run Assignment
    assign_staff_to_shifts_csp(feb_shifts, staff_members)
    
    # 3. Print Results
    print(f"\n--- Final Roster for February 2026 ---")
    for s in feb_shifts:
        name = s.assigned_staff.name if s.assigned_staff else "!!! EMPTY !!!"
        print(f"{s.date} | {s.type.name.ljust(10)} | {name}")