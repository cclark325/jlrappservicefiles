
import streamlit as st
import json
import os

SERVICE_FILE = "service_models.json"
PARTS_FILE = "parts_catalog.json"
CONFIG_FILE = "config.json"
TEMPLATE_FILE = "service_templates.json"

def load_json(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"Error loading {file_path}. Please check formatting.")
    return []

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

service_models = load_json(SERVICE_FILE)
parts_catalog = load_json(PARTS_FILE)
config = load_json(CONFIG_FILE) or {}
service_templates = load_json(TEMPLATE_FILE)

labor_rate = config.get("Labor Rate", 100.0)
service_pin = config.get("Service Admin PIN", "0000")
parts_pin = config.get("Parts Admin PIN", "0000")

def get_part_info(part_number):
    return next((p for p in parts_catalog if p["Part Number"] == part_number), None)

def calculate_total_price(service):
    parts_total = sum(get_part_info(p)["Unit Price"] for p in service.get("Parts Used", []) if get_part_info(p))
    labor_total = service.get("Labor Hours", 0.0) * labor_rate
    return parts_total + labor_total

st.set_page_config(page_title="Service Menu", layout="wide")
st.title("Land Rover / Jaguar Service Menu")

mode = st.sidebar.radio("Choose mode", [
    "View Service Menu",
    "Admin Panel 🔐",
    "Parts Manager 🧰",
    "Labor Rate Settings ⚙️",
    "PIN Settings 🔑"
])

if mode == "Admin Panel 🔐":
    st.subheader("Service Admin Panel")
    pin = st.text_input("Enter Service Admin PIN", type="password")
    if pin == service_pin:
        st.success("Access granted.")

        st.markdown("### ➕ Add New Vehicle")
        with st.form("add_vehicle_form"):
            new_model_code = st.text_input("New Model Code")
            new_display_name = st.text_input("New Display Name")
            submitted = st.form_submit_button("Add Vehicle")
            if submitted:
                if any(m["Display Name"] == new_display_name for m in service_models):
                    st.error("Vehicle with this display name already exists.")
                else:
                    new_vehicle = {
                        "Model": new_model_code,
                        "Display Name": new_display_name,
                        "Services": []
                    }
                    service_models.append(new_vehicle)
                    save_json(SERVICE_FILE, service_models)
                    st.success("New vehicle added.")
                    st.rerun()

        model_names = sorted([m["Display Name"] for m in service_models])
        selected_display = st.selectbox("Select Vehicle to Edit", model_names)
        selected_index = next((i for i, m in enumerate(service_models) if m["Display Name"] == selected_display), None)

        if selected_index is not None:
            selected_model = service_models[selected_index]
            new_display_name = st.text_input("Display Name", value=selected_model["Display Name"])
            new_model_code = st.text_input("Model Code", value=selected_model.get("Model", ""))

            if st.button("💾 Save Vehicle Info"):
                selected_model["Model"] = new_model_code
                selected_model["Display Name"] = new_display_name
                service_models[selected_index] = selected_model
                save_json(SERVICE_FILE, service_models)
                st.success("Vehicle info updated.")

            st.markdown("### 🔁 Add Service from Template")
            template_names = [tpl["Template Name"] for tpl in service_templates]
            selected_template = st.selectbox("Select Template", template_names)
            if st.button("➕ Add Selected Template"):
                tpl = next((t for t in service_templates if t["Template Name"] == selected_template), None)
                if tpl:
                    selected_model["Services"].append({
                        "Interval": tpl["Interval"],
                        "What's Included": tpl["What's Included"],
                        "Labor Hours": tpl["Labor Hours"],
                        "Parts Used": tpl["Parts Used"]
                    })
                    service_models[selected_index] = selected_model
                    save_json(SERVICE_FILE, service_models)
                    st.success("Template added to vehicle.")
                    st.rerun()

            st.markdown("### Edit Service Intervals")
            indices_to_delete = []
            for i, svc in enumerate(selected_model["Services"]):
                with st.expander(f"Edit: {svc['Interval']}"):
                    svc["Interval"] = st.text_input(f"Interval {i+1}", value=svc["Interval"], key=f"int_{i}")
                    svc["What's Included"] = st.text_area(f"What's Included {i+1}", value=svc.get("What's Included", ""), key=f"desc_{i}")
                    svc["Labor Hours"] = st.number_input(f"Labor Hours {i+1}", value=svc.get("Labor Hours", 0.0), step=0.1, key=f"lh_{i}")
                    current_parts = svc.get("Parts Used", [])
                    part_options = [p["Part Number"] for p in parts_catalog]
                    valid_defaults = [p for p in current_parts if p in part_options]
                    new_parts = st.multiselect(
                        f"Select Parts {i+1}",
                        options=part_options,
                        default=valid_defaults,
                        key=f"parts_{i}"
                    )
                    svc["Parts Used"] = new_parts

                    if st.button(f"❌ Delete This Service", key=f"del_{i}"):
                        indices_to_delete.append(i)

            if indices_to_delete:
                for i in sorted(indices_to_delete, reverse=True):
                    del selected_model["Services"][i]
                service_models[selected_index] = selected_model
                save_json(SERVICE_FILE, service_models)
                st.rerun()

            st.markdown("### ➕ Add New Custom Interval")
            with st.form("add_interval_form"):
                new_int = st.text_input("New Interval")
                new_desc = st.text_area("New What's Included")
                new_labor_hours = st.number_input("New Labor Hours", min_value=0.0, step=0.1)
                new_parts = st.multiselect("New Parts Used", options=[p["Part Number"] for p in parts_catalog])
                add_submitted = st.form_submit_button("Add Interval")
                if add_submitted:
                    selected_model["Services"].append({
                        "Interval": new_int,
                        "What's Included": new_desc,
                        "Labor Hours": new_labor_hours,
                        "Parts Used": new_parts
                    })
                    service_models[selected_index] = selected_model
                    save_json(SERVICE_FILE, service_models)
                    st.success("New interval added.")
                    st.rerun()

        st.markdown("### 🧰 Manage Service Templates")
        with st.form("add_template_form"):
            tpl_name = st.text_input("Template Name")
            tpl_interval = st.text_input("Template Interval")
            tpl_desc = st.text_area("Template What's Included")
            tpl_labor = st.number_input("Template Labor Hours", min_value=0.0, step=0.1)
            tpl_parts = st.multiselect("Template Parts Used", options=[p["Part Number"] for p in parts_catalog])
            tpl_submit = st.form_submit_button("Save Template")
            if tpl_submit:
                new_template = {
                    "Template Name": tpl_name,
                    "Interval": tpl_interval,
                    "What's Included": tpl_desc,
                    "Labor Hours": tpl_labor,
                    "Parts Used": tpl_parts
                }
                service_templates.append(new_template)
                save_json(TEMPLATE_FILE, service_templates)
                st.success("Template saved.")
                st.rerun()
