import streamlit as st
import pandas as pd
from database import fetch_data, insert_data, update_data, delete_data, fetch_table_names
from helper import get_make_id, get_model_id, get_model_name, get_cities_by_state



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
    "b_min_income": "Minimum Income",
    "b_negative_areas" : "Negative Area",
    "b_negative_models" : "Negative Models",
    "b_negative_occupations" : "Negative Occupations",
    "b_nxcar_coverage" : "NxCar Coverage",
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
            
            # elif table_name == "b_negative_areas":
            #     if "bank_id" in data.columns:
            #         selected_bank = st.selectbox("Select Bank Name", bank_names)
            #         form_data["bank_id"] = bank_name_to_id[selected_bank]
                
            #     for column in data.columns:
            #         if column not in ["id", "bank_id"]:
            #             if column == "BANK_NAME":
            #                 continue
            #             column_display = COLUMN_NAME_MAPPING.get(column, column)
            #             if data[column].dtype == "int64":
            #                 form_data[column] = st.number_input(f"Enter {column_display}", value=0)
            #             elif data[column].dtype == "float64":
            #                 form_data[column] = st.number_input(f"Enter {column_display}", value=0.0)
            #             else:
            #                 form_data[column] = st.text_input(f"Enter {column_display}").lower()

            elif table_name == "b_negative_models":
                if "bank_id" in data.columns:
                    selected_bank = st.selectbox("Select Bank Name", bank_names)
                    form_data["bank_id"] = bank_name_to_id[selected_bank]
                
                for column in data.columns:
                    if column not in ["id", "bank_id"]:
                        if column == "BANK_NAME":
                            continue
                        column_display = COLUMN_NAME_MAPPING.get(column, column)
                        if column == "status":
                            status_display = st.radio(
                                f"Select {column_display}",
                                options=["Active", "Inactive"],
                                index=0
                            )
                        elif column == "make_id":
                            selected_make = st.selectbox("Select Make Name", fetch_data("vehiclemake"))
                            form_data[column] = get_make_id(selected_make)

                        elif column == "model_id":
                            selected_model = st.selectbox("Select Make Name", get_model_name(form_data["make_id"]))
                            form_data[column] = get_model_id(selected_model)



            elif table_name == "b_negative_occupations":
                if "bank_id" in data.columns:
                    selected_bank = st.selectbox("Select Bank Name", bank_names)
                    form_data["bank_id"] = bank_name_to_id[selected_bank]
                
                for column in data.columns:
                    if column not in ["id", "bank_id"]:
                        if column == "BANK_NAME":
                            continue
                        column_display = COLUMN_NAME_MAPPING.get(column, column)
                        if column == "status":
                            status_display = st.radio(
                                f"Select {column_display}",
                                options=["Active", "Inactive"],
                                index=0
                            )
                        elif column == "occupation_id":
                            occupation = fetch_data("occupations")
                            occupation_names = occupation["occupation_name"].tolist()
                            occupation_name_to_id = dict(zip(occupation["occupation_name"], occupation["id"]))
                            occupation_names.append("Others")
                            selected_occupation = st.selectbox("Select Occupation", occupation_names)
                            if selected_occupation == "Others":
                                # Allow the user to enter their occupation if "Others" is selected
                                other_occupation = st.text_input("Enter your occupation:")
                                if other_occupation:  # Ensure the user enters something
                                    form_data[column] = other_occupation
                                    data = {"occupation_name": other_occupation}
                                    try:
                                        insert_data("occupations", data)
                                        st.success("New occupation added successfully!")
                                    except Exception as e:
                                        st.error(f"Failed to add occupation: {e}")
                            else:
                                # Map the selected occupation name to its ID
                                form_data[column] = occupation_name_to_id[selected_occupation]

            

            elif table_name == "b_nxcar_caverage":
                if "bank_id" in data.columns:
                    selected_bank = st.selectbox("Select Bank Name", bank_names)
                    form_data["bank_id"] = bank_name_to_id[selected_bank]
                
                for column in data.columns:
                    if column not in ["id", "bank_id"]:
                        if column == "BANK_NAME":
                            continue
                        column_display = COLUMN_NAME_MAPPING.get(column, column)
                        if column == "status":
                            status_display = st.radio(
                                f"Select {column_display}",
                                options=["Active", "Inactive"],
                                index=0
                            )
                        elif column == "state_id":
                            state = fetch_data("states")
                            state_names = state["state_name"].tolist()
                            state_name_to_id = dict(zip(state["state_name"], state["state_id"]))
                            selected_state = st.selectbox("Select State Name", state_names)
                            form_data[column] = state_name_to_id[selected_state]

                        elif column == "city_id":
                            city = get_cities_by_state(form_data["state_id"])
                            city_names = city["city_name"].tolist()
                            city_name_to_id = dict(zip(city["city_name"], city["city_id"]))
                            selected_city = st.selectbox("Select City Name", city_names)
                            form_data[column] = city_name_to_id[selected_city]

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
                
                elif column == "make_id":
                    make_data = fetch_data("vehiclemake")
                    make_names = make_data["make"].tolist()
                    make_name_to_id = dict(zip(make_data["make"], make_data["make_id"]))
                    make_id_to_name = dict(zip(make_data["make_id"], make_data["make"]))
                    selected_make = st.selectbox(
                        f"Update {column_display}",
                        make_data,
                        index=make_names.index(make_id_to_name[value]) if value in make_id_to_name.values() else len(make_names) - 1
                    )
                    updated_data[column] = make_id_to_name[selected_make]
                
                elif column == "model_id":
                    model_data = fetch_data("vehiclemodellist")
                    selected_model = st.selectbox(
                        f"Update {column_display}",
                        model_data,
                        index = get_model_name(updated_data.get("make_id"))
                    )
                    updated_data[column] = get_model_id(selected_model)
                
                elif column == "occupation_id":
                    occupation = fetch_data("occupations")
                    occupation_names = occupation["occupation_name"].tolist()
                    occupation_name_to_id = dict(zip(occupation["occupation_name"], occupation["id"]))
                    occupation_id_to_name = dict(zip(occupation["id"], occupation["occupation_name"]))
                    occupation_names.append("Others")

                    selected_occupation = st.selectbox(
                        f"Update {column_display}",
                        occupation_names,
                        index=occupation_names.index(occupation_id_to_name[value]) if value in occupation_id_to_name.values() else len(occupation_names) - 1
                    )

                    if selected_occupation == "Others":
                        # Allow entering a new occupation
                        other_occupation = st.text_input("Enter your occupation:")
                        if other_occupation:  # Ensure the user enters something
                            data = {"occupation_name": other_occupation}
                            try:
                                insert_data("occupations", data)
                                updated_data[column] = occupation_name_to_id[other_occupation]
                                st.success("New occupation added successfully!")
                            except Exception as e:
                                st.error(f"Failed to add occupation: {e}")
                    else:
                        updated_data[column] = occupation_name_to_id[selected_occupation]
                
                elif column == "state_id":
                    state = fetch_data("states")
                    state_names = state["state_name"].tolist()
                    state_name_to_id = dict(zip(state["state_name"], state["state_id"]))
                    state_id_to_name = dict(zip(state["state_id"], state["state_name"]))

                    selected_state = st.selectbox(
                        f"Update {column_display}",
                        state_names,
                        index=state_names.index(state_id_to_name[value]) if value in state_name_to_id.values() else 0
                    )
                    updated_data[column] = state_name_to_id[selected_state]
                
                elif column == "city_id":
                    city = get_cities_by_state(updated_data.get("state_id"))
                    city_names = city["city_name"].tolist()
                    city_name_to_id = dict(zip(city["city_name"], city["city_id"]))
                    city_id_to_name = {v: k for k, v in city_name_to_id.items()}


                    selected_city = st.selectbox(
                        f"Update {column_display}",
                        city_names,
                        index=city_names.index(city_id_to_name[value]) if value in city_name_to_id.values() else 0
                    )
                    updated_data[column] = city_name_to_id[selected_city]

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

        if "status" not in selected_row:
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
