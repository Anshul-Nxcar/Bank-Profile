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

COLUMN_NAME_MAPPING = {
    "BANK_NAME": "Bank Name",
    "type": "Bank Type",
    "status": "Status",
    "min_car_year": "Minimum Car Year",
    "max_rc_transfer": "Maximum RC Transfers",
    "applicant": "Minimum Applicant Age",
    "co_applicant": "Minimum Co-Applicant Age",
    "guarantor": "Minimum Guarantor Age",
    "applicant_credit_score": "Minimum Applicant Credit Score",
    "co_applicant_credit_score": "Minimum Co-Applicant Credit Score",
    "applicant_income": "Minimum Applicant Income",
    "total_income_co_applicant": "Minimum Total Income with Co-Applicant",
    "b_banks": "Banks",
    "b_car": "Car Details",
    "b_min_age": "Minimum Age",
    "b_min_credit_score": "Minimum Credit Score",
    "b_min_income": "Minimum Income"
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

    # Create tabs for each table
    tabs = st.tabs(renamed_tables)
    for tab, table_name_display in zip(tabs, renamed_tables):
        with tab:
            table_name = INVERTED_COLUMN_NAME_MAPPING.get(table_name_display, table_name_display)

            # Update session state if the tab is active
            if table_name != st.session_state["current_table"]:
                st.session_state["current_table"] = table_name

            # Add Data Button
            if st.button("Add Data", key=f"add_data_{table_name}"):
                st.session_state["current_view"] = "add"
                st.session_state["current_table"] = table_name
                st.rerun()

            # Fetch data for the selected table
            data = fetch_data(table_name)
            if data.empty:
                st.write(f"No data available in the {table_name_display} table.")
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
                        if st.button(f"✏️", key=f"action_{table_name}_{index}"):
                            st.session_state["selected_row"] = row.to_dict()
                            st.session_state["current_view"] = "action"  # Switch to action view
                            st.session_state["current_table"] = table_name
                            st.rerun()

elif st.session_state["current_view"] == "add":
    # Add Data Section
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
                for column in data.columns:
                    column_display = COLUMN_NAME_MAPPING.get(column, column)
                    if column not in ["id", "bank_id"]:
                        if column == "status":
                            status_display = st.radio(
                                f"Select {column_display}",
                                options=["Active", "Inactive"],
                                index=0
                            )
                            form_data[column] = 1 if status_display == "Active" else 0
                        elif data[column].dtype == "int64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0)
                        elif data[column].dtype == "float64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0.0)
                        else:
                            form_data[column] = st.text_input(f"Enter {column_display}").lower()
            else:
                if "bank_id" in data.columns:
                    selected_bank = st.selectbox("Select Bank Name", bank_names)
                    form_data["bank_id"] = bank_name_to_id[selected_bank]
                
                for column in data.columns:
                    if column not in ["id", "bank_id"]:
                        if column == "BANK_NAME":
                            continue
                        column_display = COLUMN_NAME_MAPPING.get(column, column)
                        if data[column].dtype == "int64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0)
                        elif data[column].dtype == "float64":
                            form_data[column] = st.number_input(f"Enter {column_display}", value=0.0)
                        else:
                            form_data[column] = st.text_input(f"Enter {column_display}").lower()
            submitted = st.form_submit_button("Add Record")
            if submitted:
                insert_data(table_name, form_data)
                st.success(f"Record added successfully to {table_name}!")
                st.session_state["current_view"] = "view"
                st.rerun()

    if st.button("Back to View Data"):
        st.session_state["current_view"] = "view"
        st.rerun()

elif st.session_state["current_view"] == "action":
    # Action Section (Edit/Delete Row)
    selected_row = st.session_state["selected_row"]

    if selected_row:
        st.header("Edit or Delete")
        st.write("Selected Details:")
        selected_row_display = selected_row.copy()
        selected_row_display = {k: v for k, v in selected_row_display.items() if k not in ['id', 'bank_id']}
        selected_row_display = {COLUMN_NAME_MAPPING.get(k, k): v for k, v in selected_row_display.items()}
        st.table(pd.DataFrame([selected_row_display]))

        # Update Section
        st.subheader("Edit")
        updated_data = {}
        with st.form("edit_form"):
            for column, value in selected_row.items():
                column_display = COLUMN_NAME_MAPPING.get(column, column)
                if ("id" in selected_row and "bank_id" in selected_row and column in ["id", "bank_id", "BANK_NAME"]) or \
                (column in ["id", "bank_id"]):
                    continue
                if column == "status":
                    status_display = st.radio(
                        f"Update {column_display}",
                        options=["Active", "Inactive"],
                        index=0 if value == 1 else 1
                    )
                    updated_data[column] = 1 if status_display == "Active" else 0
                elif isinstance(value, int):
                    updated_data[column] = st.number_input(f"Update {column_display}", value=value)
                elif isinstance(value, float):
                    updated_data[column] = st.number_input(f"Update {column_display}", value=value)
                else:
                    updated_data[column] = st.text_input(f"Update {column_display}", value=value).lower()
            submitted = st.form_submit_button("Update")
            if submitted:
                primary_key = "id" if "id" in selected_row else "bank_id"
                update_data(st.session_state["current_table"], updated_data, selected_row[primary_key])
                st.success("Row updated successfully!")
                st.session_state["current_view"] = "view"
                st.session_state["selected_row"] = None
                st.rerun()

        st.subheader("Delete")
        if st.button("Delete"):
            delete_data(st.session_state["current_table"], selected_row["BANK_NAME"])
            st.success("Row deleted successfully!")
            st.session_state["current_view"] = "view"
            st.session_state["selected_row"] = None
            st.rerun()

        if st.button("Back to View Data"):
            st.session_state["current_view"] = "view"
            st.session_state["selected_row"] = None
            st.rerun()
    else:
        st.error("No row selected. Returning to View Data.")
        st.session_state["current_view"] = "view"
        st.rerun()
