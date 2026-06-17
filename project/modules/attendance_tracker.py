from config.config import get_connection
from tabulate import tabulate
from datetime import date

# ============================================================
#   ATTENDANCE TRACKER - WorkforceIQ
# ============================================================


def mark_attendance(employee_id, status, check_in=None, check_out=None, overtime=0.00, notes=None):
    today = date.today().strftime('%Y-%m-%d')
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    # Check if already marked
    cursor.execute("SELECT AttendanceID FROM Attendance WHERE EmployeeID = ? AND AttendanceDate = ?",
                   employee_id, today)
    if cursor.fetchone():
        print(f"  [!] Attendance already marked for Employee ID {employee_id} today ({today})")
        conn.close()
        return
    cursor.execute("""
        INSERT INTO Attendance (EmployeeID, AttendanceDate, CheckIn, CheckOut, Status, OvertimeHours, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, employee_id, today, check_in, check_out, status, overtime, notes)
    conn.commit()
    print(f"  [OK] Attendance marked: Employee {employee_id} — {status} on {today}")
    conn.close()


def view_attendance_by_employee(employee_id):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.AttendanceDate,
            a.CheckIn,
            a.CheckOut,
            a.Status,
            a.OvertimeHours,
            a.Notes
        FROM Attendance a
        WHERE a.EmployeeID = ?
        ORDER BY a.AttendanceDate DESC
    """, employee_id)
    rows = cursor.fetchall()
    headers = ["Date", "Check In", "Check Out", "Status", "Overtime Hrs", "Notes"]
    if rows:
        # Get employee name
        cursor.execute("SELECT FirstName + ' ' + LastName FROM Employees WHERE EmployeeID = ?", employee_id)
        name = cursor.fetchone()[0]
        print(f"\n{'='*65}")
        print(f"  ATTENDANCE RECORD — {name} (ID: {employee_id})")
        print(f"{'='*65}")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print(f"  [!] No attendance records found for Employee ID {employee_id}")
    conn.close()


def view_attendance_by_date(attendance_date):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            a.CheckIn,
            a.CheckOut,
            a.Status,
            a.OvertimeHours
        FROM Attendance a
        JOIN Employees   e ON a.EmployeeID   = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        WHERE a.AttendanceDate = ?
        ORDER BY d.DepartmentName, e.FirstName
    """, attendance_date)
    rows = cursor.fetchall()
    headers = ["Emp ID", "Full Name", "Department", "Check In", "Check Out", "Status", "OT Hrs"]
    if rows:
        print(f"\n{'='*70}")
        print(f"  ATTENDANCE — {attendance_date}")
        print(f"{'='*70}")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print(f"  [!] No attendance records found for {attendance_date}")
    conn.close()


def monthly_attendance_summary(employee_id, year, month):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*)                                         AS TotalDays,
            SUM(CASE WHEN Status = 'Present'  THEN 1 ELSE 0 END) AS Present,
            SUM(CASE WHEN Status = 'Absent'   THEN 1 ELSE 0 END) AS Absent,
            SUM(CASE WHEN Status = 'Late'     THEN 1 ELSE 0 END) AS Late,
            SUM(CASE WHEN Status = 'Half Day' THEN 1 ELSE 0 END) AS HalfDay,
            SUM(CASE WHEN Status = 'On Leave' THEN 1 ELSE 0 END) AS OnLeave,
            SUM(OvertimeHours)                               AS TotalOvertime
        FROM Attendance
        WHERE EmployeeID = ?
          AND YEAR(AttendanceDate)  = ?
          AND MONTH(AttendanceDate) = ?
    """, employee_id, year, month)
    row = cursor.fetchone()
    cursor.execute("SELECT FirstName + ' ' + LastName FROM Employees WHERE EmployeeID = ?", employee_id)
    name = cursor.fetchone()[0]
    print(f"\n{'='*45}")
    print(f"  MONTHLY SUMMARY — {name}")
    print(f"  Period: {year}-{str(month).zfill(2)}")
    print(f"{'='*45}")
    print(f"  Total Days Recorded : {row[0]}")
    print(f"  Present             : {row[1]}")
    print(f"  Absent              : {row[2]}")
    print(f"  Late                : {row[3]}")
    print(f"  Half Day            : {row[4]}")
    print(f"  On Leave            : {row[5]}")
    print(f"  Total Overtime Hrs  : {row[6]:.2f}")
    attendance_rate = (row[1] / row[0] * 100) if row[0] > 0 else 0
    print(f"  Attendance Rate     : {attendance_rate:.1f}%")
    print(f"{'='*45}")
    conn.close()


def department_attendance_summary(dept_id, attendance_date):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.FirstName + ' ' + e.LastName AS FullName,
            ISNULL(a.Status, 'Not Marked')  AS Status,
            ISNULL(CAST(a.CheckIn  AS VARCHAR), '-') AS CheckIn,
            ISNULL(CAST(a.CheckOut AS VARCHAR), '-') AS CheckOut,
            ISNULL(a.OvertimeHours, 0)      AS OvertimeHours
        FROM Employees e
        LEFT JOIN Attendance a ON e.EmployeeID = a.EmployeeID
                               AND a.AttendanceDate = ?
        WHERE e.DepartmentID = ?
        ORDER BY e.FirstName
    """, attendance_date, dept_id)
    rows = cursor.fetchall()
    headers = ["Full Name", "Status", "Check In", "Check Out", "OT Hrs"]
    cursor.execute("SELECT DepartmentName FROM Departments WHERE DepartmentID = ?", dept_id)
    dept = cursor.fetchone()[0]
    print(f"\n{'='*65}")
    print(f"  {dept} DEPARTMENT — {attendance_date}")
    print(f"{'='*65}")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    conn.close()


def late_arrivals_report(year, month):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            COUNT(*) AS LateCount
        FROM Attendance a
        JOIN Employees   e ON a.EmployeeID   = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        WHERE a.Status = 'Late'
          AND YEAR(a.AttendanceDate)  = ?
          AND MONTH(a.AttendanceDate) = ?
        GROUP BY e.EmployeeID, e.FirstName, e.LastName, d.DepartmentName
        ORDER BY LateCount DESC
    """, year, month)
    rows = cursor.fetchall()
    headers = ["Emp ID", "Full Name", "Department", "Late Count"]
    print(f"\n{'='*55}")
    print(f"  LATE ARRIVALS — {year}-{str(month).zfill(2)}")
    print(f"{'='*55}")
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("  No late arrivals recorded.")
    conn.close()


def overtime_report(year, month):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            SUM(a.OvertimeHours)            AS TotalOvertimeHours,
            e.BasicSalary / 160             AS HourlyRate,
            SUM(a.OvertimeHours) * (e.BasicSalary / 160) * 1.5 AS OvertimePay
        FROM Attendance a
        JOIN Employees   e ON a.EmployeeID   = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        WHERE a.OvertimeHours > 0
          AND YEAR(a.AttendanceDate)  = ?
          AND MONTH(a.AttendanceDate) = ?
        GROUP BY e.EmployeeID, e.FirstName, e.LastName, d.DepartmentName, e.BasicSalary
        ORDER BY TotalOvertimeHours DESC
    """, year, month)
    rows = cursor.fetchall()
    headers = ["Emp ID", "Full Name", "Department", "OT Hours", "Hourly Rate", "OT Pay"]
    print(f"\n{'='*70}")
    print(f"  OVERTIME REPORT — {year}-{str(month).zfill(2)}")
    print(f"{'='*70}")
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid", floatfmt=".2f"))
    else:
        print("  No overtime recorded.")
    conn.close()


def attendance_menu():
    while True:
        print("\n" + "="*40)
        print("       ATTENDANCE TRACKER")
        print("="*40)
        print("  1. Mark Attendance")
        print("  2. View Attendance by Employee")
        print("  3. View Attendance by Date")
        print("  4. Monthly Summary for Employee")
        print("  5. Department Attendance by Date")
        print("  6. Late Arrivals Report")
        print("  7. Overtime Report")
        print("  0. Back to Main Menu")
        print("="*40)
        choice = input("  Enter choice: ")

        if choice == '1':
            emp_id   = int(input("  Employee ID           : "))
            status   = input("  Status (Present/Absent/Late/Half Day/On Leave): ")
            check_in = input("  Check In  (HH:MM or leave blank): ") or None
            check_out= input("  Check Out (HH:MM or leave blank): ") or None
            ot       = float(input("  Overtime Hours (0 if none): ") or 0)
            notes    = input("  Notes (optional): ") or None
            mark_attendance(emp_id, status, check_in, check_out, ot, notes)
        elif choice == '2':
            emp_id = int(input("  Enter Employee ID: "))
            view_attendance_by_employee(emp_id)
        elif choice == '3':
            att_date = input("  Enter Date (YYYY-MM-DD): ")
            view_attendance_by_date(att_date)
        elif choice == '4':
            emp_id = int(input("  Enter Employee ID : "))
            year   = int(input("  Enter Year  (YYYY): "))
            month  = int(input("  Enter Month (MM)  : "))
            monthly_attendance_summary(emp_id, year, month)
        elif choice == '5':
            dept_id  = int(input("  Enter Department ID     : "))
            att_date = input("  Enter Date (YYYY-MM-DD) : ")
            department_attendance_summary(dept_id, att_date)
        elif choice == '6':
            year  = int(input("  Enter Year  (YYYY): "))
            month = int(input("  Enter Month (MM)  : "))
            late_arrivals_report(year, month)
        elif choice == '7':
            year  = int(input("  Enter Year  (YYYY): "))
            month = int(input("  Enter Month (MM)  : "))
            overtime_report(year, month)
        elif choice == '0':
            break
        else:
            print("  [!] Invalid choice, try again")

# using namespace std;

def get_recent_attendance_web():
    from config.config import get_connection
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.AttendanceDate, e.FirstName + ' ' + e.LastName AS FullName,
               d.DepartmentName, a.CheckIn, a.CheckOut, a.Status, a.OvertimeHours
        FROM Attendance a
        JOIN Employees e ON a.EmployeeID = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        ORDER BY a.AttendanceDate DESC, e.FirstName
    """)
    cols = [column[0] for column in cursor.description]
    res = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return res
# using namespace std;

from config.config import get_connection
from tabulate import tabulate
from datetime import date

# ============================================================
#   ATTENDANCE TRACKER - WorkforceIQ
# ============================================================

def mark_attendance(employee_id, status, check_in=None, check_out=None, overtime=0.00, notes=None):
    today = date.today().strftime('%Y-%m-%d')
    conn = get_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("SELECT AttendanceID FROM Attendance WHERE EmployeeID = ? AND AttendanceDate = ?", employee_id, today)
    if cursor.fetchone():
        print(f"  [!] Attendance already marked for Employee ID {employee_id} today ({today})")
        conn.close()
        return
    cursor.execute("""
        INSERT INTO Attendance (EmployeeID, AttendanceDate, CheckIn, CheckOut, Status, OvertimeHours, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, employee_id, today, check_in, check_out, status, overtime, notes)
    conn.commit()
    print(f"  [OK] Attendance marked: Employee {employee_id} — {status} on {today}")
    conn.close()

def view_attendance_by_employee(employee_id):
    pass # Kept minimal for brevity, terminal functions omitted here but you can keep your original terminal functions above this line.

# --- WEB FUNCTIONS ---
def get_recent_attendance_web():
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.AttendanceDate, e.FirstName + ' ' + e.LastName AS FullName,
               d.DepartmentName, a.CheckIn, a.CheckOut, a.Status, a.OvertimeHours
        FROM Attendance a
        JOIN Employees e ON a.EmployeeID = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        ORDER BY a.AttendanceDate DESC, e.FirstName
    """)
    cols = [column[0] for column in cursor.description]
    res = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return res

def mark_attendance_web(data):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT AttendanceID FROM Attendance WHERE EmployeeID = ? AND AttendanceDate = ?", data['emp_id'], data['date'])
        if cursor.fetchone(): return False
        cursor.execute("""
            INSERT INTO Attendance (EmployeeID, AttendanceDate, CheckIn, CheckOut, Status, OvertimeHours)
            VALUES (?, ?, ?, ?, ?, ?)
        """, data['emp_id'], data['date'], data['check_in'], data['check_out'], data['status'], data['overtime'])
        conn.commit()
        return True
    except Exception as e:
        print("Web Attendance Error:", e)
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    attendance_menu()