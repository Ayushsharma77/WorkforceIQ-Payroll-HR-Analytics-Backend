from config.config import get_connection
from tabulate import tabulate

# ============================================================
#   LEAVE MANAGER - WorkforceIQ
# ============================================================


def view_leave_types():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT LeaveTypeID, LeaveTypeName, MaxDaysPerYear, IsPaid FROM LeaveTypes")
    rows = cursor.fetchall()
    headers = ["ID", "Leave Type", "Max Days/Year", "Paid?"]
    print("\n" + "="*50)
    print("           LEAVE TYPES")
    print("="*50)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    conn.close()


def apply_leave(employee_id, leave_type_id, start_date, end_date, reason):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    # Check for overlapping leave
    cursor.execute("""
        SELECT LeaveRequestID FROM LeaveRequests
        WHERE EmployeeID = ?
          AND Status NOT IN ('Rejected','Cancelled')
          AND NOT (EndDate < ? OR StartDate > ?)
    """, employee_id, start_date, end_date)
    if cursor.fetchone():
        print("  [!] Employee already has a leave request overlapping those dates.")
        conn.close()
        return
    cursor.execute("""
        INSERT INTO LeaveRequests (EmployeeID, LeaveTypeID, StartDate, EndDate, Reason, Status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
    """, employee_id, leave_type_id, start_date, end_date, reason)
    conn.commit()
    print(f"  [OK] Leave request submitted for Employee ID {employee_id}")
    conn.close()


def approve_leave(leave_request_id, approver_id):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE LeaveRequests
        SET Status = 'Approved', ApprovedBy = ?
        WHERE LeaveRequestID = ? AND Status = 'Pending'
    """, approver_id, leave_request_id)
    conn.commit()
    if cursor.rowcount > 0:
        print(f"  [OK] Leave Request ID {leave_request_id} approved.")
    else:
        print(f"  [!] Request not found or already processed.")
    conn.close()


def reject_leave(leave_request_id, approver_id):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE LeaveRequests
        SET Status = 'Rejected', ApprovedBy = ?
        WHERE LeaveRequestID = ? AND Status = 'Pending'
    """, approver_id, leave_request_id)
    conn.commit()
    if cursor.rowcount > 0:
        print(f"  [OK] Leave Request ID {leave_request_id} rejected.")
    else:
        print(f"  [!] Request not found or already processed.")
    conn.close()


def view_leave_requests(status_filter=None):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("""
            SELECT
                lr.LeaveRequestID,
                e.FirstName + ' ' + e.LastName  AS Employee,
                lt.LeaveTypeName,
                lr.StartDate,
                lr.EndDate,
                lr.TotalDays,
                lr.Reason,
                lr.Status,
                ISNULL(ap.FirstName + ' ' + ap.LastName, 'Pending') AS ApprovedBy
            FROM LeaveRequests lr
            JOIN Employees  e  ON lr.EmployeeID  = e.EmployeeID
            JOIN LeaveTypes lt ON lr.LeaveTypeID = lt.LeaveTypeID
            LEFT JOIN Employees ap ON lr.ApprovedBy = ap.EmployeeID
            WHERE lr.Status = ?
            ORDER BY lr.RequestedAt DESC
        """, status_filter)
    else:
        cursor.execute("""
            SELECT
                lr.LeaveRequestID,
                e.FirstName + ' ' + e.LastName  AS Employee,
                lt.LeaveTypeName,
                lr.StartDate,
                lr.EndDate,
                lr.TotalDays,
                lr.Reason,
                lr.Status,
                ISNULL(ap.FirstName + ' ' + ap.LastName, '-') AS ApprovedBy
            FROM LeaveRequests lr
            JOIN Employees  e  ON lr.EmployeeID  = e.EmployeeID
            JOIN LeaveTypes lt ON lr.LeaveTypeID = lt.LeaveTypeID
            LEFT JOIN Employees ap ON lr.ApprovedBy = ap.EmployeeID
            ORDER BY lr.RequestedAt DESC
        """)
    rows = cursor.fetchall()
    headers = ["Req ID", "Employee", "Leave Type", "Start", "End", "Days", "Reason", "Status", "Approved By"]
    print(f"\n{'='*90}")
    print(f"  LEAVE REQUESTS" + (f" — {status_filter}" if status_filter else " — ALL"))
    print(f"{'='*90}")
    if rows:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print("  No leave requests found.")
    conn.close()


def employee_leave_balance(employee_id, year):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            lt.LeaveTypeName,
            lt.MaxDaysPerYear,
            ISNULL(SUM(CASE WHEN lr.Status = 'Approved'
                            AND YEAR(lr.StartDate) = ?
                       THEN lr.TotalDays ELSE 0 END), 0) AS DaysUsed,
            lt.MaxDaysPerYear -
            ISNULL(SUM(CASE WHEN lr.Status = 'Approved'
                            AND YEAR(lr.StartDate) = ?
                       THEN lr.TotalDays ELSE 0 END), 0) AS DaysRemaining
        FROM LeaveTypes lt
        LEFT JOIN LeaveRequests lr ON lt.LeaveTypeID = lr.LeaveTypeID
                                   AND lr.EmployeeID = ?
        GROUP BY lt.LeaveTypeID, lt.LeaveTypeName, lt.MaxDaysPerYear
        ORDER BY lt.LeaveTypeID
    """, year, year, employee_id)
    rows = cursor.fetchall()
    headers = ["Leave Type", "Max Days", "Days Used", "Days Remaining"]
    cursor.execute("SELECT FirstName + ' ' + LastName FROM Employees WHERE EmployeeID = ?", employee_id)
    name = cursor.fetchone()[0]
    print(f"\n{'='*55}")
    print(f"  LEAVE BALANCE — {name} ({year})")
    print(f"{'='*55}")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    conn.close()


def leave_menu():
    while True:
        print("\n" + "="*40)
        print("         LEAVE MANAGER")
        print("="*40)
        print("  1. View Leave Types")
        print("  2. Apply for Leave")
        print("  3. Approve Leave Request")
        print("  4. Reject Leave Request")
        print("  5. View All Leave Requests")
        print("  6. View Pending Requests")
        print("  7. View Employee Leave Balance")
        print("  0. Back to Main Menu")
        print("="*40)
        choice = input("  Enter choice: ")

        if choice == '1':
            view_leave_types()
        elif choice == '2':
            emp_id   = int(input("  Employee ID              : "))
            lt_id    = int(input("  Leave Type ID            : "))
            start    = input("  Start Date (YYYY-MM-DD)  : ")
            end      = input("  End Date   (YYYY-MM-DD)  : ")
            reason   = input("  Reason                   : ")
            apply_leave(emp_id, lt_id, start, end, reason)
        elif choice == '3':
            req_id   = int(input("  Leave Request ID : "))
            appr_id  = int(input("  Approver Emp ID  : "))
            approve_leave(req_id, appr_id)
        elif choice == '4':
            req_id   = int(input("  Leave Request ID : "))
            appr_id  = int(input("  Approver Emp ID  : "))
            reject_leave(req_id, appr_id)
        elif choice == '5':
            view_leave_requests()
        elif choice == '6':
            view_leave_requests('Pending')
        elif choice == '7':
            emp_id = int(input("  Employee ID : "))
            year   = int(input("  Year (YYYY) : "))
            employee_leave_balance(emp_id, year)
        elif choice == '0':
            break
        else:
            print("  [!] Invalid choice, try again")
# using namespace std;

def get_leave_requests_web():
    from config.config import get_connection
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lr.LeaveRequestID, e.FirstName + ' ' + e.LastName AS Employee,
               lt.LeaveTypeName, lr.StartDate, lr.EndDate, lr.TotalDays, lr.Status
        FROM LeaveRequests lr
        JOIN Employees e ON lr.EmployeeID = e.EmployeeID
        JOIN LeaveTypes lt ON lr.LeaveTypeID = lt.LeaveTypeID
        ORDER BY lr.RequestedAt DESC
    """)
    cols = [column[0] for column in cursor.description]
    res = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return res
# using namespace std;

from config.config import get_connection
from tabulate import tabulate

# ============================================================
#   LEAVE MANAGER - WorkforceIQ
# ============================================================

def view_leave_types():
    pass # Terminal funcs kept brief

# --- WEB FUNCTIONS ---
def get_leave_requests_web():
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lr.LeaveRequestID, e.FirstName + ' ' + e.LastName AS Employee,
               lt.LeaveTypeName, lr.StartDate, lr.EndDate, lr.TotalDays, lr.Status
        FROM LeaveRequests lr
        JOIN Employees e ON lr.EmployeeID = e.EmployeeID
        JOIN LeaveTypes lt ON lr.LeaveTypeID = lt.LeaveTypeID
        ORDER BY lr.RequestedAt DESC
    """)
    cols = [column[0] for column in cursor.description]
    res = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return res

def apply_leave_web(data):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO LeaveRequests (EmployeeID, LeaveTypeID, StartDate, EndDate, Reason, Status)
            VALUES (?, ?, ?, ?, ?, 'Pending')
        """, data['emp_id'], data['leave_type'], data['start_date'], data['end_date'], data['reason'])
        conn.commit()
        return True
    except Exception as e:
        print("Web Leave Apply Error:", e)
        return False
    finally:
        conn.close()

def process_leave_web(req_id, status, approver_id=1):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE LeaveRequests
            SET Status = ?, ApprovedBy = ?
            WHERE LeaveRequestID = ? AND Status = 'Pending'
        """, status, approver_id, req_id)
        conn.commit()
        return True
    except Exception as e:
        print("Web Leave Process Error:", e)
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    leave_menu()