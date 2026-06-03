#!/usr/bin/env python3
"""Test indexing"""
from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer
import shutil, os

if os.path.exists('DB'): shutil.rmtree('DB')
if os.path.exists('DB_INDEXES'): shutil.rmtree('DB_INDEXES')

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
    elif stmt == 'create index': return dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
    elif stmt == 'show indexes': return dbms.show_indexes(table['table_name'])
    elif stmt == 'drop index': return dbms.drop_index(table['index_name'])
    return None

print('=== Test Indexing ===')
run('create table users (id int not null, name char(20), age int);')
run('insert into users values(1, "Alice", 25);')
run('insert into users values(2, "Bob", 30);')
run('insert into users values(3, "Charlie", 25);')
run('insert into users values(4, "Diana", 35);')

print('Before index:')
print(run('select * from users;'))

print('\nCreating index on age column...')
print(run('create index age_idx on users(age);'))

print('\nShowing indexes:')
print(run('show indexes from users;'))

print('\nSelect users where age=25 (should use index):')
print(run('select * from users;'))

print('\n=== Index test complete ===')
