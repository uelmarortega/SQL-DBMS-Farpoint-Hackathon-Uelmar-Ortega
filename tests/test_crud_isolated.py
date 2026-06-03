#!/usr/bin/env python3
"""
Isolated CRUD Tests - Each test uses fresh DB
"""

import shutil, os
from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer
from messages import *

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
    return None

print("=" * 70)
print("ISOLATED CRUD OPERATIONS TEST")
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

# CREATE
def test_create():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    result = parse_and_run(dbms, "select * from t;")
    assert "ID" in result
test("CREATE TABLE", test_create)

# INSERT
def test_insert():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    result = parse_and_run(dbms, "select * from t;")
    assert "Alice" in result
test("INSERT row", test_insert)

# INSERT type check
def test_insert_type():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    try:
        parse_and_run(dbms, "insert into t values('bad');")
        assert False
    except InsertTypeMismatchError:
        pass
test("INSERT type checking", test_insert_type)

# INSERT NOT NULL
def test_insert_notnull():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    try:
        parse_and_run(dbms, "insert into t values(null);")
        assert False
    except InsertColumnNonNullableError:
        pass
test("INSERT NOT NULL check", test_insert_notnull)

# INSERT PK duplicate
def test_insert_pkdup():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, primary key(id));")
    parse_and_run(dbms, "insert into t values(1);")
    try:
        parse_and_run(dbms, "insert into t values(1);")
        assert False
    except InsertDuplicatePrimaryKeyError:
        pass
test("INSERT PK duplicate", test_insert_pkdup)

# INSERT FK check
def test_insert_fk():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table parent (id int not null, primary key(id));")
    parse_and_run(dbms, "create table child (pid int, foreign key(pid) references parent(id));")
    parse_and_run(dbms, "insert into parent values(1);")
    try:
        parse_and_run(dbms, "insert into child values(999);")
        assert False
    except InsertReferentialIntegrityError:
        pass
test("INSERT FK referential", test_insert_fk)

# SELECT
def test_select():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    parse_and_run(dbms, "insert into t values(2, 'Bob');")
    result = parse_and_run(dbms, "select * from t;")
    assert "Alice" in result and "Bob" in result
test("SELECT all rows", test_select)

# SELECT WHERE
def test_select_where():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    parse_and_run(dbms, "insert into t values(1);")
    parse_and_run(dbms, "insert into t values(2);")
    result = parse_and_run(dbms, "select * from t where id=1;")
    assert "1" in result and "2" not in result
test("SELECT with WHERE", test_select_where)

# UPDATE
def test_update():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    parse_and_run(dbms, "update t set name='Bob' where id=1;")
    result = parse_and_run(dbms, "select * from t;")
    assert "Bob" in result and "Alice" not in result
test("UPDATE basic", test_update)

# UPDATE type check
def test_update_type():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20));")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    try:
        parse_and_run(dbms, "update t set name=123 where id=1;")
        assert False
    except InsertTypeMismatchError:
        pass
test("UPDATE type checking", test_update_type)

# UPDATE NOT NULL
def test_update_notnull():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(20) not null);")
    parse_and_run(dbms, "insert into t values(1, 'Alice');")
    try:
        parse_and_run(dbms, "update t set name=null where id=1;")
        assert False
    except InsertColumnNonNullableError:
        pass
test("UPDATE NOT NULL check", test_update_notnull)

# UPDATE PK duplicate
def test_update_pkdup():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, primary key(id));")
    parse_and_run(dbms, "insert into t values(1);")
    parse_and_run(dbms, "insert into t values(2);")
    try:
        parse_and_run(dbms, "update t set id=2 where id=1;")
        assert False
    except InsertDuplicatePrimaryKeyError:
        pass
test("UPDATE PK uniqueness", test_update_pkdup)

# DELETE
def test_delete():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null);")
    parse_and_run(dbms, "insert into t values(1);")
    parse_and_run(dbms, "insert into t values(2);")
    parse_and_run(dbms, "delete from t where id=1;")
    result = parse_and_run(dbms, "select * from t;")
    assert "1" not in result and "2" in result
test("DELETE basic", test_delete)

# DELETE FK
def test_delete_fk():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table parent (id int not null, primary key(id));")
    parse_and_run(dbms, "create table child (pid int, foreign key(pid) references parent(id));")
    parse_and_run(dbms, "insert into parent values(1);")
    parse_and_run(dbms, "insert into child values(1);")
    result = parse_and_run(dbms, "delete from parent where id=1;")
    # Should be blocked or return 0 deleted
    assert "0" in str(result) or "not deleted" in str(result).lower()
test("DELETE FK referential", test_delete_fk)

# CHAR length
def test_charlen():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table t (id int not null, name char(5));")
    try:
        parse_and_run(dbms, "insert into t values(1, 'Alexander');")
        assert False
    except InsertTypeMismatchError:
        pass
test("CHAR length validation", test_charlen)

# SHOW TABLES
def test_show():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table mytable (id int);")
    result = parse_and_run(dbms, "show tables;")
    assert result is not None
test("SHOW TABLES", test_show)

# DESCRIBE
def test_describe():
    dbms = fresh_dbms()
    parse_and_run(dbms, "create table mytable (id int, name char(20));")
    result = parse_and_run(dbms, "describe mytable;")
    assert "ID" in result
test("DESCRIBE table", test_describe)

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 70)

if failed == 0:
    print("\n🎉 ALL CRUD OPERATIONS WORK PERFECTLY! ✅\n")
else:
    print(f"\n⚠️  {failed} test(s) failed\n")
