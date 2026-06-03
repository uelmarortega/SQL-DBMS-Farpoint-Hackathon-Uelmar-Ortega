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

queries = [
    "create table test_update (id int not null, name char(20));",
    "insert into test_update values(1, 'Alice');",
    "insert into test_update values(2, 'Bob');",
]

for query in queries:
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    statement, table, record, tables, select_columns, where = result
    
    print(f"=== {statement} ===")
    if statement == "create table":
        print(dbms.create_table(table))
    elif statement == "insert":
        print(dbms.insert(table, record))

# Now test UPDATE directly
print("\n=== Testing UPDATE directly ===")
result = dbms.update("test_update", [("name", "Charlie")], {'op': '=', 'left_operand': (None, 'id'), 'right_operand': (1,)})
print(f"Update result: {result}")

# Check data
print("\n=== Select after update ===")
t = SQLTransformer()
parsed = parser.parse("select * from test_update;")
result = t.transform(parsed)
statement, table, record, tables, select_columns, where = result
print(dbms.select(tables, select_columns, where))
