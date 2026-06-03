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
    print(f'Statement: {stmt}')
    print(f'Table: {table}')
    
    if stmt == 'create table':
        dbms.create_table(table)
        print('Created table')
    elif stmt == 'create index':
        r = dbms.create_index(table['table_name'], table['column_name'], table['index_name'])
        print(f'Index result: {r}')
    elif stmt == 'show indexes':
        r = dbms.show_indexes(table['table_name'])
        print(f'Show result: {r}')
    elif stmt == 'drop index':
        r = dbms.drop_index(table['index_name'])
        print(f'Drop result: {r}')
    print()

run('create table t (id int not null, val int);')
run('create index val_idx on t(val);')
run('show indexes from t;')
run('drop index val_idx;')
run('show indexes from t;')
