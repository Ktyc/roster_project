from dataclasses import dataclass, field
from enum import Enum, auto 
from typing import Set, Optional
from datetime import date

class Role(Enum):
    """"Types of staff memebrs based on their shift constraints"""
    STANDARD = auto() # auto assigns a unique value to the attributes starting from 1 
    NO_PM = auto()
    WEEKEND_ONLY = auto()

class ShiftType(Enum):
    # Format: (Value, Points)
    WEEKDAY_PM = (1, 1.0)
    WEEKEND_AM = (2, 2.0)
    WEEKEND_PM = (3, 2.0)
    # PUBLIC_HOL = (4, 3.0)
    
    def __init__(self, id, points):
        self.id = id
        self.points = points

@dataclass
class Staff:
    """Represents a staff member and their scheduling constraints"""
    name: str
    role: Role
    ytd_points: float = 0.0
    blackout_dates: Set[date] = field(default_factory=set) # Ensures every Staff object created has their own unique dates
    # May need additional attributes to track prev shifts to account for PM shifts


@dataclass 
class Shift:
    """Keeps track of who is doing what shift on which date"""
    date: date
    type: ShiftType
    assigned_staff: Optional[Staff] = None # Optional[Staff] = None just enable for this attribute to be None to cater for cases where no staff are assigned yet