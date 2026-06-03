from lark import Lark
from sql_transformer import SQLTransformer

with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

t = SQLTransformer()
parsed = parser.parse('create index val_idx on t(val);')
result = t.transform(parsed)
print('Full result:', result)
print('Statement:', t.statement)
print('Table:', t.table)
