from decimal import Decimal, ROUND_HALF_UP
from config.config import get_connection
from tabulate import tabulate

# ============================================================
#   PAYROLL ENGINE - WorkforceIQ
# ============================================================

def calculate_tax(annual_salary):
    """Calculate income tax based on tax brackets in DB."""
    conn = get_connection()
    if not conn:
        return Decimal('0.00')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MinIncome, MaxIncome, TaxRate
        FROM TaxBrackets
        WHERE EffectiveTo IS NULL OR EffectiveTo >= GETDATE()
        ORDER BY MinIncome
    """)
    brackets = cursor.fetchall()
    conn.close()

    total_tax = Decimal('0.00')
    # Treat annual_salary safely as a Decimal string representation
    annual_salary_dec = Decimal(str(annual_salary))

    for bracket in brackets:
        min_inc = Decimal(str(bracket[0]))
        max_inc = Decimal(str(bracket[1])) if bracket[1] is not None else Decimal('Infinity')
        rate = Decimal(str(bracket[2]))

        if annual_salary_dec > min_inc:
            taxable_in_bracket = min(annual_salary_dec, max_inc) - min_inc
            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * rate

    # Return monthly tax
    monthly_tax = total_tax / Decimal('12')
    return monthly_tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_deductions(employee_id, gross_monthly):
    """Calculate all deductions for an employee for the month."""
    conn = get_connection()
    if not conn:
        return Decimal('0.00'), []
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            dt.DeductionName,
            dt.CalculationMethod,
            ISNULL(ed.CustomValue, dt.DefaultValue) AS Value
        FROM EmployeeDeductions ed
        JOIN DeductionTypes dt ON ed.DeductionTypeID = dt.DeductionTypeID
        WHERE ed.EmployeeID = ?
          AND dt.IsActive = 1
          AND (ed.EndDate IS NULL OR ed.EndDate >= GETDATE())
    """, employee_id)
    deductions = cursor.fetchall()
    conn.close()

    total = Decimal('0.00')
    breakdown = []
    gross_monthly_dec = Decimal(str(gross_monthly))

    for ded in deductions:
        name, method, value = ded
        value_dec = Decimal(str(value))
        
        if method == 'Percentage':
            amount = (gross_monthly_dec * value_dec).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            amount = value_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        total += amount
        breakdown.append((name, method, float(value_dec), float(amount)))

    return total, breakdown


def calculate_overtime_pay(employee_id, year, month):
    """Calculate overtime pay for the month (1.5x hourly rate)."""
    conn = get_connection()
    if not conn:
        return Decimal('0.00'), 0
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.BasicSalary,
            ISNULL(SUM(a.OvertimeHours), 0) AS TotalOT
        FROM Employees e
        LEFT JOIN Attendance a ON e.EmployeeID = a.EmployeeID
                               AND YEAR(a.AttendanceDate)  = ?
                               AND MONTH(a.AttendanceDate) = ?
        WHERE e.EmployeeID = ?
        GROUP BY e.BasicSalary
    """, year, month, employee_id)
    row = cursor.fetchone()
    conn.close()
    if not row:
        return Decimal('0.00'), 0
        
    monthly_salary = Decimal(str(row[0]))
    ot_hours = Decimal(str(row[1]))
    
    hourly_rate = monthly_salary / Decimal('160')
    ot_pay = (hourly_rate * ot_hours * Decimal('1.5')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return ot_pay, float(ot_hours)


def process_payroll(period_id):
    """Process payroll for all active employees for a given period."""
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()

    # Get period details
    cursor.execute("SELECT PeriodName, StartDate, EndDate FROM PayrollPeriods WHERE PeriodID = ?", period_id)
    period = cursor.fetchone()
    if not period:
        print(f"  [!] Period ID {period_id} not found.")
        conn.close()
        return

    period_name = period[0]
    year = period[1].year
    month = period[1].month
    print(f"\n  Processing Payroll for: {period_name}")
    print(f"  {'─'*40}")

    # Get all active employees
    cursor.execute("""
        SELECT EmployeeID, BasicSalary
        FROM Employees
        WHERE EmploymentStatus = 'Active'
    """)
    employees = cursor.fetchall()

    processed = 0
    for emp in employees:
        emp_id = emp[0]
        # Calculate base monthly from annual salary
        basic_monthly = (Decimal(str(emp[1])) / Decimal('12')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Check if already processed
        cursor.execute("SELECT PayrollID FROM Payroll WHERE EmployeeID = ? AND PeriodID = ?",
                       emp_id, period_id)
        if cursor.fetchone():
            print(f"  [SKIP] Employee {emp_id} already processed.")
            continue

        # Calculate components
        ot_pay, ot_hours = calculate_overtime_pay(emp_id, year, month)
        allowances = Decimal('300.00')   # fixed allowance
        gross = basic_monthly + ot_pay + allowances
        tax_amount = calculate_tax(emp[1])
        total_ded, breakdown = calculate_deductions(emp_id, gross)

        # Insert payroll record
        cursor.execute("""
            INSERT INTO Payroll
            (EmployeeID, PeriodID, BasicSalary, OvertimePay, Allowances,
             TotalDeductions, TaxAmount, PaymentStatus, ProcessedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', GETDATE())
        """, emp_id, period_id, float(basic_monthly), float(ot_pay), float(allowances), float(total_ded), float(tax_amount))
        conn.commit()

        # Get new PayrollID
        cursor.execute("SELECT PayrollID FROM Payroll WHERE EmployeeID = ? AND PeriodID = ?",
                       emp_id, period_id)
        payroll_id = cursor.fetchone()[0]

        # Insert deduction breakdown
        cursor.execute("""
            SELECT ed.DeductionTypeID,
                   dt.CalculationMethod,
                   ISNULL(ed.CustomValue, dt.DefaultValue) AS Value
            FROM EmployeeDeductions ed
            JOIN DeductionTypes dt ON ed.DeductionTypeID = dt.DeductionTypeID
            WHERE ed.EmployeeID = ? AND dt.IsActive = 1
              AND (ed.EndDate IS NULL OR ed.EndDate >= GETDATE())
        """, emp_id)
        deds = cursor.fetchall()
        for d in deds:
            ded_type_id, method, value = d
            value_dec = Decimal(str(value))
            if method == 'Percentage':
                amount = (gross * value_dec).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                amount = value_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
            cursor.execute("""
                INSERT INTO PayrollDeductions (PayrollID, DeductionTypeID, AmountDeducted)
                VALUES (?, ?, ?)
            """, payroll_id, ded_type_id, float(amount))
        conn.commit()

        net = gross - total_ded - tax_amount
        print(f"  [OK] Employee {emp_id} | Gross: ${float(gross):,.2f} | Tax: ${float(tax_amount):,.2f} | Net: ${float(net):,.2f}")
        processed += 1

    print(f"\n  [DONE] {processed} employees processed for {period_name}")
    conn.close()


def get_payroll_summary_web(period_id=5):
    """
    Fetches payroll data from SQL and returns it as a list of dictionaries 
    so the Flask web app can render it directly into HTML.
    """
    conn = get_connection()
    if not conn:
        return []
        
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName AS FullName,
            d.DepartmentName,
            p.GrossSalary,
            p.TotalDeductions,
            p.TaxAmount,
            p.NetSalary,
            p.PaymentStatus
        FROM Payroll p
        JOIN Employees e ON p.EmployeeID = e.EmployeeID
        JOIN Departments d ON e.DepartmentID = d.DepartmentID
        WHERE p.PeriodID = ?
        ORDER BY p.NetSalary DESC
    """, period_id)
    
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    conn.close()
    return results


# Keep remaining legacy CLI view_payroll_summary, view_payroll_periods, mark_payroll_paid, payroll_menu functions down below unchanged...