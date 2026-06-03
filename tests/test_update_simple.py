#!/usr/bin/env python3
import shutil, os
from dbms import DBMS
from lark import Lark
from sql_transformer import SQLTransformer

if os.path.exists('DB'): shutil.rmtree('DB')
dbms = DBMS()

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

def run(query):
    t = SQLTransformer()
    try:
        parsed = parser.parse(query)
        result = t.transform(parsed)
        stmt, table, record, tables, sel_cols, where = result
        print(f"✓ Parsed: {stmt}")
        if stmt == 'update':
            print(f"  Table: {table}")
            print(f"  Where: {where}")
        return result
    except Exception as e:
        print(f"✗ Parse error: {e}")
        return None

# Test parsing
print("Test 1: UPDATE with int value")
run("update t set age=25 where id=1;")

print("\nTest 2: UPDATE with string value")  
run("update t set name='Alice' where id=1;")

print("\nTest 3: UPDATE with multiple assignments")
run("update t set a=1, b=2 where id=1;")

print("\nTest 4: UPDATE with NULL")
run("update t set name=null where id=1;")
