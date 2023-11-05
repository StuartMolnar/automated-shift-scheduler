import sqlite3

conn = sqlite3.connect('scheduling.db')
cursor = conn.cursor()

# Create the Roles Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Roles (
    RoleID INTEGER PRIMARY KEY AUTOINCREMENT,
    RoleName TEXT UNIQUE NOT NULL,
    Description TEXT,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);
''')

# Create the Shifts Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Shifts (
    ShiftID INTEGER PRIMARY KEY AUTOINCREMENT,
    RoleID INTEGER NOT NULL,
    Description TEXT,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME NOT NULL,
    EmployeeID INTEGER,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (RoleID) REFERENCES Roles (RoleID),
    FOREIGN KEY (EmployeeID) REFERENCES Employees (EmployeeID)
);
''')

# Create the Employees Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Employees (
    EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Email TEXT UNIQUE NOT NULL,
    RoleID INTEGER,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (RoleID) REFERENCES Roles (RoleID)
);
''')

# Create the Availability Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS EmployeeAvailability (
    AvailabilityID INTEGER PRIMARY KEY AUTOINCREMENT,
    EmployeeID INTEGER NOT NULL,
    DayOfWeek INTEGER NOT NULL,  -- 0 = Sunday, 1 = Monday, etc.
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    FOREIGN KEY (EmployeeID) REFERENCES Employees (EmployeeID)
);
''')

# Create the Preference Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS EmployeePreferences (
    PreferenceID INTEGER PRIMARY KEY AUTOINCREMENT,
    EmployeeID INTEGER NOT NULL,
    ShiftPatternID INTEGER,
    PreferenceLevel INTEGER NOT NULL,  -- Example: 1 = High, 2 = Medium, 3 = Low
    FOREIGN KEY (EmployeeID) REFERENCES Employees (EmployeeID),
    FOREIGN KEY (ShiftPatternID) REFERENCES ShiftPatterns (PatternID)
);
''')

# Commit the changes
conn.commit()

# Close the connection
conn.close()
