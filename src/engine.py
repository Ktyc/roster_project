from datetime import date
import calendar 
from typing import List
from src.models import Shift, ShiftType, Staff, Role
from src.io_handler import load_staff_from_excel
from ortools.sat.python import cp_model

def generate_month_shifts(year: int, month:int, holidays: List[date]=None): # generates a shift for every day in the month of that particular year
    shifts = []
    holidays = holidays or []
    # calendar.monthrange(year, month) returns tuple (first_day_of_week, num_days_in_month)
    _, num_days = calendar.monthrange(year, month) # _, num_days shows that I understand that 2 field will be generated, first_day_of_week and num_days_in_month, however I dont intend to use first one and hence _ is used
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        if current_date in holidays:
            shifts.append(Shift(date=current_date, type=ShiftType.PUBLIC_HOL))
        elif current_date.weekday() >= 5: # if weekend: (Satuday=5, Sunday=6)
            shifts.append(Shift(date=current_date, type=ShiftType.WEEKEND_AM))
            shifts.append(Shift(date=current_date, type=ShiftType.WEEKEND_PM))
        else: # current_date is a weekday
            shifts.append(Shift(date=current_date, type=ShiftType.WEEKDAY_PM))
    return shifts

'''
    1. Account for Shift Types and Roles (DONE)
    2. Account for YTD scores (DONE)
    3. Account for PM Shifts where Staff do not need to work the next day (DONE)
    4. Account for voluntary basis
    5. Account for PHs
    6. Account for blackout dates (DONE)
'''

''''WORKS WITH VARIABLES - GENERATES MULTIPLE ROSTERS AND TESTS IT OUT TO FIND MINIMUM PENALTY THAT SATISFIES ALL CONSTRAINTS '''
def assign_staff_to_shifts_csp(shifts: List[Shift], staff_list: List[Staff]):
    model = cp_model.CpModel()
    assignments = {} # (staff_name, shift_index) -> bit variable 

    # 1. Create Variables
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            # We keep the dictionary key as (staff.name, s_idx) so your loops work,
            # but we make the INTERNAL name safe for the C++ engine.
            safe_name = "".join(filter(str.isalnum, staff.name))
            var_name = f"s{s_idx}_st{safe_name}"
            
            assignments[(staff.name, s_idx)] = model.NewBoolVar(var_name)

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
        if current_shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_PM, ShiftType.PUBLIC_HOL]:

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

    # 5. Hard Constraint: NO_PM Role
    for s_idx, shift in enumerate(shifts):
        if shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_PM, ShiftType.PUBLIC_HOL]:
            for staff in staff_list:
                if staff.role == Role.NO_PM:
                    model.Add(assignments[(staff.name, s_idx)] == 0)

    # 6. Hard Constraint: WEEKEND_ONLY staff cannot be assigned to weekdays 
    for s_idx, shift in enumerate(shifts):
        if shift.date.weekday() in [0,1,2,3,4] and shift.type != ShiftType.PUBLIC_HOL: 
            for staff in staff_list:
                if staff.role == Role.WEEKEND_ONLY:
                    model.Add(assignments[(staff.name, s_idx)] == 0)
    
    # 7. Soft Constraint: Workload Balancing
    total_penalties = []

    num_shifts = len(shifts)
    num_staff = len(staff_list)
    avg_shifts_per_person = num_shifts // num_staff

    for staff in staff_list:
        # 1 - Count total shifts for this person
        staff_total_shifts = sum(assignments[(staff.name, s_idx)] for s_idx in range(len(shifts)))

        # 2 - Calculate distance from average (The "Deviation")
        safe_name = "".join(filter(str.isalnum, staff.name))
        deviation = model.NewIntVar(0, num_shifts, f"dev_{safe_name}")
        model.Add(deviation >= staff_total_shifts - avg_shifts_per_person)
        model.Add(deviation >= avg_shifts_per_person - staff_total_shifts)

        # 3 - Apply a weight of 10 (Fairness is quite important)
        total_penalties.append(deviation * 10)

    # 8. Point Balancing 
    SCALE = 10 # Cater for points such as 1.5,2.5 etc

    total_points_to_assign = sum(s.type.points for s in shifts) * SCALE
    total_existing_ytd = sum(st.ytd_points for st in staff_list) * SCALE
    target_avg = int((total_points_to_assign + total_existing_ytd) // len(staff_list))

    for staff in staff_list:
        # Points earned THIS month
        staff_new_points = sum(assignments[(staff.name, s_idx)] * int(shifts[s_idx].type.points * SCALE) for s_idx in range(len(shifts)))
        
        # Staff Current Accumulated Points
        starting_points = int(staff.ytd_points * SCALE)

        # Equation for point system
        staff_total = starting_points + staff_new_points

        # Deviation from target 
        safe_name = "".join(filter(str.isalnum, staff.name))
        p_deviation = model.NewIntVar(0, 1000, f"p_dev_{safe_name}")
        
        # Basicaly calculating absolute value 
        model.Add(p_deviation >= staff_total - target_avg) 
        model.Add(p_deviation >= target_avg - staff_total)

        total_penalties.append(p_deviation * 10)

    # 9. Soft Constraint: Standard Staff to Avoid Weekends
    for s_idx, shift in enumerate(shifts):
        # Check if the date is Saturday (5) or Sunday (6)
        if shift.date.weekday() >= 5:
            for staff in staff_list:
                # if they are NOT a weekend-only worker, they should not be here
                if staff.role != Role.WEEKEND_ONLY:
                    # Penalty of 5 points for every weekend shift given to standard staff
                    # (Weight lower than Balancing so fairness wins if there's a conflict)
                    total_penalties.append(assignments[(staff.name, s_idx)] * 5)
    
    # 10. Tell Solver to minimize the fines
    model.Minimize(sum(total_penalties))

    # 11. Initialize Solver
    solver = cp_model.CpSolver()
    
    # 12. Tell solver to run
    status = solver.Solve(model)

    # Status handling
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"Roster generated! Score: {solver.ObjectiveValue()}")

        results = [] # Start an empty list
        
        for s_idx, s_obj in enumerate(shifts):
            for staff in staff_list:
                # Check if this staff member was assigned to this shift
                if solver.Value(assignments[(staff.name, s_idx)]) == 1:
                    # UPDATE Staff object's YTD points immediately
                    staff.ytd_points += s_obj.type.points
                    
                    # Create a "Row" for our future table
                    results.append({
                        "Date": s_obj.date,
                        "Shift": s_obj.type.name, # e.g., "WEEKDAY_PM"
                        "Staff": staff.name
                    })
        return results # Send the list back to app.py
    else:
        print("No solution found. Try loosening your Hard Constraints")
        return None
    
if __name__ == "__main__":
    staff_members = load_staff_from_excel("staff_list.xlsx")
    feb_shifts = generate_month_shifts(2026, 2)
    
    # Run and catch results
    results = assign_staff_to_shifts_csp(feb_shifts, staff_members)
    
    if results:
        print("\n--- Final Roster ---")
        for s in results:
            # Using dictionary keys as updated in the results loop
            print(f"{s['Date']} | {s['Shift']} | {s['Staff']}")