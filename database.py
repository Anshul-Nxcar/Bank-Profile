import mysql.connector
import pandas as pd
import numpy as np


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="bank_data",
        port=3308  # Update this if your MySQL runs on a different port
    )


def fetch_table_names():
    try:
        # Connect to the database
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES")

        # Fetch and process the result
        tables_result = cursor.fetchall()
        # print("Fetched tables result:", tables_result)  # Debugging

        if not tables_result:  # Check if the result is empty
            return []

        # Extract table names from the result
        tables = [table['Tables_in_bank_data'] for table in tables_result]

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        # Clean up the database connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return tables


# Fetch all records from a table
def fetch_data(table_name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Handle tables with `bank_id` by joining with the `banks` table
    if table_name in ["car", "min_age", "min_credit_score", "min_income"]:
        query = f"""
            SELECT banks.bank_name AS BANK_NAME, {table_name}.*
            FROM {table_name}
            JOIN banks ON {table_name}.bank_id = banks.bank_id
        """
    elif table_name == "banks":
        query = "SELECT bank_id, bank_name AS BANK_NAME, type, status FROM banks"
    else:
        query = f"SELECT * FROM {table_name}"
    
    cursor.execute(query)
    records = cursor.fetchall()
    conn.close()

    # Convert to DataFrame and process columns
    df = pd.DataFrame(records)
    # if "id" in df.columns:
    #     df = df.drop(columns=["id"])  # Exclude `id` except for banks
    # if "bank_id" in df.columns and table_name != "banks":
    #     df = df.drop(columns=["bank_id"])  # Exclude `bank_id` except for banks
    
    # Ensure BANK_NAME is in uppercase and at the beginning
    if "BANK_NAME" in df.columns:
        df["BANK_NAME"] = df["BANK_NAME"].str.upper()  # Convert to uppercase
        columns = ["BANK_NAME"] + [col for col in df.columns if col != "BANK_NAME"]
        df = df[columns]  # Reorder columns to place `BANK_NAME` first

    df.index += 1
    return df



# Fetch a specific record by ID
def fetch_record_by_id(table_name, record_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if table_name != "banks":
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
    else:
        cursor.execute(f"SELECT * FROM {table_name} WHERE bank_id = %s", (record_id,))
    record = cursor.fetchone()
    conn.close()
    return record

# Insert a new record into a table
def insert_data(table_name, data):
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ", ".join(["%s"] * len(data))
    columns = ", ".join(data.keys())
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    cursor.execute(query, tuple(data.values()))
    conn.commit()
    conn.close()

# Update a record in a table
def update_data(table_name, data, id_value):
    """
    Updates a record in the specified table based on the provided data dictionary and id_value.

    :param table_name: Name of the database table.
    :param data: Dictionary where keys are column names to update, and values are the new values.
    :param id_value: ID value of the row to be updated (assumes the primary key column is "id").
    """
    # Ensure input validation
    if not data or not isinstance(data, dict):
        raise ValueError("Data must be a non-empty dictionary.")
    
    # Convert numpy types to native Python types
    data = {key: (int(value) if isinstance(value, np.integer) else value) for key, value in data.items()}
    id_value = int(id_value) if isinstance(id_value, np.integer) else id_value

    conn = get_connection()  # Get database connection
    cursor = conn.cursor()

    # Build the SQL update query
    set_clause = ", ".join([f"{key} = %s" for key in data.keys()])

    if table_name != "banks":
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
    else:
        query = f"UPDATE {table_name} SET {set_clause} WHERE bank_id = %s"

    try:
        # Execute the query
        cursor.execute(query, tuple(data.values()) + (id_value,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e  # Re-raise the exception to notify the caller
    finally:
        # Clean up resources
        cursor.close()
        conn.close()


# Delete a record from a table
def delete_data(table_name, bank_name):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Map bank name to bank_id
    if table_name != "banks":
        cursor.execute("SELECT bank_id FROM banks WHERE bank_name = %s", (bank_name,))
        result = cursor.fetchone()
        if not result:
            st.error("Bank name not found!")
            return
        bank_id = result[0]
        cursor.execute(f"DELETE FROM {table_name} WHERE bank_id = %s", (bank_id,))
    else:
        cursor.execute("DELETE FROM banks WHERE bank_name = %s", (bank_name,))
    
    conn.commit()
    conn.close()
