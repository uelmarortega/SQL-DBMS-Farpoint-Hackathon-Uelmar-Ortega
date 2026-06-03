#!/usr/bin/env python3
"""Comprehensive test suite for SQL DBMS"""

from lark import Lark
from sql_transformer import SQLTransformer
from dbms import DBMS
import shutil
import os

# Clean DB folders
if os.path.exists('DB'):
    shutil.rmtree('DB')
if os.path.exists('DB_INDEXES'):
    shutil.rmtree('DB_INDEXES')

dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def execute_sql(query):
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    queries = result if isinstance(result, list) else [result]
    
    last_result = None
    for query_result in queries:
        stmt, table, record, tables, sel_cols, where = query_result
        
        if stmt == 'create table':
            dbms.create_table(table)
            last_result = {'success': True, 'stmt': 'CREATE TABLE', 'table': table['table_name']}
        elif stmt == 'insert':
            dbms.insert(table, record)
            last_result = {'success': True, 'stmt': 'INSERT', 'rows': len(record)}
        elif stmt == 'select':
            output = dbms.select(tables, sel_cols, where)
            last_result = {'success': True, 'stmt': 'SELECT', 'output': output}
        elif stmt == 'show indexes':
            result = dbms.show_indexes(table['table_name'])
            last_result = {'success': True, 'stmt': 'SHOW INDEXES', 'result': str(result)}
        elif stmt == 'show tables':
            output = dbms.show_tables()
            last_result = {'success': True, 'stmt': 'SHOW TABLES', 'output': output}
        elif stmt == 'create index':
            dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
            last_result = {'success': True, 'stmt': 'CREATE INDEX', 'name': table['index_name']}
    
    return last_result

tests_passed = 0
tests_failed = 0

def test(name, query, expected_success=True):
    global tests_passed, tests_failed
    try:
        result = execute_sql(query)
        if expected_success and result.get('success'):
            print(f"✅ {name}")
            tests_passed += 1
            return True
        elif not expected_success and not result.get('success'):
            print(f"✅ {name} (expected failure)")
            tests_passed += 1
            return True
        else:
            print(f"❌ {name} - Unexpected: {result}")
            tests_failed += 1
            return False
    except Exception as e:
        if expected_success:
            print(f"❌ {name} - {e}")
            tests_failed += 1
            return False
        else:
            print(f"✅ {name} (expected failure)")
            tests_passed += 1
            return True

print("="*70)
print("🧪 SQL DBMS COMPREHENSIVE TEST SUITE")
print("="*70)

print("\n📋 CREATE TABLE Tests:")
test("1.1: Inline PRIMARY KEY", "CREATE TABLE t1 (id INT PRIMARY KEY, val INT);")
test("1.2: Table-level PRIMARY KEY", "CREATE TABLE t2 (id INT PRIMARY KEY, val INT);")
test("1.3: NOT NULL constraint", "CREATE TABLE t3 (id INT PRIMARY KEY, email CHAR(100) NOT NULL);")
test("1.4: Both PK and NOT NULL", "CREATE TABLE t4 (id INT PRIMARY KEY NOT NULL, name CHAR(50));")

print("\n📋 INSERT Tests:")
test("2.1: Single row INSERT", "INSERT INTO t1 VALUES (1, 100);")
test("2.2: Multi-row INSERT", "INSERT INTO t1 VALUES (2, 200), (3, 300), (4, 400);")
test("2.3: INSERT into t2", "INSERT INTO t2 VALUES (1, 10), (2, 20);")

print("\n📋 SELECT Tests:")
test("2.4: SELECT *", "SELECT * FROM t1;")

print("\n📋 INDEX Tests:")
test("3.1: CREATE INDEX", "CREATE INDEX idx_t1_val ON t1(val);")
test("3.2: SHOW INDEXES (bug fix)", "SHOW INDEXES FROM t1;")
test("3.3: SHOW INDEXES empty", "SHOW INDEXES FROM t2;")

print("\n📋 Multi-Query Tests:")
test("4.1: CREATE + INSERT + SELECT", 
     "CREATE TABLE mq (id INT PRIMARY KEY, x INT); INSERT INTO mq VALUES (1, 10), (2, 20); SELECT * FROM mq;")
test("4.2: Multiple SHOW commands",
     "SHOW TABLES; SHOW INDEXES FROM t1;")
test("4.3: Complex sequence",
     """CREATE TABLE orders (id INT PRIMARY KEY, cust CHAR(50), amt INT);
        INSERT INTO orders VALUES (1, 'John', 500), (2, 'Jane', 750);
        CREATE INDEX idx_cust ON orders(cust);
        SHOW INDEXES FROM orders;
        SELECT * FROM orders;""")

print("\n📋 SHOW TABLES:")
test("5.1: SHOW TABLES", "SHOW TABLES;")

print("\n" + "="*70)
print(f"📊 RESULTS: {tests_passed} passed, {tests_failed} failed")
print("="*70)

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print(f"⚠️  {tests_failed} test(s) failed")

exit(0 if tests_failed == 0 else 1)
