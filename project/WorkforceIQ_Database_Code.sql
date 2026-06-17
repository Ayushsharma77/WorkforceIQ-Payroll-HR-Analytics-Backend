CREATE DATABASE WorkforceIQ;
GO
USE WorkforceIQ;
GO
CREATE TABLE Departments (
    DepartmentID   INT IDENTITY(1,1) PRIMARY KEY,
    DepartmentName VARCHAR(100)  NOT NULL UNIQUE,
    ManagerID      INT           NULL,
    Location       VARCHAR(100)  NULL,
    CreatedAt      DATETIME      DEFAULT GETDATE()
);
GO
CREATE TABLE Positions (
    PositionID     INT IDENTITY(1,1) PRIMARY KEY,
    PositionTitle  VARCHAR(100)   NOT NULL UNIQUE,
    DepartmentID   INT            NOT NULL,
    MinSalary      DECIMAL(12,2)  NOT NULL,
    MaxSalary      DECIMAL(12,2)  NOT NULL,
    CONSTRAINT FK_Positions_Dept FOREIGN KEY (DepartmentID)
        REFERENCES Departments(DepartmentID)
);
GO
CREATE TABLE Employees (
    EmployeeID      INT IDENTITY(1,1) PRIMARY KEY,
    FirstName       VARCHAR(50)    NOT NULL,
    LastName        VARCHAR(50)    NOT NULL,
    Email           VARCHAR(100)   NOT NULL UNIQUE,
    Phone           VARCHAR(20)    NULL,
    NationalID      VARCHAR(20)    NOT NULL UNIQUE,
    Gender          CHAR(1)        CHECK (Gender IN ('M','F','O')),
    DateOfBirth     DATE           NOT NULL,
    HireDate        DATE           NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    TerminationDate DATE           NULL,
    EmploymentStatus VARCHAR(20)   DEFAULT 'Active'
                                   CHECK (EmploymentStatus IN ('Active','Inactive','On Leave','Terminated')),
    DepartmentID    INT            NOT NULL,
    PositionID      INT            NOT NULL,
    BasicSalary     DECIMAL(12,2)  NOT NULL,
    BankAccount     VARCHAR(30)    NULL,
    BankName        VARCHAR(50)    NULL,
    CreatedAt       DATETIME       DEFAULT GETDATE(),
    CONSTRAINT FK_Employees_Dept FOREIGN KEY (DepartmentID)
        REFERENCES Departments(DepartmentID),
    CONSTRAINT FK_Employees_Pos  FOREIGN KEY (PositionID)
        REFERENCES Positions(PositionID)
);
GO
ALTER TABLE Departments
    ADD CONSTRAINT FK_Dept_Manager
    FOREIGN KEY (ManagerID) REFERENCES Employees(EmployeeID);
GO
CREATE TABLE Attendance (
    AttendanceID   INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID     INT           NOT NULL,
    AttendanceDate DATE          NOT NULL,
    CheckIn        TIME          NULL,
    CheckOut       TIME          NULL,
    Status         VARCHAR(20)   DEFAULT 'Present'
                                 CHECK (Status IN ('Present','Absent','Late','Half Day','On Leave')),
    OvertimeHours  DECIMAL(4,2)  DEFAULT 0.00,
    Notes          VARCHAR(255)  NULL,
    CONSTRAINT FK_Attendance_Emp FOREIGN KEY (EmployeeID)
        REFERENCES Employees(EmployeeID),
    CONSTRAINT UQ_Attendance UNIQUE (EmployeeID, AttendanceDate)
);
GO
CREATE TABLE LeaveTypes (
    LeaveTypeID   INT IDENTITY(1,1) PRIMARY KEY,
    LeaveTypeName VARCHAR(50)   NOT NULL UNIQUE,
    MaxDaysPerYear INT          NOT NULL,
    IsPaid        BIT           DEFAULT 1
);
GO
CREATE TABLE LeaveRequests (
    LeaveRequestID INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID     INT           NOT NULL,
    LeaveTypeID    INT           NOT NULL,
    StartDate      DATE          NOT NULL,
    EndDate        DATE          NOT NULL,
    TotalDays      AS (DATEDIFF(DAY, StartDate, EndDate) + 1) PERSISTED,
    Reason         VARCHAR(255)  NULL,
    Status         VARCHAR(20)   DEFAULT 'Pending'
                                 CHECK (Status IN ('Pending','Approved','Rejected','Cancelled')),
    ApprovedBy     INT           NULL,
    RequestedAt    DATETIME      DEFAULT GETDATE(),
    CONSTRAINT FK_Leave_Emp      FOREIGN KEY (EmployeeID)
        REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_Leave_Type     FOREIGN KEY (LeaveTypeID)
        REFERENCES LeaveTypes(LeaveTypeID),
    CONSTRAINT FK_Leave_Approver FOREIGN KEY (ApprovedBy)
        REFERENCES Employees(EmployeeID)
);
GO
CREATE TABLE TaxBrackets (
    TaxBracketID  INT IDENTITY(1,1) PRIMARY KEY,
    BracketName   VARCHAR(50)    NOT NULL,
    MinIncome     DECIMAL(12,2)  NOT NULL,
    MaxIncome     DECIMAL(12,2)  NULL,
    TaxRate       DECIMAL(5,4)   NOT NULL,
    EffectiveFrom DATE           NOT NULL,
    EffectiveTo   DATE           NULL
);
GO
CREATE TABLE DeductionTypes (
    DeductionTypeID   INT IDENTITY(1,1) PRIMARY KEY,
    DeductionName     VARCHAR(100)   NOT NULL UNIQUE,
    DeductionCategory VARCHAR(50)    CHECK (DeductionCategory IN ('Statutory','Voluntary','Loan')),
    CalculationMethod VARCHAR(20)    CHECK (CalculationMethod IN ('Fixed','Percentage')),
    DefaultValue      DECIMAL(10,4)  NOT NULL,
    IsActive          BIT            DEFAULT 1
);
GO
CREATE TABLE EmployeeDeductions (
    EmpDeductionID  INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID      INT            NOT NULL,
    DeductionTypeID INT            NOT NULL,
    CustomValue     DECIMAL(10,4)  NULL,
    StartDate       DATE           NOT NULL,
    EndDate         DATE           NULL,
    CONSTRAINT FK_EmpDed_Emp  FOREIGN KEY (EmployeeID)
        REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_EmpDed_Type FOREIGN KEY (DeductionTypeID)
        REFERENCES DeductionTypes(DeductionTypeID)
);
GO
CREATE TABLE PayrollPeriods (
    PeriodID   INT IDENTITY(1,1) PRIMARY KEY,
    PeriodName VARCHAR(50)    NOT NULL,
    StartDate  DATE           NOT NULL,
    EndDate    DATE           NOT NULL,
    PayDate    DATE           NOT NULL,
    Status     VARCHAR(20)    DEFAULT 'Open'
                              CHECK (Status IN ('Open','Processing','Closed')),
    CONSTRAINT UQ_Period UNIQUE (StartDate, EndDate)
);
GO
CREATE TABLE Payroll (
    PayrollID       INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID      INT            NOT NULL,
    PeriodID        INT            NOT NULL,
    BasicSalary     DECIMAL(12,2)  NOT NULL,
    OvertimePay     DECIMAL(12,2)  DEFAULT 0.00,
    Allowances      DECIMAL(12,2)  DEFAULT 0.00,
    GrossSalary     AS (BasicSalary + OvertimePay + Allowances) PERSISTED,
    TotalDeductions DECIMAL(12,2)  DEFAULT 0.00,
    TaxAmount       DECIMAL(12,2)  DEFAULT 0.00,
    NetSalary       AS (BasicSalary + OvertimePay + Allowances
                        - TotalDeductions - TaxAmount) PERSISTED,
    PaymentStatus   VARCHAR(20)    DEFAULT 'Pending'
                                   CHECK (PaymentStatus IN ('Pending','Paid','On Hold')),
    ProcessedAt     DATETIME       NULL,
    CONSTRAINT FK_Payroll_Emp    FOREIGN KEY (EmployeeID)
        REFERENCES Employees(EmployeeID),
    CONSTRAINT FK_Payroll_Period FOREIGN KEY (PeriodID)
        REFERENCES PayrollPeriods(PeriodID),
    CONSTRAINT UQ_Payroll UNIQUE (EmployeeID, PeriodID)
);
GO
CREATE TABLE PayrollDeductions (
    PayrollDeductionID INT IDENTITY(1,1) PRIMARY KEY,
    PayrollID          INT            NOT NULL,
    DeductionTypeID    INT            NOT NULL,
    AmountDeducted     DECIMAL(12,2)  NOT NULL,
    CONSTRAINT FK_PayDed_Payroll FOREIGN KEY (PayrollID)
        REFERENCES Payroll(PayrollID),
    CONSTRAINT FK_PayDed_Type   FOREIGN KEY (DeductionTypeID)
        REFERENCES DeductionTypes(DeductionTypeID)
);
GO
CREATE TABLE Payslips (
    PayslipID      INT IDENTITY(1,1) PRIMARY KEY,
    PayrollID      INT            NOT NULL UNIQUE,
    GeneratedAt    DATETIME       DEFAULT GETDATE(),
    FilePath       VARCHAR(255)   NULL,
    SentToEmployee BIT            DEFAULT 0,
    SentAt         DATETIME       NULL,
    CONSTRAINT FK_Payslip_Payroll FOREIGN KEY (PayrollID)
        REFERENCES Payroll(PayrollID)
);
GO
INSERT INTO Departments (DepartmentName, Location) VALUES
('Human Resources', 'Floor 1'),
('Engineering',     'Floor 2'),
('Finance',         'Floor 3'),
('Sales',           'Floor 4'),
('Operations',      'Floor 1');
GO
INSERT INTO Positions (PositionTitle, DepartmentID, MinSalary, MaxSalary) VALUES
('HR Manager',           1,  60000.00,  90000.00),
('HR Officer',           1,  30000.00,  55000.00),
('Senior Engineer',      2,  80000.00, 120000.00),
('Junior Engineer',      2,  40000.00,  70000.00),
('Finance Manager',      3,  65000.00,  95000.00),
('Accountant',           3,  35000.00,  60000.00),
('Sales Manager',        4,  60000.00,  90000.00),
('Sales Representative', 4,  25000.00,  50000.00),
('Operations Manager',   5,  55000.00,  85000.00),
('Operations Analyst',   5,  30000.00,  55000.00);
GO
INSERT INTO Employees
(FirstName, LastName, Email, Phone, NationalID, Gender, DateOfBirth,
 HireDate, EmploymentStatus, DepartmentID, PositionID, BasicSalary, BankAccount, BankName)
VALUES
('Sarah',   'Johnson',  'sarah.johnson@workiq.com',   '555-0101', 'NID10001', 'F', '1985-03-12', '2018-01-15', 'Active', 1,  1,  85000.00, 'ACC100001', 'First National Bank'),
('James',   'Williams', 'james.williams@workiq.com',  '555-0102', 'NID10002', 'M', '1990-07-22', '2019-04-01', 'Active', 1,  2,  48000.00, 'ACC100002', 'City Bank'),
('Michael', 'Brown',    'michael.brown@workiq.com',   '555-0103', 'NID10003', 'M', '1988-11-05', '2017-06-10', 'Active', 2,  3, 110000.00, 'ACC100003', 'Metro Bank'),
('Emily',   'Davis',    'emily.davis@workiq.com',     '555-0104', 'NID10004', 'F', '1995-02-18', '2021-09-01', 'Active', 2,  4,  58000.00, 'ACC100004', 'First National Bank'),
('Robert',  'Martinez', 'robert.martinez@workiq.com', '555-0105', 'NID10005', 'M', '1982-08-30', '2016-03-20', 'Active', 3,  5,  90000.00, 'ACC100005', 'City Bank'),
('Linda',   'Garcia',   'linda.garcia@workiq.com',    '555-0106', 'NID10006', 'F', '1992-05-14', '2020-11-15', 'Active', 3,  6,  52000.00, 'ACC100006', 'Metro Bank'),
('David',   'Wilson',   'david.wilson@workiq.com',    '555-0107', 'NID10007', 'M', '1987-09-25', '2018-07-01', 'Active', 4,  7,  80000.00, 'ACC100007', 'First National Bank'),
('Jessica', 'Anderson', 'jessica.anderson@workiq.com','555-0108', 'NID10008', 'F', '1993-12-03', '2022-02-14', 'Active', 4,  8,  38000.00, 'ACC100008', 'City Bank'),
('Thomas',  'Taylor',   'thomas.taylor@workiq.com',   '555-0109', 'NID10009', 'M', '1984-04-17', '2015-05-01', 'Active', 5,  9,  78000.00, 'ACC100009', 'Metro Bank'),
('Amanda',  'Lee',      'amanda.lee@workiq.com',      '555-0110', 'NID10010', 'F', '1997-01-29', '2023-01-10', 'Active', 5, 10,  42000.00, 'ACC100010', 'First National Bank');
GO
UPDATE Departments SET ManagerID = 1 WHERE DepartmentID = 1;
UPDATE Departments SET ManagerID = 3 WHERE DepartmentID = 2;
UPDATE Departments SET ManagerID = 5 WHERE DepartmentID = 3;
UPDATE Departments SET ManagerID = 7 WHERE DepartmentID = 4;
UPDATE Departments SET ManagerID = 9 WHERE DepartmentID = 5;
GO
INSERT INTO Attendance (EmployeeID, AttendanceDate, CheckIn, CheckOut, Status, OvertimeHours) VALUES
(1,'2025-05-01','08:55','17:05','Present',0.00),
(1,'2025-05-02','09:10','17:00','Late',   0.00),
(1,'2025-05-05','08:50','19:00','Present',2.00),
(1,'2025-05-06','08:45','17:00','Present',0.00),
(1,'2025-05-07','09:00','17:00','Present',0.00),
(1,'2025-05-08','08:55','17:00','Present',0.00),
(1,'2025-05-09','09:00','17:00','Present',0.00),
(1,'2025-05-12', NULL,   NULL,  'Absent', 0.00),
(1,'2025-05-13','08:50','17:00','Present',0.00),
(1,'2025-05-14','08:55','17:00','Present',0.00),
(1,'2025-05-15','09:00','18:30','Present',1.50),
(1,'2025-05-16','09:00','17:00','Present',0.00),
(1,'2025-05-19','08:45','17:00','Present',0.00),
(1,'2025-05-20','09:00','17:00','Present',0.00),
(1,'2025-05-21','09:05','17:00','Present',0.00),
(1,'2025-05-22','09:00','17:00','Present',0.00),
(1,'2025-05-23','08:55','17:00','Present',0.00),
(1,'2025-05-26','09:00','17:00','Present',0.00),
(1,'2025-05-27','08:50','17:00','Present',0.00),
(1,'2025-05-28','09:00','17:30','Present',0.50),
(1,'2025-05-29','09:00','17:00','Present',0.00),
(1,'2025-05-30','08:55','17:00','Present',0.00),
(2,'2025-05-01','09:00','17:00','Present',0.00),
(2,'2025-05-02','09:00','17:00','Present',0.00),
(2,'2025-05-05','09:15','17:00','Late',   0.00),
(2,'2025-05-06','09:00','17:00','Present',0.00),
(2,'2025-05-07','09:00','17:00','Present',0.00),
(2,'2025-05-08', NULL,   NULL,  'Absent', 0.00),
(2,'2025-05-09','09:00','17:00','Present',0.00),
(2,'2025-05-12','09:00','17:00','Present',0.00),
(2,'2025-05-13','09:00','17:00','Present',0.00),
(2,'2025-05-14','09:00','13:00','Half Day',0.00),
(2,'2025-05-15','09:00','17:00','Present',0.00),
(2,'2025-05-16','09:00','17:00','Present',0.00),
(2,'2025-05-19','09:00','17:00','Present',0.00),
(2,'2025-05-20','09:00','17:00','Present',0.00),
(2,'2025-05-21','09:00','17:00','Present',0.00),
(2,'2025-05-22','09:00','17:00','Present',0.00),
(2,'2025-05-23','09:00','17:00','Present',0.00),
(2,'2025-05-26','09:00','19:30','Present',2.50),
(2,'2025-05-27','09:00','17:00','Present',0.00),
(2,'2025-05-28','09:00','17:00','Present',0.00),
(2,'2025-05-29','09:00','17:00','Present',0.00),
(2,'2025-05-30','09:10','17:00','Late',   0.00),
(3,'2025-05-01','08:30','18:00','Present',1.00),
(3,'2025-05-02','08:45','17:00','Present',0.00),
(3,'2025-05-05','08:30','17:00','Present',0.00),
(3,'2025-05-06','08:30','20:00','Present',3.00),
(3,'2025-05-07','08:45','17:00','Present',0.00),
(3,'2025-05-08','08:30','17:00','Present',0.00),
(3,'2025-05-09','08:45','17:00','Present',0.00),
(3,'2025-05-12','08:30','17:00','Present',0.00),
(3,'2025-05-13','08:30','17:00','Present',0.00),
(3,'2025-05-14','08:45','17:00','Present',0.00),
(3,'2025-05-15','08:30','17:00','Present',0.00),
(3,'2025-05-16','08:30','17:00','Present',0.00),
(3,'2025-05-19','08:45','17:00','Present',0.00),
(3,'2025-05-20','08:30','17:00','Present',0.00),
(3,'2025-05-21', NULL,   NULL,  'Absent', 0.00),
(3,'2025-05-22','08:30','17:00','Present',0.00),
(3,'2025-05-23','08:30','17:00','Present',0.00),
(3,'2025-05-26','08:30','17:00','Present',0.00),
(3,'2025-05-27','08:45','19:00','Present',2.00),
(3,'2025-05-28','08:30','17:00','Present',0.00),
(3,'2025-05-29','08:30','17:00','Present',0.00),
(3,'2025-05-30','08:45','17:00','Present',0.00),
(4,'2025-05-01','09:00','17:00','Present',0.00),
(4,'2025-05-02','09:20','17:00','Late',   0.00),
(4,'2025-05-05','09:00','17:00','Present',0.00),
(4,'2025-05-06','09:00','17:00','Present',0.00),
(4,'2025-05-07', NULL,   NULL,  'Absent', 0.00),
(4,'2025-05-08','09:00','17:00','Present',0.00),
(4,'2025-05-09','09:00','17:00','Present',0.00),
(4,'2025-05-12','09:00','18:00','Present',1.00),
(4,'2025-05-13','09:00','17:00','Present',0.00),
(4,'2025-05-14','09:00','17:00','Present',0.00),
(4,'2025-05-15','09:00','17:00','Present',0.00),
(4,'2025-05-16','09:00','17:00','Present',0.00),
(4,'2025-05-19','09:00','17:00','Present',0.00),
(4,'2025-05-20','09:00','17:00','Present',0.00),
(4,'2025-05-21','09:00','17:00','Present',0.00),
(4,'2025-05-22','09:00','17:00','Present',0.00),
(4,'2025-05-23','09:00','17:00','Present',0.00),
(4,'2025-05-26','09:00','17:00','Present',0.00),
(4,'2025-05-27','09:00','17:00','Present',0.00),
(4,'2025-05-28','09:00','17:00','Present',0.00),
(4,'2025-05-29','09:00','17:00','Present',0.00),
(4,'2025-05-30','09:00','17:00','Present',0.00),
(5,'2025-05-01','08:00','17:00','Present',0.00),
(5,'2025-05-02','08:00','17:00','Present',0.00),
(5,'2025-05-05','08:00','17:00','Present',0.00),
(5,'2025-05-06','08:00','17:00','Present',0.00),
(5,'2025-05-07','08:00','17:00','Present',0.00),
(5,'2025-05-08','08:00','17:00','Present',0.00),
(5,'2025-05-09','08:00','17:00','Present',0.00),
(5,'2025-05-12','08:00','17:00','Present',0.00),
(5,'2025-05-13','08:00','17:00','Present',0.00),
(5,'2025-05-14','08:00','17:00','Present',0.00),
(5,'2025-05-15','08:00','17:00','Present',0.00),
(5,'2025-05-16','08:00','19:30','Present',2.50),
(5,'2025-05-19','08:00','17:00','Present',0.00),
(5,'2025-05-20','08:00','17:00','Present',0.00),
(5,'2025-05-21','08:00','17:00','Present',0.00),
(5,'2025-05-22','08:00','17:00','Present',0.00),
(5,'2025-05-23','08:00','17:00','Present',0.00),
(5,'2025-05-26','08:00','17:00','Present',0.00),
(5,'2025-05-27','08:00','17:00','Present',0.00),
(5,'2025-05-28','08:00','17:00','Present',0.00),
(5,'2025-05-29','08:00','17:00','Present',0.00),
(5,'2025-05-30','08:00','17:00','Present',0.00),
(6,'2025-05-01','09:05','17:00','Present',0.00),
(6,'2025-05-02','09:00','17:00','Present',0.00),
(6,'2025-05-05','09:00','17:00','Present',0.00),
(6,'2025-05-06', NULL,   NULL,  'Absent', 0.00),
(6,'2025-05-07','09:00','17:00','Present',0.00),
(6,'2025-05-08','09:00','17:00','Present',0.00),
(6,'2025-05-09','09:30','17:00','Late',   0.00),
(6,'2025-05-12','09:00','17:00','Present',0.00),
(6,'2025-05-13','09:00','17:00','Present',0.00),
(6,'2025-05-14','09:00','17:00','Present',0.00),
(6,'2025-05-15','09:00','17:00','Present',0.00),
(6,'2025-05-16','09:00','17:00','Present',0.00),
(6,'2025-05-19','09:00','17:00','Present',0.00),
(6,'2025-05-20','09:00','13:00','Half Day',0.00),
(6,'2025-05-21','09:00','17:00','Present',0.00),
(6,'2025-05-22','09:00','17:00','Present',0.00),
(6,'2025-05-23','09:00','17:00','Present',0.00),
(6,'2025-05-26','09:00','17:00','Present',0.00),
(6,'2025-05-27','09:00','17:00','Present',0.00),
(6,'2025-05-28','09:00','17:00','Present',0.00),
(6,'2025-05-29','09:00','17:00','Present',0.00),
(6,'2025-05-30','09:00','17:00','Present',0.00),
(7,'2025-05-01','09:00','17:00','Present',0.00),
(7,'2025-05-02','09:00','17:00','Present',0.00),
(7,'2025-05-05','09:00','17:00','Present',0.00),
(7,'2025-05-06','09:00','17:00','Present',0.00),
(7,'2025-05-07','09:00','17:00','Present',0.00),
(7,'2025-05-08','09:00','17:00','Present',0.00),
(7,'2025-05-09','09:00','19:00','Present',2.00),
(7,'2025-05-12','09:00','17:00','Present',0.00),
(7,'2025-05-13','09:00','17:00','Present',0.00),
(7,'2025-05-14','09:00','17:00','Present',0.00),
(7,'2025-05-15','09:00','17:00','Present',0.00),
(7,'2025-05-16', NULL,   NULL,  'Absent', 0.00),
(7,'2025-05-19','09:00','17:00','Present',0.00),
(7,'2025-05-20','09:00','17:00','Present',0.00),
(7,'2025-05-21','09:00','17:00','Present',0.00),
(7,'2025-05-22','09:00','17:00','Present',0.00),
(7,'2025-05-23','09:00','17:00','Present',0.00),
(7,'2025-05-26','09:00','17:00','Present',0.00),
(7,'2025-05-27','09:00','17:00','Present',0.00),
(7,'2025-05-28','09:00','17:00','Present',0.00),
(7,'2025-05-29','09:00','17:00','Present',0.00),
(7,'2025-05-30','09:00','17:00','Present',0.00),
(8,'2025-05-01','09:00','17:00','Present',0.00),
(8,'2025-05-02','09:25','17:00','Late',   0.00),
(8,'2025-05-05','09:00','17:00','Present',0.00),
(8,'2025-05-06','09:00','17:00','Present',0.00),
(8,'2025-05-07','09:00','17:00','Present',0.00),
(8,'2025-05-08','09:00','17:00','Present',0.00),
(8,'2025-05-09','09:00','17:00','Present',0.00),
(8,'2025-05-12', NULL,   NULL,  'Absent', 0.00),
(8,'2025-05-13','09:00','17:00','Present',0.00),
(8,'2025-05-14','09:00','17:00','Present',0.00),
(8,'2025-05-15','09:00','17:00','Present',0.00),
(8,'2025-05-16','09:00','17:00','Present',0.00),
(8,'2025-05-19','09:00','17:00','Present',0.00),
(8,'2025-05-20','09:00','17:00','Present',0.00),
(8,'2025-05-21','09:00','17:00','Present',0.00),
(8,'2025-05-22','09:00','17:00','Present',0.00),
(8,'2025-05-23','09:00','17:00','Present',0.00),
(8,'2025-05-26','09:00','17:00','Present',0.00),
(8,'2025-05-27','09:00','17:00','Present',0.00),
(8,'2025-05-28','09:00','17:00','Present',0.00),
(8,'2025-05-29','09:00','17:00','Present',0.00),
(8,'2025-05-30','09:00','17:00','Present',0.00),
(9,'2025-05-01','08:00','17:00','Present',0.00),
(9,'2025-05-02','08:00','17:00','Present',0.00),
(9,'2025-05-05','08:00','17:00','Present',0.00),
(9,'2025-05-06','08:00','17:00','Present',0.00),
(9,'2025-05-07','08:00','17:00','Present',0.00),
(9,'2025-05-08','08:00','17:00','Present',0.00),
(9,'2025-05-09','08:00','17:00','Present',0.00),
(9,'2025-05-12','08:00','17:00','Present',0.00),
(9,'2025-05-13','08:00','17:00','Present',0.00),
(9,'2025-05-14','08:00','17:00','Present',0.00),
(9,'2025-05-15','08:00','18:30','Present',1.50),
(9,'2025-05-16','08:00','17:00','Present',0.00),
(9,'2025-05-19','08:00','17:00','Present',0.00),
(9,'2025-05-20','08:00','17:00','Present',0.00),
(9,'2025-05-21','08:00','17:00','Present',0.00),
(9,'2025-05-22', NULL,   NULL,  'Absent', 0.00),
(9,'2025-05-23','08:00','17:00','Present',0.00),
(9,'2025-05-26','08:00','17:00','Present',0.00),
(9,'2025-05-27','08:00','17:00','Present',0.00),
(9,'2025-05-28','08:00','17:00','Present',0.00),
(9,'2025-05-29','08:00','17:00','Present',0.00),
(9,'2025-05-30','08:00','17:00','Present',0.00),
(10,'2025-05-01','09:00','17:00','Present',0.00),
(10,'2025-05-02','09:00','17:00','Present',0.00),
(10,'2025-05-05','09:00','17:00','Present',0.00),
(10,'2025-05-06','09:35','17:00','Late',   0.00),
(10,'2025-05-07','09:00','17:00','Present',0.00),
(10,'2025-05-08','09:00','17:00','Present',0.00),
(10,'2025-05-09','09:00','17:00','Present',0.00),
(10,'2025-05-12','09:00','17:00','Present',0.00),
(10,'2025-05-13', NULL,   NULL,  'Absent', 0.00),
(10,'2025-05-14','09:00','17:00','Present',0.00),
(10,'2025-05-15','09:00','17:00','Present',0.00),
(10,'2025-05-16','09:00','17:00','Present',0.00),
(10,'2025-05-19','09:00','17:00','Present',0.00),
(10,'2025-05-20','09:00','17:00','Present',0.00),
(10,'2025-05-21','09:00','17:00','Present',0.00),
(10,'2025-05-22','09:00','17:00','Present',0.00),
(10,'2025-05-23','09:00','17:00','Present',0.00),
(10,'2025-05-26','09:00','17:00','Present',0.00),
(10,'2025-05-27','09:00','17:00','Present',0.00),
(10,'2025-05-28','09:00','17:00','Present',0.00),
(10,'2025-05-29','09:00','17:00','Present',0.00),
(10,'2025-05-30','09:00','17:00','Present',0.00);
GO
INSERT INTO LeaveTypes (LeaveTypeName, MaxDaysPerYear, IsPaid) VALUES
('Annual Leave',    21, 1),
('Sick Leave',      10, 1),
('Maternity Leave', 90, 1),
('Paternity Leave', 14, 1),
('Unpaid Leave',    30, 0),
('Study Leave',      5, 1);
GO
INSERT INTO LeaveRequests (EmployeeID, LeaveTypeID, StartDate, EndDate, Reason, Status, ApprovedBy) VALUES
(2,  1, '2025-05-08', '2025-05-08', 'Personal errand',       'Approved', 1),
(4,  2, '2025-05-07', '2025-05-07', 'Feeling unwell',        'Approved', 3),
(6,  1, '2025-05-20', '2025-05-20', 'Family commitment',     'Approved', 5),
(8,  2, '2025-05-12', '2025-05-12', 'Doctor appointment',    'Approved', 7),
(10, 2, '2025-05-13', '2025-05-13', 'Medical checkup',       'Approved', 9),
(3,  1, '2025-06-02', '2025-06-06', 'Annual vacation',       'Pending',  NULL),
(5,  6, '2025-06-10', '2025-06-11', 'Professional training', 'Pending',  NULL);
GO
INSERT INTO TaxBrackets (BracketName, MinIncome, MaxIncome, TaxRate, EffectiveFrom) VALUES
('Tax Free',        0.00,       12000.00, 0.0000, '2024-01-01'),
('Basic Rate',      12000.01,   50000.00, 0.2000, '2024-01-01'),
('Higher Rate',     50000.01,  100000.00, 0.4000, '2024-01-01'),
('Additional Rate', 100000.01,  NULL,     0.4500, '2024-01-01');
GO
INSERT INTO DeductionTypes (DeductionName, DeductionCategory, CalculationMethod, DefaultValue, IsActive) VALUES
('National Insurance',   'Statutory', 'Percentage', 0.1200, 1),
('Employee Pension',     'Statutory', 'Percentage', 0.0500, 1),
('Health Insurance',     'Voluntary', 'Fixed',      150.00, 1),
('Life Insurance',       'Voluntary', 'Fixed',       50.00, 1),
('Staff Loan Repayment', 'Loan',      'Fixed',      200.00, 1);
GO
INSERT INTO EmployeeDeductions (EmployeeID, DeductionTypeID, CustomValue, StartDate) VALUES
(1,1,NULL,'2018-01-15'),(2,1,NULL,'2019-04-01'),(3,1,NULL,'2017-06-10'),
(4,1,NULL,'2021-09-01'),(5,1,NULL,'2016-03-20'),(6,1,NULL,'2020-11-15'),
(7,1,NULL,'2018-07-01'),(8,1,NULL,'2022-02-14'),(9,1,NULL,'2015-05-01'),
(10,1,NULL,'2023-01-10'),
(1,2,NULL,'2018-01-15'),(2,2,NULL,'2019-04-01'),(3,2,NULL,'2017-06-10'),
(4,2,NULL,'2021-09-01'),(5,2,NULL,'2016-03-20'),(6,2,NULL,'2020-11-15'),
(7,2,NULL,'2018-07-01'),(8,2,NULL,'2022-02-14'),(9,2,NULL,'2015-05-01'),
(10,2,NULL,'2023-01-10'),
(1,3,NULL,'2018-01-15'),(3,3,NULL,'2017-06-10'),(5,3,NULL,'2016-03-20'),
(7,3,NULL,'2018-07-01'),(9,3,NULL,'2015-05-01'),
(1,4,NULL,'2018-01-15'),(3,4,NULL,'2017-06-10'),(5,4,NULL,'2016-03-20'),
(7,4,NULL,'2018-07-01'),(9,4,NULL,'2015-05-01'),
(2,5,NULL,'2024-01-01'),(6,5,NULL,'2024-03-01'),(8,5,NULL,'2024-06-01');
GO
INSERT INTO PayrollPeriods (PeriodName, StartDate, EndDate, PayDate, Status) VALUES
('January 2025',  '2025-01-01', '2025-01-31', '2025-01-31', 'Closed'),
('February 2025', '2025-02-01', '2025-02-28', '2025-02-28', 'Closed'),
('March 2025',    '2025-03-01', '2025-03-31', '2025-03-31', 'Closed'),
('April 2025',    '2025-04-01', '2025-04-30', '2025-04-30', 'Closed'),
('May 2025',      '2025-05-01', '2025-05-31', '2025-05-31', 'Closed'),
('June 2025',     '2025-06-01', '2025-06-30', '2025-06-30', 'Open');
GO
INSERT INTO Payroll
(EmployeeID, PeriodID, BasicSalary, OvertimePay, Allowances, TotalDeductions, TaxAmount, PaymentStatus, ProcessedAt)
VALUES
(1,  5, 85000.00/12,  354.17, 500.00, 1310.42, 2097.22, 'Paid', '2025-05-31'),
(2,  5, 48000.00/12,  250.00, 300.00,  936.00,  740.00, 'Paid', '2025-05-31'),
(3,  5,110000.00/12,  687.50, 800.00, 1591.67, 3479.17, 'Paid', '2025-05-31'),
(4,  5, 58000.00/12,  120.83, 300.00, 1003.33, 1076.67, 'Paid', '2025-05-31'),
(5,  5, 90000.00/12,  562.50, 600.00, 1545.00, 2595.00, 'Paid', '2025-05-31'),
(6,  5, 52000.00/12,    0.00, 300.00, 1136.67,  886.67, 'Paid', '2025-05-31'),
(7,  5, 80000.00/12,  416.67, 500.00, 1483.33, 2083.33, 'Paid', '2025-05-31'),
(8,  5, 38000.00/12,    0.00, 200.00, 1020.00,  576.67, 'Paid', '2025-05-31'),
(9,  5, 78000.00/12,  354.17, 500.00, 1480.00, 2004.17, 'Paid', '2025-05-31'),
(10, 5, 42000.00/12,    0.00, 200.00,  820.00,  700.00, 'Paid', '2025-05-31');
GO
INSERT INTO PayrollDeductions (PayrollID, DeductionTypeID, AmountDeducted) VALUES
(1,1, 850.00),(1,2, 354.17),(1,3,150.00),(1,4,50.00),
(2,1, 480.00),(2,2, 200.00),(2,5,200.00),
(3,1,1100.00),(3,2, 458.33),(3,3,150.00),(3,4,50.00),
(4,1, 580.00),(4,2, 241.67),
(5,1, 900.00),(5,2, 375.00),(5,3,150.00),(5,4,50.00),
(6,1, 520.00),(6,2, 216.67),(6,5,200.00),
(7,1, 800.00),(7,2, 333.33),(7,3,150.00),(7,4,50.00),
(8,1, 380.00),(8,2, 158.33),(8,5,200.00),
(9,1, 780.00),(9,2, 325.00),(9,3,150.00),(9,4,50.00),
(10,1,420.00),(10,2,175.00);
GO
INSERT INTO Payslips (PayrollID, GeneratedAt, SentToEmployee, SentAt) VALUES
(1,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(2,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(3,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(4,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(5,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(6,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(7,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(8,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(9,  '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00'),
(10, '2025-05-31 18:00:00', 1, '2025-05-31 18:05:00');
GO
SELECT 'Departments'       AS TableName, COUNT(*) AS Records FROM Departments       UNION ALL
SELECT 'Positions',                      COUNT(*)            FROM Positions          UNION ALL
SELECT 'Employees',                      COUNT(*)            FROM Employees          UNION ALL
SELECT 'Attendance',                     COUNT(*)            FROM Attendance         UNION ALL
SELECT 'LeaveTypes',                     COUNT(*)            FROM LeaveTypes         UNION ALL
SELECT 'LeaveRequests',                  COUNT(*)            FROM LeaveRequests      UNION ALL
SELECT 'TaxBrackets',                    COUNT(*)            FROM TaxBrackets        UNION ALL
SELECT 'DeductionTypes',                 COUNT(*)            FROM DeductionTypes     UNION ALL
SELECT 'EmployeeDeductions',             COUNT(*)            FROM EmployeeDeductions UNION ALL
SELECT 'PayrollPeriods',                 COUNT(*)            FROM PayrollPeriods     UNION ALL
SELECT 'Payroll',                        COUNT(*)            FROM Payroll            UNION ALL
SELECT 'PayrollDeductions',              COUNT(*)            FROM PayrollDeductions  UNION ALL
SELECT 'Payslips',                       COUNT(*)            FROM Payslips;
GO
