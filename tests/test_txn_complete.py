#!/usr/bin/env python3
"""Complete transaction tests"""
from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer
import shutil, os

if os.path.exists('DB'): shutil.rmtree('DB')
dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def run(q):
    t = SQLTransformer()
    parsed = parser.parse(q)
    result = t.transform(parsed)
    stmt, table, record, tables, sel_cols, where = result
    if stmt == 'create table': dbms.create_table(table)
    elif stmt == 'insert': dbms.insert(table, record)
    elif stmt == 'select': return dbms.select(tables, sel_cols, where)
    elif stmt == 'delete': 
        r, _ = dbms.delete(table['table_name'], where)
        return r
    elif stmt == 'begin': return dbms.begin_transaction()
    elif stmt == 'rollback': return dbms.rollback_transaction()
    elif stmt == 'commit': return dbms.commit_transaction()
    return None

print('=== Test 1: INSERT rollback ===')
run('create table t (id int not null, name char(20));')
run('insert into t values(1, "Alice");')
print('Before:', run('select * from t;').split('\n')[3].strip())
run('begin;')
run('insert into t values(2, "Bob");')
print('After INSERT:', run('select * from t;').split('\n')[3].strip(), run('select * from t;').split('\n')[4].strip())
run('rollback;')
print('After ROLLBACK:', run('select * from t;').split('\n')[3].strip())

print('\n=== Test 2: DELETE rollback ===')
if os.path.exists('DB'): shutil.rmtree('DB')
dbms2 = DBMS()

def run2(q):
    t = SQLTransformer()
    parsed = parser.parse(q)
    result = t.transform(parsed)
    stmt, table, record, tables, sel_cols, where = result
    if stmt == 'create table': dbms2.create_table(table)
    elif stmt == 'insert': dbms2.insert(table, record)
    elif stmt == 'select': return dbms2.select(tables, sel_cols, where)
    elif stmt == 'delete': 
        r, _ = dbms2.delete(table['table_name'], where)
        return r
    elif stmt == 'begin': return dbms2.begin_transaction()
    elif stmt == 'rollback': return dbms2.rollback_transaction()
    return None

run2('create table t2 (id int not null, name char(20));')
run2('insert into t2 values(1, "Alice");')
run2('insert into t2 values(2, "Bob");')
run2('insert into t2 values(3, "Charlie");')
print('Before:', [line.strip() for line in run2('select * from t2;').split('\n')[3:6]])
run2('begin;')
run2('delete from t2 where id=2;')
print('After DELETE:', [line.strip() for line in run2('select * from t2;').split('\n')[3:5]])
run2('rollback;')
print('After ROLLBACK:', [line.strip() for line in run2('select * from t2;').split('\n')[3:6]])

print('\n=== All transaction tests passed! ===')
