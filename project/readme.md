# 🚀 WorkforceIQ – Enterprise HR Management System

WorkforceIQ is a full-stack Human Resources Management System built with **Python, Flask, and Microsoft SQL Server**. The platform streamlines core HR operations including employee management, attendance tracking, leave processing, payroll calculation, HR analytics, and automated PDF payslip generation through a modern web interface.

Designed as an academic enterprise-level project, WorkforceIQ demonstrates real-world integration between **Python backend services**, **SQL Server databases**, and a responsive **Flask-based web application**.

---

## ✨ Features

### 📊 Executive Dashboard

* Real-time workforce statistics
* Department-wise employee tracking
* Attendance and leave summaries
* Interactive HR analytics

### 👥 Employee Management

* Add, update, view, and delete employee records
* Department and designation management
* Employee profile tracking
* SQL Server integrated CRUD operations

### 📅 Attendance Management

* Daily employee check-in/check-out logging
* Working hours calculation
* Automatic overtime tracking
* Attendance history reports

### 🌴 Leave Management

* Leave application submission
* Leave approval and rejection workflow
* Leave balance monitoring
* Employee leave history

### 💰 Payroll Processing

* Automated salary computation
* Tax deduction calculations
* Payroll ledger management
* Net salary generation

### 📄 PDF Payslip Generation

* Professional payslip creation
* Downloadable PDF reports
* Employee salary breakdown
* Automated document generation using ReportLab

### 📈 HR Analytics

* Department performance insights
* Attendance analytics
* Payroll summaries
* Workforce reporting

---

## 🛠️ Technology Stack

### Backend

* Python 3.x
* Flask
* PyODBC
* ReportLab

### Database

* Microsoft SQL Server
* SQL Server Management Studio (SSMS)

### Frontend

* HTML5
* CSS3
* JavaScript
* Tabler Icons
* Glassmorphism UI Design

---

## 📂 Project Structure

```text
WorkforceIQ/
│
├── app.py
├── requirements.txt
├── WorkforceIQ_Database.sql
│
├── config/
│   └── config.py
│
├── modules/
│   ├── attendance_tracker.py
│   ├── employee_manager.py
│   ├── hr_analytics.py
│   ├── leave_manager.py
│   ├── payroll_engine.py
│   └── payslip_generator.py
│
├── static/
│   └── style.css
│
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── employees.html
    ├── attendance.html
    ├── leaves.html
    └── payroll.html
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd WorkforceIQ
```

### 2. Create the Database

1. Open Microsoft SQL Server Management Studio (SSMS).
2. Open `WorkforceIQ_Database.sql`.
3. Execute the script to create:

   * Database
   * Tables
   * Relationships
   * Sample Data

### 3. Configure Database Connection

Open:

```python
config/config.py
```

Update the SQL Server configuration:

```python
SERVER = "localhost\\SQLEXPRESS"
USE_WINDOWS_AUTH = True
```

Or provide SQL Authentication credentials if required.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

### 6. Open in Browser

```text
http://127.0.0.1:5000
```

---

## 💻 Application Workflow

### Employee Onboarding

1. Navigate to Employees.
2. Enter employee details.
3. Save records directly to SQL Server.

### Attendance Tracking

1. Open Attendance module.
2. Record employee check-in/check-out.
3. System calculates working hours and overtime.

### Leave Processing

1. Employee submits leave request.
2. HR reviews application.
3. Request is approved or rejected.

### Payroll Execution

1. Open Payroll module.
2. Run Payroll Engine.
3. System calculates:

   * Gross Salary
   * Tax Deductions
   * Net Salary

### Payslip Generation

1. Select employee.
2. Click Download Payslip.
3. PDF payslip is generated instantly.

---

## 🎯 Learning Outcomes

This project demonstrates:

* Full-Stack Web Development
* Python Backend Development
* Flask Framework Implementation
* SQL Server Database Design
* Database Connectivity using PyODBC
* CRUD Operations
* Payroll System Logic
* PDF Report Generation
* HR Analytics Implementation
* Responsive UI/UX Design

---

## 👨‍💻 Author

**Ayush Sharma**
B.Tech CSE (Artificial Intelligence)
SKIT Jaipur

Academic Project – Python, Flask & SQL Server Integration
