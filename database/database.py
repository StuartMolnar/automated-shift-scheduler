import sqlite3

conn = sqlite3.connect('scheduling.db')
cursor = conn.cursor()

# Create the Employees Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Employees (
    EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Email TEXT UNIQUE NOT NULL,
    Role TEXT NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);
''')

# Create the Shifts Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Shifts (
    ShiftID INTEGER PRIMARY KEY AUTOINCREMENT,
    Role TEXT NOT NULL,
    Description TEXT,
    StartTime TEXT NOT NULL,
    EndTime TEXT NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS EmployeeShifts (
    EmployeeShiftID INTEGER PRIMARY KEY AUTOINCREMENT,
    EmployeeID INTEGER NOT NULL,
    ShiftID INTEGER NOT NULL,
    PreferenceLevel INTEGER NOT NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (EmployeeID) REFERENCES Employees (EmployeeID),
    FOREIGN KEY (ShiftID) REFERENCES Shifts (ShiftID)
);
''')

# Create the IdealSchedules Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS IdealSchedules (
    IdealScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
    Role TEXT NOT NULL,
    ScheduleDetails TEXT NOT NULL, -- Consider JSON or another structured format
    CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    IsValid BOOLEAN NOT NULL DEFAULT TRUE
)
''')

# Commit the changes
conn.commit()

# Close the connection
conn.close()
