#!/usr/bin/env python3
"""Simple transaction test"""
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

def run_query(query, show_select=True):
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    statement, table, record, tables, select_columns, where = result
    
    print(f"> {query}")
    if statement == "create table":
        print(f"  {dbms.create_table(table)}")
    elif statement == "insert":
        print(f"  {dbms.insert(table, record)}")
    elif statement == "select" and show_select:
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

print("=== Test: UPDATE with ROLLBACK ===")
run_query("create table test (id int not null, name char(20));")
run_query("insert into test values(1, 'Alice');")
run_query("insert into test values(2, 'Bob');")
print("Before UPDATE:")
run_query("select * from test;")

run_query("begin;")
run_query("update test set name='Charlie' where id=1;")
print("After UPDATE (before rollback):")
run_query("select * from test;")

run_query("rollback;")
print("After ROLLBACK:")
run_query("select * from test;")

print("\n=== Test: DELETE with ROLLBACK ===")
if os.path.exists('DB'):
    shutil.rmtree('DB')
dbms2 = DBMS()

def run_query2(query, show_select=True):
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    statement, table, record, tables, select_columns, where = result
    
    print(f"> {query}")
    if statement == "create table":
        print(f"  {dbms2.create_table(table)}")
    elif statement == "insert":
        print(f"  {dbms2.insert(table, record)}")
    elif statement == "select" and show_select:
        print(dbms2.select(tables, select_columns, where))
    elif statement == "delete":
        result, extra = dbms2.delete(table["table_name"], where)
        print(f"  {result}")
    elif statement == "begin":
        print(f"  {dbms2.begin_transaction()}")
    elif statement == "rollback":
        print(f"  {dbms2.rollback_transaction()}")
    print()

run_query2("create table test2 (id int not null, name char(20));")
run_query2("insert into test2 values(1, 'Alice');")
run_query2("insert into test2 values(2, 'Bob');")
run_query2("insert into test2 values(3, 'Charlie');")
print("Before DELETE:")
run_query2("select * from test2;")

run_query2("begin;")
run_query2("delete from test2 where id=2;")
print("After DELETE (before rollback):")
run_query2("select * from test2;")

run_query2("rollback;")
print("After ROLLBACK:")
run_query2("select * from test2;")
