
import streamlit as st
import json
import os

DATA_FILE = "service_models.json"
ADMIN_PIN = "4397"

# Load grouped model data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        service_models = json.load(f)
else:
    service_models = []

st.set_page_config(page_title="Service Menu", layout="wide")
st.title("Land Rover / Jaguar Service Menu")

mode = st.sidebar.radio("Choose mode", ["View Service Menu", "Admin Panel 🔐"])

if mode == "View Service Menu":
    display_names = sorted([model["Display Name"] for model in service_models])
    selected_display = st.selectbox("Select Vehicle", display_names)

    selected_model = next((m for m in service_models if m["Display Name"] == selected_display), None)
    if selected_model:
        for svc in selected_model["Services"]:
            st.markdown(f"### {svc['Interval']}")
            st.write(svc["What’s Included"])
            st.markdown(f"**Price: ${svc['Price']:.2f}**")
            st.markdown("---")

elif mode == "Admin Panel 🔐":
    st.subheader("Admin Access Required")
    pin = st.text_input("Enter Admin PIN", type="password")
    if pin == ADMIN_PIN:
        st.success("Access granted.")

        model_names = sorted([m["Display Name"] for m in service_models])
        selected_display = st.selectbox("Select Vehicle to Edit", model_names)
        selected_index = next((i for i, m in enumerate(service_models) if m["Display Name"] == selected_display), None)

        if selected_index is not None:
            selected_model = service_models[selected_index]

            st.markdown("### Edit Vehicle Info")
            new_model_code = st.text_input("Model (Internal Code)", value=selected_model["Model"])
            new_display_name = st.text_input("Display Name", value=selected_model["Display Name"])

            if st.button("💾 Save Vehicle Info"):
                selected_model["Model"] = new_model_code
                selected_model["Display Name"] = new_display_name
                service_models[selected_index] = selected_model
                with open(DATA_FILE, "w") as f:
                    json.dump(service_models, f, indent=4)
                st.success("Vehicle info updated.")

            st.markdown("---")
            st.markdown("### Edit Service Intervals")
            for i, svc in enumerate(selected_model["Services"]):
                with st.expander(f"Edit: {svc['Interval']}"):
                    new_interval = st.text_input(f"Interval {i+1}", value=svc["Interval"], key=f"int_{i}")
                    new_desc = st.text_area(f"What's Included {i+1}", value=svc["What’s Included"], key=f"desc_{i}")
                    new_price = st.number_input(f"Price {i+1}", value=svc["Price"], key=f"price_{i}")

                    svc["Interval"] = new_interval
                    svc["What’s Included"] = new_desc
                    svc["Price"] = new_price

            st.markdown("### Add New Interval")
            with st.form("add_interval_form"):
                new_int = st.text_input("New Interval")
                new_desc = st.text_area("New What's Included")
                new_price = st.number_input("New Price", min_value=0.0, format="%.2f")
                add_submitted = st.form_submit_button("Add Interval")
                if add_submitted:
                    selected_model["Services"].append({
                        "Interval": new_int,
                        "What’s Included": new_desc,
                        "Price": new_price
                    })
                    service_models[selected_index] = selected_model
                    with open(DATA_FILE, "w") as f:
                        json.dump(service_models, f, indent=4)
                    st.success("New interval added successfully!")

            if st.button("💾 Save All Changes"):
                with open(DATA_FILE, "w") as f:
                    json.dump(service_models, f, indent=4)
                st.success("All changes saved.")

    else:
        st.warning("Enter the correct PIN to access admin features.")
