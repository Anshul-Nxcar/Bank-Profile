import streamlit as st
import pandas as pd
from database import fetch_data, insert_data, update_data, delete_data, fetch_table_names

# Initialize session state
if "operation" not in st.session_state:
    st.session_state["operation"] = None
if "selected_row" not in st.session_state:
    st.session_state["selected_row"] = None
if "current_view" not in st.session_state:
    st.session_state["current_view"] = "view"  # Default view is the data table
# if "current_table" not in st.session_state:
#     st.session_state["current_table"] = None


COLUMN_NAME_MAPPING = {
    "BANK_NAME": "Bank Name",  # Good
    "type": "Bank Type",  # Good
    "status": "Status",  # Good
    "min_car_year": "Minimum Car Year",  # Capitalize "Car Year" for consistency
    "max_rc_transfer": "Maximum RC Transfers",  # Make plural for clarity
    "applicant": "Minimum Applicant Age",  # Good
    "co_applicant": "Minimum Co-Applicant Age",  # Capitalize "Co-Applicant" for consistency
    "guarantor": "Minimum Guarantor Age",  # Good
    "applicant_credit_score": "Minimum Applicant Credit Score",  # Good
    "co_applicant_credit_score": "Minimum Co-Applicant Credit Score",  # Capitalize "Co-Applicant"
    "applicant_income": "Minimum Applicant Income",  # Good
    "total_income_co_applicant": "Minimum Total Income with Co-Applicant",  # Capitalize "Total" and "Co-Applicant"
    "b_banks" : "Banks",
    "b_car" : "Car Details",
    "b_min_age" : "Minimum Age",
    "b_min_credit_score" : "Minimum Credit Score",
    "b_min_income" : "Minimum Income"
}


# Main App
st.title("Bank Data Management")
tables = fetch_table_names()
INVERTED_COLUMN_NAME_MAPPING = {v: k for k, v in COLUMN_NAME_MAPPING.items()}

# Conditional Views
if st.session_state["current_view"] == "view":
    # View Data Section
    st.header("View Data")
    if "current_table" not in st.session_state or st.session_state["current_table"] not in tables:
        st.session_state["current_table"] = tables[0]  # Default to the first table if none selected

    renamed_tables = [COLUMN_NAME_MAPPING.get(item, item) for item in tables]
    current_table_display = COLUMN_NAME_MAPPING.get(st.session_state["current_table"], st.session_state["current_table"])

    table_name_display = st.selectbox(
        "Select Table",
        renamed_tables,
        index=renamed_tables.index(current_table_display),
        key="view_table"
    )
    table_name = INVERTED_COLUMN_NAME_MAPPING.get(table_name_display, table_name_display)

    # Update session state and trigger rerun if the table changes
    if table_name != st.session_state["current_table"]:
        st.session_state["current_table"] = table_name
        st.rerun()


    # Add Data Button
    if st.button("Add Data"):
        st.session_state["current_view"] = "add"  # Switch to Add Data view
        st.rerun()

    # Fetch data for the selected table
    data = fetch_data(table_name)
    if data.empty:
        st.write("No data available in this table.")
    else:

        # Add Action button for each row
        for index, row in data.iterrows():
            col1, col2 = st.columns([4, 1])  # Adjust column widths
            with col1:
                # Dynamically exclude specific columns
                row_display = row.copy()  # Copy the row to avoid modifying the original
                row_display = row_display.drop([col for col in ['id', 'bank_id'] if col in data.columns])
                if "status" in row_display:
                    row_display["status"] = "Active" if row_display["status"] == 1 else "Inactive"
                row_display = row_display.rename(COLUMN_NAME_MAPPING)
                st.table(pd.DataFrame([row_display]))  # Display the modified row
            with col2:
                if st.button(f"✏️ Row {index}", key=f"action_{index}"):
                    st.session_state["selected_row"] = row.to_dict()
                    st.session_state["current_view"] = "action"  # Switch to action view
                    st.session_state["current_table"] = table_name
                    st.rerun()

elif st.session_state["current_view"] == "add":
    # Add Data Section
    st.header(f"Add Data to {st.session_state['current_table']}")
    table_name = st.session_state["current_table"]
    if table_name != "b_banks":
        banks = fetch_data("b_banks")
        bank_names = banks["BANK_NAME"].tolist()
        bank_name_to_id = dict(zip(banks["BANK_NAME"], banks["bank_id"]))

    # Fetch column names and create input fields dynamically
    data = fetch_data(table_name)
    if data.empty:
        st.write("No schema available for this table.")
    else:
        with st.form("add_form"):
            form_data = {}
            if table_name == "b_banks":
                # Special case: Adding data to the banks table
                for column in data.columns:
                    column_display = COLUMN_NAME_MAPPING.get(column, column)
                    if column not in ["id", "bank_id"]:
                        if column == "status":
                            # Special handling for 'status' column
                            status_display = st.radio(
                                f"Select {column_display}",
                                options=["Active", "Inactive"],  # User-friendly options
                                index=0  # Default to "Active"
                            )
                            # Map the selected value to 1 for Active and 0 for Inactive
                            form_data[column] = 1 if status_display == "Active" else 0
                        elif data[column].dtype == "int64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0)
                        elif data[column].dtype == "float64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0.0)
                        else:
                            form_data[column] = st.text_input(f"Enter {column_display}").lower()
            else:
                # Generic case: Adding data to other tables
                if "bank_id" in data.columns:  # If the table has a `bank_id` foreign key
                    selected_bank = st.selectbox("Select Bank Name", bank_names)
                    form_data["bank_id"] = bank_name_to_id[selected_bank]  # Map selected bank name to bank_id
                
                for column in data.columns:
                    if column not in ["id", "bank_id"]:
                        if column == "BANK_NAME":  # Skip displaying BANK_NAME as it’s replaced by bank selection
                            continue
                        column_display = COLUMN_NAME_MAPPING.get(column, column)
                        if data[column].dtype == "int64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0)
                        elif data[column].dtype == "float64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0.0)
                        else:
                            form_data[column] = st.text_input(f"Enter {column_display}").lower()
                    # form_data[column] = st.text_input(f"Enter {column}")
            submitted = st.form_submit_button("Add Record")
            if submitted:
                insert_data(table_name, form_data)
                st.success(f"Record added successfully to {table_name}!")
                st.session_state["current_view"] = "view"  # Return to View Data
                st.rerun()

    # Back Button
    if st.button("Back to View Data"):
        st.session_state["current_view"] = "view"
        st.rerun()

elif st.session_state["current_view"] == "action":
    # Action Section (Edit/Delete Row)
    selected_row = st.session_state["selected_row"]

    if selected_row:
        st.header("Edit or Delete Row")
        st.write("Selected Row Details:")
        selected_row_display = selected_row.copy()  # Copy the row to avoid modifying the original
        selected_row_display = {k: v for k, v in selected_row_display.items() if k not in ['id', 'bank_id']}
        selected_row_display = {COLUMN_NAME_MAPPING.get(k, k): v for k, v in selected_row_display.items()}
        st.table(pd.DataFrame([selected_row_display]))

        # Update Section
        st.subheader("Edit Row")
        updated_data = {}
        with st.form("edit_form"):
            for column, value in selected_row.items():
                column_display = COLUMN_NAME_MAPPING.get(column, column)
                # if column not in ["id", "bank_id"]:  # Skip primary keys
                #     updated_data[column] = st.text_input(f"Edit {column}", value=str(value))
                if ("id" in selected_row and "bank_id" in selected_row and column in ["id", "bank_id", "BANK_NAME"]) or \
                (column in ["id", "bank_id"]):
                    continue
                if column == "status":
                    status_display = st.radio(
                        f"Update {column_display}",
                        options=["Active", "Inactive"],
                        index=0 if value == 1 else 1  # Set default based on current value
                    )
                    # Map the selected value to 1 for Active and 0 for Inactive
                    updated_data[column] = 1 if status_display == "Active" else 0

                # Handle other columns based on data type
                elif isinstance(value, int):
                    updated_data[column] = st.number_input(f"Update {column_display}", value=value)
                elif isinstance(value, float):
                    updated_data[column] = st.number_input(f"Update {column_display}", value=value)
                else:
                    updated_data[column] = st.text_input(f"Update {column_display}", value=value).lower()
            submitted = st.form_submit_button("Update Row")
            if submitted:
                primary_key = "id" if "id" in selected_row else "bank_id"
                update_data(st.session_state["current_table"], updated_data, selected_row[primary_key])
                st.success("Row updated successfully!")
                st.session_state["current_view"] = "view"  # Return to View Data
                st.session_state["selected_row"] = None
                st.rerun()

        # Delete Section
        st.subheader("Delete Row")
        if st.button("Delete Row"):
            delete_data(st.session_state["current_table"], selected_row["BANK_NAME"])
            st.success("Row deleted successfully!")
            st.session_state["current_view"] = "view"  # Return to View Data
            st.session_state["selected_row"] = None
            st.rerun()

        # Back Button
        if st.button("Back to View Data"):
            st.session_state["current_view"] = "view"
            st.session_state["selected_row"] = None
            st.rerun()
    else:
        st.error("No row selected. Returning to View Data.")
        st.session_state["current_view"] = "view"
        st.rerun()
