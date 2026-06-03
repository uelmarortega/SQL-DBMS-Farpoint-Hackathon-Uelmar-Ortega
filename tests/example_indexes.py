#!/usr/bin/env python3
"""
🎓 STUDENT RECORD MANAGEMENT SYSTEM - INDEXING EXAMPLES
========================================================
This script demonstrates practical indexing examples for the student database.
"""

from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer
import shutil, os

# Clean start
if os.path.exists('DB'):
    shutil.rmtree('DB')
if os.path.exists('DB_INDEXES'):
    shutil.rmtree('DB_INDEXES')

dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def run_sql(query, description=""):
    """Execute SQL and print results"""
    print(f"\n{'='*70}")
    if description:
        print(f"📌 {description}")
    print(f"{'='*70}")
    print(f"SQL: {query}\n")
    
    t = SQLTransformer()
    try:
        parsed = parser.parse(query)
        result = t.transform(parsed)
        stmt, table, record, tables, sel_cols, where = result
        
        if stmt == 'create table':
            dbms.create_table(table)
            print(f"✅ Table '{table['table_name']}' created")
        elif stmt == 'insert':
            dbms.insert(table, record)
            print("✅ Row inserted")
        elif stmt == 'select':
            output = dbms.select(tables, sel_cols, where)
            print(output)
        elif stmt == 'create index':
            result = dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
            print(f"✅ {result}")
        elif stmt == 'show indexes':
            result = dbms.show_indexes(table['table_name'])
            print(f"📑 {result}")
        elif stmt == 'drop index':
            result = dbms.drop_index(table['index_name'])
            print(f"✅ {result}")
        elif stmt == 'begin':
            dbms.begin_transaction()
            print("✅ Transaction started")
        elif stmt == 'commit':
            dbms.commit_transaction()
            print("✅ Transaction committed")
        elif stmt == 'rollback':
            dbms.rollback_transaction()
            print("✅ Transaction rolled back")
    except Exception as e:
        print(f"❌ Error: {e}")

# ============================================================================
# PART 1: CREATE TABLES
# ============================================================================
print("\n" + "="*70)
print("🎓 STUDENT RECORD MANAGEMENT SYSTEM - INDEXING DEMONSTRATION")
print("="*70)

print("\n📋 STEP 1: Creating Tables...")
print("-"*70)

run_sql("CREATE TABLE departments (dept_id int not null, dept_name char(50) not null, dept_code char(10) not null, primary key(dept_id))",
        "Create departments table")

run_sql("CREATE TABLE students (student_id int not null, first_name char(30) not null, last_name char(30) not null, email char(50), major char(50), enrollment_year int, gpa char(4), primary key(student_id))",
        "Create students table")

run_sql("CREATE TABLE courses (course_id int not null, course_code char(10) not null, course_name char(100) not null, credits int not null, dept_id int not null, instructor_id int, semester char(20), year int, primary key(course_id))",
        "Create courses table")

run_sql("CREATE TABLE enrollments (enrollment_id int not null, student_id int not null, course_id int not null, enrollment_date date, status char(20), primary key(enrollment_id))",
        "Create enrollments table")

run_sql("CREATE TABLE grades (grade_id int not null, enrollment_id int not null, grade char(2), grade_points char(4), semester char(20), year int, primary key(grade_id))",
        "Create grades table")

# ============================================================================
# PART 2: INSERT SAMPLE DATA
# ============================================================================
print("\n\n📝 STEP 2: Inserting Sample Data...")
print("-"*70)

# Departments
run_sql("INSERT INTO departments VALUES(1, 'Computer Science', 'CS')")
run_sql("INSERT INTO departments VALUES(2, 'Mathematics', 'MATH')")
run_sql("INSERT INTO departments VALUES(3, 'Physics', 'PHYS')")
run_sql("INSERT INTO departments VALUES(4, 'English', 'ENG')")
run_sql("INSERT INTO departments VALUES(5, 'Business', 'BUS')")

# Students (10 students with various majors)
run_sql("INSERT INTO students VALUES(1, 'Alice', 'Anderson', 'alice@uni.edu', 'Computer Science', 2022, '3.85')")
run_sql("INSERT INTO students VALUES(2, 'Bob', 'Baker', 'bob@uni.edu', 'Computer Science', 2021, '3.62')")
run_sql("INSERT INTO students VALUES(3, 'Carol', 'Clark', 'carol@uni.edu', 'Mathematics', 2022, '3.91')")
run_sql("INSERT INTO students VALUES(4, 'David', 'Evans', 'david@uni.edu', 'Physics', 2020, '3.45')")
run_sql("INSERT INTO students VALUES(5, 'Emma', 'Foster', 'emma@uni.edu', 'Business', 2023, '3.78')")
run_sql("INSERT INTO students VALUES(6, 'Frank', 'Green', 'frank@uni.edu', 'Computer Science', 2021, '3.55')")
run_sql("INSERT INTO students VALUES(7, 'Grace', 'Harris', 'grace@uni.edu', 'English', 2022, '3.88')")
run_sql("INSERT INTO students VALUES(8, 'Henry', 'Irwin', 'henry@uni.edu', 'Mathematics', 2023, '3.72')")
run_sql("INSERT INTO students VALUES(9, 'Ivy', 'Johnson', 'ivy@uni.edu', 'Computer Science', 2020, '3.95')")
run_sql("INSERT INTO students VALUES(10, 'Jack', 'King', 'jack@uni.edu', 'Business', 2022, '3.40')")

# Courses
run_sql("INSERT INTO courses VALUES(1, 'CS101', 'Introduction to Programming', 3, 1, 1, 'Fall', 2024)")
run_sql("INSERT INTO courses VALUES(2, 'CS201', 'Data Structures', 4, 1, 2, 'Fall', 2024)")
run_sql("INSERT INTO courses VALUES(3, 'MATH101', 'Calculus I', 4, 2, NULL, 'Fall', 2024)")
run_sql("INSERT INTO courses VALUES(4, 'PHYS101', 'Physics I', 4, 3, NULL, 'Fall', 2024)")
run_sql("INSERT INTO courses VALUES(5, 'BUS101', 'Introduction to Business', 3, 5, NULL, 'Fall', 2024)")
run_sql("INSERT INTO courses VALUES(6, 'CS301', 'Database Systems', 4, 1, 1, 'Spring', 2025)")
run_sql("INSERT INTO courses VALUES(7, 'ENG101', 'English Composition', 3, 4, NULL, 'Fall', 2024)")

# Enrollments
run_sql("INSERT INTO enrollments VALUES(1, 1, 1, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(2, 1, 2, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(3, 2, 1, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(4, 2, 2, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(5, 3, 3, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(6, 4, 4, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(7, 5, 5, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(8, 6, 1, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(9, 6, 2, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(10, 7, 7, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(11, 8, 3, '2024-08-25', 'Active')")
run_sql("INSERT INTO enrollments VALUES(12, 9, 6, '2024-08-25', 'Active')")

# Grades
run_sql("INSERT INTO grades VALUES(1, 1, 'A', '4.00', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(2, 2, 'A-', '3.70', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(3, 3, 'B+', '3.30', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(4, 4, 'B', '3.00', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(5, 5, 'A', '4.00', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(6, 6, 'A', '4.00', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(7, 7, 'B+', '3.30', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(8, 8, 'B', '3.00', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(9, 9, 'A-', '3.70', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(10, 10, 'B+', '3.30', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(11, 11, 'A-', '3.70', 'Fall', 2024)")
run_sql("INSERT INTO grades VALUES(12, 12, 'A', '4.00', 'Fall', 2024)")

print("\n✅ Sample data inserted successfully!")

# ============================================================================
# PART 3: SHOW INITIAL STATE (NO INDEXES)
# ============================================================================
print("\n\n📊 STEP 3: Current State - No Indexes Yet")
print("-"*70)

run_sql("SHOW INDEXES FROM students", "Indexes on students table (should be empty)")

# ============================================================================
# PART 4: CREATE INDEXES AND EXPLAIN BENEFITS
# ============================================================================
print("\n\n🔧 STEP 4: Creating Indexes for Common Queries")
print("-"*70)

print("""
📚 WHY INDEXES MATTER:
----------------------
Without Index: Database scans EVERY row (O(n) - linear search)
With Index:    Database jumps directly to matching rows (O(1) - hash lookup)

Example: Finding students by major
  - Without index: Scan all 10,000 students ❌
  - With index:    Direct hash lookup ✅
""")

# Index 1: Major lookup
print("\n" + "-"*70)
print("INDEX 1: idx_students_major")
print("-"*70)
print("Purpose: Fast lookup of students by major")
print("Use case: 'Find all Computer Science students'")
run_sql("CREATE INDEX idx_students_major ON students(major)", "Create index on major column")

# Index 2: Enrollment year
print("\n" + "-"*70)
print("INDEX 2: idx_students_enrollment")
print("-"*70)
print("Purpose: Find students by enrollment year")
print("Use case: 'Find all students who enrolled in 2022'")
run_sql("CREATE INDEX idx_students_enrollment ON students(enrollment_year)", "Create index on enrollment_year column")

# Index 3: Email lookup
print("\n" + "-"*70)
print("INDEX 3: idx_students_email")
print("-"*70)
print("Purpose: Fast email lookup (login, contact)")
print("Use case: 'Find student by email address'")
run_sql("CREATE INDEX idx_students_email ON students(email)", "Create index on email column")

# Index 4: Course code
print("\n" + "-"*70)
print("INDEX 4: idx_courses_code")
print("-"*70)
print("Purpose: Fast course lookup by code")
print("Use case: 'Find CS101 course details'")
run_sql("CREATE INDEX idx_courses_code ON courses(course_code)", "Create index on course_code column")

# Index 5: Course department
print("\n" + "-"*70)
print("INDEX 5: idx_courses_dept")
print("-"*70)
print("Purpose: Find courses by department")
print("Use case: 'List all CS courses'")
run_sql("CREATE INDEX idx_courses_dept ON courses(dept_id)", "Create index on dept_id column")

# Index 6: Enrollment student
print("\n" + "-"*70)
print("INDEX 6: idx_enrollments_student")
print("-"*70)
print("Purpose: Find all enrollments for a student")
print("Use case: 'Show all courses Alice is enrolled in'")
run_sql("CREATE INDEX idx_enrollments_student ON enrollments(student_id)", "Create index on student_id column")

# Index 7: Enrollment course
print("\n" + "-"*70)
print("INDEX 7: idx_enrollments_course")
print("-"*70)
print("Purpose: Find all students in a course")
print("Use case: 'List all students in CS101'")
run_sql("CREATE INDEX idx_enrollments_course ON enrollments(course_id)", "Create index on course_id column")

# Index 8: Grades by enrollment
print("\n" + "-"*70)
print("INDEX 8: idx_grades_enrollment")
print("-"*70)
print("Purpose: Fast grade lookup by enrollment")
print("Use case: 'Get grade for specific enrollment'")
run_sql("CREATE INDEX idx_grades_enrollment ON grades(enrollment_id)", "Create index on enrollment_id column")

# ============================================================================
# PART 5: VERIFY INDEXES CREATED
# ============================================================================
print("\n\n✅ STEP 5: Verifying All Indexes")
print("-"*70)

tables_to_check = ['students', 'courses', 'enrollments', 'grades']
for table in tables_to_check:
    run_sql(f"SHOW INDEXES FROM {table}", f"Indexes on {table}")

# ============================================================================
# PART 6: DEMONSTRATE INDEX USAGE
# ============================================================================
print("\n\n🚀 STEP 6: Demonstrating Index Usage")
print("-"*70)

print("""
📊 QUERY EXAMPLES THAT USE INDEXES:
------------------------------------
""")

# Example 1: Find students by major (uses idx_students_major)
print("\n" + "="*70)
print("EXAMPLE 1: Find all Computer Science students")
print("Uses index: idx_students_major")
print("="*70)
run_sql("SELECT student_id, first_name, last_name, major FROM students WHERE major = 'Computer Science'")

# Example 2: Find students by enrollment year (uses idx_students_enrollment)
print("\n" + "="*70)
print("EXAMPLE 2: Find students who enrolled in 2022")
print("Uses index: idx_students_enrollment")
print("="*70)
run_sql("SELECT student_id, first_name, last_name, enrollment_year FROM students WHERE enrollment_year = 2022")

# Example 3: Find course by code (uses idx_courses_code)
print("\n" + "="*70)
print("EXAMPLE 3: Find course CS101")
print("Uses index: idx_courses_code")
print("="*70)
run_sql("SELECT course_id, course_code, course_name, credits FROM courses WHERE course_code = 'CS101'")

# Example 4: Find enrollments by student (uses idx_enrollments_student)
print("\n" + "="*70)
print("EXAMPLE 4: Find all courses for student ID 1 (Alice)")
print("Uses index: idx_enrollments_student")
print("="*70)
run_sql("SELECT enrollment_id, student_id, course_id, status FROM enrollments WHERE student_id = 1")

# Example 5: Find enrollments by course (uses idx_enrollments_course)
print("\n" + "="*70)
print("EXAMPLE 5: Find all students in course ID 1 (CS101)")
print("Uses index: idx_enrollments_course")
print("="*70)
run_sql("SELECT enrollment_id, student_id, course_id FROM enrollments WHERE course_id = 1")

# ============================================================================
# PART 7: INDEX MAINTENANCE DEMO
# ============================================================================
print("\n\n🔧 STEP 7: Index Maintenance - Automatic Updates")
print("-"*70)

print("""
📌 IMPORTANT: Indexes are automatically maintained!
---------------------------------------------------
When you INSERT, UPDATE, or DELETE data, indexes are automatically updated.
No manual intervention required!
""")

# Show current CS students
print("\nBefore INSERT - CS Students:")
run_sql("SELECT student_id, first_name, major FROM students WHERE major = 'Computer Science'")

# Insert new CS student
print("\nInserting new CS student (Kevin)...")
run_sql("INSERT INTO students VALUES(11, 'Kevin', 'Lee', 'kevin@uni.edu', 'Computer Science', 2024, '3.80')")

# Show updated CS students (index automatically includes new row)
print("\nAfter INSERT - CS Students (index updated automatically):")
run_sql("SELECT student_id, first_name, major FROM students WHERE major = 'Computer Science'")

# ============================================================================
# PART 8: DROP INDEX EXAMPLE
# ============================================================================
print("\n\n🗑️  STEP 8: Dropping an Index (if needed)")
print("-"*70)

print("""
📌 When to drop an index:
--------------------------
- Index is rarely used
- Index slows down INSERT/UPDATE/DELETE operations
- Index is redundant (covered by another index)
""")

# Create a temporary index
print("\nCreating temporary index...")
run_sql("CREATE INDEX idx_temp ON students(gpa);", "Temporary index on GPA")

# Show indexes
run_sql("SHOW INDEXES FROM students;", "Indexes on students (includes temp)")

# Drop the temporary index
print("\nDropping temporary index...")
run_sql("DROP INDEX idx_temp;", "Drop temporary index")

# Show indexes after drop
run_sql("SHOW INDEXES FROM students;", "Indexes on students (temp removed)")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "="*70)
print("📊 INDEXING SUMMARY")
print("="*70)

print("""
✅ INDEXES CREATED:
-------------------
1. idx_students_major      - Fast major lookup
2. idx_students_enrollment - Fast enrollment year lookup
3. idx_students_email      - Fast email lookup
4. idx_courses_code        - Fast course code lookup
5. idx_courses_dept        - Fast department lookup
6. idx_enrollments_student - Fast student enrollment lookup
7. idx_enrollments_course  - Fast course enrollment lookup
8. idx_grades_enrollment   - Fast grade lookup

🎯 PERFORMANCE BENEFITS:
------------------------
- WITHOUT index: O(n) - Scan all rows (slow for large tables)
- WITH index:    O(1) - Direct hash lookup (instant!)

📈 WHEN INDEXES HELP MOST:
--------------------------
✅ Large tables (1000+ rows)
✅ Frequently queried columns (WHERE clauses)
✅ Join columns (foreign keys)
✅ Unique or high-cardinality columns

⚠️  WHEN TO AVOID INDEXES:
--------------------------
❌ Small tables (< 100 rows)
❌ Columns rarely used in WHERE
❌ Columns with many duplicate values
❌ Tables with frequent bulk inserts

💡 BEST PRACTICES:
------------------
1. Index foreign key columns (for joins)
2. Index columns used in WHERE clauses
3. Index columns used in ORDER BY
4. Monitor index usage and remove unused ones
5. Remember: indexes speed up SELECT, but slow down INSERT/UPDATE/DELETE
""")

print("\n" + "="*70)
print("✅ INDEXING DEMONSTRATION COMPLETE!")
print("="*70)
print("\n🌐 Open http://localhost:5001 to explore the data and indexes!")
print("   - Click on any table in the sidebar")
print("   - Go to the 'Indexes' tab to see indexes")
print("   - Use the 'SQL' tab to run queries")
print("="*70 + "\n")
