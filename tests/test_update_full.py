#!/usr/bin/env python3
from lark import Lark
from sql_transformer import SQLTransformer
from dbms import DBMS

dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

queries = [
    "create table test_update (id int not null, name char(20));",
    "insert into test_update values(1, 'Alice');",
    "insert into test_update values(2, 'Bob');",
    "update test_update set name='Charlie' where id=1;",
    "select * from test_update;",
]

for query in queries:
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    statement, table, record, tables, select_columns, where = result
    
    print(f"\n=== {statement} ===")
    if statement == "create table":
        print(dbms.create_table(table))
    elif statement == "insert":
        print(dbms.insert(table, record))
    elif statement == "update":
        print(dbms.update(table["table_name"], table["assignments"], where))
    elif statement == "select":
        print(dbms.select(tables, select_columns, where))
