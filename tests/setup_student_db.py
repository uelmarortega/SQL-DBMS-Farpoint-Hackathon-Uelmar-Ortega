#!/usr/bin/env python3
"""
Student Record Management System - Database Setup
Creates all tables, inserts sample data, and creates indexes
"""

from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer
import shutil, os

# Clean database
if os.path.exists('DB'):
    shutil.rmtree('DB')
if os.path.exists('DB_INDEXES'):
    shutil.rmtree('DB_INDEXES')

dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def run(query):
    """Execute a SQL query"""
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    stmt, table, record, tables, sel_cols, where = result
    
    if stmt == 'create table':
        dbms.create_table(table)
        print(f"✅ Created table: {table['table_name']}")
    elif stmt == 'insert':
        dbms.insert(table, record)
    elif stmt == 'select':
        output = dbms.select(tables, sel_cols, where)
        print(output)
        return output
    elif stmt == 'create index':
        dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
        print(f"✅ Created index: {table['index_name']} on {table['table_name']}.{table['column_name']}")
    elif stmt == 'show indexes':
        output = dbms.show_indexes(table['table_name'])
        print(f"📑 Indexes: {output}")
        return output
    return None

print("=" * 70)
print("🎓 STUDENT RECORD MANAGEMENT SYSTEM - DATABASE SETUP")
print("=" * 70)

# ============== CREATE TABLES ==============
print("\n📋 CREATING TABLES...")
print("-" * 70)

run("CREATE TABLE departments (dept_id int not null, dept_name char(50) not null, dept_code char(10) not null, primary key(dept_id));")

run("CREATE TABLE instructors (instructor_id int not null, first_name char(30) not null, last_name char(30) not null, email char(50), dept_id int not null, hire_date date, primary key(instructor_id), foreign key(dept_id) references departments(dept_id));")

run("CREATE TABLE courses (course_id int not null, course_code char(10) not null, course_name char(100) not null, credits int not null, dept_id int not null, instructor_id int, semester char(20), year int, primary key(course_id), foreign key(dept_id) references departments(dept_id), foreign key(instructor_id) references instructors(instructor_id));")

run("CREATE TABLE students (student_id int not null, first_name char(30) not null, last_name char(30) not null, email char(50), date_of_birth date, enrollment_year int, major char(50), gpa char(4), primary key(student_id));")

run("CREATE TABLE enrollments (enrollment_id int not null, student_id int not null, course_id int not null, enrollment_date date, status char(20), primary key(enrollment_id), foreign key(student_id) references students(student_id), foreign key(course_id) references courses(course_id));")

run("CREATE TABLE grades (grade_id int not null, enrollment_id int not null, grade char(2), grade_points char(4), semester char(20), year int, primary key(grade_id), foreign key(enrollment_id) references enrollments(enrollment_id));")

run("CREATE TABLE attendance (attendance_id int not null, enrollment_id int not null, att_date date, status char(20), primary key(attendance_id), foreign key(enrollment_id) references enrollments(enrollment_id));")

# ============== INSERT DEPARTMENTS ==============
print("\n📚 INSERTING DEPARTMENTS...")
print("-" * 70)

run("INSERT INTO departments VALUES(1, 'Computer Science', 'CS');")
run("INSERT INTO departments VALUES(2, 'Mathematics', 'MATH');")
run("INSERT INTO departments VALUES(3, 'Physics', 'PHYS');")
run("INSERT INTO departments VALUES(4, 'English', 'ENG');")
run("INSERT INTO departments VALUES(5, 'Business', 'BUS');")

# ============== INSERT INSTRUCTORS ==============
print("\n👨‍🏫 INSERTING INSTRUCTORS...")
print("-" * 70)

run("INSERT INTO instructors VALUES(1, 'John', 'Smith', 'jsmith@uni.edu', 1, '2015-08-15');")
run("INSERT INTO instructors VALUES(2, 'Sarah', 'Johnson', 'sjohnson@uni.edu', 1, '2018-01-10');")
run("INSERT INTO instructors VALUES(3, 'Michael', 'Brown', 'mbrown@uni.edu', 2, '2012-06-20');")
run("INSERT INTO instructors VALUES(4, 'Emily', 'Davis', 'edavis@uni.edu', 3, '2020-03-01');")
run("INSERT INTO instructors VALUES(5, 'Robert', 'Wilson', 'rwilson@uni.edu', 5, '2016-09-05');")

# ============== INSERT COURSES ==============
print("\n📖 INSERTING COURSES...")
print("-" * 70)

run("INSERT INTO courses VALUES(1, 'CS101', 'Introduction to Programming', 3, 1, 1, 'Fall', 2024);")
run("INSERT INTO courses VALUES(2, 'CS201', 'Data Structures', 4, 1, 2, 'Fall', 2024);")
run("INSERT INTO courses VALUES(3, 'MATH101', 'Calculus I', 4, 2, 3, 'Fall', 2024);")
run("INSERT INTO courses VALUES(4, 'PHYS101', 'Physics I', 4, 3, 4, 'Fall', 2024);")
run("INSERT INTO courses VALUES(5, 'BUS101', 'Introduction to Business', 3, 5, 5, 'Fall', 2024);")
run("INSERT INTO courses VALUES(6, 'CS301', 'Database Systems', 4, 1, 1, 'Spring', 2025);")
run("INSERT INTO courses VALUES(7, 'ENG101', 'English Composition', 3, 4, 1, 'Fall', 2024);")

# ============== INSERT STUDENTS ==============
print("\n🎓 INSERTING STUDENTS...")
print("-" * 70)

run("INSERT INTO students VALUES(1, 'Alice', 'Anderson', 'alice@uni.edu', '2003-05-15', 2022, 'Computer Science', '3.85');")
run("INSERT INTO students VALUES(2, 'Bob', 'Baker', 'bob@uni.edu', '2002-11-20', 2021, 'Computer Science', '3.62');")
run("INSERT INTO students VALUES(3, 'Carol', 'Clark', 'carol@uni.edu', '2003-08-10', 2022, 'Mathematics', '3.91');")
run("INSERT INTO students VALUES(4, 'David', 'Evans', 'david@uni.edu', '2001-03-25', 2020, 'Physics', '3.45');")
run("INSERT INTO students VALUES(5, 'Emma', 'Foster', 'emma@uni.edu', '2004-01-30', 2023, 'Business', '3.78');")
run("INSERT INTO students VALUES(6, 'Frank', 'Green', 'frank@uni.edu', '2002-07-12', 2021, 'Computer Science', '3.55');")
run("INSERT INTO students VALUES(7, 'Grace', 'Harris', 'grace@uni.edu', '2003-12-05', 2022, 'English', '3.88');")

# ============== INSERT ENROLLMENTS ==============
print("\n📝 INSERTING ENROLLMENTS...")
print("-" * 70)

run("INSERT INTO enrollments VALUES(1, 1, 1, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(2, 1, 2, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(3, 1, 3, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(4, 2, 1, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(5, 2, 2, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(6, 3, 3, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(7, 3, 4, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(8, 4, 4, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(9, 5, 5, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(10, 6, 1, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(11, 6, 2, '2024-08-25', 'Active');")
run("INSERT INTO enrollments VALUES(12, 7, 7, '2024-08-25', 'Active');")

# ============== INSERT GRADES ==============
print("\n📊 INSERTING GRADES...")
print("-" * 70)

run("INSERT INTO grades VALUES(1, 1, 'A', '4.00', 'Fall', 2024);")
run("INSERT INTO grades VALUES(2, 2, 'A-', '3.70', 'Fall', 2024);")
run("INSERT INTO grades VALUES(3, 3, 'B+', '3.30', 'Fall', 2024);")
run("INSERT INTO grades VALUES(4, 4, 'B', '3.00', 'Fall', 2024);")
run("INSERT INTO grades VALUES(5, 5, 'A', '4.00', 'Fall', 2024);")
run("INSERT INTO grades VALUES(6, 6, 'A', '4.00', 'Fall', 2024);")
run("INSERT INTO grades VALUES(7, 7, 'B+', '3.30', 'Fall', 2024);")
run("INSERT INTO grades VALUES(8, 8, 'B', '3.00', 'Fall', 2024);")
run("INSERT INTO grades VALUES(9, 9, 'A-', '3.70', 'Fall', 2024);")
run("INSERT INTO grades VALUES(10, 10, 'B+', '3.30', 'Fall', 2024);")
run("INSERT INTO grades VALUES(11, 11, 'A-', '3.70', 'Fall', 2024);")
run("INSERT INTO grades VALUES(12, 12, 'A', '4.00', 'Fall', 2024);")

# ============== INSERT ATTENDANCE ==============
print("\n✅ INSERTING ATTENDANCE...")
print("-" * 70)

run("INSERT INTO attendance VALUES(1, 1, '2024-09-01', 'Present');")
run("INSERT INTO attendance VALUES(2, 1, '2024-09-08', 'Present');")
run("INSERT INTO attendance VALUES(3, 1, '2024-09-15', 'Absent');")
run("INSERT INTO attendance VALUES(4, 2, '2024-09-01', 'Present');")
run("INSERT INTO attendance VALUES(5, 2, '2024-09-08', 'Present');")
run("INSERT INTO attendance VALUES(6, 3, '2024-09-01', 'Late');")
run("INSERT INTO attendance VALUES(7, 4, '2024-09-01', 'Present');")
run("INSERT INTO attendance VALUES(8, 5, '2024-09-01', 'Present');")

# ============== CREATE INDEXES ==============
print("\n📑 CREATING INDEXES...")
print("-" * 70)

# Indexes on students table
run("CREATE INDEX idx_students_major ON students(major);")
run("CREATE INDEX idx_students_enrollment ON students(enrollment_year);")
run("CREATE INDEX idx_students_email ON students(email);")

# Indexes on courses table
run("CREATE INDEX idx_courses_code ON courses(course_code);")
run("CREATE INDEX idx_courses_dept ON courses(dept_id);")
run("CREATE INDEX idx_courses_instructor ON courses(instructor_id);")

# Indexes on enrollments table
run("CREATE INDEX idx_enrollments_student ON enrollments(student_id);")
run("CREATE INDEX idx_enrollments_course ON enrollments(course_id);")
run("CREATE INDEX idx_enrollments_status ON enrollments(status);")

# Indexes on grades table
run("CREATE INDEX idx_grades_enrollment ON grades(enrollment_id);")
run("CREATE INDEX idx_grades_semester ON grades(semester);")

# Indexes on instructors table
run("CREATE INDEX idx_instructors_dept ON instructors(dept_id);")
run("CREATE INDEX idx_instructors_email ON instructors(email);")

# Indexes on departments table
run("CREATE INDEX idx_departments_code ON departments(dept_code);")

# Indexes on attendance table
run("CREATE INDEX idx_attendance_enrollment ON attendance(enrollment_id);")
run("CREATE INDEX idx_attendance_att_date ON attendance(att_date);")

# ============== SHOW SUMMARY ==============
print("\n" + "=" * 70)
print("✅ DATABASE SETUP COMPLETE!")
print("=" * 70)

print("\n📊 TABLES CREATED:")
print("   • departments (3 columns)")
print("   • instructors (6 columns, FK to departments)")
print("   • courses (8 columns, FK to departments, instructors)")
print("   • students (8 columns)")
print("   • enrollments (5 columns, FK to students, courses)")
print("   • grades (6 columns, FK to enrollments)")
print("   • attendance (4 columns, FK to enrollments)")

print("\n📑 INDEXES CREATED:")
print("   • idx_students_major, idx_students_enrollment, idx_students_email")
print("   • idx_courses_code, idx_courses_dept, idx_courses_instructor")
print("   • idx_enrollments_student, idx_enrollments_course, idx_enrollments_status")
print("   • idx_grades_enrollment, idx_grades_semester")
print("   • idx_instructors_dept, idx_instructors_email")
print("   • idx_departments_code")
print("   • idx_attendance_enrollment, idx_attendance_date")

print("\n📈 DATA SUMMARY:")
print("   • 5 departments")
print("   • 5 instructors")
print("   • 7 courses")
print("   • 7 students")
print("   • 12 enrollments")
print("   • 12 grades")
print("   • 8 attendance records")

print("\n🎓 READY TO USE!")
print("   Open http://localhost:5001 to explore the database")
print("=" * 70)
