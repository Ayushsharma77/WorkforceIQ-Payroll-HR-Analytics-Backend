from config.config import get_connection
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import os

# ============================================================
#   PAYSLIP GENERATOR - WorkforceIQ
# ============================================================

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'payslips')


def get_payslip_data(employee_id, period_id):
    conn = get_connection()
    if not conn:
        return None, None
    cursor = conn.cursor()

    # Employee + Payroll info
    cursor.execute("""
        SELECT
            e.EmployeeID,
            e.FirstName + ' ' + e.LastName AS FullName,
            e.Email,
            d.DepartmentName,
            pos.PositionTitle,
            e.BankAccount,
            e.BankName,
            pp.PeriodName,
            pp.PayDate,
            p.BasicSalary,
            p.OvertimePay,
            p.Allowances,
            p.GrossSalary,
            p.TotalDeductions,
            p.TaxAmount,
            p.NetSalary,
            p.PayrollID
        FROM Payroll p
        JOIN Employees    e   ON p.EmployeeID   = e.EmployeeID
        JOIN Departments  d   ON e.DepartmentID = d.DepartmentID
        JOIN Positions    pos ON e.PositionID   = pos.PositionID
        JOIN PayrollPeriods pp ON p.PeriodID    = pp.PeriodID
        WHERE p.EmployeeID = ? AND p.PeriodID = ?
    """, employee_id, period_id)
    payroll = cursor.fetchone()
    if not payroll:
        conn.close()
        return None, None

    payroll_id = payroll[16]

    # Deduction breakdown
    cursor.execute("""
        SELECT dt.DeductionName, pd.AmountDeducted
        FROM PayrollDeductions pd
        JOIN DeductionTypes dt ON pd.DeductionTypeID = dt.DeductionTypeID
        WHERE pd.PayrollID = ?
    """, payroll_id)
    deductions = cursor.fetchall()
    conn.close()
    return payroll, deductions


def generate_payslip_pdf(employee_id, period_id):
    payroll, deductions = get_payslip_data(employee_id, period_id)
    if not payroll:
        print(f"  [!] No payroll found for Employee {employee_id}, Period {period_id}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"Payslip_Emp{employee_id}_Period{period_id}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc    = SimpleDocTemplate(filepath, pagesize=A4,
                               rightMargin=1.5*cm, leftMargin=1.5*cm,
                               topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Title ──────────────────────────────────────────────
    title_style = ParagraphStyle('title', fontSize=20, alignment=TA_CENTER,
                                 textColor=colors.HexColor('#1a3c5e'),
                                 fontName='Helvetica-Bold', spaceAfter=4)
    sub_style   = ParagraphStyle('sub',   fontSize=11, alignment=TA_CENTER,
                                 textColor=colors.HexColor('#555555'), spaceAfter=12)

    story.append(Paragraph("WorkforceIQ", title_style))
    story.append(Paragraph("Employee Payslip", sub_style))

    # ── Header Bar ─────────────────────────────────────────
    header_data = [[
        f"Period: {payroll[7]}",
        f"Pay Date: {payroll[8]}"
    ]]
    header_table = Table(header_data, colWidths=[9*cm, 9*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), colors.HexColor('#1a3c5e')),
        ('TEXTCOLOR',    (0,0), (-1,-1), colors.white),
        ('FONTNAME',     (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 10),
        ('ALIGN',        (0,0), (0,0),   'LEFT'),
        ('ALIGN',        (1,0), (1,0),   'RIGHT'),
        ('PADDING',      (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Employee Info ───────────────────────────────────────
    emp_data = [
        ["Employee Name",  payroll[1],   "Employee ID",  str(payroll[0])],
        ["Department",     payroll[3],   "Position",     payroll[4]],
        ["Email",          payroll[2],   "Bank Account", payroll[5]],
        ["Bank Name",      payroll[6],   "",             ""],
    ]
    emp_table = Table(emp_data, colWidths=[4*cm, 6*cm, 4*cm, 4*cm])
    emp_table.setStyle(TableStyle([
        ('FONTNAME',     (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',     (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 9),
        ('BACKGROUND',   (0,0), (0,-1), colors.HexColor('#f0f4f8')),
        ('BACKGROUND',   (2,0), (2,-1), colors.HexColor('#f0f4f8')),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('PADDING',      (0,0), (-1,-1), 6),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Earnings ────────────────────────────────────────────
    earn_title = ParagraphStyle('et', fontSize=10, fontName='Helvetica-Bold',
                                textColor=colors.white)
    story.append(Paragraph("EARNINGS", ParagraphStyle('eh', fontSize=11,
                            fontName='Helvetica-Bold',
                            textColor=colors.HexColor('#1a3c5e'), spaceAfter=4)))

    earn_data = [
        ["Description",          "Amount"],
        ["Basic Salary",         f"${float(payroll[9]):,.2f}"],
        ["Overtime Pay",         f"${float(payroll[10]):,.2f}"],
        ["Allowances",           f"${float(payroll[11]):,.2f}"],
        ["GROSS SALARY",         f"${float(payroll[12]):,.2f}"],
    ]
    earn_table = Table(earn_data, colWidths=[12*cm, 6*cm])
    earn_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  colors.HexColor('#2e6da4')),
        ('TEXTCOLOR',    (0,0), (-1,0),  colors.white),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('BACKGROUND',   (0,-1),(-1,-1), colors.HexColor('#d4e6f1')),
        ('FONTNAME',     (0,-1),(-1,-1), 'Helvetica-Bold'),
        ('ALIGN',        (1,0), (1,-1),  'RIGHT'),
        ('FONTSIZE',     (0,0), (-1,-1), 9),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('PADDING',      (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(earn_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Deductions ──────────────────────────────────────────
    story.append(Paragraph("DEDUCTIONS", ParagraphStyle('dh', fontSize=11,
                            fontName='Helvetica-Bold',
                            textColor=colors.HexColor('#1a3c5e'), spaceAfter=4)))

    ded_data = [["Description", "Amount"]]
    for ded in deductions:
        ded_data.append([ded[0], f"${float(ded[1]):,.2f}"])
    ded_data.append(["TOTAL DEDUCTIONS", f"${float(payroll[13]):,.2f}"])
    ded_data.append(["INCOME TAX",       f"${float(payroll[14]):,.2f}"])

    ded_table = Table(ded_data, colWidths=[12*cm, 6*cm])
    ded_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),  (-1,0),  colors.HexColor('#c0392b')),
        ('TEXTCOLOR',    (0,0),  (-1,0),  colors.white),
        ('FONTNAME',     (0,0),  (-1,0),  'Helvetica-Bold'),
        ('BACKGROUND',   (0,-2), (-1,-1), colors.HexColor('#fadbd8')),
        ('FONTNAME',     (0,-2), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN',        (1,0),  (1,-1),  'RIGHT'),
        ('FONTSIZE',     (0,0),  (-1,-1), 9),
        ('GRID',         (0,0),  (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('PADDING',      (0,0),  (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-3), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(ded_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Net Pay ─────────────────────────────────────────────
    net_data = [["NET SALARY", f"${float(payroll[15]):,.2f}"]]
    net_table = Table(net_data, colWidths=[12*cm, 6*cm])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a3c5e')),
        ('TEXTCOLOR',  (0,0), (-1,-1), colors.white),
        ('FONTNAME',   (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 12),
        ('ALIGN',      (1,0), (1,0),   'RIGHT'),
        ('PADDING',    (0,0), (-1,-1), 10),
    ]))
    story.append(net_table)
    story.append(Spacer(1, 0.6*cm))

    # ── Footer ──────────────────────────────────────────────
    footer_style = ParagraphStyle('footer', fontSize=8, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#888888'))
    story.append(Paragraph("This is a system-generated payslip. No signature required.", footer_style))
    story.append(Paragraph("WorkforceIQ HR Management System", footer_style))

    doc.build(story)

    # Update Payslips table
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            IF EXISTS (SELECT 1 FROM Payroll WHERE EmployeeID = ? AND PeriodID = ?)
            BEGIN
                DECLARE @pid INT = (SELECT PayrollID FROM Payroll WHERE EmployeeID = ? AND PeriodID = ?)
                IF EXISTS (SELECT 1 FROM Payslips WHERE PayrollID = @pid)
                    UPDATE Payslips SET FilePath = ?, GeneratedAt = GETDATE() WHERE PayrollID = @pid
                ELSE
                    INSERT INTO Payslips (PayrollID, FilePath, SentToEmployee)
                    VALUES (@pid, ?, 0)
            END
        """, employee_id, period_id, employee_id, period_id, filepath, filepath)
        conn.commit()
        conn.close()

    print(f"  [OK] Payslip generated: {filepath}")
    return filepath


def generate_all_payslips(period_id):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT EmployeeID FROM Payroll WHERE PeriodID = ?", period_id)
    employees = cursor.fetchall()
    conn.close()
    print(f"\n  Generating payslips for Period ID {period_id}...")
    for emp in employees:
        generate_payslip_pdf(emp[0], period_id)
    print(f"  [DONE] All payslips saved to: {OUTPUT_DIR}")


def payslip_menu():
    while True:
        print("\n" + "="*40)
        print("       PAYSLIP GENERATOR")
        print("="*40)
        print("  1. Generate Payslip for One Employee")
        print("  2. Generate All Payslips for a Period")
        print("  0. Back to Main Menu")
        print("="*40)
        choice = input("  Enter choice: ")

        if choice == '1':
            emp_id    = int(input("  Employee ID : "))
            period_id = int(input("  Period ID   : "))
            generate_payslip_pdf(emp_id, period_id)
        elif choice == '2':
            period_id = int(input("  Enter Period ID: "))
            generate_all_payslips(period_id)
        elif choice == '0':
            break
        else:
            print("  [!] Invalid choice, try again")


if __name__ == "__main__":
    payslip_menu()