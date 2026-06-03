#!/usr/bin/env python3
"""
🎓 STUDENT RECORD MANAGEMENT SYSTEM - DATABASE SEEDER
=====================================================
This script creates all tables, inserts sample data, and creates indexes
for a complete student record management system.

Usage:
    python seeder.py              # Fresh start (deletes existing DB)
    python seeder.py --keep       # Keep existing data, just add if missing
"""

from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer
import shutil, os, sys

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_DIR = 'DB'
INDEX_DIR = 'DB_INDEXES'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def init_dbms(fresh=True):
    """Initialize DBMS, optionally cleaning existing data"""
    if fresh:
        if os.path.exists(DB_DIR):
            shutil.rmtree(DB_DIR)
            print(f"🗑️  Removed existing {DB_DIR}/")
        if os.path.exists(INDEX_DIR):
            shutil.rmtree(INDEX_DIR)
            print(f"🗑️  Removed existing {INDEX_DIR}/")
    
    return DBMS()

def create_parser():
    """Create Lark parser from grammar"""
    with open('grammar.lark') as f:
        return Lark(f.read(), start='command', lexer='basic')

def execute_sql(dbms, parser, query, silent=False):
    """Execute SQL query and return result. Supports multiple queries."""
    t = SQLTransformer()
    try:
        parsed = parser.parse(query)
        result = t.transform(parsed)
        
        # Handle multiple queries (query_list) vs single query
        queries = result if isinstance(result, list) else [result]
        
        last_result = None
        for query_result in queries:
            stmt, table, record, tables, sel_cols, where = query_result
            
            if stmt == 'create table':
                dbms.create_table(table)
                if not silent:
                    print(f"  ✅ Created table: {table['table_name']}")
                last_result = True
            elif stmt == 'insert':
                dbms.insert(table, record)
                if not silent:
                    print(f"  ✅ Inserted row")
                last_result = True
            elif stmt == 'create index':
                dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
                if not silent:
                    print(f"  ✅ Created index: {table['index_name']}")
                last_result = True
            elif stmt == 'select':
                last_result = dbms.select(tables, sel_cols, where)
            elif stmt == 'show indexes':
                last_result = dbms.show_indexes(table['table_name'])
            elif stmt == 'drop index':
                dbms.drop_index(table['index_name'])
                if not silent:
                    print(f"  ✅ Dropped index: {table['index_name']}")
                last_result = True
            elif stmt == 'begin':
                dbms.begin_transaction()
                last_result = True
            elif stmt == 'commit':
                dbms.commit_transaction()
                last_result = True
            elif stmt == 'rollback':
                dbms.rollback_transaction()
                last_result = True
        
        return last_result
    except Exception as e:
        if not silent:
            print(f"  ❌ Error: {e}")
        return False

# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

def get_create_tables_sql():
    """Return list of CREATE TABLE statements"""
    return [
        # Departments - academic departments
        """CREATE TABLE departments (
            dept_id int not null,
            dept_name char(50) not null,
            dept_code char(10) not null,
            primary key(dept_id)
        );""",
        
        # Instructors - professors and teachers
        """CREATE TABLE instructors (
            instructor_id int not null,
            first_name char(30) not null,
            last_name char(30) not null,
            email char(50),
            dept_id int not null,
            hire_date date,
            primary key(instructor_id),
            foreign key(dept_id) references departments(dept_id)
        );""",
        
        # Courses - available courses
        """CREATE TABLE courses (
            course_id int not null,
            course_code char(10) not null,
            course_name char(100) not null,
            credits int not null,
            dept_id int not null,
            instructor_id int,
            semester char(20),
            year int,
            primary key(course_id),
            foreign key(dept_id) references departments(dept_id),
            foreign key(instructor_id) references instructors(instructor_id)
        );""",
        
        # Students - enrolled students
        """CREATE TABLE students (
            student_id int not null,
            first_name char(30) not null,
            last_name char(30) not null,
            email char(50),
            date_of_birth date,
            enrollment_year int,
            major char(50),
            gpa char(4),
            primary key(student_id)
        );""",
        
        # Enrollments - student-course registrations
        """CREATE TABLE enrollments (
            enrollment_id int not null,
            student_id int not null,
            course_id int not null,
            enrollment_date date,
            status char(20),
            primary key(enrollment_id),
            foreign key(student_id) references students(student_id),
            foreign key(course_id) references courses(course_id)
        );""",
        
        # Grades - student grades for courses
        """CREATE TABLE grades (
            grade_id int not null,
            enrollment_id int not null,
            grade char(2),
            grade_points char(4),
            semester char(20),
            year int,
            primary key(grade_id),
            foreign key(enrollment_id) references enrollments(enrollment_id)
        );""",
        
        # Attendance - class attendance records
        """CREATE TABLE attendance (
            attendance_id int not null,
            enrollment_id int not null,
            att_date date,
            status char(20),
            primary key(attendance_id),
            foreign key(enrollment_id) references enrollments(enrollment_id)
        );"""
    ]

def get_insert_data_sql():
    """Return list of INSERT statements"""
    return [
        # ========== DEPARTMENTS ==========
        "INSERT INTO departments VALUES(1, 'Computer Science', 'CS');",
        "INSERT INTO departments VALUES(2, 'Mathematics', 'MATH');",
        "INSERT INTO departments VALUES(3, 'Physics', 'PHYS');",
        "INSERT INTO departments VALUES(4, 'English', 'ENG');",
        "INSERT INTO departments VALUES(5, 'Business', 'BUS');",
        
        # ========== INSTRUCTORS ==========
        "INSERT INTO instructors VALUES(1, 'John', 'Smith', 'jsmith@uni.edu', 1, '2015-08-15');",
        "INSERT INTO instructors VALUES(2, 'Sarah', 'Johnson', 'sjohnson@uni.edu', 1, '2018-01-10');",
        "INSERT INTO instructors VALUES(3, 'Michael', 'Brown', 'mbrown@uni.edu', 2, '2012-06-20');",
        "INSERT INTO instructors VALUES(4, 'Emily', 'Davis', 'edavis@uni.edu', 3, '2020-03-01');",
        "INSERT INTO instructors VALUES(5, 'Robert', 'Wilson', 'rwilson@uni.edu', 5, '2016-09-05');",
        
        # ========== COURSES ==========
        "INSERT INTO courses VALUES(1, 'CS101', 'Introduction to Programming', 3, 1, 1, 'Fall', 2024);",
        "INSERT INTO courses VALUES(2, 'CS201', 'Data Structures', 4, 1, 2, 'Fall', 2024);",
        "INSERT INTO courses VALUES(3, 'MATH101', 'Calculus I', 4, 2, 3, 'Fall', 2024);",
        "INSERT INTO courses VALUES(4, 'PHYS101', 'Physics I', 4, 3, 4, 'Fall', 2024);",
        "INSERT INTO courses VALUES(5, 'BUS101', 'Introduction to Business', 3, 5, 5, 'Fall', 2024);",
        "INSERT INTO courses VALUES(6, 'CS301', 'Database Systems', 4, 1, 1, 'Spring', 2025);",
        "INSERT INTO courses VALUES(7, 'ENG101', 'English Composition', 3, 4, 4, 'Fall', 2024);",
        
        # ========== STUDENTS ==========
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
        
        # ========== ENROLLMENTS ==========
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
        
        # ========== GRADES ==========
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
        
        # ========== ATTENDANCE ==========
        "INSERT INTO attendance VALUES(1, 1, '2024-09-01', 'Present');",
        "INSERT INTO attendance VALUES(2, 1, '2024-09-08', 'Present');",
        "INSERT INTO attendance VALUES(3, 1, '2024-09-15', 'Absent');",
        "INSERT INTO attendance VALUES(4, 2, '2024-09-01', 'Present');",
        "INSERT INTO attendance VALUES(5, 2, '2024-09-08', 'Present');",
        "INSERT INTO attendance VALUES(6, 3, '2024-09-01', 'Late');",
        "INSERT INTO attendance VALUES(7, 4, '2024-09-01', 'Present');",
        "INSERT INTO attendance VALUES(8, 5, '2024-09-01', 'Present');"
    ]

def get_create_indexes_sql():
    """Return list of CREATE INDEX statements"""
    return [
        # Student indexes
        "CREATE INDEX idx_students_major ON students(major);",
        "CREATE INDEX idx_students_enrollment ON students(enrollment_year);",
        "CREATE INDEX idx_students_email ON students(email);",
        "CREATE INDEX idx_students_gpa ON students(gpa);",
        
        # Course indexes
        "CREATE INDEX idx_courses_code ON courses(course_code);",
        "CREATE INDEX idx_courses_dept ON courses(dept_id);",
        "CREATE INDEX idx_courses_instructor ON courses(instructor_id);",
        "CREATE INDEX idx_courses_semester ON courses(semester);",
        
        # Enrollment indexes
        "CREATE INDEX idx_enrollments_student ON enrollments(student_id);",
        "CREATE INDEX idx_enrollments_course ON enrollments(course_id);",
        "CREATE INDEX idx_enrollments_status ON enrollments(status);",
        
        # Grade indexes
        "CREATE INDEX idx_grades_enrollment ON grades(enrollment_id);",
        "CREATE INDEX idx_grades_semester ON grades(semester);",
        "CREATE INDEX idx_grades_year ON grades(year);",
        
        # Attendance indexes
        "CREATE INDEX idx_attendance_enrollment ON attendance(enrollment_id);",
        "CREATE INDEX idx_attendance_date ON attendance(att_date);",
        
        # Instructor indexes
        "CREATE INDEX idx_instructors_dept ON instructors(dept_id);",
        "CREATE INDEX idx_instructors_email ON instructors(email);",
        
        # Department indexes
        "CREATE INDEX idx_departments_code ON departments(dept_code);"
    ]

# ============================================================================
# MAIN SEEDER FUNCTION
# ============================================================================

def seed_database(fresh=True, verbose=True):
    """
    Seed the database with tables, data, and indexes.
    
    Args:
        fresh: If True, delete existing database first
        verbose: If True, print progress messages
    
    Returns:
        dict: Summary of what was created
    """
    summary = {
        'tables': 0,
        'records': 0,
        'indexes': 0,
        'errors': []
    }
    
    print("\n" + "="*70)
    print("🎓 STUDENT RECORD MANAGEMENT SYSTEM - DATABASE SEEDER")
    print("="*70)
    
    # Initialize DBMS
    if verbose:
        print(f"\n📁 Initializing database (fresh={fresh})...")
    dbms = init_dbms(fresh=fresh)
    parser = create_parser()
    
    # Create tables
    if verbose:
        print(f"\n📋 Creating tables...")
    create_statements = get_create_tables_sql()
    for sql in create_statements:
        if execute_sql(dbms, parser, sql, silent=not verbose):
            summary['tables'] += 1
        else:
            summary['errors'].append(f"Failed to create table: {sql[:50]}")
    
    # Insert data
    if verbose:
        print(f"\n📝 Inserting sample data...")
    insert_statements = get_insert_data_sql()
    for sql in insert_statements:
        if execute_sql(dbms, parser, sql, silent=not verbose):
            summary['records'] += 1
        else:
            summary['errors'].append(f"Failed to insert: {sql[:50]}")
    
    # Create indexes
    if verbose:
        print(f"\n🔧 Creating indexes...")
    index_statements = get_create_indexes_sql()
    for sql in index_statements:
        if execute_sql(dbms, parser, sql, silent=not verbose):
            summary['indexes'] += 1
        else:
            summary['errors'].append(f"Failed to create index: {sql[:50]}")
    
    # Print summary
    if verbose:
        print("\n" + "="*70)
        print("✅ SEEDING COMPLETE!")
        print("="*70)
        print(f"📊 TABLES CREATED:  {summary['tables']}")
        print(f"📝 RECORDS INSERTED: {summary['records']}")
        print(f"🔧 INDEXES CREATED:  {summary['indexes']}")
        
        if summary['errors']:
            print(f"\n⚠️  ERRORS ({len(summary['errors'])}):")
            for error in summary['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
        
        print("\n🌐 Open http://localhost:5001 to explore the database!")
        print("="*70 + "\n")
    
    return summary

# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Parse command line arguments
    fresh = '--keep' not in sys.argv
    verbose = '--quiet' not in sys.argv
    
    # Run seeder
    summary = seed_database(fresh=fresh, verbose=verbose)
    
    # Exit with error code if there were errors
    sys.exit(1 if summary['errors'] else 0)
