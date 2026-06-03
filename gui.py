from flask import Flask, render_template_string, request, jsonify
from lark import Lark
from sql_transformer import SQLTransformer
from dbms import DBMS
import os
import subprocess
import json
import shutil

# Auto-kill any process using port 5001 before starting
PORT = 5001
AUTO_SEED = True  # Set to False to disable auto-seeding

def kill_process_on_port(port):
    """Kill any process using the specified port (excluding our own PID)"""
    try:
        current_pid = os.getpid()
        result = subprocess.run(
            f'lsof -ti :{port}',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid.strip() != str(current_pid):
                    subprocess.run(f'kill -9 {pid}', shell=True)
                    print(f"✅ Killed existing process (PID {pid}) on port {port}")
    except Exception:
        pass

# Kill existing process on port 5001
kill_process_on_port(PORT)

app = Flask(__name__)

# ============================================================================
# AUTO-SEED DATABASE ON STARTUP
# ============================================================================

def seed_database_on_startup():
    """Automatically seed the database with student management system data (only if DB doesn't exist)"""
    if not AUTO_SEED:
        print("⚠️  Auto-seeding disabled")
        return
    
    # Check if database already exists
    db_exists = os.path.exists('DB') and os.path.exists('DB_INDEXES')
    
    if db_exists:
        print("\n" + "="*60)
        print("✅ DATABASE ALREADY EXISTS - Skipping auto-seed")
        print("="*60)
        print("💡 To force re-seeding, delete DB/ and DB_INDEXES/ folders")
        print("   or run: python seeder.py --fresh")
        print("="*60 + "\n")
        return
    
    print("\n" + "="*60)
    print("🌱 AUTO-SEEDING DATABASE (Fresh Install)...")
    print("="*60)
    
    # Clean existing database for fresh start (if partially exists)
    if os.path.exists('DB'):
        shutil.rmtree('DB')
    if os.path.exists('DB_INDEXES'):
        shutil.rmtree('DB_INDEXES')
    
    # Initialize fresh DBMS
    dbms = DBMS()
    
    # Load parser
    with open('grammar.lark') as f:
        parser = Lark(f.read(), start='command', lexer='basic')
    
    def run_sql(query, silent=False):
        t = SQLTransformer()
        try:
            parsed = parser.parse(query)
            result = t.transform(parsed)
            stmt, table, record, tables, sel_cols, where = result
            
            if stmt == 'create table':
                dbms.create_table(table)
                if not silent:
                    print(f"  ✅ Table: {table['table_name']}")
            elif stmt == 'insert':
                dbms.insert(table, record)
            elif stmt == 'create index':
                dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
                if not silent:
                    print(f"  ✅ Index: {table['index_name']}")
            return True
        except Exception as e:
            if not silent:
                print(f"  ⚠️  {str(e)[:60]}")
            return False
    
    # Create tables
    tables = [
        "CREATE TABLE departments (dept_id int not null, dept_name char(50) not null, dept_code char(10) not null, primary key(dept_id));",
        "CREATE TABLE instructors (instructor_id int not null, first_name char(30) not null, last_name char(30) not null, email char(50), dept_id int not null, hire_date date, primary key(instructor_id), foreign key(dept_id) references departments(dept_id));",
        "CREATE TABLE courses (course_id int not null, course_code char(10) not null, course_name char(100) not null, credits int not null, dept_id int not null, instructor_id int, semester char(20), year int, primary key(course_id), foreign key(dept_id) references departments(dept_id), foreign key(instructor_id) references instructors(instructor_id));",
        "CREATE TABLE students (student_id int not null, first_name char(30) not null, last_name char(30) not null, email char(50), date_of_birth date, enrollment_year int, major char(50), gpa char(4), primary key(student_id));",
        "CREATE TABLE enrollments (enrollment_id int not null, student_id int not null, course_id int not null, enrollment_date date, status char(20), primary key(enrollment_id), foreign key(student_id) references students(student_id), foreign key(course_id) references courses(course_id));",
        "CREATE TABLE grades (grade_id int not null, enrollment_id int not null, grade char(2), grade_points char(4), semester char(20), year int, primary key(grade_id), foreign key(enrollment_id) references enrollments(enrollment_id));",
        "CREATE TABLE attendance (attendance_id int not null, enrollment_id int not null, att_date date, status char(20), primary key(attendance_id), foreign key(enrollment_id) references enrollments(enrollment_id));"
    ]
    
    print("\n📋 Creating tables...")
    for sql in tables:
        run_sql(sql)
    
    # Insert data
    data = [
        # Departments
        "INSERT INTO departments VALUES(1, 'Computer Science', 'CS');",
        "INSERT INTO departments VALUES(2, 'Mathematics', 'MATH');",
        "INSERT INTO departments VALUES(3, 'Physics', 'PHYS');",
        "INSERT INTO departments VALUES(4, 'English', 'ENG');",
        "INSERT INTO departments VALUES(5, 'Business', 'BUS');",
        # Instructors
        "INSERT INTO instructors VALUES(1, 'John', 'Smith', 'jsmith@uni.edu', 1, '2015-08-15');",
        "INSERT INTO instructors VALUES(2, 'Sarah', 'Johnson', 'sjohnson@uni.edu', 1, '2018-01-10');",
        "INSERT INTO instructors VALUES(3, 'Michael', 'Brown', 'mbrown@uni.edu', 2, '2012-06-20');",
        "INSERT INTO instructors VALUES(4, 'Emily', 'Davis', 'edavis@uni.edu', 3, '2020-03-01');",
        "INSERT INTO instructors VALUES(5, 'Robert', 'Wilson', 'rwilson@uni.edu', 5, '2016-09-05');",
        # Courses
        "INSERT INTO courses VALUES(1, 'CS101', 'Introduction to Programming', 3, 1, 1, 'Fall', 2024);",
        "INSERT INTO courses VALUES(2, 'CS201', 'Data Structures', 4, 1, 2, 'Fall', 2024);",
        "INSERT INTO courses VALUES(3, 'MATH101', 'Calculus I', 4, 2, 3, 'Fall', 2024);",
        "INSERT INTO courses VALUES(4, 'PHYS101', 'Physics I', 4, 3, 4, 'Fall', 2024);",
        "INSERT INTO courses VALUES(5, 'BUS101', 'Introduction to Business', 3, 5, 5, 'Fall', 2024);",
        "INSERT INTO courses VALUES(6, 'CS301', 'Database Systems', 4, 1, 1, 'Spring', 2025);",
        "INSERT INTO courses VALUES(7, 'ENG101', 'English Composition', 3, 4, 4, 'Fall', 2024);",
        # Students
        "INSERT INTO students VALUES(1, 'Alice', 'Anderson', 'alice@uni.edu', '2003-05-15', 2022, 'Computer Science', '3.85');",
        "INSERT INTO students VALUES(2, 'Bob', 'Baker', 'bob@uni.edu', '2002-11-20', 2021, 'Computer Science', '3.62');",
        "INSERT INTO students VALUES(3, 'Carol', 'Clark', 'carol@uni.edu', '2003-08-10', 2022, 'Mathematics', '3.91');",
        "INSERT INTO students VALUES(4, 'David', 'Evans', 'david@uni.edu', '2001-03-25', 2020, 'Physics', '3.45');",
        "INSERT INTO students VALUES(5, 'Emma', 'Foster', 'emma@uni.edu', '2004-01-30', 2023, 'Business', '3.78');",
        "INSERT INTO students VALUES(6, 'Frank', 'Green', 'frank@uni.edu', '2002-07-12', 2021, 'Computer Science', '3.55');",
        "INSERT INTO students VALUES(7, 'Grace', 'Harris', 'grace@uni.edu', '2003-12-05', 2022, 'English', '3.88');",
        "INSERT INTO students VALUES(8, 'Henry', 'Irwin', 'henry@uni.edu', '2003-09-18', 2023, 'Mathematics', '3.72');",
        "INSERT INTO students VALUES(9, 'Ivy', 'Johnson', 'ivy@uni.edu', '2001-06-22', 2020, 'Computer Science', '3.95');",
        "INSERT INTO students VALUES(10, 'Jack', 'King', 'jack@uni.edu', '2002-04-08', 2022, 'Business', '3.40');",
        # Enrollments
        "INSERT INTO enrollments VALUES(1, 1, 1, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(2, 1, 2, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(3, 2, 1, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(4, 2, 2, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(5, 3, 3, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(6, 4, 4, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(7, 5, 5, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(8, 6, 1, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(9, 6, 2, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(10, 7, 7, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(11, 8, 3, '2024-08-25', 'Active');",
        "INSERT INTO enrollments VALUES(12, 9, 6, '2024-08-25', 'Active');",
        # Grades
        "INSERT INTO grades VALUES(1, 1, 'A', '4.00', 'Fall', 2024);",
        "INSERT INTO grades VALUES(2, 2, 'A-', '3.70', 'Fall', 2024);",
        "INSERT INTO grades VALUES(3, 3, 'B+', '3.30', 'Fall', 2024);",
        "INSERT INTO grades VALUES(4, 4, 'B', '3.00', 'Fall', 2024);",
        "INSERT INTO grades VALUES(5, 5, 'A', '4.00', 'Fall', 2024);",
        "INSERT INTO grades VALUES(6, 6, 'A', '4.00', 'Fall', 2024);",
        "INSERT INTO grades VALUES(7, 7, 'B+', '3.30', 'Fall', 2024);",
        "INSERT INTO grades VALUES(8, 8, 'B', '3.00', 'Fall', 2024);",
        "INSERT INTO grades VALUES(9, 9, 'A-', '3.70', 'Fall', 2024);",
        "INSERT INTO grades VALUES(10, 10, 'B+', '3.30', 'Fall', 2024);",
        "INSERT INTO grades VALUES(11, 11, 'A-', '3.70', 'Fall', 2024);",
        "INSERT INTO grades VALUES(12, 12, 'A', '4.00', 'Fall', 2024);",
        # Attendance
        "INSERT INTO attendance VALUES(1, 1, '2024-09-01', 'Present');",
        "INSERT INTO attendance VALUES(2, 1, '2024-09-08', 'Present');",
        "INSERT INTO attendance VALUES(3, 1, '2024-09-15', 'Absent');",
        "INSERT INTO attendance VALUES(4, 2, '2024-09-01', 'Present');",
        "INSERT INTO attendance VALUES(5, 2, '2024-09-08', 'Present');",
        "INSERT INTO attendance VALUES(6, 3, '2024-09-01', 'Late');",
        "INSERT INTO attendance VALUES(7, 4, '2024-09-01', 'Present');",
        "INSERT INTO attendance VALUES(8, 5, '2024-09-01', 'Present');"
    ]
    
    print("📝 Inserting data...")
    for sql in data:
        run_sql(sql, silent=True)
    
    # Create indexes
    indexes = [
        "CREATE INDEX idx_students_major ON students(major);",
        "CREATE INDEX idx_students_enrollment ON students(enrollment_year);",
        "CREATE INDEX idx_students_email ON students(email);",
        "CREATE INDEX idx_students_gpa ON students(gpa);",
        "CREATE INDEX idx_courses_code ON courses(course_code);",
        "CREATE INDEX idx_courses_dept ON courses(dept_id);",
        "CREATE INDEX idx_courses_instructor ON courses(instructor_id);",
        "CREATE INDEX idx_courses_semester ON courses(semester);",
        "CREATE INDEX idx_enrollments_student ON enrollments(student_id);",
        "CREATE INDEX idx_enrollments_course ON enrollments(course_id);",
        "CREATE INDEX idx_enrollments_status ON enrollments(status);",
        "CREATE INDEX idx_grades_enrollment ON grades(enrollment_id);",
        "CREATE INDEX idx_grades_semester ON grades(semester);",
        "CREATE INDEX idx_grades_year ON grades(year);",
        "CREATE INDEX idx_attendance_enrollment ON attendance(enrollment_id);",
        "CREATE INDEX idx_attendance_date ON attendance(att_date);",
        "CREATE INDEX idx_instructors_dept ON instructors(dept_id);",
        "CREATE INDEX idx_instructors_email ON instructors(email);",
        "CREATE INDEX idx_departments_code ON departments(dept_code);"
    ]
    
    print("🔧 Creating indexes...")
    for sql in indexes:
        run_sql(sql)
    
    print("\n" + "="*60)
    print("✅ DATABASE SEEDED SUCCESSFULLY!")
    print("="*60)
    print("📊 Tables: 7 | Records: 59 | Indexes: 19")
    print("="*60 + "\n")

# Auto-seed on startup
seed_database_on_startup()

# Re-initialize DBMS after seeding (to use the seeded data)
dbms = DBMS()

# Load grammar parser
with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def execute_sql(query):
    """Execute SQL query and return result"""
    try:
        t = SQLTransformer()
        parsed = parser.parse(query)
        result = t.transform(parsed)
        stmt, table, record, tables, sel_cols, where = result
        
        if stmt == 'create table':
            dbms.create_table(table)
            return {'success': True, 'message': f"Table '{table['table_name']}' created", 'type': 'success'}
        
        elif stmt == 'drop table':
            dbms.drop_table(table['table_name'])
            return {'success': True, 'message': f"Table '{table['table_name']}' dropped", 'type': 'success'}
        
        elif stmt == 'insert':
            dbms.insert(table, record)
            return {'success': True, 'message': 'Row inserted', 'type': 'success'}
        
        elif stmt == 'update':
            result = dbms.update(table['table_name'], table['assignments'], where)
            return {'success': True, 'message': str(result), 'type': 'success'}
        
        elif stmt == 'delete':
            deleted, skipped = dbms.delete(table['table_name'], where)
            return {'success': True, 'message': f'{deleted} row(s) deleted', 'type': 'success'}
        
        elif stmt == 'select':
            output = dbms.select(tables, sel_cols, where)
            # Parse the table output into structured data
            rows, columns = parse_select_output(output)
            return {'success': True, 'type': 'select', 'columns': columns, 'rows': rows, 'raw': output}
        
        elif stmt == 'show tables':
            output = dbms.show_tables()
            tables_list = [t.strip() for t in output.strip().split('\n')[2:-1] if t.strip()]
            return {'success': True, 'type': 'show_tables', 'tables': tables_list, 'raw': output}
        
        elif stmt == 'describe' or stmt == 'desc' or stmt == 'explain':
            table_obj = dbms.explain_describe_desc(table['table_name'])
            structure = {
                'columns': table_obj.columns,
                'not_null': list(table_obj.not_null_keys),
                'primary_key': list(table_obj.primary_key) if table_obj.primary_key else [],
                'foreign_keys': table_obj.foreign_keys
            }
            return {'success': True, 'type': 'describe', 'structure': structure, 'raw': str(structure)}
        
        elif stmt == 'create index':
            result = dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
            return {'success': True, 'message': str(result), 'type': 'success'}
        
        elif stmt == 'drop index':
            result = dbms.drop_index(table['index_name'])
            return {'success': True, 'message': str(result), 'type': 'success'}
        
        elif stmt == 'show indexes':
            result = dbms.show_indexes(table['table_name'])
            return {'success': True, 'message': str(result), 'type': 'success'}
        
        elif stmt == 'begin':
            result = dbms.begin_transaction()
            return {'success': True, 'message': str(result), 'type': 'success'}
        
        elif stmt == 'commit':
            result = dbms.commit_transaction()
            return {'success': True, 'message': str(result), 'type': 'success'}
        
        elif stmt == 'rollback':
            result = dbms.rollback_transaction()
            return {'success': True, 'message': str(result), 'type': 'success'}
        
        else:
            return {'success': False, 'error': f'Unknown statement: {stmt}', 'type': 'error'}
    
    except Exception as e:
        return {'success': False, 'error': str(e), 'type': 'error'}

def parse_select_output(output):
    """Parse the ASCII table output into structured data"""
    lines = output.strip().split('\n')
    if len(lines) < 3:
        return [], []
    
    # Parse header (line 1 is the header row between separators)
    header_line = lines[1]
    columns = [c.strip().replace('|', '').strip() for c in header_line.split('|') if c.strip()]
    
    # Parse data rows (skip separator lines starting with + or -)
    rows = []
    for i, line in enumerate(lines):
        # Skip separator lines
        if line.startswith('+') or line.startswith('-'):
            continue
        # Skip header line (already parsed)
        if i == 1:
            continue
        # Parse data rows that contain |
        if '|' in line:
            values = [v.strip() for v in line.split('|')[1:-1]]
            # Only add if column count matches
            if len(values) == len(columns) and values != columns:
                rows.append(dict(zip(columns, values)))
    
    return rows, columns

def get_all_tables():
    """Get list of all tables"""
    try:
        output = dbms.show_tables()
        tables = [t.strip() for t in output.strip().split('\n')[2:-1] if t.strip()]
        return tables
    except:
        return []

def get_table_structure(table_name):
    """Get structure of a specific table"""
    try:
        table_obj = dbms.explain_describe_desc(table_name)
        return {
            'name': table_obj.table_name,
            'columns': table_obj.columns,
            'not_null': list(table_obj.not_null_keys),
            'primary_key': list(table_obj.primary_key) if table_obj.primary_key else [],
            'foreign_keys': {k: v for k, v in table_obj.foreign_keys.items()} if table_obj.foreign_keys else {}
        }
    except:
        return None

# phpMyAdmin-inspired CSS
CSS = """
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: #f0f0f0;
    color: #333;
    display: flex;
    height: 100vh;
    overflow: hidden;
}

/* Left Sidebar */
.sidebar {
    width: 250px;
    background: #2c3e50;
    color: white;
    overflow-y: auto;
    flex-shrink: 0;
}

.sidebar-header {
    padding: 15px;
    background: #1a252f;
    border-bottom: 1px solid #34495e;
}

.sidebar-header h2 {
    font-size: 16px;
    font-weight: 600;
}

.sidebar-header small {
    color: #7f8c8d;
    font-size: 11px;
}

.db-section {
    padding: 10px 0;
}

.db-header {
    padding: 10px 15px;
    background: #34495e;
    font-weight: 600;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.db-header:hover {
    background: #3d566e;
}

.table-list {
    list-style: none;
}

.table-list li {
    padding: 8px 15px 8px 30px;
    cursor: pointer;
    font-size: 13px;
    border-left: 3px solid transparent;
    transition: all 0.2s;
}

.table-list li:hover {
    background: #34495e;
    border-left-color: #3498db;
}

.table-list li.active {
    background: #3498db;
    border-left-color: #2980b9;
}

.table-list li .table-icon {
    margin-right: 8px;
    opacity: 0.7;
}

/* Main Content */
.main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* Top Navigation */
.top-nav {
    background: white;
    border-bottom: 1px solid #ddd;
    padding: 0 20px;
    flex-shrink: 0;
}

.nav-tabs {
    display: flex;
    gap: 5px;
}

.nav-tab {
    padding: 12px 20px;
    background: #f8f9fa;
    border: 1px solid #ddd;
    border-bottom: none;
    border-radius: 5px 5px 0 0;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    color: #555;
    transition: all 0.2s;
    margin-bottom: -1px;
}

.nav-tab:hover {
    background: #e9ecef;
}

.nav-tab.active {
    background: white;
    border-color: #ddd;
    color: #3498db;
    position: relative;
    top: 1px;
}

.nav-tab .tab-icon {
    margin-right: 6px;
}

/* Content Area */
.content-area {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background: white;
    margin: 15px;
    border-radius: 5px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* SQL Editor */
.sql-editor {
    width: 100%;
    min-height: 150px;
    padding: 15px;
    border: 2px solid #ddd;
    border-radius: 5px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 14px;
    resize: vertical;
    transition: border-color 0.2s;
}

.sql-editor:focus {
    outline: none;
    border-color: #3498db;
}

.execute-btn {
    margin-top: 10px;
    padding: 12px 30px;
    background: #27ae60;
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.execute-btn:hover {
    background: #219a52;
}

.execute-btn .icon {
    margin-right: 8px;
}

/* Results Table */
.results-container {
    margin-top: 20px;
    overflow-x: auto;
}

.results-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

.results-table th {
    background: #3498db;
    color: white;
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
    border: 1px solid #2980b9;
}

.results-table td {
    padding: 10px 15px;
    border: 1px solid #ddd;
    background: #fff;
}

.results-table tr:nth-child(even) td {
    background: #f8f9fa;
}

.results-table tr:hover td {
    background: #e3f2fd;
}

/* Messages */
.message {
    padding: 15px 20px;
    border-radius: 5px;
    margin-bottom: 15px;
    font-size: 14px;
}

.message.success {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.message.error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}

.message.info {
    background: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
}

/* Structure View */
.structure-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

.structure-table th {
    background: #6c757d;
    color: white;
    padding: 10px 15px;
    text-align: left;
    font-weight: 600;
}

.structure-table td {
    padding: 10px 15px;
    border: 1px solid #ddd;
}

.structure-table tr:nth-child(even) {
    background: #f8f9fa;
}

.key-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
    margin-right: 5px;
}

.key-badge.pk {
    background: #e74c3c;
    color: white;
}

.key-badge.nn {
    background: #f39c12;
    color: white;
}

.key-badge.fk {
    background: #9b59b6;
    color: white;
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #7f8c8d;
}

.empty-state .icon {
    font-size: 48px;
    margin-bottom: 15px;
    opacity: 0.5;
}

.empty-state h3 {
    font-size: 18px;
    margin-bottom: 10px;
    color: #555;
}

.empty-state p {
    font-size: 14px;
}

/* Quick Actions */
.quick-actions {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
    flex-wrap: wrap;
}

.action-btn {
    padding: 8px 15px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    transition: background 0.2s;
}

.action-btn:hover {
    background: #2980b9;
}

.action-btn.secondary {
    background: #6c757d;
}

.action-btn.secondary:hover {
    background: #5a6268;
}

.action-btn.danger {
    background: #e74c3c;
}

.action-btn.danger:hover {
    background: #c0392b;
}

/* Row Count */
.row-count {
    padding: 10px 15px;
    background: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 15px;
    font-size: 13px;
    color: #555;
}

.row-count strong {
    color: #3498db;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a1a1a1;
}
</style>
"""

# Main HTML Template
HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL DBMS - phpMyAdmin Style</title>
    {CSS}
</head>
<body>
    <!-- Left Sidebar -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h2>🗄️ SQL DBMS</h2>
            <small>Database Manager</small>
        </div>
        <div class="db-section">
            <div class="db-header">
                <span>📊 Database</span>
                <span>▼</span>
            </div>
            <ul class="table-list" id="tableList">
                <!-- Tables loaded dynamically -->
            </ul>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tabs">
                <div class="nav-tab active" data-tab="sql" onclick="switchTab('sql')">
                    <span class="tab-icon">⚡</span> SQL
                </div>
                <div class="nav-tab" data-tab="browse" onclick="switchTab('browse')">
                    <span class="tab-icon">📋</span> Browse
                </div>
                <div class="nav-tab" data-tab="structure" onclick="switchTab('structure')">
                    <span class="tab-icon">🏗️</span> Structure
                </div>
                <div class="nav-tab" data-tab="indexes" onclick="switchTab('indexes')">
                    <span class="tab-icon">📑</span> Indexes
                </div>
            </div>
        </div>

        <!-- Content Area -->
        <div class="content-area" id="contentArea">
            <!-- Content loaded dynamically -->
        </div>
    </div>

    <script>
        let currentTable = null;
        let tables = [];

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            loadTables();
            showSQLTab();
        }});

        // Load tables from server
        async function loadTables() {{
            try {{
                const response = await fetch('/api/tables');
                const data = await response.json();
                tables = data.tables || [];
                renderTableList();
            }} catch (error) {{
                console.error('Error loading tables:', error);
            }}
        }}

        // Render table list in sidebar
        function renderTableList() {{
            const list = document.getElementById('tableList');
            if (tables.length === 0) {{
                list.innerHTML = '<li style="color: #7f8c8d; padding: 15px;">No tables yet</li>';
                return;
            }}
            list.innerHTML = tables.map(t => `
                <li class="${{t === currentTable ? 'active' : ''}}" onclick="selectTable('${{t}}')">
                    <span class="table-icon">📄</span>${{t}}
                </li>
            `).join('');
        }}

        // Select a table
        function selectTable(tableName) {{
            currentTable = tableName;
            renderTableList();
            // Switch to browse tab when table is selected
            switchTab('browse');
        }}

        // Switch tabs
        function switchTab(tabName) {{
            // Update tab styling
            document.querySelectorAll('.nav-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelector(`[data-tab="${{tabName}}"]`).classList.add('active');

            // Show appropriate content
            switch(tabName) {{
                case 'sql':
                    showSQLTab();
                    break;
                case 'browse':
                    showBrowseTab();
                    break;
                case 'structure':
                    showStructureTab();
                    break;
                case 'indexes':
                    showIndexesTab();
                    break;
            }}
        }}

        // Show SQL tab
        function showSQLTab() {{
            const content = document.getElementById('contentArea');
            content.innerHTML = `
                <div class="quick-actions">
                    <button class="action-btn" onclick="insertTemplate('SELECT * FROM ;')">SELECT</button>
                    <button class="action-btn" onclick="insertTemplate('INSERT INTO  VALUES ();')">INSERT</button>
                    <button class="action-btn" onclick="insertTemplate('UPDATE  SET  WHERE ;')">UPDATE</button>
                    <button class="action-btn" onclick="insertTemplate('DELETE FROM  WHERE ;')">DELETE</button>
                    <button class="action-btn secondary" onclick="insertTemplate('CREATE TABLE  ( id int not null, primary key(id) );')">CREATE TABLE</button>
                    <button class="action-btn secondary" onclick="insertTemplate('CREATE INDEX  ON ();')">CREATE INDEX</button>
                    <button class="action-btn" onclick="insertTemplate('BEGIN;')">BEGIN</button>
                    <button class="action-btn" onclick="insertTemplate('COMMIT;')">COMMIT</button>
                    <button class="action-btn danger" onclick="insertTemplate('ROLLBACK;')">ROLLBACK</button>
                </div>
                <textarea class="sql-editor" id="sqlEditor" placeholder="Enter your SQL query here...&#10;&#10;Examples:&#10;SELECT * FROM users;&#10;INSERT INTO users VALUES(1, 'John');&#10;CREATE TABLE products (id int not null, name char(50), primary key(id));"></textarea>
                <button class="execute-btn" onclick="executeSQL()">
                    <span class="icon">▶️</span> Execute
                </button>
                <div id="sqlResults"></div>
            `;
        }}

        // Insert template into editor
        function insertTemplate(template) {{
            const editor = document.getElementById('sqlEditor');
            if (editor) {{
                editor.value = template;
                editor.focus();
            }}
        }}

        // Execute SQL
        async function executeSQL() {{
            const editor = document.getElementById('sqlEditor');
            const query = editor.value.trim();
            if (!query) {{
                alert('Please enter a SQL query');
                return;
            }}

            const resultsDiv = document.getElementById('sqlResults');
            resultsDiv.innerHTML = '<div class="message info">Executing...</div>';

            try {{
                const response = await fetch('/api/execute', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ query }})
                }});
                const data = await response.json();

                if (data.success) {{
                    if (data.type === 'select') {{
                        renderResults(data);
                    }} else if (data.type === 'show_tables') {{
                        loadTables();
                        resultsDiv.innerHTML = `<div class="message success">${{data.message || 'Tables refreshed'}}</div>`;
                    }} else {{
                        resultsDiv.innerHTML = `<div class="message success">${{data.message}}</div>`;
                        loadTables(); // Refresh table list
                    }}
                }} else {{
                    resultsDiv.innerHTML = `<div class="message error">❌ ${{data.error}}</div>`;
                }}
            }} catch (error) {{
                resultsDiv.innerHTML = `<div class="message error">❌ Error: ${{error.message}}</div>`;
            }}
        }}

        // Render SELECT results
        function renderResults(data) {{
            const resultsDiv = document.getElementById('sqlResults');
            if (!data.rows || data.rows.length === 0) {{
                resultsDiv.innerHTML = '<div class="message info">No results</div>';
                return;
            }}

            const columns = data.columns;
            const rows = data.rows;

            let html = `<div class="row-count"><strong>${{rows.length}}</strong> row(s) returned</div>`;
            html += '<div class="results-container"><table class="results-table"><thead><tr>';
            columns.forEach(col => {{
                html += `<th>${{col}}</th>`;
            }});
            html += '</tr></thead><tbody>';

            rows.forEach(row => {{
                html += '<tr>';
                columns.forEach(col => {{
                    html += `<td>${{row[col] || 'NULL'}}</td>`;
                }});
                html += '</tr>';
            }});

            html += '</tbody></table></div>';
            resultsDiv.innerHTML = html;
        }}

        // Show Browse tab
        async function showBrowseTab() {{
            const content = document.getElementById('contentArea');
            if (!currentTable) {{
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">📄</div>
                        <h3>No Table Selected</h3>
                        <p>Select a table from the sidebar to browse its data</p>
                    </div>
                `;
                return;
            }}

            content.innerHTML = '<div class="message info">Loading...</div>';

            try {{
                const response = await fetch(`/api/browse/${{encodeURIComponent(currentTable)}}`);
                const data = await response.json();

                if (data.success) {{
                    renderBrowseResults(data);
                }} else {{
                    content.innerHTML = `<div class="message error">❌ ${{data.error}}</div>`;
                }}
            }} catch (error) {{
                content.innerHTML = `<div class="message error">❌ Error: ${{error.message}}</div>`;
            }}
        }}

        // Render browse results
        function renderBrowseResults(data) {{
            const content = document.getElementById('contentArea');
            const columns = data.columns;
            const rows = data.rows || [];

            let html = `<h2 style="margin-bottom: 15px;">📄 Browsing: ${{currentTable}}</h2>`;
            html += `<div class="quick-actions">
                <button class="action-btn" onclick="switchTab('sql'); insertTemplate('SELECT * FROM ${{currentTable}};');">Custom Query</button>
                <button class="action-btn secondary" onclick="showStructureTab()">View Structure</button>
            </div>`;
            html += `<div class="row-count"><strong>${{rows.length}}</strong> row(s) in table</div>`;

            if (rows.length === 0) {{
                html += '<div class="empty-state"><div class="icon">📭</div><h3>Table is Empty</h3><p>No data in this table yet</p></div>';
            }} else {{
                html += '<div class="results-container"><table class="results-table"><thead><tr>';
                columns.forEach(col => {{
                    html += `<th>${{col}}</th>`;
                }});
                html += '</tr></thead><tbody>';

                rows.forEach(row => {{
                    html += '<tr>';
                    columns.forEach(col => {{
                        html += `<td>${{row[col] || 'NULL'}}</td>`;
                    }});
                    html += '</tr>';
                }});

                html += '</tbody></table></div>';
            }}

            content.innerHTML = html;
        }}

        // Show Structure tab
        async function showStructureTab() {{
            const content = document.getElementById('contentArea');
            if (!currentTable) {{
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">🏗️</div>
                        <h3>No Table Selected</h3>
                        <p>Select a table from the sidebar to view its structure</p>
                    </div>
                `;
                return;
            }}

            content.innerHTML = '<div class="message info">Loading structure...</div>';

            try {{
                const response = await fetch(`/api/structure/${{encodeURIComponent(currentTable)}}`);
                const data = await response.json();

                if (data.success) {{
                    renderStructure(data.structure);
                }} else {{
                    content.innerHTML = `<div class="message error">❌ ${{data.error}}</div>`;
                }}
            }} catch (error) {{
                content.innerHTML = `<div class="message error">❌ Error: ${{error.message}}</div>`;
            }}
        }}

        // Render table structure
        function renderStructure(structure) {{
            const content = document.getElementById('contentArea');
            const columns = structure.columns;
            const notNull = structure.not_null || [];
            const pk = structure.primary_key || [];
            const fk = structure.foreign_keys || {{}};

            let html = `<h2 style="margin-bottom: 15px;">🏗️ Structure: ${{structure.name}}</h2>`;
            html += '<div class="results-container"><table class="structure-table">';
            html += '<thead><tr><th>Column</th><th>Type</th><th>Key</th><th>Constraints</th></tr></thead>';
            html += '<tbody>';

            for (const [col, type] of Object.entries(columns)) {{
                const isPK = pk.includes(col);
                const isNN = notNull.includes(col);
                const isFK = fk[col];

                let keys = [];
                if (isPK) keys.push('<span class="key-badge pk">PK</span>');
                if (isFK) keys.push(`<span class="key-badge fk">FK→${{isFK[0]}}.${{isFK[1]}}</span>`);

                let constraints = [];
                if (isNN) constraints.push('NOT NULL');

                html += `<tr>
                    <td><strong>${{col}}</strong></td>
                    <td><code>${{type}}</code></td>
                    <td>${{keys.join(' ')}}</td>
                    <td>${{constraints.join(', ')}}</td>
                </tr>`;
            }}

            html += '</tbody></table></div>';
            content.innerHTML = html;
        }}

        // Show Indexes tab
        async function showIndexesTab() {{
            const content = document.getElementById('contentArea');
            if (!currentTable) {{
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">📑</div>
                        <h3>No Table Selected</h3>
                        <p>Select a table from the sidebar to view its indexes</p>
                    </div>
                `;
                return;
            }}

            content.innerHTML = '<div class="message info">Loading indexes...</div>';

            try {{
                const response = await fetch(`/api/indexes/${{encodeURIComponent(currentTable)}}`);
                const data = await response.json();

                if (data.success) {{
                    renderIndexes(data.message);
                }} else {{
                    content.innerHTML = `<div class="message error">❌ ${{data.error}}</div>`;
                }}
            }} catch (error) {{
                content.innerHTML = `<div class="message error">❌ Error: ${{error.message}}</div>`;
            }}
        }}

        // Render indexes
        function renderIndexes(message) {{
            const content = document.getElementById('contentArea');
            let html = `<h2 style="margin-bottom: 15px;">📑 Indexes</h2>`;
            html += `<div class="message info">${{message}}</div>`;
            html += `<div class="quick-actions">
                <button class="action-btn" onclick="switchTab('sql'); insertTemplate('CREATE INDEX idx_name ON ${{currentTable}}(column_name);');">Create Index</button>
            </div>`;
            content.innerHTML = html;
        }}

        // Refresh tables (called after operations)
        function refreshTables() {{
            loadTables();
        }}
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tables', methods=['GET'])
def api_tables():
    """Get list of all tables"""
    tables = get_all_tables()
    return jsonify({'tables': tables})

@app.route('/api/execute', methods=['POST'])
def api_execute():
    """Execute SQL query"""
    data = request.get_json()
    query = data.get('query', '')
    result = execute_sql(query)
    return jsonify(result)

@app.route('/api/browse/<table_name>', methods=['GET'])
def api_browse(table_name):
    """Browse table data"""
    result = execute_sql(f'SELECT * FROM {table_name};')
    return jsonify(result)

@app.route('/api/structure/<table_name>', methods=['GET'])
def api_structure(table_name):
    """Get table structure"""
    structure = get_table_structure(table_name)
    if structure:
        return jsonify({'success': True, 'structure': structure})
    return jsonify({'success': False, 'error': f'Table {table_name} not found'})

@app.route('/api/indexes/<table_name>', methods=['GET'])
def api_indexes(table_name):
    """Get table indexes"""
    result = execute_sql(f'SHOW INDEXES FROM {table_name};')
    return jsonify(result)

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🗄️  SQL DBMS GUI Server")
    print("=" * 50)
    print(f"📍 Open http://localhost:{PORT} in your browser")
    print(f"🛑 Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=PORT, use_reloader=False)
