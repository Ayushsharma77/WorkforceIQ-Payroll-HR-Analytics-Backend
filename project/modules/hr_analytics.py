from config.config import get_connection
from tabulate import tabulate

# ============================================================
#   HR ANALYTICS - WorkforceIQ
# ============================================================


def headcount_by_department():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            d.DepartmentName,
            COUNT(e.EmployeeID)                                          AS TotalEmployees,
            SUM(CASE WHEN e.Gender = 'M' THEN 1 ELSE 0 END)             AS Male,
            SUM(CASE WHEN e.Gender = 'F' THEN 1 ELSE 0 END)             AS Female,
            AVG(e.BasicSalary)                                           AS AvgSalary,
            MAX(e.BasicSalary)                                           AS MaxSalary,
            MIN(e.BasicSalary)                                           AS MinSalary
        FROM Departments d
        LEFT JOIN Employees e ON d.DepartmentID = e.DepartmentID
                              AND e.EmploymentStatus = 'Active'
        GROUP BY d.DepartmentID, d.DepartmentName
        ORDER BY TotalEmployees DESC
    """)
    rows = cursor.fetchall()
    headers = ["Department", "Total", "Male", "Female", "Avg Salary", "Max Salary", "Min Salary"]
    print("\n" + "="*75)
    print("              HEADCOUNT BY DEPARTMENT")
    print("="*75)
    print(tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f"))
    conn.close()


def salary_distribution():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            p.PositionTitle,
            e.BasicSalary,
            RANK() OVER (ORDER BY e.BasicSalary DESC)               AS SalaryRank,
            RANK() OVER (PARTITION BY d.DepartmentID
                         ORDER BY e.BasicSalary DESC)               AS RankInDept,
            AVG(e.BasicSalary) OVER (PARTITION BY d.DepartmentID)   AS DeptAvgSalary,
            e.BasicSalary - AVG(e.BasicSalary)
                           OVER (PARTITION BY d.DepartmentID)       AS VsAverage
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions   p ON e.PositionID   = p.PositionID
        WHERE e.EmploymentStatus = 'Active'
        ORDER BY e.BasicSalary DESC
    """)
    rows = cursor.fetchall()
    headers = ["Name", "Department", "Position", "Salary", "Overall Rank",
               "Dept Rank", "Dept Avg", "Vs Avg"]
    print("\n" + "="*95)
    print("              SALARY DISTRIBUTION (Window Functions)")
    print("="*95)
    print(tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f"))
    conn.close()


def top_earners(limit=5):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP (?)
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            p.PositionTitle,
            e.BasicSalary,
            e.HireDate
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions   p ON e.PositionID   = p.PositionID
        WHERE e.EmploymentStatus = 'Active'
        ORDER BY e.BasicSalary DESC
    """, limit)
    rows = cursor.fetchall()
    headers = ["Name", "Department", "Position", "Salary", "Hire Date"]
    print(f"\n{'='*65}")
    print(f"  TOP {limit} EARNERS")
    print(f"{'='*65}")
    print(tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f"))
    conn.close()


def attendance_analytics(year, month):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            COUNT(*)                                                    AS TotalDays,
            SUM(CASE WHEN a.Status = 'Present'  THEN 1 ELSE 0 END)    AS Present,
            SUM(CASE WHEN a.Status = 'Absent'   THEN 1 ELSE 0 END)    AS Absent,
            SUM(CASE WHEN a.Status = 'Late'     THEN 1 ELSE 0 END)    AS Late,
            SUM(a.OvertimeHours)                                        AS TotalOT,
            CAST(
                SUM(CASE WHEN a.Status = 'Present' THEN 1.0 ELSE 0 END)
                / COUNT(*) * 100 AS DECIMAL(5,1))                      AS AttendanceRate
        FROM Attendance a
        JOIN Employees   e ON a.EmployeeID   = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        WHERE YEAR(a.AttendanceDate)  = ?
          AND MONTH(a.AttendanceDate) = ?
        GROUP BY e.EmployeeID, e.FirstName, e.LastName, d.DepartmentName
        ORDER BY AttendanceRate DESC
    """, year, month)
    rows = cursor.fetchall()
    headers = ["Name", "Department", "Days", "Present", "Absent", "Late", "OT Hrs", "Rate%"]
    print(f"\n{'='*80}")
    print(f"  ATTENDANCE ANALYTICS — {year}-{str(month).zfill(2)}")
    print(f"{'='*80}")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    conn.close()


def payroll_cost_by_department(period_id):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            d.DepartmentName,
            COUNT(p.PayrollID)      AS Employees,
            SUM(p.GrossSalary)      AS TotalGross,
            SUM(p.TotalDeductions)  AS TotalDeductions,
            SUM(p.TaxAmount)        AS TotalTax,
            SUM(p.NetSalary)        AS TotalNet,
            AVG(p.NetSalary)        AS AvgNetSalary
        FROM Payroll p
        JOIN Employees   e ON p.EmployeeID   = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        WHERE p.PeriodID = ?
        GROUP BY d.DepartmentID, d.DepartmentName
        ORDER BY TotalGross DESC
    """, period_id)
    rows = cursor.fetchall()
    headers = ["Department", "Employees", "Total Gross", "Deductions", "Tax", "Total Net", "Avg Net"]
    cursor.execute("SELECT PeriodName FROM PayrollPeriods WHERE PeriodID = ?", period_id)
    period = cursor.fetchone()
    print(f"\n{'='*85}")
    print(f"  PAYROLL COST BY DEPARTMENT — {period[0] if period else period_id}")
    print(f"{'='*85}")
    print(tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f"))
    conn.close()


def employee_tenure_report():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.FirstName + ' ' + e.LastName                          AS FullName,
            d.DepartmentName,
            p.PositionTitle,
            e.HireDate,
            DATEDIFF(YEAR,  e.HireDate, GETDATE())                  AS YearsOfService,
            DATEDIFF(MONTH, e.HireDate, GETDATE()) % 12             AS ExtraMonths,
            e.BasicSalary,
            NTILE(4) OVER (ORDER BY e.HireDate)                     AS SeniorityQuartile
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions   p ON e.PositionID   = p.PositionID
        WHERE e.EmploymentStatus = 'Active'
        ORDER BY e.HireDate
    """)
    rows = cursor.fetchall()
    headers = ["Name", "Department", "Position", "Hire Date", "Years", "Months", "Salary", "Quartile"]
    print(f"\n{'='*90}")
    print(f"  EMPLOYEE TENURE REPORT")
    print(f"{'='*90}")
    print(tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f"))
    conn.close()


def leave_usage_report(year):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            lt.LeaveTypeName,
            COUNT(lr.LeaveRequestID)        AS Requests,
            SUM(lr.TotalDays)               AS TotalDaysTaken,
            lt.MaxDaysPerYear               AS MaxAllowed,
            lt.MaxDaysPerYear - SUM(lr.TotalDays) AS Remaining
        FROM LeaveRequests lr
        JOIN Employees  e  ON lr.EmployeeID  = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN LeaveTypes lt ON lr.LeaveTypeID = lt.LeaveTypeID
        WHERE lr.Status = 'Approved'
          AND YEAR(lr.StartDate) = ?
        GROUP BY e.EmployeeID, e.FirstName, e.LastName,
                 d.DepartmentName, lt.LeaveTypeName, lt.MaxDaysPerYear
        ORDER BY e.FirstName, lt.LeaveTypeName
    """, year)
    rows = cursor.fetchall()
    headers = ["Name", "Department", "Leave Type", "Requests", "Days Taken", "Max", "Remaining"]
    print(f"\n{'='*80}")
    print(f"  LEAVE USAGE REPORT — {year}")
    print(f"{'='*80}")
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("  No approved leave records found.")
    conn.close()


def company_overview():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmploymentStatus = 'Active'")
    total_emp = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(BasicSalary), SUM(BasicSalary) FROM Employees WHERE EmploymentStatus = 'Active'")
    sal = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM LeaveRequests WHERE Status = 'Pending'")
    pending_leaves = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM PayrollPeriods WHERE Status = 'Open'")
    open_periods = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Departments")
    dept_count = cursor.fetchone()[0]

    print("\n" + "="*45)
    print("       COMPANY OVERVIEW — WorkforceIQ")
    print("="*45)
    print(f"  Total Active Employees  : {total_emp}")
    print(f"  Total Departments       : {dept_count}")
    print(f"  Average Salary          : ${float(sal[0]):,.2f}")
    print(f"  Total Annual Salary Bill: ${float(sal[1]):,.2f}")
    print(f"  Pending Leave Requests  : {pending_leaves}")
    print(f"  Open Payroll Periods    : {open_periods}")
    print("="*45)
    conn.close()


def analytics_menu():
    while True:
        print("\n" + "="*40)
        print("         HR ANALYTICS")
        print("="*40)
        print("  1. Company Overview")
        print("  2. Headcount by Department")
        print("  3. Salary Distribution")
        print("  4. Top Earners")
        print("  5. Attendance Analytics")
        print("  6. Payroll Cost by Department")
        print("  7. Employee Tenure Report")
        print("  8. Leave Usage Report")
        print("  0. Back to Main Menu")
        print("="*40)
        choice = input("  Enter choice: ")

        if choice == '1':
            company_overview()
        elif choice == '2':
            headcount_by_department()
        elif choice == '3':
            salary_distribution()
        elif choice == '4':
            n = int(input("  How many top earners to show? "))
            top_earners(n)
        elif choice == '5':
            year  = int(input("  Year  (YYYY): "))
            month = int(input("  Month (MM)  : "))
            attendance_analytics(year, month)
        elif choice == '6':
            period_id = int(input("  Period ID: "))
            payroll_cost_by_department(period_id)
        elif choice == '7':
            employee_tenure_report()
        elif choice == '8':
            year = int(input("  Year (YYYY): "))
            leave_usage_report(year)
        elif choice == '0':
            break
        else:
            print("  [!] Invalid choice, try again")
# using namespace std;

def get_company_overview_web():
    from config.config import get_connection
    conn = get_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmploymentStatus = 'Active'")
    total_emp = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(BasicSalary), SUM(BasicSalary) FROM Employees WHERE EmploymentStatus = 'Active'")
    sal = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM LeaveRequests WHERE Status = 'Pending'")
    pending_leaves = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM PayrollPeriods WHERE Status = 'Open'")
    open_periods = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Departments")
    dept_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Return as a dictionary for the web
    return {
        'total_employees': total_emp,
        'departments': dept_count,
        'avg_salary': float(sal[0]) if sal[0] else 0,
        'total_salary': float(sal[1]) if sal[1] else 0,
        'pending_leaves': pending_leaves,
        'open_periods': open_periods
    }

if __name__ == "__main__":
    analytics_menu()