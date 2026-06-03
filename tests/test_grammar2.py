from lark import Lark
import traceback
try:
    with open('grammar.lark') as f:
        Lark(f.read(), start='command', lexer='basic')
    print('Grammar OK')
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()
