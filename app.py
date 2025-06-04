
import streamlit as st
import json
import os

DATA_FILE = "service_intervals.json"
ADMIN_PIN = "4397"

# Load existing services
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        services = json.load(f)
else:
    services = []

st.set_page_config(page_title="Service Menu", layout="wide")
st.title("Land Rover / Jaguar Service Menu")

# Sidebar navigation
mode = st.sidebar.radio("Choose mode", ["View Service Menu", "Admin Panel 🔐"])

if mode == "View Service Menu":
    models = sorted(set(item["Model"] for item in services))
    selected_model = st.selectbox("Select Vehicle Model", models)

    filtered = [item for item in services if item["Model"] == selected_model]

    for item in filtered:
        st.markdown(f"### {item['Interval']}")
        st.write(item["What’s Included"])
        st.markdown(f"**Price: ${item['Price']:.2f}**")
        st.markdown("---")

elif mode == "Admin Panel 🔐":
    st.subheader("Admin Access Required")
    pin = st.text_input("Enter Admin PIN", type="password")
    if pin == ADMIN_PIN:
        st.success("Access granted.")

        st.markdown("### Add New Service Entry")
        with st.form("add_service_form"):
            new_model = st.text_input("Model")
            new_interval = st.text_input("Interval")
            new_description = st.text_area("What's Included")
            new_price = st.number_input("Price", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Service")
            if submitted:
                services.append({
                    "Model": new_model,
                    "Interval": new_interval,
                    "What’s Included": new_description,
                    "Price": new_price
                })
                with open(DATA_FILE, "w") as f:
                    json.dump(services, f, indent=4)
                st.success("Service added successfully!")

        st.markdown("---")
        st.markdown("### Edit Existing Service Entry")
        existing_models = sorted(set(item["Model"] for item in services))
        selected_model = st.selectbox("Select Existing Model", existing_models, key="edit_model")
        matching_intervals = [item["Interval"] for item in services if item["Model"] == selected_model]
        selected_interval = st.selectbox("Select Interval", matching_intervals, key="edit_interval")

        # Find the selected record
        record = next((item for item in services if item["Model"] == selected_model and item["Interval"] == selected_interval), None)

        if record:
            with st.form("edit_service_form"):
                updated_model = st.text_input("Model", value=record["Model"])
                updated_interval = st.text_input("Interval", value=record["Interval"])
                updated_description = st.text_area("What's Included", value=record["What’s Included"])
                updated_price = st.number_input("Price", min_value=0.0, format="%.2f", value=record["Price"])
                update_submitted = st.form_submit_button("Update Service")

                if update_submitted:
                    # Remove original record
                    services = [item for item in services if not (item["Model"] == selected_model and item["Interval"] == selected_interval)]
                    # Add updated record
                    services.append({
                        "Model": updated_model,
                        "Interval": updated_interval,
                        "What’s Included": updated_description,
                        "Price": updated_price
                    })
                    with open(DATA_FILE, "w") as f:
                        json.dump(services, f, indent=4)
                    st.success("Service updated successfully!")

    else:
        st.warning("Enter the correct PIN to access admin features.")
