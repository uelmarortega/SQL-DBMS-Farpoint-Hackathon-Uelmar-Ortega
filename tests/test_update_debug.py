from lark import Lark
from sql_transformer import SQLTransformer

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

t = SQLTransformer()
query = "update test_update set name='Charlie' where id=1;"
parsed = parser.parse(query)
result = t.transform(parsed)
print('Statement:', repr(result[0]))
print('Table:', result[1])
print('Record:', result[2])
print('Tables:', result[3])
print('Select cols:', result[4])
print('Where:', result[5])
