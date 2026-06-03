from lark import Lark
with open('grammar.lark') as f:
    Lark(f.read(), start='command', lexer='basic')
print('Grammar OK')
