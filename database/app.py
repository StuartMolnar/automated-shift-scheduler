import sqlite3
from sqlite3 import Error
import uvicorn
import re
import yaml
from pydantic import BaseModel
from datetime import datetime, time
from typing import Optional, List
from fastapi import FastAPI, HTTPException
import logging
from starlette.requests import Request

# --- Configs ---
# Read log config
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Set up logger
logger = logging.getLogger('basicLogger')

# Read app config
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())


# --- Pydantic Models ---
class Role(BaseModel):
    ID: Optional[int] = None
    RoleName: str
    Description: Optional[str] = None
    Created_At: Optional[datetime] = None
    Updated_At: Optional[datetime] = None

    class Config:
        from_attributes = True

class Shift(BaseModel):
    ID: Optional[int] = None
    RoleID: int 
    Description: Optional[str] = None
    StartTime: datetime
    EndTime: datetime
    EmployeeID: Optional[int] = None 
    CreatedAt: Optional[datetime] = None
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

class Employee(BaseModel):
    ID: Optional[int] = None
    Name: str
    Email: str
    RoleID: Optional[int] = None
    CreatedAt: Optional[datetime] = None
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmployeeAvailability(BaseModel):
    ID: Optional[int] = None
    EmployeeID: int
    DayOfWeek: int
    StartTime: time
    EndTime: time

    class Config:
        from_attributes = True

class EmployeePreferences(BaseModel):
    ID: Optional[int] = None
    EmployeeID: int
    AvailabilityID: Optional[int] = None 
    PreferenceLevel: int

    class Config:
        from_attributes = True

# --- App Setup ---
# SQLite Connection
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('scheduling.db')
        logger.info("Database connection established.")
    except Error as e:
        logger.error(f"Database connection failed: {e}")
    return conn

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request path: {request.url.path} - Client IP: {request.client.host}")
    response = await call_next(request)
    return response

@app.middleware("http")
async def log_responses(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"Response status code: {response.status_code} for path: {request.url.path}")
    return response

# --- API Routes ---
# Add a role
@app.post("/roles/add", response_model=Role)
def create_role(role: Role):

    # Check that role name is not empty
    if not role.RoleName.strip():
        logger.exception("Role name must not be empty.")
        raise HTTPException(status_code=400, detail="Role name must not be empty.")

    conn = create_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to the database.")

    try:
        cursor = conn.cursor()

        # Check if role exists
        cursor.execute("SELECT * FROM Roles WHERE RoleName = ?", (role.RoleName,))
        existing_role = cursor.fetchone()
        if existing_role:
            logger.exception(f"Role name {existing_role} already exists.")
            raise HTTPException(status_code=400, detail=f"Role name {existing_role} already exists.")

        # Add the role
        cursor.execute(
            "INSERT INTO Roles (RoleName, Description) VALUES (?, ?)",
            (role.RoleName, role.Description),
        )
        conn.commit()
        role.ID = cursor.lastrowid
    except Error as e:
        conn.rollback()
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return role

# Get all roles
@app.get("/roles/get", response_model=List[Role])
def read_roles():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Roles")
    roles_data = cursor.fetchall()
    conn.close()
    return [Role(
        ID=row[0], RoleName=row[1], Description=row[2], 
        Created_At=row[3], Updated_At=row[4]
    ) for row in roles_data]


# Add a shift
@app.post("/shifts/add", response_model=Shift)
def create_shift(shift: Shift):
    conn = create_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to the database.")

    try:
        cursor = conn.cursor()
        
        # Check if role exists
        cursor.execute("SELECT * FROM Roles WHERE RoleID = ?", (shift.RoleID,))
        if cursor.fetchone() is None:
            logger.exception(f"Role with ID {shift.RoleID} does not exist.")
            raise HTTPException(status_code=400, detail=f"Role with ID {shift.RoleID} does not exist.")

        # If provided, check if employee exists
        if shift.EmployeeID is not None:
            cursor.execute("SELECT * FROM Employees WHERE EmployeeID = ?", (shift.EmployeeID,))
            if cursor.fetchone() is None:
                logger.exception(f"Employee with ID {shift.EmployeeID} does not exist.")
                raise HTTPException(status_code=400, detail=f"Employee with ID {shift.EmployeeID} does not exist.")
        
        # Validate start time < end time
        if shift.StartTime >= shift.EndTime:
            logger.exception(f"Start time must be before end time.")
            raise HTTPException(status_code=400, detail="Start time must be before end time.")

        # Add the shift
        cursor.execute(
            "INSERT INTO Shifts (RoleID, Description, StartTime, EndTime, EmployeeID) VALUES (?, ?, ?, ?, ?)",
            (shift.RoleID, shift.Description, shift.StartTime, shift.EndTime, shift.EmployeeID),
        )
        conn.commit()
        shift.ID = cursor.lastrowid
    except Error as e:
        conn.rollback()
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return shift

# Get all shifts
@app.get("/shifts/get", response_model=List[Shift])
def read_shifts():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Shifts")
    shifts_data = cursor.fetchall()
    conn.close()
    return [Shift(
        ID=row[0], RoleID=row[1], Description=row[2], 
        StartTime=datetime.fromisoformat(row[3]), 
        EndTime=datetime.fromisoformat(row[4]), 
        EmployeeID=row[5], CreatedAt=datetime.fromisoformat(row[6]), 
        UpdatedAt=datetime.fromisoformat(row[7])
    ) for row in shifts_data]


# Add an employee
@app.post("/employees/add", response_model=Employee)
def create_employee(employee: Employee):
    # Check that name is not empty
    if not employee.Name:
        raise HTTPException(status_code=400, detail="The name must not be empty.")
    
    # Check that email is correct format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", employee.Email):
        raise HTTPException(status_code=400, detail="Invalid email format.")

    conn = create_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to the database.")

    try:
        cursor = conn.cursor()
        
        # Check if the email exists
        cursor.execute("SELECT * FROM Employees WHERE Email = ?", (employee.Email,))
        if cursor.fetchone():
            logger.exception(f"An employee with email {employee.Email} already exists.")
            raise HTTPException(status_code=400, detail=f"An employee with email {employee.Email} already exists.")
        
        # If role id is provided, check if it exists
        if employee.RoleID is not None:
            cursor.execute("SELECT * FROM Roles WHERE RoleID = ?", (employee.RoleID,))
            if cursor.fetchone() is None:
                logger.exception(f"Role with ID {employee.RoleID} does not exist.")
                raise HTTPException(status_code=400, detail=f"Role with ID {employee.RoleID} does not exist.")

        # Add the employee
        cursor.execute(
            "INSERT INTO Employees (Name, Email, RoleID) VALUES (?, ?, ?)",
            (employee.Name, employee.Email, employee.RoleID),
        )
        conn.commit()
        employee.ID = cursor.lastrowid
    except Error as e:
        conn.rollback()
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return employee

# Get all employees
@app.get("/employees/get", response_model=List[Employee])
def read_employees():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Employees")
    employees_data = cursor.fetchall()
    conn.close()
    return [Employee(
        ID=row[0], Name=row[1], Email=row[2], 
        RoleID=row[3], CreatedAt=datetime.fromisoformat(row[4]), 
        UpdatedAt=datetime.fromisoformat(row[5])
    ) for row in employees_data]


@app.post("/availability/add", response_model=EmployeeAvailability)
def create_employee_availability(employee_availability: EmployeeAvailability):
    conn = create_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Could not connect to the database.")
    
    cursor = conn.cursor()
    start_time_str = employee_availability.StartTime.strftime("%H:%M:%S")
    end_time_str = employee_availability.EndTime.strftime("%H:%M:%S")
    
    try:
        # Check if the employee exists
        cursor.execute(
            "SELECT * FROM Employees WHERE EmployeeID = ?",
            (employee_availability.EmployeeID,),
        )
        employee = cursor.fetchone()
        if not employee:
            logger.exception(f"Employee with ID {employee_availability.EmployeeID} does not exist.")
            raise HTTPException(status_code=400, detail=f"Employee with ID {employee_availability.EmployeeID} does not exist.")
        
        # Check if the availability already exists
        cursor.execute(
            "SELECT * FROM EmployeeAvailability WHERE EmployeeID = ? AND DayOfWeek = ? AND StartTime = ? AND EndTime = ?",
            (employee_availability.EmployeeID, employee_availability.DayOfWeek, start_time_str, end_time_str),
        )
        existing_availability = cursor.fetchone()
        if existing_availability:
            logger.exception(f"An availability for the given employee and time slot already exists.")
            raise HTTPException(status_code=400, detail="An availability for the given employee and time slot already exists.")

        # Add the availability
        cursor.execute(
            "INSERT INTO EmployeeAvailability (EmployeeID, DayOfWeek, StartTime, EndTime) VALUES (?, ?, ?, ?)",
            (employee_availability.EmployeeID, employee_availability.DayOfWeek, start_time_str, end_time_str),
        )
        conn.commit()
        employee_availability.ID = cursor.lastrowid
    except Error as e:
        conn.rollback()
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    
    return employee_availability

# Get all employee availabilities
@app.get("/availability/get", response_model=List[EmployeeAvailability])
def read_employee_availabilities():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM EmployeeAvailability")
    employee_availabilities_data = cursor.fetchall()
    conn.close()
    return [EmployeeAvailability(
        ID=row[0], EmployeeID=row[1], DayOfWeek=row[2], 
        StartTime=time.fromisoformat(row[3]), 
        EndTime=time.fromisoformat(row[4])
    ) for row in employee_availabilities_data]

# Get all employee availabilities for a specific employee
@app.get("/availability/get/{employee_id}", response_model=List[EmployeeAvailability])
def read_employee_availabilities(employee_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM EmployeeAvailability WHERE EmployeeID = ?", (employee_id,))
    employee_availabilities_data = cursor.fetchall()
    conn.close()
    return [EmployeeAvailability(
        id=row[0], employee_id=row[1], day_of_week=row[2], 
        start_time=row[3], end_time=row[4]
    ) for row in employee_availabilities_data]

# Add an employee preference
@app.post("/preferences/add", response_model=EmployeePreferences)
def create_employee_preference(employee_preference: EmployeePreferences):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        # Check if the employee exists
        cursor.execute(
            "SELECT * FROM Employees WHERE EmployeeID = ?",
            (employee_preference.EmployeeID,),
        )
        employee = cursor.fetchone()
        if not employee:
            logger.exception(f"Employee with ID {employee_preference.EmployeeID} does not exist.")
            raise HTTPException(status_code=400, detail=f"Employee with ID {employee_preference.EmployeeID} does not exist.")
        
        # Check if the availability exists
        cursor.execute(
            "SELECT * FROM EmployeeAvailability WHERE AvailabilityID = ?",
            (employee_preference.AvailabilityID,),
        )
        availability = cursor.fetchone()
        if not availability:
            logger.exception()
            raise HTTPException(status_code=400, detail="Availability does not exist.")

        # Check if a preference for the given availability slot exists        
        cursor.execute(
            "SELECT * FROM EmployeePreferences WHERE EmployeeID = ? AND AvailabilityID = ?",
            (employee_preference.EmployeeID, employee_preference.AvailabilityID),
        )
        existing_preference = cursor.fetchone()
        if existing_preference:
            logger.exception(f"A preference for the given employee and availability already exists.")
            raise HTTPException(status_code=400, detail="A preference for the given employee and availability already exists.")
        
        # Add the preference
        cursor.execute(
            "INSERT INTO EmployeePreferences (EmployeeID, AvailabilityID, PreferenceLevel) VALUES (?, ?, ?)",
            (employee_preference.EmployeeID, employee_preference.AvailabilityID, employee_preference.PreferenceLevel),
        )
        conn.commit()
        employee_preference.ID = cursor.lastrowid
    except Error as e:
        conn.rollback()
        logger.exception(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return employee_preference

# Get all employee preferences
@app.get("/preferences/get", response_model=List[EmployeePreferences])
def read_employee_preferences():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM EmployeePreferences")
    employee_preferences_data = cursor.fetchall()
    conn.close()
    return [EmployeePreferences(
        ID=row[0], EmployeeID=row[1], AvailabilityID=row[2], 
        PreferenceLevel=row[3]
    ) for row in employee_preferences_data]

# Get all employee preferences for a specific employee
@app.get("/preferences/get/{employee_id}", response_model=List[EmployeePreferences])
def read_employee_preferences(employee_id: int):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM EmployeePreferences WHERE EmployeeID = ?", (employee_id,))
    employee_preferences_data = cursor.fetchall()
    conn.close()
    return [EmployeePreferences(
        id=row[0], employee_id=row[1], availability_id=row[2], 
        preference_level=row[3]
    ) for row in employee_preferences_data]


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)