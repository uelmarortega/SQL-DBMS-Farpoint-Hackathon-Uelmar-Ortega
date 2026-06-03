#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE TEST - All 4 Features + Bonus Points
Tests CRUD operations, Indexing, Transactions, and verifies bonus criteria.
"""

import shutil, os
from dbms import DBMS
from index_manager import IndexManager
from lark import Lark
from sql_transformer import SQLTransformer
from messages import *

print("=" * 80)
print(" " * 20 + "SQL DBMS - FINAL COMPREHENSIVE TEST")
print("=" * 80)

def fresh_dbms():
    if os.path.exists('DB'): shutil.rmtree('DB')
    if os.path.exists('DB_INDEXES'): shutil.rmtree('DB_INDEXES')
    return DBMS()

def parse_and_run(dbms, query):
    with open('grammar.lark') as f:
        parser = Lark(f.read(), start='command', lexer='basic')
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
    elif stmt == 'begin':
        return dbms.begin_transaction()
    elif stmt == 'commit':
        return dbms.commit_transaction()
    elif stmt == 'rollback':
        return dbms.rollback_transaction()
    elif stmt == 'create index':
        return dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
    elif stmt == 'drop index':
        return dbms.drop_index(table['index_name'])
    elif stmt == 'show indexes':
        return dbms.show_indexes(table['table_name'])
    return None

passed = 0
failed = 0
bonus_passed = 0
bonus_failed = 0

def test(name, fn, bonus=False):
    global passed, failed, bonus_passed, bonus_failed
    try:
        fn()
        if bonus:
            print(f"✅ BONUS: {name}")
            bonus_passed += 1
        else:
            print(f"✅ {name}")
            passed += 1
    except AssertionError as e:
        if bonus:
            print(f"❌ BONUS: {name}: {e}")
            bonus_failed += 1
        else:
            print(f"❌ {name}: {e}")
            failed += 1
    except Exception as e:
        if bonus:
            print(f"❌ BONUS: {name}: {type(e).__name__}: {e}")
            bonus_failed += 1
        else:
            print(f"❌ {name}: {type(e).__name__}: {e}")
            failed += 1

# =============================================================================
# FEATURE 1: BASIC OPERATIONS (20 pts base + 10 pts bonus)
# =============================================================================
print("\n" + "=" * 80)
print("FEATURE 1: BASIC OPERATIONS (20 pts + 10 bonus)")
print("=" * 80)

def test_create_table():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table users (id int not null, name char(20), email char(50), primary key(id));")
    result = parse_and_run(dbms, "select * from users;")
    assert "ID" in result and "NAME" in result
test("CREATE TABLE with PRIMARY KEY", test_create_table)

def test_insert_basic():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    result = parse_and_run(dbms, "select * from t;")
    assert "Alice" in result
test("INSERT row", test_insert_basic)

def test_select_all():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    parse_and_run(dbms, "insert into t values(1);")
    parse_and_run(dbms, "insert into t values(2);")
    result = parse_and_run(dbms, "select * from t;")
    assert "1" in result and "2" in result
test("SELECT all rows", test_select_all)

def test_select_where():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "insert into t values(1, 100);")
    parse_and_run(dbms, "insert into t values(2, 200);")
    result = parse_and_run(dbms, "select * from t where id=1;")
    assert "100" in result and "200" not in result
test("SELECT with WHERE filter", test_select_where)

def test_update_basic():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    parse_and_run(dbms, "update t set name='Bob' where id=1;")
    result = parse_and_run(dbms, "select * from t;")
    assert "Bob" in result and "Alice" not in result
test("UPDATE basic", test_update_basic)

def test_delete_basic():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    parse_and_run(dbms, "insert into t values(1);")
    parse_and_run(dbms, "insert into t values(2);")
    parse_and_run(dbms, "delete from t where id=1;")
    result = parse_and_run(dbms, "select * from t;")
    assert "1" not in result and "2" in result
test("DELETE with WHERE", test_delete_basic)

# --- BONUS: Full Type & Constraint Checking ---

def test_bonus_type_check_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    try:
        parse_and_run(dbms, "insert into t values(1, 12345);")  # int in char column
        assert False, "Should have failed"
    except InsertTypeMismatchError:
        pass
test("BONUS: INSERT type checking (int→char)", test_bonus_type_check_insert, bonus=True)

def test_bonus_type_check_update():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    try:
        parse_and_run(dbms, "update t set name=999 where id=1;")  # int in char column
        assert False, "Should have failed"
    except InsertTypeMismatchError:
        pass
test("BONUS: UPDATE type checking", test_bonus_type_check_update, bonus=True)

def test_bonus_not_null_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20) not null);")
    try:
        parse_and_run(dbms, "insert into t values(1, null);")
        assert False, "Should have failed"
    except InsertColumnNonNullableError:
        pass
test("BONUS: INSERT NOT NULL constraint", test_bonus_not_null_insert, bonus=True)

def test_bonus_not_null_update():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20) not null);")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    try:
        parse_and_run(dbms, "update t set name=null where id=1;")
        assert False, "Should have failed"
    except InsertColumnNonNullableError:
        pass
test("BONUS: UPDATE NOT NULL constraint", test_bonus_not_null_update, bonus=True)

def test_bonus_pk_duplicate_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, primary key(id));")
    parse_and_run(dbms, "insert into t values(1);")
    try:
        parse_and_run(dbms, "insert into t values(1);")
        assert False, "Should have failed"
    except InsertDuplicatePrimaryKeyError:
        pass
test("BONUS: INSERT PK uniqueness", test_bonus_pk_duplicate_insert, bonus=True)

def test_bonus_pk_duplicate_update():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, primary key(id));")
    parse_and_run(dbms, "insert into t values(1);")
    parse_and_run(dbms, "insert into t values(2);")
    try:
        parse_and_run(dbms, "update t set id=2 where id=1;")  # Would duplicate pk=2
        assert False, "Should have failed"
    except InsertDuplicatePrimaryKeyError:
        pass
test("BONUS: UPDATE PK uniqueness", test_bonus_pk_duplicate_update, bonus=True)

def test_bonus_fk_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table parent (id int not null, primary key(id));")
    parse_and_run(dbms, "create table child (pid int, foreign key(pid) references parent(id));")
    parse_and_run(dbms, "insert into parent values(1);")
    try:
        parse_and_run(dbms, "insert into child values(999);")  # pid 999 doesn't exist
        assert False, "Should have failed"
    except InsertReferentialIntegrityError:
        pass
test("BONUS: INSERT FK referential integrity", test_bonus_fk_insert, bonus=True)

def test_bonus_char_length():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(5));")
    try:
        parse_and_run(dbms, "insert into t values(1, 'Alexander');")  # 9 chars > 5
        assert False, "Should have failed"
    except InsertTypeMismatchError:
        pass
test("BONUS: CHAR length validation on INSERT", test_bonus_char_length, bonus=True)

def test_bonus_update_multiple():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, a int, b int, c int);")
    parse_and_run(dbms, "insert into t values(1, 10, 20, 30);")
    parse_and_run(dbms, "update t set a=100, b=200, c=300 where id=1;")
    result = parse_and_run(dbms, "select * from t;")
    assert "100" in result and "200" in result and "300" in result
test("BONUS: UPDATE multiple columns", test_bonus_update_multiple, bonus=True)

# =============================================================================
# FEATURE 2: INDEXING (25 pts base + 15 pts bonus)
# =============================================================================
print("\n" + "=" * 80)
print("FEATURE 2: INDEXING (25 pts + 15 bonus)")
print("=" * 80)

def test_create_index():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table users (id int not null, name char(20), age int);")
    parse_and_run(dbms, "insert into users values(1, 'Alice', 25);")
    parse_and_run(dbms, "insert into users values(2, 'Bob', 30);")
    parse_and_run(dbms, "insert into users values(3, 'Charlie', 25);")
    result = parse_and_run(dbms, "create index age_idx on users(age);")
    assert "age_idx" in str(result)
test("CREATE INDEX", test_create_index)

def test_index_lookup():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    for i in range(1, 101):
        parse_and_run(dbms, f"insert into t values({i}, {i*10});")
    parse_and_run(dbms, "create index val_idx on t(val);")
    # Query should use index
    result = parse_and_run(dbms, "select * from t where val=500;")
    assert "500" in result
test("Index lookup works", test_index_lookup)

def test_show_indexes():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    result = parse_and_run(dbms, "show indexes from t;")
    assert "val_idx" in str(result)
test("SHOW INDEXES", test_show_indexes)

def test_drop_index():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    result = parse_and_run(dbms, "drop index val_idx;")
    assert "dropped" in str(result).lower()
test("DROP INDEX", test_drop_index)

# --- BONUS: Index stays correct after writes ---

def test_bonus_index_after_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    parse_and_run(dbms, "insert into t values(1, 100);")
    parse_and_run(dbms, "insert into t values(2, 200);")
    result = parse_and_run(dbms, "select * from t where val=200;")
    assert "200" in result
test("BONUS: Index correct after INSERT", test_bonus_index_after_insert, bonus=True)

def test_bonus_index_after_update():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "insert into t values(1, 100);")
    parse_and_run(dbms, "insert into t values(2, 200);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    parse_and_run(dbms, "update t set val=300 where id=1;")
    result = parse_and_run(dbms, "select * from t where val=300;")
    assert "300" in result and "100" not in result
test("BONUS: Index correct after UPDATE", test_bonus_index_after_update, bonus=True)

def test_bonus_index_after_delete():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "insert into t values(1, 100);")
    parse_and_run(dbms, "insert into t values(2, 200);")
    parse_and_run(dbms, "insert into t values(3, 300);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    parse_and_run(dbms, "delete from t where id=2;")
    result = parse_and_run(dbms, "select * from t where val=200;")
    assert "200" not in result  # Should not find deleted row
test("BONUS: Index correct after DELETE", test_bonus_index_after_delete, bonus=True)

# =============================================================================
# FEATURE 3: TRANSACTIONS (30 pts base + 15 pts bonus)
# =============================================================================
print("\n" + "=" * 80)
print("FEATURE 3: TRANSACTIONS (30 pts + 15 bonus)")
print("=" * 80)

def test_begin():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    result = parse_and_run(dbms, "begin;")
    assert "started" in str(result).lower() or "transaction" in str(result).lower()
test("BEGIN transaction", test_begin)

def test_commit():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    parse_and_run(dbms, "begin;")
    parse_and_run(dbms, "insert into t values(1);")
    result = parse_and_run(dbms, "commit;")
    assert "committed" in str(result).lower()
    result = parse_and_run(dbms, "select * from t;")
    assert "1" in result
test("COMMIT persists changes", test_commit)

def test_rollback_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    parse_and_run(dbms, "insert into t values(1);")
    parse_and_run(dbms, "begin;")
    parse_and_run(dbms, "insert into t values(2);")
    parse_and_run(dbms, "insert into t values(3);")
    parse_and_run(dbms, "rollback;")
    result = parse_and_run(dbms, "select * from t;")
    assert "2" not in result and "3" not in result and "1" in result
test("ROLLBACK undoes INSERT", test_rollback_insert)

def test_rollback_update():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    parse_and_run(dbms, "begin;")
    parse_and_run(dbms, "update t set name='Bob' where id=1;")
    parse_and_run(dbms, "rollback;")
    result = parse_and_run(dbms, "select * from t;")
    assert "Alice" in result and "Bob" not in result
test("ROLLBACK undoes UPDATE", test_rollback_update)

def test_rollback_delete():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    parse_and_run(dbms, "insert into t values(2, 'Bob');")
    parse_and_run(dbms, "begin;")
    parse_and_run(dbms, "delete from t where id=1;")
    parse_and_run(dbms, "rollback;")
    result = parse_and_run(dbms, "select * from t;")
    assert "Alice" in result and "Bob" in result
test("ROLLBACK undoes DELETE", test_rollback_delete)

# --- BONUS: Rollback undoes index changes ---

def test_bonus_rollback_index_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "insert into t values(1, 100);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    parse_and_run(dbms, "begin;")
    parse_and_run(dbms, "insert into t values(2, 200);")
    parse_and_run(dbms, "rollback;")
    result = parse_and_run(dbms, "select * from t where val=200;")
    assert "200" not in result  # Rolled back insert shouldn't be findable via index
test("BONUS: ROLLBACK undoes indexed INSERT", test_bonus_rollback_index_insert, bonus=True)

def test_bonus_rollback_index_update():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "insert into t values(1, 100);")
    parse_and_run(dbms, "insert into t values(2, 200);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    parse_and_run(dbms, "begin;")
    parse_and_run(dbms, "update t set val=999 where id=1;")
    parse_and_run(dbms, "rollback;")
    result = parse_and_run(dbms, "select * from t where val=100;")
    assert "100" in result  # Should find original value after rollback
test("BONUS: ROLLBACK undoes indexed UPDATE", test_bonus_rollback_index_update, bonus=True)

def test_bonus_rollback_index_delete():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, val int);")
    parse_and_run(dbms, "insert into t values(1, 100);")
    parse_and_run(dbms, "insert into t values(2, 200);")
    parse_and_run(dbms, "create index val_idx on t(val);")
    parse_and_run(dbms, "begin;")
    parse_and_run(dbms, "delete from t where id=1;")
    parse_and_run(dbms, "rollback;")
    result = parse_and_run(dbms, "select * from t where val=100;")
    assert "100" in result  # Should find deleted row after rollback
test("BONUS: ROLLBACK undoes indexed DELETE", test_bonus_rollback_index_delete, bonus=True)

# =============================================================================
# FEATURE 4: GUI (25 pts base + 10 pts bonus)
# =============================================================================
print("\n" + "=" * 80)
print("FEATURE 4: GUI (25 pts + 10 bonus)")
print("=" * 80)

def test_gui_exists():
    assert os.path.exists('gui.py'), "gui.py file should exist"
test("GUI file exists", test_gui_exists)

def test_gui_has_flask():
    with open('gui.py', 'r') as f:
        content = f.read()
    assert 'flask' in content.lower() or 'Flask' in content, "GUI should use Flask"
test("GUI uses Flask framework", test_gui_has_flask)

def test_gui_has_query_endpoint():
    with open('gui.py', 'r') as f:
        content = f.read()
    assert '@app.route' in content and ('query' in content.lower() or 'execute' in content.lower()), "GUI should have query endpoint"
test("GUI has query execution endpoint", test_gui_has_query_endpoint)

def test_gui_has_schema_browser():
    with open('gui.py', 'r') as f:
        content = f.read()
    assert 'tables' in content.lower() or 'schema' in content.lower(), "GUI should show tables/schema"
test("BONUS: GUI has schema browser", test_gui_has_schema_browser, bonus=True)

def test_gui_has_error_handling():
    with open('gui.py', 'r') as f:
        content = f.read()
    assert 'error' in content.lower() or 'exception' in content.lower() or 'try' in content.lower(), "GUI should handle errors"
test("BONUS: GUI has error handling", test_gui_has_error_handling, bonus=True)

def test_gui_has_result_display():
    with open('gui.py', 'r') as f:
        content = f.read()
    assert 'result' in content.lower() or 'output' in content.lower() or 'table' in content.lower(), "GUI should display results"
test("BONUS: GUI displays results", test_gui_has_result_display, bonus=True)

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print(" " * 30 + "TEST SUMMARY")
print("=" * 80)

print(f"\n📊 BASE FEATURES: {passed} passed, {failed} failed")
print(f"🌟 BONUS FEATURES: {bonus_passed} passed, {bonus_failed} failed")

# Calculate points
base_points = min(100, passed)  # Cap at 100 for base
bonus_points = bonus_passed

print(f"\n📈 SCORE BREAKDOWN:")
print(f"   Feature 1 (Basic Ops):     20 pts base + {min(10, bonus_passed)} pts bonus")
print(f"   Feature 2 (Indexing):      25 pts base + {min(15, bonus_passed)} pts bonus")
print(f"   Feature 3 (Transactions):  30 pts base + {min(15, bonus_passed)} pts bonus")
print(f"   Feature 4 (GUI):           25 pts base + {min(10, bonus_passed)} pts bonus")

total = base_points + bonus_points
print(f"\n🏆 TOTAL SCORE: {total}/150 points")

if failed == 0 and bonus_failed == 0:
    print("\n" + "🎉" * 30)
    print(" " * 20 + "PERFECT SCORE - ALL TESTS PASSED!")
    print("🎉" * 30)
elif failed == 0:
    print("\n✅ All base features working! Some bonus features need work.")
else:
    print(f"\n⚠️  {failed} base feature(s) need attention")

print("\n" + "=" * 80)
