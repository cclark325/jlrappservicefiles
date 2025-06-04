
import streamlit as st
import json
import os

SERVICE_FILE = "service_models.json"
PARTS_FILE = "parts_catalog.json"
ADMIN_PIN = "4397"

# Load data
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

service_models = load_json(SERVICE_FILE)
parts_catalog = load_json(PARTS_FILE)

# Utility functions
def get_part_info(part_number):
    return next((p for p in parts_catalog if p["Part Number"] == part_number), None)

def calculate_total_price(service):
    parts_total = sum(get_part_info(p)["Unit Price"] for p in service.get("Parts Used", []) if get_part_info(p))
    labor_total = service.get("Labor Hours", 0.0) * service.get("Labor Rate", 0.0)
    return parts_total + labor_total

st.set_page_config(page_title="Service Menu", layout="wide")
st.title("Land Rover / Jaguar Service Menu")

mode = st.sidebar.radio("Choose mode", ["View Service Menu", "Admin Panel 🔐", "Parts Manager 🧰"])

if mode == "View Service Menu":
    display_names = sorted([model["Display Name"] for model in service_models])
    selected_display = st.selectbox("Select Vehicle", display_names)

    selected_model = next((m for m in service_models if m["Display Name"] == selected_display), None)
    if selected_model:
        intervals = [svc["Interval"] for svc in selected_model["Services"]]
        selected_interval = st.selectbox("Select Service Interval", intervals)

        svc = next((s for s in selected_model["Services"] if s["Interval"] == selected_interval), None)
        if svc:
            st.markdown(f"### {svc['Interval']}")
            st.write(svc["What’s Included"])

            st.markdown("#### Parts Used:")
            for part_num in svc.get("Parts Used", []):
                part = get_part_info(part_num)
                if part:
                    st.write(f"- **{part['Part Name']}** ({part['Part Number']}): ${part['Unit Price']:.2f}")

            st.write(f"**Labor:** {svc.get('Labor Hours', 0.0):.2f} hrs")
            st.markdown(f"### 💰 Total Price: **${calculate_total_price(svc):.2f}**")

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
                save_json(SERVICE_FILE, service_models)
                st.success("Vehicle info updated.")

            st.markdown("---")
            st.markdown("### Edit Service Intervals")
            for i, svc in enumerate(selected_model["Services"]):
                with st.expander(f"Edit: {svc['Interval']}"):
                    svc["Interval"] = st.text_input(f"Interval {i+1}", value=svc["Interval"], key=f"int_{i}")
                    svc["What’s Included"] = st.text_area(f"What's Included {i+1}", value=svc["What’s Included"], key=f"desc_{i}")
                    svc["Labor Hours"] = st.number_input(f"Labor Hours {i+1}", value=svc.get("Labor Hours", 0.0), step=0.1, key=f"lh_{i}")
                    svc["Labor Rate"] = st.number_input(f"Labor Rate {i+1}", value=svc.get("Labor Rate", 0.0), step=1.0, key=f"lr_{i}")

                    current_parts = svc.get("Parts Used", [])
                    st.write("Parts Used:")
                    new_parts = st.multiselect(
                        f"Select Parts {i+1}",
                        options=[p["Part Number"] for p in parts_catalog],
                        default=current_parts,
                        key=f"parts_{i}"
                    )
                    svc["Parts Used"] = new_parts

            st.markdown("### Add New Interval")
            with st.form("add_interval_form"):
                new_int = st.text_input("New Interval")
                new_desc = st.text_area("New What's Included")
                new_labor_hours = st.number_input("New Labor Hours", min_value=0.0, step=0.1)
                new_labor_rate = st.number_input("New Labor Rate", min_value=0.0, step=1.0)
                new_parts = st.multiselect("New Parts Used", options=[p["Part Number"] for p in parts_catalog])
                add_submitted = st.form_submit_button("Add Interval")
                if add_submitted:
                    selected_model["Services"].append({
                        "Interval": new_int,
                        "What’s Included": new_desc,
                        "Labor Hours": new_labor_hours,
                        "Labor Rate": new_labor_rate,
                        "Parts Used": new_parts
                    })
                    service_models[selected_index] = selected_model
                    save_json(SERVICE_FILE, service_models)
                    st.success("New interval added successfully!")

            if st.button("💾 Save All Changes"):
                save_json(SERVICE_FILE, service_models)
                st.success("All changes saved.")

elif mode == "Parts Manager 🧰":
    st.subheader("Parts Catalog Editor (Admin Only)")
    pin = st.text_input("Enter Admin PIN", type="password", key="parts_pin")
    if pin == ADMIN_PIN:
        st.success("Access granted.")

        st.markdown("### Existing Parts")
        for i, part in enumerate(parts_catalog):
            with st.expander(f"{part['Part Name']} ({part['Part Number']})"):
                part["Part Name"] = st.text_input(f"Part Name {i}", value=part["Part Name"], key=f"name_{i}")
                part["Part Number"] = st.text_input(f"Part Number {i}", value=part["Part Number"], key=f"num_{i}")
                part["Unit Price"] = st.number_input(f"Unit Price {i}", value=part["Unit Price"], key=f"price_{i}")

        st.markdown("### Add New Part")
        with st.form("add_part_form"):
            pname = st.text_input("Part Name")
            pnum = st.text_input("Part Number")
            pprice = st.number_input("Unit Price", min_value=0.0, format="%.2f")
            add_part = st.form_submit_button("Add Part")
            if add_part:
                parts_catalog.append({
                    "Part Name": pname,
                    "Part Number": pnum,
                    "Unit Price": pprice
                })
                save_json(PARTS_FILE, parts_catalog)
                st.success("New part added.")

        if st.button("💾 Save All Parts"):
            save_json(PARTS_FILE, parts_catalog)
            st.success("All part changes saved.")
    else:
        st.warning("Enter admin PIN to manage parts.")
