from lark import Lark
with open('grammar.lark') as f:
    parser = Lark(f.read(), start='command', lexer='basic')

# Try different date formats
tests = [
    "INSERT INTO students VALUES(1, 'Alice', 'Anderson', 'alice@uni.edu', '2003-05-15', 2022, 'Computer Science', '3.85');",
    "INSERT INTO students VALUES(1, 'Alice', 'Anderson', 'alice@uni.edu', DATE '2003-05-15', 2022, 'Computer Science', '3.85');",
    "INSERT INTO students VALUES(1, 'Alice', 'Anderson', 'alice@uni.edu', '20030515', 2022, 'Computer Science', '3.85');",
]
for t in tests:
    try:
        parser.parse(t)
        print(f'OK: {t[:60]}...')
    except Exception as e:
        print(f'FAIL: {str(e)[:80]}')
