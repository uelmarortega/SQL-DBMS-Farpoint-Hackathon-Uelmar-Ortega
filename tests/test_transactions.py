#!/usr/bin/env python3
from lark import Lark
from sql_transformer import SQLTransformer
from dbms import DBMS
import shutil
import os

# Clean DB directory
if os.path.exists('DB'):
    shutil.rmtree('DB')

dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def run_query(query):
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    statement, table, record, tables, select_columns, where = result
    
    print(f"> {query}")
    if statement == "create table":
        print(f"  {dbms.create_table(table)}")
    elif statement == "insert":
        print(f"  {dbms.insert(table, record)}")
    elif statement == "select":
        print(dbms.select(tables, select_columns, where))
    elif statement == "update":
        print(f"  {dbms.update(table['table_name'], table['assignments'], where)}")
    elif statement == "delete":
        result, extra = dbms.delete(table["table_name"], where)
        print(f"  {result}")
    elif statement == "begin":
        print(f"  {dbms.begin_transaction()}")
    elif statement == "commit":
        print(f"  {dbms.commit_transaction()}")
    elif statement == "rollback":
        print(f"  {dbms.rollback_transaction()}")
    print()

# Test 1: Basic transaction with rollback
print("=== Test 1: ROLLBACK ===")
run_query("create table test (id int not null, name char(20));")
run_query("insert into test values(1, 'Alice');")
run_query("select * from test;")
run_query("begin;")
run_query("insert into test values(2, 'Bob');")
run_query("insert into test values(3, 'Charlie');")
run_query("select * from test;")
run_query("rollback;")
run_query("select * from test;")  # Should only show Alice

# Test 2: Transaction with commit
print("\n=== Test 2: COMMIT ===")
dbms2 = DBMS()
if os.path.exists('DB'):
    shutil.rmtree('DB')

def run_query2(query):
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    statement, table, record, tables, select_columns, where = result
    
    print(f"> {query}")
    if statement == "create table":
        print(f"  {dbms2.create_table(table)}")
    elif statement == "insert":
        print(f"  {dbms2.insert(table, record)}")
    elif statement == "select":
        print(dbms2.select(tables, select_columns, where))
    elif statement == "begin":
        print(f"  {dbms2.begin_transaction()}")
    elif statement == "commit":
        print(f"  {dbms2.commit_transaction()}")
    print()

run_query2("create table test2 (id int not null, name char(20));")
run_query2("insert into test2 values(1, 'Alice');")
run_query2("begin;")
run_query2("insert into test2 values(2, 'Bob');")
run_query2("commit;")
run_query2("select * from test2;")  # Should show both

# Test 3: UPDATE rollback
print("\n=== Test 3: UPDATE ROLLBACK ===")
dbms3 = DBMS()
if os.path.exists('DB'):
    shutil.rmtree('DB')

def run_query3(query):
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    statement, table, record, tables, select_columns, where = result
    
    print(f"> {query}")
    if statement == "create table":
        print(f"  {dbms3.create_table(table)}")
    elif statement == "insert":
        print(f"  {dbms3.insert(table, record)}")
    elif statement == "select":
        print(dbms3.select(tables, select_columns, where))
    elif statement == "update":
        print(f"  {dbms3.update(table['table_name'], table['assignments'], where)}")
    elif statement == "begin":
        print(f"  {dbms3.begin_transaction()}")
    elif statement == "rollback":
        print(f"  {dbms3.rollback_transaction()}")
    print()

run_query3("create table test3 (id int not null, name char(20));")
run_query3("insert into test3 values(1, 'Alice');")
run_query3("insert into test3 values(2, 'Bob');")
run_query3("select * from test3;")
run_query3("begin;")
run_query3("update test3 set name='Charlie' where id=1;")
run_query3("select * from test3;")  # Shows Charlie
run_query3("rollback;")
run_query3("select * from test3;")  # Should show Alice again
