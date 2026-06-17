# using namespace std;

from flask import Flask, render_template, send_file, request, redirect, url_for
from modules.hr_analytics import get_company_overview_web
from modules.payroll_engine import get_payroll_summary_web, process_payroll
from modules.employee_manager import get_all_employees_web, add_employee_web
from modules.attendance_tracker import get_recent_attendance_web, mark_attendance_web
from modules.leave_manager import get_leave_requests_web, apply_leave_web, process_leave_web
from modules.payslip_generator import generate_payslip_pdf

app = Flask(__name__)

@app.route('/')
def dashboard():
    stats = get_company_overview_web()
    return render_template('dashboard.html', stats=stats)

@app.route('/payroll')
def payroll():
    current_period = 5 # Set to Period 6 to run the open payroll
    payroll_data = get_payroll_summary_web(period_id=current_period) 
    return render_template('payroll.html', payroll=payroll_data, period=current_period)

@app.route('/run-payroll/<int:period_id>')
def run_payroll_action(period_id):
    process_payroll(period_id)
    return redirect(url_for('payroll'))

@app.route('/download/<int:emp_id>/<int:period_id>')
def download_payslip(emp_id, period_id):
    pdf_path = generate_payslip_pdf(emp_id, period_id)
    if pdf_path:
        return send_file(pdf_path, as_attachment=True)
    return "Error generating payslip", 404

@app.route('/employees')
def employees():
    emp_data = get_all_employees_web()
    return render_template('employees.html', employees=emp_data)

@app.route('/add-employee', methods=['POST'])
def save_employee():
    form_data = {
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone'),
        'national_id': request.form.get('national_id'),
        'gender': request.form.get('gender'),
        'dob': request.form.get('dob'),
        'hire_date': request.form.get('hire_date'),
        'dept_id': request.form.get('dept_id'),
        'pos_id': request.form.get('pos_id'),
        'salary': request.form.get('salary'),
        'bank_acc': request.form.get('bank_acc'),
        'bank_name': request.form.get('bank_name')
    }
    add_employee_web(form_data)
    return redirect(url_for('employees'))

@app.route('/attendance')
def attendance():
    att_data = get_recent_attendance_web()
    return render_template('attendance.html', attendance=att_data)

@app.route('/mark-attendance', methods=['POST'])
def mark_attendance():
    form_data = {
        'emp_id': request.form.get('emp_id'),
        'date': request.form.get('date'),
        'status': request.form.get('status'),
        'check_in': request.form.get('check_in') or None,
        'check_out': request.form.get('check_out') or None,
        'overtime': request.form.get('overtime') or 0
    }
    mark_attendance_web(form_data)
    return redirect(url_for('attendance'))

@app.route('/leaves')
def leaves():
    leave_data = get_leave_requests_web()
    return render_template('leaves.html', leaves=leave_data)

@app.route('/apply-leave', methods=['POST'])
def apply_leave():
    form_data = {
        'emp_id': request.form.get('emp_id'),
        'leave_type': request.form.get('leave_type'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
        'reason': request.form.get('reason')
    }
    apply_leave_web(form_data)
    return redirect(url_for('leaves'))

@app.route('/leave-action/<action>/<int:req_id>')
def leave_action(action, req_id):
    status = 'Approved' if action == 'approve' else 'Rejected'
    process_leave_web(req_id, status)
    return redirect(url_for('leaves'))

if __name__ == '__main__':
    app.run(debug=True)