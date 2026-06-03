#!/usr/bin/env python3
"""
Comprehensive CRUD Operations Test
Verifies CREATE, READ, UPDATE, DELETE work perfectly with all constraints.
"""

import shutil, os
from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer
from messages import *

# Clean start
if os.path.exists('DB'): shutil.rmtree('DB')
if os.path.exists('DB_INDEXES'): shutil.rmtree('DB_INDEXES')

dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def run(query):
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    stmt, table, record, tables, sel_cols, where = result
    
    if stmt == 'create table':
        return dbms.create_table(table)
    elif stmt == 'insert':
        return dbms.insert(table, record)
    elif stmt == 'select':
        return dbms.select(tables, sel_cols, where)
    elif stmt == 'update':
        return dbms.update(table['table_name'], table['assignments'], where)
    elif stmt == 'delete':
        r, _ = dbms.delete(table['table_name'], where)
        return r
    return None

print("=" * 70)
print("COMPREHENSIVE CRUD OPERATIONS TEST")
print("=" * 70)

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"✅ {name}")
        passed += 1
    except AssertionError as e:
        print(f"❌ {name}: {e}")
        failed += 1
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}: {e}")
        failed += 1

# =============================================================================
# CREATE TABLE TESTS
# =============================================================================

def test_create_basic():
    run("create table users (id int not null, name char(20), email char(50));")
    result = run("select * from users;")
    assert "ID" in result and "NAME" in result and "EMAIL" in result

def test_create_with_pk():
    run("create table products (pid int not null, pname char(30), primary key(pid));")
    result = run("select * from products;")
    assert "PID" in result

def test_create_with_fk():
    run("create table orders (oid int not null, pid int, foreign key(pid) references products(pid));")
    result = run("select * from orders;")
    assert "OID" in result

def test_create_with_not_null():
    run("create table accounts (aid int not null, balance int not null);")
    result = run("select * from accounts;")
    assert "AID" in result

def test_create_date_type():
    run("create table events (eid int not null, event_date date);")
    result = run("select * from events;")
    assert "EID" in result

# =============================================================================
# INSERT TESTS
# =============================================================================

def test_insert_basic():
    run("insert into users values(1, 'Alice', 'alice@test.com');")
    result = run("select * from users;")
    assert "Alice" in result

def test_insert_multiple():
    run("insert into users values(2, 'Bob', 'bob@test.com');")
    run("insert into users values(3, 'Charlie', 'charlie@test.com');")
    result = run("select * from users;")
    assert "Alice" in result and "Bob" in result and "Charlie" in result

def test_insert_with_null():
    run("create table nullable (id int not null, val int);")
    run("insert into nullable values(1, null);")
    result = run("select * from nullable;")
    assert "null" in result.lower()

def test_insert_type_check():
    try:
        run("insert into users values('bad', 'Test', 'test@test.com');")
        assert False, "Should have failed"
    except InsertTypeMismatchError:
        pass  # Expected

def test_insert_not_null_check():
    try:
        run("insert into accounts values(1, null);")
        assert False, "Should have failed"
    except InsertColumnNonNullableError:
        pass  # Expected

def test_insert_pk_duplicate():
    try:
        run("insert into products values(1, 'Duplicate');")
        assert False, "Should have failed"
    except InsertDuplicatePrimaryKeyError:
        pass  # Expected

def test_insert_fk_check():
    try:
        run("insert into orders values(1, 999);")  # pid 999 doesn't exist
        assert False, "Should have failed"
    except InsertReferentialIntegrityError:
        pass  # Expected

# =============================================================================
# SELECT TESTS
# =============================================================================

def test_select_all():
    result = run("select * from users;")
    assert "Alice" in result and "Bob" in result

def test_select_columns():
    result = run("select id, name from users;")
    assert "ID" in result and "NAME" in result and "EMAIL" not in result

def test_select_where_eq():
    result = run("select * from users where id=2;")
    assert "Bob" in result and "Alice" not in result

def test_select_where_gt():
    result = run("select * from users where id>1;")
    assert "Bob" in result and "Charlie" in result and "Alice" not in result

def test_select_where_and():
    run("create table multi (id int not null, a int, b int);")
    run("insert into multi values(1, 10, 20);")
    run("insert into multi values(2, 10, 30);")
    run("insert into multi values(3, 20, 20);")
    result = run("select * from multi where a=10 and b=20;")
    assert result.count("10") == 2  # Only one row should match

def test_select_where_or():
    result = run("select * from users where id=1 or id=3;")
    assert "Alice" in result and "Charlie" in result and "Bob" not in result

def test_select_join():
    run("insert into products values(1, 'Widget');")
    run("insert into orders values(10, 1);")
    result = run("select * from products, orders;")
    assert "Widget" in result

# =============================================================================
# UPDATE TESTS
# =============================================================================

def test_update_basic():
    run("create table upd_test (id int not null, val int);")
    run("insert into upd_test values(1, 100);")
    run("update upd_test set val=999 where id=1;")
    result = run("select * from upd_test;")
    assert "999" in result and "100" not in result

def test_update_where():
    run("insert into upd_test values(2, 200);")
    run("insert into upd_test values(3, 300);")
    run("update upd_test set val=888 where id=2;")
    result = run("select * from upd_test;")
    assert "888" in result and "200" not in result and "300" in result

def test_update_multiple_cols():
    run("create table multi_upd (id int not null, a int, b int);")
    run("insert into multi_upd values(1, 10, 20);")
    run("update multi_upd set a=100, b=200 where id=1;")
    result = run("select * from multi_upd;")
    assert "100" in result and "200" in result

def test_update_type_check():
    try:
        run("update users set name=12345 where id=1;")
        assert False, "Should have failed"
    except InsertTypeMismatchError:
        pass  # Expected

def test_update_not_null():
    try:
        run("update users set name=null where id=1;")
        assert False, "Should have failed"
    except InsertColumnNonNullableError:
        pass  # Expected

def test_update_pk_unique():
    try:
        run("update products set pid=1 where pid=2;")  # pid=1 exists
        assert False, "Should have failed"
    except InsertDuplicatePrimaryKeyError:
        pass  # Expected

# =============================================================================
# DELETE TESTS
# =============================================================================

def test_delete_basic():
    run("create table del_test (id int not null, val int);")
    run("insert into del_test values(1, 100);")
    run("insert into del_test values(2, 200);")
    run("delete from del_test where id=1;")
    result = run("select * from del_test;")
    assert "100" not in result and "200" in result

def test_delete_where():
    run("insert into del_test values(3, 300);")
    run("delete from del_test where val=300;")
    result = run("select * from del_test;")
    assert "300" not in result and "200" in result

def test_delete_referential():
    # Try to delete a product that has an order referencing it
    try:
        run("delete from products where pid=1;")
        assert False, "Should have failed"
    except DeleteReferentialIntegrityPassed:
        pass  # Expected - delete blocked by FK

def test_delete_no_where():
    run("create table del_all (id int not null);")
    run("insert into del_all values(1);")
    run("insert into del_all values(2);")
    run("delete from del_all;")
    result = run("select * from del_all;")
    assert "1" not in result and "2" not in result

# =============================================================================
# EDGE CASES
# =============================================================================

def test_empty_select():
    run("create table empty_t (id int not null);")
    result = run("select * from empty_t;")
    assert "ID" in result  # Headers should show even with no data

def test_char_length():
    run("create table char_test (id int not null, name char(5));")
    run("insert into char_test values(1, 'Bob');")
    try:
        run("insert into char_test values(2, 'Alexander');")  # Too long
        assert False, "Should have failed"
    except InsertTypeMismatchError:
        pass  # Expected

def test_show_tables():
    result = run("show tables;")
    assert "users" in result.lower() or "USERS" in result

def test_describe_table():
    result = run("describe users;")
    assert "ID" in result and "NAME" in result

# =============================================================================
# RUN ALL TESTS
# =============================================================================

print("\n--- CREATE TABLE ---")
test("CREATE TABLE basic", test_create_basic)
test("CREATE TABLE with PRIMARY KEY", test_create_with_pk)
test("CREATE TABLE with FOREIGN KEY", test_create_with_fk)
test("CREATE TABLE with NOT NULL", test_create_with_not_null)
test("CREATE TABLE with DATE type", test_create_date_type)

print("\n--- INSERT ---")
test("INSERT basic", test_insert_basic)
test("INSERT multiple rows", test_insert_multiple)
test("INSERT with NULL", test_insert_with_null)
test("INSERT type checking", test_insert_type_check)
test("INSERT NOT NULL check", test_insert_not_null_check)
test("INSERT PK duplicate check", test_insert_pk_duplicate)
test("INSERT FK referential check", test_insert_fk_check)

print("\n--- SELECT ---")
test("SELECT * all columns", test_select_all)
test("SELECT specific columns", test_select_columns)
test("SELECT WHERE equals", test_select_where_eq)
test("SELECT WHERE greater than", test_select_where_gt)
test("SELECT WHERE AND", test_select_where_and)
test("SELECT WHERE OR", test_select_where_or)
test("SELECT JOIN (cartesian)", test_select_join)

print("\n--- UPDATE ---")
test("UPDATE basic", test_update_basic)
test("UPDATE with WHERE filter", test_update_where)
test("UPDATE multiple columns", test_update_multiple_cols)
test("UPDATE type checking", test_update_type_check)
test("UPDATE NOT NULL check", test_update_not_null)
test("UPDATE PK uniqueness", test_update_pk_unique)

print("\n--- DELETE ---")
test("DELETE basic", test_delete_basic)
test("DELETE with WHERE", test_delete_where)
test("DELETE referential integrity", test_delete_referential)
test("DELETE all rows (no WHERE)", test_delete_no_where)

print("\n--- EDGE CASES ---")
test("SELECT from empty table", test_empty_select)
test("CHAR length validation", test_char_length)
test("SHOW TABLES", test_show_tables)
test("DESCRIBE table", test_describe_table)

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 70)

if failed == 0:
    print("\n🎉 ALL CRUD OPERATIONS WORK PERFECTLY! ✅\n")
else:
    print(f"\n⚠️  {failed} test(s) failed - see above for details\n")
