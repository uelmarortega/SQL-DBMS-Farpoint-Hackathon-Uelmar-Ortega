from pathlib import Path
from typing import Dict, List
import itertools
from collections import Counter
from copy import deepcopy

from db_model import Table, Record, DB, MetaDB
from utils import *
from messages import *
from index_manager import IndexManager



class DBMS:
    def __init__(self):
        self.db_dir = Path("./DB")
        self.db_dir.mkdir(exist_ok=True)
        self.meta_db = MetaDB()
        self.index_manager = IndexManager()
        
        # Transaction support
        self.in_transaction = False
        self.undo_log = []  # Stack of (operation, reverse_data) tuples
        self.transaction_changes = []  # List of changes in current transaction
        
        
    def create_table(self, table_dict: dict):
        table_name = table_dict["table_name"]
        column_list = table_dict["column_list"]
        not_null_key_set = table_dict["not_null_key_set"]
        primary_key_list = table_dict["primary_key_list"]
        foreign_key_dict = table_dict["foreign_key_dict"]

        # Error within the table info
        if len(set([column_name for column_name, _ in column_list])) < len(column_list):
            raise DuplicateColumnDefError()
        columns = {column_name: column_type for column_name, column_type in column_list}
        
        for data_type in columns.values():
            if data_type.startswith("char"):
                if eval_char_max_len(data_type) < 1:  # hardcoding
                    raise CharLengthError()
        
        if len(primary_key_list) > 1:
            raise DuplicatePrimaryKeyDefError()
        elif len(primary_key_list) == 0:
            primary_key = None
        else:
            primary_key = primary_key_list[0]
            for key in primary_key:
                if key not in columns:
                    raise NonExistingColumnDefError(key)
            not_null_key_set.update(primary_key)
        
        if foreign_key_dict:
            for foreign_key in foreign_key_dict:
                if foreign_key not in columns:
                    raise NonExistingColumnDefError(foreign_key)   

        # Error within the database
        self.meta_db.open_db()
        
        table_key = self.meta_db.create_key_from_value(table_name)
        if self.meta_db.exists(table_key):
            raise TableExistenceError()
        
        if foreign_key_dict:
            for foreign_key, (referenced_table_name, referenced_key) in foreign_key_dict.items():
                referenced_table_key = self.meta_db.create_key_from_value(referenced_table_name)
                referenced_table = self.meta_db.get(referenced_table_key)
                if not referenced_table:
                    raise ReferenceTableExistenceError()
                if referenced_key not in referenced_table:
                    raise ReferenceColumnExistenceError()
                if not referenced_table.check_reference_primary_key(referenced_key):
                    raise ReferenceNonPrimaryKeyError()
                foreign_key_type = columns[foreign_key]
                if not referenced_table.check_reference_type(foreign_key_type, referenced_key):
                    raise ReferenceTypeError()
                referenced_table.add_reference(table_name)
                # update referenced table info
                self.meta_db.put(referenced_table_key, referenced_table)
        
        table = Table(
            table_name=table_name,
            columns=columns,
            not_null_keys=not_null_key_set,
            primary_key=primary_key,
            foreign_keys=foreign_key_dict
        )
        # add table info to meta db
        self.meta_db.put(table_key, table)
        self.meta_db.close_db()
        
        # create table db
        table_db = DB(table_name)
        table_db.open_db()
        table_db.close_db()
        
        return CreateTableSuccess(table_name)
    
    
    def drop_table(self, table_name: str):
        # remove table info
        self.meta_db.open_db()
        table_key = self.meta_db.create_key_from_value(table_name)
        table = self.meta_db.get(table_key)
        if not table:
            raise NoSuchTable()
        if table.has_reference():
            raise DropReferencedTableError(table_name)
        referencing_tables = table.get_referencing_tables()
        if referencing_tables:
            for referencing_table in referencing_tables:
                referencing_table_key = self.meta_db.create_key_from_value(referencing_table)
                referencing_table_db = self.meta_db.get(referencing_table_key)
                referencing_table_db.remove_reference(table_name)
                self.meta_db.put(referencing_table_key, referencing_table_db)
        self.meta_db.delete(table_key)
        
        # remove table records (delete all backend files, see DB.remove_files)
        DB(table_name).remove_files()
        self.meta_db.close_db()
        
        return DropSuccess(table_name)
    
    
    def explain_describe_desc(self, table_name: str):
        self.meta_db.open_db()
        table_key = self.meta_db.create_key_from_value(table_name)
        table = self.meta_db.get(table_key)
        if not table:
            raise NoSuchTable()
        self.meta_db.close_db()
        return table
    
    
    def show_tables(self):
        self.meta_db.open_db()
        output = "\n------------------------\n"
        all_tables = self.meta_db.keys()
        for table_key in all_tables:
            output += table_key.decode() + "\n"
        output += "------------------------"
        self.meta_db.close_db()
        return output
    
    
    def insert(self, table_dict: dict, records_list: list):
        """Insert one or multiple records. records_list is a list of value tuples."""
        table_name = table_dict["table_name"]
        column_name_list = table_dict.get("column_name_list")
        
        self.meta_db.open_db()
        table_key = self.meta_db.create_key_from_value(table_name)
        table = self.meta_db.get(table_key)
        if not table:
            raise NoSuchTable()
        self.meta_db.close_db()
        
        # Ensure records_list is a list of records
        if records_list and not isinstance(records_list[0], list):
            records_list = [records_list]
        
        for value_list in records_list:
            if column_name_list:
                if len(column_name_list) != len(value_list):
                    raise InsertTypeMismatchError()
                for column_name in column_name_list:
                    if column_name not in table:
                        raise InsertColumnExistenceError(column_name)
                    
            if len(table.columns.keys()) != len(value_list):
                raise InsertTypeMismatchError()
            
            for column_name, value in zip(table.columns.keys(), value_list):
                if value is None and column_name in table.not_null_keys:
                    raise InsertColumnNonNullableError(column_name)
            
            if not all([is_valid_type(data_type, value) for data_type, value in zip(table.columns.values(), value_list)]):
                raise InsertTypeMismatchError()
            
            data = {}
            primary_value = []
            referencing = dict()
            for (column_name, data_type), value in zip(table.columns.items(), value_list):
                if data_type.startswith("char") and value is not None:
                    max_len = eval_char_max_len(data_type)
                    value = value[:max_len]
                if table.primary_key and column_name in table.primary_key:  # may be composite primary key
                    primary_value.append(value)
                if table.foreign_keys and column_name in table.foreign_keys:  # one foreign key per column
                    referenced_table_name, referenced_column_name = table.foreign_keys[column_name]
                    # get referenced table schema
                    self.meta_db.open_db()
                    referenced_table_key = self.meta_db.create_key_from_value(referenced_table_name)
                    referenced_table = self.meta_db.get(referenced_table_key)
                    self.meta_db.close_db()
                    # get referenced record
                    referenced_table_db = DB(referenced_table_name)
                    referenced_table_db.open_db()
                    referenced_key = referenced_table_db.create_key_from_value((value,))
                    referenced_record = None
                    if len(referenced_table.primary_key) == 1:
                        referenced_record = referenced_table_db.get(referenced_key)
                    else:  # composite primary key
                        all_primary_values = referenced_table_db.keys()
                        for primary_value in all_primary_values:
                            if referenced_key.decode() in primary_value.decode():
                                referenced_record = referenced_table_db.get(primary_value)
                                break
                    if referenced_record is None:
                        raise InsertReferentialIntegrityError()
                    referencing[(referenced_table_name, referenced_column_name)] = {referenced_record.data[referenced_column_name]}
                    assert referenced_record.data[referenced_column_name] == value
                    referenced_record.add_to_referenced_by(table_name, column_name, value)
                    referenced_table_db.put(referenced_key, referenced_record)
                    referenced_table_db.close_db()
                data[column_name] = value
            primary_value = tuple(primary_value) if primary_value else None
            record = Record(table_name, data, primary_value, referencing)
            
            table_db = DB(table_name)
            table_db.open_db()
            record_key = table_db.create_key_from_value(primary_value) if primary_value else table_db.create_random_key()
            if table_db.exists(record_key):
                table_db.close_db()
                raise InsertDuplicatePrimaryKeyError()
            
            # Log for rollback
            self._log_change("INSERT", table_name, record_key, None)
            
            table_db.put(record_key, record)
            table_db.close_db()
        
        return InsertResult()

    
    def delete(self, table_name: str, where_clause: str):
        self.meta_db.open_db()
        table_key = self.meta_db.create_key_from_value(table_name)
        table = self.meta_db.get(table_key)
        if not table:
            raise NoSuchTable()
        self.meta_db.close_db()
        
        table_db = DB(table_name)
        table_db.open_db()
        outer_cursor = table_db.create_cursor()
        
        success_cnt = 0
        fail_cnt = 0
        key_value_pair = outer_cursor.first()
        while key_value_pair:
            key, value = key_value_pair
            record = Record.deserialize(value)
            satisfies = self._evaluate_condition(deepcopy(where_clause), [table], record.data) if where_clause else True
            if satisfies == True:
                if list(record.referenced_by.values()):
                    fail_cnt += 1
                else:
                    # Log for rollback (before deletion)
                    self._log_change("DELETE", table_name, key, record.data.copy())
                    
                    if record.referencing:
                        for (referenced_table_name, referenced_column_name), referenced_value_set in record.referencing.items():
                            for referenced_value in referenced_value_set:
                                referenced_table_db = DB(referenced_table_name)
                                referenced_table_db.open_db()
                                inner_cursor = referenced_table_db.create_cursor()
                                key_value_pair = inner_cursor.first()
                                while key_value_pair:
                                    key, value = key_value_pair
                                    referenced_record = Record.deserialize(value)
                                    for column in table.columns:
                                        if ((table_name, column) in referenced_record.referenced_by and 
                                            referenced_value in referenced_record.referenced_by[(table_name, column)]):
                                            referenced_record.remove_referenced_by(table_name, column, referenced_value)
                                            referenced_table_db.put(key, referenced_record)  # update reference
                                    key_value_pair = inner_cursor.next()
                                referenced_table_db.discard_cursor(inner_cursor)
                                referenced_table_db.close_db()
                    table_db.delete_by_cursor(outer_cursor)
                    success_cnt += 1
            key_value_pair = outer_cursor.next()
            
        table_db.discard_cursor(outer_cursor)
        table_db.close_db()
        
        return DeleteResult(success_cnt), DeleteReferentialIntegrityPassed(fail_cnt) if fail_cnt else None
        
    
    def _evaluate_condition(self, condition, table_list: List[Table], record: dict):
        def get_record_value(operand):
            table_name, column_name = operand
            if table_name and not any([table_name == table.table_name for table in table_list]):
                raise WhereTableNotSpecified()
            found_tables = [table for table in table_list if column_name in table]
            if len(found_tables) < 1:
                raise WhereColumnNotExist()
            elif len(found_tables) > 1:
                if not table_name:  # column name is ambiguous
                    raise WhereAmbiguousReference()
                table = next(table for table in found_tables if table_name == table.table_name)
            else:
                table = found_tables[0]
            if table_name and table_name != table.table_name:
                raise WhereColumnNotExist()
            if table_name:
                prefixed_column_name = f"{table_name}.{column_name}"
                if prefixed_column_name in record:
                    return record[prefixed_column_name]
            return record[column_name]
        
        def determine_operand_value(operand):
            if operand is None:
                value = operand
            elif len(operand) == 1:  # comparable_value
                value = operand[0]
            else:  # table_name, column_name
                value = get_record_value(operand)
            return value
            
        op = condition["op"]
        if op in comparison_op_map | null_op_map:
            op, left_operand, right_operand = map(condition.get, ["op", "left_operand", "right_operand"])
            left_value = determine_operand_value(left_operand)
            right_value = determine_operand_value(right_operand)
            
            if op in comparison_op_map and is_comparable(left_value, right_value) == False:
                raise WhereIncomparableError()
            
            if op in comparison_op_map:
                if left_value is None or right_value is None:
                    output = UNKNOWN
                else:
                    output = comparison_op_map[op](left_value, right_value)
            else:
                output = null_op_map[op](left_value, right_value)
            return output
            
        elif op == "not":
            boolean_test = condition["boolean_test"]
            return not_(self._evaluate_condition(boolean_test, table_list, record))
        
        elif op == "and":
            boolean_factors = condition["boolean_factors"]
            return and_(*[self._evaluate_condition(boolean_factor, table_list, record) for boolean_factor in boolean_factors])
        
        elif op == "or":
            boolean_terms = condition["boolean_terms"]
            return or_(*[self._evaluate_condition(boolean_term, table_list, record) for boolean_term in boolean_terms])
        
        else:  # None
            _, remaining_condition = condition.popitem()  # "boolean_terms", "boolean_factors", "boolean_test"
            if remaining_condition is not None:
                return self._evaluate_condition(remaining_condition, table_list, record)
    
    
    def select(self, tables: list, select_columns: list, where_clause: dict):
        table_list = []
        self.meta_db.open_db()
        for table_name in tables:
            table_key = self.meta_db.create_key_from_value(table_name)
            table = self.meta_db.get(table_key)
            if not table:
                raise SelectTableExistenceError(table_name)
            table_list.append(table)
        self.meta_db.close_db()
        
        final_columns = []
        if select_columns:
            for table_name, column_name in select_columns:
                found_tables = [table for table in table_list if column_name in table]
                if len(found_tables) < 1:
                    raise SelectColumnResolveError(column_name)
                elif len(found_tables) > 1:
                    if not table_name:
                        raise SelectColumnResolveError(column_name)
                    found_table = next(table for table in found_tables if table_name == table.table_name)
                else:
                    found_table = found_tables[0]       
                if table_name and table_name != found_table.table_name:
                    raise SelectColumnResolveError(column_name)
                final_column = f"{found_table.table_name}.{column_name}" if table_name else column_name
                final_columns.append(final_column)
        
        all_columns = []
        for table_schema in table_list:
            all_columns.extend(list(table_schema.columns.keys()))
        counter = Counter(all_columns)
        common_columns = set([column for column, count in counter.items() if count > 1])
                    
        all_records_with_table = {}
        for table_name in tables:
            all_records_with_table[table_name] = []
            table_db = DB(table_name)
            table_db.open_db()
            cursor = table_db.create_cursor()
            key_value_pair = cursor.first()
            while key_value_pair:
                key, value = key_value_pair
                record = Record.deserialize(value)
                record_data = {}
                for column_name, value in record.data.items():
                    if column_name in common_columns:
                        prefixed_column_name = f"{table_name}.{column_name}"
                        record_data[prefixed_column_name] = value
                    else:
                        record_data[column_name] = value
                all_records_with_table[table_name].append(record_data)
                key_value_pair = cursor.next()
            table_db.discard_cursor(cursor)
            table_db.close_db()
        
        cartesian_product = itertools.product(*all_records_with_table.values())
        records_product = [{k: v for record in combination_tuple for k, v in record.items()} for combination_tuple in cartesian_product]
        
        if where_clause:
            filtered_records = []
            for record in records_product:
                satisfies = self._evaluate_condition(deepcopy(where_clause), table_list, record)  # otherwise the original where is modified
                if satisfies == True:
                    filtered_records.append(record)
        else:
            filtered_records = records_product  # list of dict[column_name, value]
            
        if select_columns:  # final output has headers by the specification of select_columns
            final_records = []
            for record in filtered_records:
                final_record = {}
                for table_name, column_name in select_columns:
                    value = None
                    if table_name:
                        prefixed_column_name = f"{table_name}.{column_name}"
                        try:
                            final_record[prefixed_column_name] = record[prefixed_column_name]
                        except KeyError:
                            final_record[prefixed_column_name] = record[column_name]
                    else:
                        final_record[column_name] = record[column_name]
                final_records.append(final_record)
        else:
            final_records = filtered_records
            final_columns = []
            for table_schema in table_list:
                for column in table_schema.columns:
                    if column in common_columns:
                        final_columns.append(f"{table_schema.table_name}.{column}")
                    else:
                        final_columns.append(column)
            
        headers = final_records[0].keys() if final_records else final_columns
        
        return self._format_select_output(final_records, headers)
        
    
    def update(self, table_name: str, assignments: list, where_clause: dict):
        """UPDATE table SET col1=val1, col2=val2 WHERE condition"""
        self.meta_db.open_db()
        table_key = self.meta_db.create_key_from_value(table_name)
        table = self.meta_db.get(table_key)
        if not table:
            raise NoSuchTable()
        self.meta_db.close_db()
        
        # Validate assignments
        for col_name, value in assignments:
            if col_name not in table.columns:
                raise InsertColumnExistenceError(col_name)
            if value is None and col_name in table.not_null_keys:
                raise InsertColumnNonNullableError(col_name)
            if not is_valid_type(table.columns[col_name], value):
                raise InsertTypeMismatchError()
            # Check char length
            col_type = table.columns[col_name]
            if col_type.startswith("char(") and isinstance(value, str):
                # Extract max length from char(N)
                max_len = int(col_type[5:-1])
                if len(value) > max_len:
                    raise InsertTypeMismatchError()
        
        table_db = DB(table_name)
        table_db.open_db()
        cursor = table_db.create_cursor()
        
        success_cnt = 0
        key_value_pair = cursor.first()
        while key_value_pair:
            key, value = key_value_pair
            record = Record.deserialize(value)
            satisfies = self._evaluate_condition(deepcopy(where_clause), [table], record.data) if where_clause else True
            
            if satisfies == True:
                # Log old values for rollback (before update)
                self._log_change("UPDATE", table_name, key, record.data.copy())
                
                # Apply assignments
                for col_name, value in assignments:
                    if table.foreign_keys and col_name in table.foreign_keys:
                        # Handle foreign key update
                        referenced_table_name, referenced_column_name = table.foreign_keys[col_name]
                        if value is not None:
                            referenced_table_db = DB(referenced_table_name)
                            referenced_table_db.open_db()
                            ref_cursor = referenced_table_db.create_cursor()
                            found = False
                            kvp = ref_cursor.first()
                            while kvp:
                                ref_key, ref_val = kvp
                                ref_record = Record.deserialize(ref_val)
                                if ref_record.data[referenced_column_name] == value:
                                    found = True
                                    break
                                kvp = ref_cursor.next()
                            referenced_table_db.discard_cursor(ref_cursor)
                            referenced_table_db.close_db()
                            if not found:
                                raise InsertReferentialIntegrityError()
                    
                    # Update referencing tracking if FK changed
                    if table.foreign_keys and col_name in table.foreign_keys:
                        old_val = record.data.get(col_name)
                        if old_val is not None and old_val != value:
                            # Remove old reference
                            ref_table, ref_col = table.foreign_keys[col_name]
                            if (ref_table, ref_col) in record.referencing:
                                record.referencing[(ref_table, ref_col)].discard(old_val)
                        
                        if value is not None:
                            # Add new reference
                            ref_table, ref_col = table.foreign_keys[col_name]
                            if (ref_table, ref_col) not in record.referencing:
                                record.referencing[(ref_table, ref_col)] = set()
                            record.referencing[(ref_table, ref_col)].add(value)
                    
                    record.data[col_name] = value
                
                # Check primary key uniqueness (if PK is being updated)
                if table.primary_key:
                    pk_col = table.primary_key[0]  # Single-column PK (tuple)
                    if pk_col in [col for col, _ in assignments]:
                        new_pk_value = record.data[pk_col]
                        new_key = table_db.create_key_from_value((new_pk_value,))  # Pass as tuple
                        if new_key != key and table_db.exists(new_key):
                            raise InsertDuplicatePrimaryKeyError()
                
                table_db.put(key, record)
                success_cnt += 1
            
            key_value_pair = cursor.next()
        
        table_db.discard_cursor(cursor)
        table_db.close_db()
        
        return UpdateResult(success_cnt)
    
    def begin_transaction(self):
        """BEGIN - Start a new transaction"""
        if self.in_transaction:
            raise TransactionAlreadyActiveError()
        self.in_transaction = True
        self.undo_log = []
        self.transaction_changes = []
        return BeginSuccess()
    
    def commit_transaction(self):
        """COMMIT - End transaction and make changes permanent"""
        if not self.in_transaction:
            raise NoActiveTransactionError()
        self.in_transaction = False
        self.undo_log = []
        self.transaction_changes = []
        return CommitSuccess()
    
    def rollback_transaction(self):
        """ROLLBACK - Undo all changes in the current transaction"""
        if not self.in_transaction:
            raise NoActiveTransactionError()
        
        # Undo changes in reverse order
        for change in reversed(self.undo_log):
            op_type, table_name, key, extra_data = change
            
            if op_type == "INSERT":
                # Undo insert by deleting the inserted record
                table_db = DB(table_name)
                table_db.open_db()
                table_db.delete(key)
                table_db.close_db()
                
            elif op_type == "DELETE":
                # Undo delete by restoring the record
                record_data = extra_data
                table_db = DB(table_name)
                table_db.open_db()
                record = Record(table_name, record_data, None, {})
                table_db.put(key, record)
                table_db.close_db()
                
            elif op_type == "UPDATE":
                # Undo update by restoring old values
                old_data = extra_data
                table_db = DB(table_name)
                table_db.open_db()
                record = table_db.get(key)
                if record:
                    # Restore old values
                    for col, val in old_data.items():
                        record.data[col] = val
                    table_db.put(key, record)
                table_db.close_db()
        
        self.in_transaction = False
        self.undo_log = []
        self.transaction_changes = []
        return RollbackSuccess()
    
    def _log_change(self, op_type, table_name, key, extra_data=None):
        """Log a change for potential rollback"""
        if self.in_transaction:
            self.undo_log.append((op_type, table_name, key, extra_data))
    
    def create_index(self, table_name: str, column_name: str, index_name: str):
        """CREATE INDEX - Build an index on a column"""
        # Get table schema
        self.meta_db.open_db()
        table_key = self.meta_db.create_key_from_value(table_name)
        table = self.meta_db.get(table_key)
        self.meta_db.close_db()
        
        if not table:
            raise NoSuchTable()
        
        if column_name not in table.columns:
            raise InsertColumnExistenceError(column_name)
        
        # Scan all records and build index
        table_db = DB(table_name)
        table_db.open_db()
        cursor = table_db.create_cursor()
        
        records = []
        kvp = cursor.first()
        while kvp:
            key, value = kvp
            record = Record.deserialize(value)
            column_value = record.data.get(column_name)
            if column_value is not None:  # Don't index NULL
                records.append((column_value, key))
            kvp = cursor.next()
        
        table_db.discard_cursor(cursor)
        table_db.close_db()
        
        # Build the index
        self.index_manager.create_index(table_name, column_name, records, index_name)
        
        return CreateIndexSuccess(index_name, table_name, column_name)
    
    def drop_index(self, index_name: str):
        """DROP INDEX - Remove an index"""
        # Find which table.column this index belongs to
        for key, idx in self.index_manager.indexes.items():
            if idx.index_name == index_name:
                self.index_manager.drop_index(idx.table_name, idx.column_name)
                return DropIndexSuccess(index_name)
        
        raise NoSuchIndex(index_name)
    
    def show_indexes(self, table_name: str):
        """SHOW INDEXES - List indexes on a table"""
        indexes = self.index_manager.get_all_indexes_for_table(table_name)
        return IndexList(table_name, indexes)
    
    def _use_index_for_select(self, table_name: str, column_name: str, value: Any) -> Optional[List]:
        """Try to use an index for a SELECT query. Returns record keys if index found."""
        if self.index_manager.has_index(table_name, column_name):
            index = self.index_manager.get_index(table_name, column_name)
            return index.lookup(value)
        return None
    
    def _format_select_output(self, records: List[Dict], headers: List[str]):
        def create_separator(column_widths):
            return '+-' + '-+-'.join('-' * width for width in column_widths) + '-+'
        
        for record in records:
            for k, v in record.items():
                if v is None:
                    record[k] = "null"
        
        column_widths = [len(header) for header in headers]
        for record in records:
            for i, value in enumerate(record.values()):
                column_widths[i] = max(column_widths[i], len(str(value)))
        
        output = '\n'
        output += create_separator(column_widths) + '\n'
        output += '| ' + ' | '.join(header.upper().ljust(width) for header, width in zip(headers, column_widths)) + ' |\n'
        output += create_separator(column_widths) + '\n'
        
        for record in records:
            output += '| ' + ' | '.join(str(value).ljust(width) for value, width in zip(record.values(), column_widths)) + ' |\n'
        output += create_separator(column_widths)
        
        return output