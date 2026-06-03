"""
Index Manager for SQL DBMS
Supports hash-based indexes on single columns for fast lookups.
"""
import dbm
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class Index:
    """Hash-based index for a single column"""
    
    def __init__(self, table_name: str, column_name: str, index_name: str = None):
        self.table_name = table_name
        self.column_name = column_name
        self.index_name = index_name if index_name else f"{table_name}_{column_name}_idx"
        self.index_dir = Path("./DB_INDEXES")
        self.index_dir.mkdir(exist_ok=True)
        self.db_path = self.index_dir / self.index_name
        self.db = None
    
    def open(self):
        """Open the index database"""
        self.db = dbm.open(str(self.db_path), 'c')
    
    def close(self):
        """Close the index database"""
        if self.db:
            self.db.close()
            self.db = None
    
    def build(self, records: List[Tuple[Any, Any]]):
        """
        Build index from list of (key_value, record_key) tuples.
        key_value: the value of the indexed column
        record_key: the primary key of the record in the table DB
        """
        self.open()
        for key_value, record_key in records:
            if key_value is not None:  # Don't index NULL values
                key_bytes = pickle.dumps(key_value)
                # Handle multiple records with same key value
                if key_bytes in self.db:
                    existing = pickle.loads(self.db[key_bytes])
                    existing.append(record_key)
                    self.db[key_bytes] = pickle.dumps(existing)
                else:
                    self.db[key_bytes] = pickle.dumps([record_key])
        self.close()
    
    def lookup(self, key_value: Any) -> Optional[List[Any]]:
        """
        Find all record keys matching the indexed column value.
        Returns list of record keys or None if not found.
        """
        self.open()
        key_bytes = pickle.dumps(key_value)
        result = None
        if key_bytes in self.db:
            result = pickle.loads(self.db[key_bytes])
        self.close()
        return result
    
    def insert(self, key_value: Any, record_key: Any):
        """Add a single entry to the index"""
        if key_value is None:
            return
        self.open()
        key_bytes = pickle.dumps(key_value)
        if key_bytes in self.db:
            existing = pickle.loads(self.db[key_bytes])
            existing.append(record_key)
            self.db[key_bytes] = pickle.dumps(existing)
        else:
            self.db[key_bytes] = pickle.dumps([record_key])
        self.close()
    
    def delete(self, key_value: Any, record_key: Any):
        """Remove a single entry from the index"""
        if key_value is None:
            return
        self.open()
        key_bytes = pickle.dumps(key_value)
        if key_bytes in self.db:
            existing = pickle.loads(self.db[key_bytes])
            if record_key in existing:
                existing.remove(record_key)
            if existing:
                self.db[key_bytes] = pickle.dumps(existing)
            else:
                del self.db[key_bytes]
        self.close()
    
    def drop(self):
        """Delete the entire index"""
        if self.db_path.exists():
            self.db_path.unlink()
            # Also delete dbm auxiliary files
            for ext in ['.dir', '.bak', '.dat']:
                aux_file = Path(str(self.db_path) + ext)
                if aux_file.exists():
                    aux_file.unlink()


class IndexManager:
    """Manages all indexes for the DBMS"""
    
    def __init__(self):
        self.indexes: Dict[str, Index] = {}  # table.column -> Index
        self.index_dir = Path("./DB_INDEXES")
        self.index_dir.mkdir(exist_ok=True)
        self._load_existing_indexes()
    
    def _load_existing_indexes(self):
        """Load metadata about existing indexes"""
        meta_file = self.index_dir / "index_meta.pkl"
        if meta_file.exists():
            import pickle
            with open(meta_file, 'rb') as f:
                self.indexes = pickle.load(f)
    
    def _save_meta(self):
        """Save index metadata"""
        import pickle
        meta_file = self.index_dir / "index_meta.pkl"
        with open(meta_file, 'wb') as f:
            pickle.dump({k: {'table_name': v.table_name, 'column_name': v.column_name} 
                        for k, v in self.indexes.items()}, f)
    
    def create_index(self, table_name: str, column_name: str, records: List[Tuple[Any, Any]], index_name: str = None):
        """
        Create a new index on a column.
        records: list of (column_value, record_key) tuples to build the index from.
        index_name: optional user-provided name for the index
        """
        key = f"{table_name}.{column_name}"
        if key in self.indexes:
            raise IndexAlreadyExistsError(table_name, column_name)
        
        index = Index(table_name, column_name, index_name)
        index.build(records)
        self.indexes[key] = index
        self._save_meta()
        return index
    
    def get_index(self, table_name: str, column_name: str) -> Optional[Index]:
        """Get an index if it exists"""
        key = f"{table_name}.{column_name}"
        return self.indexes.get(key)
    
    def has_index(self, table_name: str, column_name: str) -> bool:
        """Check if an index exists"""
        key = f"{table_name}.{column_name}"
        return key in self.indexes
    
    def drop_index(self, table_name: str, column_name: str):
        """Drop an index"""
        key = f"{table_name}.{column_name}"
        if key in self.indexes:
            self.indexes[key].drop()
            del self.indexes[key]
            self._save_meta()
    
    def update_on_insert(self, table_name: str, column_name: str, column_value: Any, record_key: Any):
        """Update all indexes on a column when a record is inserted"""
        key = f"{table_name}.{column_name}"
        if key in self.indexes:
            self.indexes[key].insert(column_value, record_key)
    
    def update_on_delete(self, table_name: str, column_name: str, column_value: Any, record_key: Any):
        """Update all indexes on a column when a record is deleted"""
        key = f"{table_name}.{column_name}"
        if key in self.indexes:
            self.indexes[key].delete(column_value, record_key)
    
    def update_on_update(self, table_name: str, column_name: str, 
                         old_value: Any, new_value: Any, record_key: Any):
        """Update index when a record's indexed column is updated"""
        if old_value != new_value:
            self.update_on_delete(table_name, column_name, old_value, record_key)
            self.update_on_insert(table_name, column_name, new_value, record_key)
    
    def get_all_indexes_for_table(self, table_name: str) -> List[str]:
        """Get list of index names for a table"""
        return [idx.index_name for key, idx in self.indexes.items() 
                if idx.table_name == table_name]


class IndexAlreadyExistsError(Exception):
    def __init__(self, table_name: str, column_name: str):
        self.table_name = table_name
        self.column_name = column_name
        super().__init__(f"Index already exists on {table_name}.{column_name}")
