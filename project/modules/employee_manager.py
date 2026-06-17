from config.config import get_connection
from tabulate import tabulate

# ============================================================
#   EMPLOYEE MANAGER - WorkforceIQ
# ============================================================


def view_all_employees():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName  AS FullName,
            d.DepartmentName                AS Department,
            p.PositionTitle                 AS Position,
            e.BasicSalary,
            e.EmploymentStatus,
            e.HireDate
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions   p ON e.PositionID   = p.PositionID
        ORDER BY e.EmployeeID
    """)
    rows = cursor.fetchall()
    headers = ["ID", "Full Name", "Department", "Position", "Basic Salary", "Status", "Hire Date"]
    print("\n" + "="*70)
    print("                     ALL EMPLOYEES")
    print("="*70)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    conn.close()


def view_employee_by_id(employee_id):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.EmployeeID,
            e.FirstName,
            e.LastName,
            e.Email,
            e.Phone,
            e.NationalID,
            e.Gender,
            e.DateOfBirth,
            e.HireDate,
            e.EmploymentStatus,
            d.DepartmentName,
            p.PositionTitle,
            e.BasicSalary,
            e.BankAccount,
            e.BankName
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions   p ON e.PositionID   = p.PositionID
        WHERE e.EmployeeID = ?
    """, employee_id)
    row = cursor.fetchone()
    if row:
        print("\n" + "="*50)
        print("          EMPLOYEE DETAILS")
        print("="*50)
        print(f"  ID             : {row[0]}")
        print(f"  First Name     : {row[1]}")
        print(f"  Last Name      : {row[2]}")
        print(f"  Email          : {row[3]}")
        print(f"  Phone          : {row[4]}")
        print(f"  National ID    : {row[5]}")
        print(f"  Gender         : {row[6]}")
        print(f"  Date of Birth  : {row[7]}")
        print(f"  Hire Date      : {row[8]}")
        print(f"  Status         : {row[9]}")
        print(f"  Department     : {row[10]}")
        print(f"  Position       : {row[11]}")
        print(f"  Basic Salary   : ${row[12]:,.2f}")
        print(f"  Bank Account   : {row[13]}")
        print(f"  Bank Name      : {row[14]}")
        print("="*50)
    else:
        print(f"[!] No employee found with ID {employee_id}")
    conn.close()


def add_employee():
    print("\n" + "="*50)
    print("          ADD NEW EMPLOYEE")
    print("="*50)
    first_name  = input("  First Name                 : ")
    last_name   = input("  Last Name                  : ")
    email       = input("  Email                      : ")
    phone       = input("  Phone                      : ")
    national_id = input("  National ID                : ")
    gender      = input("  Gender (M/F/O)             : ").upper()
    dob         = input("  Date of Birth (YYYY-MM-DD) : ")
    hire_date   = input("  Hire Date     (YYYY-MM-DD) : ")
    dept_id     = int(input("  Department ID              : "))
    pos_id      = int(input("  Position ID                : "))
    salary      = float(input("  Basic Salary               : "))
    bank_acc    = input("  Bank Account               : ")
    bank_name   = input("  Bank Name                  : ")

    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Employees
        (FirstName, LastName, Email, Phone, NationalID, Gender, DateOfBirth,
         HireDate, EmploymentStatus, DepartmentID, PositionID, BasicSalary, BankAccount, BankName)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?, ?, ?, ?)
    """, first_name, last_name, email, phone, national_id, gender, dob,
         hire_date, dept_id, pos_id, salary, bank_acc, bank_name)
    conn.commit()
    print(f"\n  [OK] Employee '{first_name} {last_name}' added successfully!")
    conn.close()


def update_salary(employee_id, new_salary):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("UPDATE Employees SET BasicSalary = ? WHERE EmployeeID = ?", new_salary, employee_id)
    conn.commit()
    if cursor.rowcount > 0:
        print(f"\n  [OK] Salary updated to ${new_salary:,.2f} for Employee ID {employee_id}")
    else:
        print(f"\n  [!] Employee ID {employee_id} not found")
    conn.close()


def update_status(employee_id, new_status):
    valid = ['Active', 'Inactive', 'On Leave', 'Terminated']
    if new_status not in valid:
        print(f"  [!] Invalid status. Choose from: {valid}")
        return
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("UPDATE Employees SET EmploymentStatus = ? WHERE EmployeeID = ?", new_status, employee_id)
    conn.commit()
    if cursor.rowcount > 0:
        print(f"\n  [OK] Status updated to '{new_status}' for Employee ID {employee_id}")
    else:
        print(f"\n  [!] Employee ID {employee_id} not found")
    conn.close()


def search_employee(name):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            p.PositionTitle,
            e.BasicSalary,
            e.EmploymentStatus
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions   p ON e.PositionID   = p.PositionID
        WHERE e.FirstName LIKE ? OR e.LastName LIKE ?
    """, f'%{name}%', f'%{name}%')
    rows = cursor.fetchall()
    headers = ["ID", "Full Name", "Department", "Position", "Salary", "Status"]
    if rows:
        print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print(f"\n  [!] No employee found matching '{name}'")
    conn.close()


def view_by_department(dept_id):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName AS FullName,
            p.PositionTitle,
            e.BasicSalary,
            e.EmploymentStatus,
            e.HireDate
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions   p ON e.PositionID   = p.PositionID
        WHERE e.DepartmentID = ?
        ORDER BY e.BasicSalary DESC
    """, dept_id)
    rows = cursor.fetchall()
    headers = ["ID", "Full Name", "Position", "Salary", "Status", "Hire Date"]
    if rows:
        print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        print(f"\n  [!] No employees found in Department ID {dept_id}")
    conn.close()


def view_departments():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            d.DepartmentID,
            d.DepartmentName,
            d.Location,
            e.FirstName + ' ' + e.LastName AS Manager,
            COUNT(emp.EmployeeID)           AS TotalEmployees
        FROM Departments d
        LEFT JOIN Employees e   ON d.ManagerID    = e.EmployeeID
        LEFT JOIN Employees emp ON d.DepartmentID = emp.DepartmentID
        GROUP BY d.DepartmentID, d.DepartmentName, d.Location, e.FirstName, e.LastName
        ORDER BY d.DepartmentID
    """)
    rows = cursor.fetchall()
    headers = ["Dept ID", "Department", "Location", "Manager", "Total Employees"]
    print("\n" + "="*70)
    print("                     DEPARTMENTS")
    print("="*70)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    conn.close()


def employee_menu():
    while True:
        print("\n" + "="*40)
        print("       EMPLOYEE MANAGER")
        print("="*40)
        print("  1. View All Employees")
        print("  2. View Employee by ID")
        print("  3. Add New Employee")
        print("  4. Update Employee Salary")
        print("  5. Update Employee Status")
        print("  6. Search Employee by Name")
        print("  7. View Employees by Department")
        print("  8. View All Departments")
        print("  0. Back to Main Menu")
        print("="*40)
        choice = input("  Enter choice: ")

        if choice == '1':
            view_all_employees()
        elif choice == '2':
            emp_id = int(input("  Enter Employee ID: "))
            view_employee_by_id(emp_id)
        elif choice == '3':
            add_employee()
        elif choice == '4':
            emp_id  = int(input("  Enter Employee ID : "))
            new_sal = float(input("  Enter New Salary  : "))
            update_salary(emp_id, new_sal)
        elif choice == '5':
            emp_id     = int(input("  Enter Employee ID: "))
            new_status = input("  Status (Active/Inactive/On Leave/Terminated): ")
            update_status(emp_id, new_status)
        elif choice == '6':
            name = input("  Enter Name to Search: ")
            search_employee(name)
        elif choice == '7':
            dept_id = int(input("  Enter Department ID: "))
            view_by_department(dept_id)
        elif choice == '8':
            view_departments()
        elif choice == '0':
            break
        else:
            print("  [!] Invalid choice, try again")

# using namespace std;

def get_all_employees_web():
    from config.config import get_connection
    conn = get_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.EmployeeID, e.FirstName + ' ' + e.LastName AS FullName,
               d.DepartmentName, p.PositionTitle, e.BasicSalary, e.EmploymentStatus
        FROM Employees e
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        JOIN Positions p ON e.PositionID = p.PositionID
        ORDER BY e.EmployeeID
    """)
    cols = [column[0] for column in cursor.description]
    res = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return res

# using namespace std;

def add_employee_web(data):
    """Takes form data from the web and inserts it into the SQL Database."""
    from config.config import get_connection
    conn = get_connection()
    if not conn: 
        return False
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Employees
            (FirstName, LastName, Email, Phone, NationalID, Gender, DateOfBirth,
             HireDate, EmploymentStatus, DepartmentID, PositionID, BasicSalary, BankAccount, BankName)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?, ?, ?, ?)
        """, 
            data['first_name'], data['last_name'], data['email'], data['phone'],
            data['national_id'], data['gender'], data['dob'], data['hire_date'],
            data['dept_id'], data['pos_id'], data['salary'], data['bank_acc'], data['bank_name']
        )
        conn.commit()
        return True
    except Exception as e:
        print("SQL Insert Error:", e)
        return False
    finally:
        conn.close()
        
if __name__ == "__main__":
    employee_menu()