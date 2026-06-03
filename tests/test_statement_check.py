from lark import Lark
from sql_transformer import SQLTransformer

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

tests = [
    "insert into t values(1);",
    "delete from t;",
    "select * from t;",
    "update t set x=1;",
    "create table t (x int);",
    "drop table t;",
]

for query in tests:
    t = SQLTransformer()
    parsed = parser.parse(query)
    result = t.transform(parsed)
    print(f"{query:35s} -> statement='{result[0]}'")
