import psycopg2
import oracledb
from typing import Dict, List, Optional, Any, Callable
import json,os
from datetime import datetime

import sys
# ADD PROJECT ROOT TO PYTHONPATH
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parents[4]  # Go up 4 levels to reach /apis
sys.path.insert(0, str(project_root))
import django
# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.conf import settings

def transfer_data(
    pg_config: Dict[str, str],
    oracle_config: Dict[str, str],
    pg_table: str,
    oracle_table: str,
    column_mapping: List[Dict[str, Any]],
    batch_size: int = 1000,
    where_clause: Optional[str] = None,
    tracking_flag_column: str = 'oif',
    tracking_timestamp_column: str = 'ora_ins_time',
    primary_key_columns: Optional[List[str]] = None
) -> int:
    """
    Transfer data from PostgreSQL to Oracle with support for fixed values, duplicate mappings,
    data transformation, and tracking to prevent duplicate transfers.
    
    Args:
        pg_config: PostgreSQL connection config 
        oracle_config: Oracle connection config
        pg_table: Source table name in PostgreSQL
        oracle_table: Target table name in Oracle
        column_mapping: List of column mapping dicts. Each dict has:
                        - 'oracle_column': Target Oracle column name (required)
                        - 'pg_column': Source PostgreSQL column (optional)
                        - 'fixed_value': Fixed value to insert (optional)
                        - 'function': Special function like 'CURRENT_TIMESTAMP' (optional)
                        - 'max_length': Maximum length to truncate to (optional)
                        - 'transform': Custom transformation function (optional)
        batch_size: Number of rows to insert per batch
        where_clause: Optional WHERE clause for filtering PG data
        tracking_flag_column: PostgreSQL column name for tracking flag
        tracking_timestamp_column: PostgreSQL column name for timestamp
        primary_key_columns: List of primary key columns for UPDATE tracking
    
    Returns:
        Number of rows transferred
    """
    pg_conn = None
    oracle_conn = None
    total_rows = 0
    
    try:
        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(**pg_config)
        pg_cursor = pg_conn.cursor()
        
        # Connect to Oracle
        oracle_conn = oracledb.connect(**oracle_config)
        oracle_cursor = oracle_conn.cursor()
        
        # Separate PG columns to fetch (unique set) and build mapping indices
        pg_columns_to_fetch = []
        pg_column_indices = {}
        
        # Add primary key columns for tracking updates
        if primary_key_columns:
            for pk_col in primary_key_columns:
                if pk_col not in pg_column_indices:
                    pg_column_indices[pk_col] = len(pg_columns_to_fetch)
                    pg_columns_to_fetch.append(pk_col)
        
        for mapping in column_mapping:
            pg_col = mapping.get('pg_column')
            if pg_col and pg_col not in pg_column_indices:
                pg_column_indices[pg_col] = len(pg_columns_to_fetch)
                pg_columns_to_fetch.append(pg_col)
        
        # Build SELECT query for PostgreSQL
        if not pg_columns_to_fetch:
            raise ValueError("No PostgreSQL columns specified to fetch")
        
        # Add tracking condition to WHERE clause
        tracking_condition = f"{tracking_flag_column} = '0'"
        if where_clause:
            combined_where = f"({where_clause}) AND {tracking_condition}"
        else:
            combined_where = tracking_condition
            
        select_query = f"SELECT {', '.join(pg_columns_to_fetch)} FROM {pg_table} WHERE {combined_where}"
        
        print(f"Fetching data from PostgreSQL: {select_query}")
        pg_cursor.execute(select_query)
        
        # Build UPDATE query for tracking
        if primary_key_columns:
            pk_placeholders = ' AND '.join([f"{pk} = %s" for pk in primary_key_columns])
            update_query = f"""
                UPDATE {pg_table} 
                SET {tracking_flag_column} = '1', 
                    {tracking_timestamp_column} = CURRENT_TIMESTAMP 
                WHERE {pk_placeholders}
            """
        else:
            update_query = None
            print("WARNING: No primary_key_columns provided. Tracking updates will be skipped.")
        
        # Build INSERT query for Oracle
        oracle_columns = [m['oracle_column'] for m in column_mapping]
        
        # Build VALUES clause with placeholders and functions
        values_parts = []
        bind_positions = []
        
        for i, mapping in enumerate(column_mapping):
            if 'function' in mapping:
                values_parts.append(mapping['function'])
            elif 'fixed_value' in mapping:
                values_parts.append(f':{i+1}')
                bind_positions.append(('fixed', mapping['fixed_value'], mapping))
            elif 'pg_column' in mapping:
                values_parts.append(f':{i+1}')
                bind_positions.append(('pg', pg_column_indices[mapping['pg_column']], mapping))
            else:
                raise ValueError(f"Invalid mapping for Oracle column {mapping['oracle_column']}")
        
        insert_query = f"INSERT INTO {oracle_table} ({', '.join(oracle_columns)}) VALUES ({', '.join(values_parts)})"
        
        print(f"Inserting into Oracle: {insert_query}")
        
        # Fetch and insert in batches
        while True:
            pg_rows = pg_cursor.fetchmany(batch_size)
            if not pg_rows:
                break
            
            # Transform PG rows to Oracle rows based on mapping
            oracle_rows = []
            pk_values_batch = []
            
            for pg_row in pg_rows:
                oracle_row = []
                for bind_type, bind_info, mapping in bind_positions:
                    if bind_type == 'fixed':
                        value = bind_info
                    elif bind_type == 'pg':
                        value = pg_row[bind_info]
                    
                    # Apply transformations
                    if value is not None:
                        # Apply max_length truncation
                        if 'max_length' in mapping and isinstance(value, str):
                            value = value[:mapping['max_length']]
                        
                        # Apply custom transformation
                        if 'transform' in mapping:
                            value = mapping['transform'](value)
                    
                    oracle_row.append(value)
                
                oracle_rows.append(oracle_row)
                
                # Extract primary key values for tracking update
                if primary_key_columns and update_query:
                    pk_vals = tuple(pg_row[pg_column_indices[pk]] for pk in primary_key_columns)
                    pk_values_batch.append(pk_vals)
            
            # Insert batch into Oracle
            oracle_cursor.executemany(insert_query, oracle_rows)
            oracle_conn.commit()
            
            # Update tracking flags in PostgreSQL after successful Oracle insert
            if update_query and pk_values_batch:
                pg_cursor.executemany(update_query, pk_values_batch)
                pg_conn.commit()
            
            total_rows += len(oracle_rows)
            print(f"Transferred {total_rows} rows...")
        
        print(f"Transfer complete. Total rows: {total_rows}")
        return total_rows
        
    except Exception as e:
        if oracle_conn:
            oracle_conn.rollback()
        print(f"Error during transfer: {e}")
        raise
        
    finally:
        if pg_conn:
            pg_conn.close()
        if oracle_conn:
            oracle_conn.close()


# Example usage
if __name__ == "__main__":
    db_config = settings.DATABASES['legacy']  # or 'read' or 'default'
    pg_config = {
        'host': db_config['HOST'],
        'port': int(db_config['PORT']),
        'database': db_config['NAME'],
        'user': db_config['USER'],
        'password': db_config['PASSWORD'],
    }

    # Get Oracle config from settings
    oracle_config = settings.ORACLE_CONFIG
    
    # Column mapping with max_length constraints
    column_mapping = [
        # Core identifiers
        {'oracle_column': 'CSCCODE', 'pg_column': 'csc_code', 'max_length': 30},
        {'oracle_column': 'GSMNUMBER', 'pg_column': 'mobile_number', 'max_length': 10},
        {'oracle_column': 'PRESENT_IMSI', 'pg_column': 'imsi_old', 'max_length': 15},
        {'oracle_column': 'NEW_IMSI', 'pg_column': 'imsi', 'max_length': 15},
        {'oracle_column': 'CONNECTION_TYPE', 'pg_column': 'connection_type'},
        
        # SIM / IMSI
        {'oracle_column': 'NEW_SIM', 'pg_column': 'sim_number', 'max_length': 20},
        {'oracle_column': 'OLD_SIM', 'pg_column': 'ss_simnumber', 'max_length': 20},
        
        # Customer Name
        {'oracle_column': 'NAME', 'pg_column': 'bill_fname', 'max_length': 150},
        
        # Local Address - WITH TRUNCATION
        {'oracle_column': 'LOCAL_ADDR_HNO', 'pg_column': 'bill_address1', 'max_length': 100},
        {'oracle_column': 'LOCAL_ADDR_STREET', 'pg_column': 'bill_address2', 'max_length': 100},
        {'oracle_column': 'LOCAL_ADDR_LOCALITY', 'pg_column': 'bill_address3', 'max_length': 100},
        {'oracle_column': 'LOCAL_ADDR_CITY', 'pg_column': 'bill_city', 'max_length': 50},
        {'oracle_column': 'LOCAL_ADDR_STATE', 'pg_column': 'bill_state', 'max_length': 50},
        {'oracle_column': 'LOCAL_ADDR_PIN', 'pg_column': 'bill_zip'},
        
        # Permanent Address - WITH TRUNCATION
        {'oracle_column': 'PERM_ADDR_HNO', 'pg_column': 'bill_address1', 'max_length': 100},
        {'oracle_column': 'PERM_ADDR_STREET', 'pg_column': 'bill_address2', 'max_length': 100},
        {'oracle_column': 'PERM_ADDR_LOCALITY', 'pg_column': 'bill_address3', 'max_length': 100},
        {'oracle_column': 'PERM_ADDR_CITY', 'pg_column': 'bill_city', 'max_length': 50},
        {'oracle_column': 'PERM_ADDR_STATE', 'pg_column': 'bill_state', 'max_length': 50},
        {'oracle_column': 'PERM_ADDR_PIN', 'pg_column': 'bill_zip'},
        {'oracle_column': 'ALTERNATE_CONTACT_NO', 'pg_column': 'alternate_mobile_number'},
        
        # Remarks
        {'oracle_column': 'SWAP_REMARKS', 'fixed_value': '4gupgrade', 'max_length': 100},
        {'oracle_column': 'SWAP_REASON_ID ', 'fixed_value': '17', 'max_length': 100},
        
        # Audit / Approval
        {'oracle_column': 'INS_USR', 'pg_column': 'insert_user', 'max_length': 30},
        {'oracle_column': 'INS_DATE', 'pg_column': 'insert_date'},
        {'oracle_column': 'CIRCLE_CODE', 'pg_column': 'cust_circle_code'},
        {'oracle_column': 'ACT_TYPE', 'pg_column': 'activation_type', 'max_length': 25},
        
        # Fixed values
        {'oracle_column': 'ACTIVATION_STATUS', 'fixed_value': 'AI'},
    ]
    
    # Transfer data
    try:
        rows_transferred = transfer_data(
            pg_config=pg_config,
            oracle_config=oracle_config,
            pg_table='sim_upgrade_request',
            oracle_table='CAF_ADMIN.SIM_SWAP_DATA',
            column_mapping=column_mapping,
            batch_size=1000,
            tracking_flag_column='oif',
            tracking_timestamp_column='ora_ins_time',
            primary_key_columns=['parent_ctop_number', 'mobile_number']
        )
        print(f"Successfully transferred {rows_transferred} rows")
    except Exception as e:
        print(f"Transfer failed: {e}")