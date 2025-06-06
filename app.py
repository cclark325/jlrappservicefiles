
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
            st.error(f"Error loading {file_path}. Check formatting.")
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

mode = st.sidebar.radio("Select Mode", [
    "👨‍🔧 Advisor Dashboard",
    "🔧 Vehicle Manager",
    "📦 Template Manager",
    "🧰 Parts Manager",
    "⚙️ Labor Rate Settings",
    "🔑 PIN Settings"
])

if mode == "👨‍🔧 Advisor Dashboard":
    st.header("Advisor View")
    display_names = sorted([model["Display Name"] for model in service_models

    if not display_names:
        st.warning("No vehicles available.")
    else:
        selected_vehicle = st.selectbox("Select Vehicle", display_names)
        model = next((m for m in service_models if m["Display Name"] == selected_vehicle), None)
        if model and model.get("Services"):
            intervals = [svc["Interval"] for svc in model["Services"]]
            selected_interval = st.selectbox("Select Interval", intervals)
            svc = next((s for s in model["Services"] if s["Interval"] == selected_interval), None)
            if svc:
                st.subheader(f"Service Interval: {svc['Interval']}")
                st.markdown(svc.get("What's Included", ""))
                st.markdown("### Parts Used:")
                for p in svc.get("Parts Used", [
:
                    part = get_part_info(p)
                    if part:
                        st.write(f"- **{part['Part Name']}** ({part['Part Number']}): ${part['Unit Price']:.2f}")
                st.write(f"**Labor Hours:** {svc.get('Labor Hours', 0.0)}")
                st.write(f"💰 **Total Price:** ${calculate_total_price(svc):.2f}")
        else:
            st.info("No service intervals for this vehicle.")

elif mode == "🔧 Vehicle Manager":
    st.header("Manage Vehicles and Services")
    pin = st.text_input("Enter Service Admin PIN", type="password")
    if pin == service_pin:
        selected_display = st.selectbox("Edit Existing Vehicle", [m["Display Name"] for m in service_models

        selected_model = next((m for m in service_models if m["Display Name"] == selected_display), None)
        idx = service_models.index(selected_model)

        st.markdown("### Edit Vehicle")
        selected_model["Display Name"] = st.text_input("Display Name", value=selected_model["Display Name"

        selected_model["Model"] = st.text_input("Model Code", value=selected_model.get("Model", ""))
        if st.button("💾 Save Vehicle Info"):
            service_models[idx] = selected_model
            save_json(SERVICE_FILE, service_models)
            st.success("Vehicle saved.")

        st.markdown("### Add Service Interval")
        with st.form("add_interval_form"):
            interval = st.text_input("Interval Name")
            selected_templates = st.multiselect("Templates to include", [t["Template Name"] for t in service_templates

            # custom_desc = st.text_area("Additional Notes")
            submitted = st.form_submit_button("Add Interval")
            if submitted:
                combined_desc = ""
                combined_labor = 0.0
                combined_parts = []
                for name in selected_templates:
                    tpl = next(t for t in service_templates if t["Template Name"] == name)
                    combined_desc += f"\n- {tpl.get('Template Name', tpl.get('Interval', 'Unnamed Template'))}"
                    combined_labor += tpl.get("Labor Hours", 0.0)
                    for part in tpl.get("Parts Used", [
:
                        if part not in combined_parts:
                            combined_parts.append(part)
                svc = {
                    "Interval": interval,
                    "What's Included": combined_desc,
                    "Labor Hours": combined_labor,
                    "Parts Used": combined_parts
                }
                selected_model.setdefault("Services", [
.append(svc)
                service_models[idx] = selected_model
                save_json(SERVICE_FILE, service_models)
                st.success("Service interval added.")

        st.markdown("### Existing Intervals")
        for i, svc in enumerate(selected_model.get("Services", [
):
            with st.expander(f"{svc['Interval']}"):
                st.text(svc.get("What's Included", ""))
                if st.button("❌ Delete", key=f"del_{i}"):
                    selected_model["Services"].pop(i)
                    service_models[idx] = selected_model
                    save_json(SERVICE_FILE, service_models)
                    st.rerun()

        st.markdown("### ➕ Add New Vehicle")
        with st.form("add_vehicle_form"):
            new_model = st.text_input("New Model Code")
            new_display = st.text_input("New Display Name")
            submitted = st.form_submit_button("Add Vehicle")
            if submitted:
                if any(m["Display Name"] == new_display for m in service_models):
                    st.error("Vehicle already exists.")
                else:
                    new_vehicle = {
                        "Model": new_model,
                        "Display Name": new_display,
                        "Services": []
                    }
                    service_models.append(new_vehicle)
                    save_json(SERVICE_FILE, service_models)
                    st.success("Vehicle added.")
                    st.rerun()
    else:
        st.warning("Enter valid Service Admin PIN.")

elif mode == "📦 Template Manager":
    st.header("Service Template Manager")
    pin = st.text_input("Enter Service Admin PIN", type="password", key="template_pin")
    if pin == service_pin:
        st.markdown("### Add Template")
        with st.form("add_template_form"):
            name = st.text_input("Template Name")
            desc = st.text_area("What's Included")
            labor = st.number_input("Labor Hours", min_value=0.0, step=0.1)
            parts = st.multiselect("Parts Used", options=[p["Part Number"] for p in parts_catalog

            submitted = st.form_submit_button("Save Template")
            if submitted:
                service_templates.append({
                    "Template Name": name,
                    "Interval": name,
                    "What's Included": desc,
                    "Labor Hours": labor,
                    "Parts Used": parts
                })
                save_json(TEMPLATE_FILE, service_templates)
                st.success("Template saved.")
                st.rerun()

        st.markdown("### Existing Templates")
        for i, tpl in enumerate(service_templates):
            with st.expander(tpl["Template Name"
:
                st.write(tpl["What's Included"

                st.write(f"Labor: {tpl['Labor Hours']} hrs")
                st.write(f"Parts: {', '.join(tpl['Parts Used'
}")
                if st.button("❌ Delete Template", key=f"tpl_del_{i}"):
                    service_templates.pop(i)
                    save_json(TEMPLATE_FILE, service_templates)
                    st.rerun()
    else:
        st.warning("Enter valid PIN to manage templates.")


elif mode == "🧰 Parts Manager":
    st.header("Parts Catalog Editor")
    pin = st.text_input("Enter Parts Admin PIN", type="password", key="parts_pin")
    if pin == parts_pin:
        st.success("Access granted.")
        for i, part in enumerate(parts_catalog):
            with st.expander(f"{part['Part Name']} ({part['Part Number']})"):
                part["Part Name"] = st.text_input(f"Part Name {i}", value=part["Part Name"], key=f"name_{i}")
                part["Part Number"] = st.text_input(f"Part Number {i}", value=part["Part Number"], key=f"num_{i}")
                part["Unit Price"] = st.number_input(f"Unit Price {i}", value=part["Unit Price"], key=f"price_{i}")
        if st.button("💾 Save All Parts"):
            save_json(PARTS_FILE, parts_catalog)
            st.success("All parts saved.")
    else:
        st.warning("Enter correct Parts Admin PIN.")

elif mode == "🔑 PIN Settings":
    st.header("Update Admin PINs")
    pin = st.text_input("Enter Current Service Admin PIN", type="password", key="pin_pin")
    if pin == service_pin:
        new_service_pin = st.text_input("New Service Admin PIN", type="password")
        new_parts_pin = st.text_input("New Parts Admin PIN", type="password")
        if st.button("Update Admin PINs"):
            config["Service Admin PIN"] = new_service_pin
            config["Parts Admin PIN"] = new_parts_pin
            save_json(CONFIG_FILE, config)
            st.success("PINs updated.")
    else:
        st.warning("Enter correct current Service Admin PIN.")


elif mode == "⚙️ Labor Rate Settings":
    st.header("Global Labor Rate Setting")
    pin = st.text_input("Enter Service Admin PIN", type="password", key="rate_pin")
    if pin == service_pin:
        new_rate = st.number_input("Labor Rate ($/hr)", min_value=0.0, value=labor_rate, step=1.0)
        if st.button("💾 Update Labor Rate"):
            config["Labor Rate"] = new_rate
            save_json(CONFIG_FILE, config)
            st.success("Labor rate updated. Refresh to apply.")
    else:
        st.warning("Enter correct Service Admin PIN.")

# Patch Template Manager for edit support
elif mode == "📦 Template Manager":
    st.header("Service Template Manager")
    pin = st.text_input("Enter Service Admin PIN", type="password", key="template_pin")
    if pin == service_pin:
        st.markdown("### Add Template")
        with st.form("add_template_form"):
            name = st.text_input("Template Name")
            desc = st.text_area("What's Included")
            labor = st.number_input("Labor Hours", min_value=0.0, step=0.1)
            parts = st.multiselect("Parts Used", options=[p["Part Number"] for p in parts_catalog

            submitted = st.form_submit_button("Save Template")
            if submitted:
                service_templates.append({
                    "Template Name": name,
                    "Interval": name,
                    "What's Included": desc,
                    "Labor Hours": labor,
                    "Parts Used": parts
                })
                save_json(TEMPLATE_FILE, service_templates)
                st.success("Template saved.")
                st.rerun()

        st.markdown("### Existing Templates")
        for i, tpl in enumerate(service_templates):
            with st.expander(tpl["Template Name"
:
                tpl["Template Name"] = st.text_input(f"Edit Template Name {i}", value=tpl["Template Name"], key=f"tpl_name_{i}")
                tpl["What's Included"] = st.text_area(f"Edit What's Included {i}", value=tpl["What's Included"], key=f"tpl_desc_{i}")
                tpl["Labor Hours"] = st.number_input(f"Edit Labor {i}", min_value=0.0, value=tpl["Labor Hours"], step=0.1, key=f"tpl_labor_{i}")
                tpl["Parts Used"] = st.multiselect(f"Edit Parts {i}", options=[p["Part Number"] for p in parts_catalog], default=tpl["Parts Used"], key=f"tpl_parts_{i}")
                if st.button(f"💾 Save Changes to Template {i}", key=f"tpl_save_{i}"):
                    service_templates[i] = tpl
                    save_json(TEMPLATE_FILE, service_templates)
                    st.success("Template updated.")
                if st.button(f"❌ Delete Template {i}", key=f"tpl_del_{i}"):
                    service_templates.pop(i)
                    save_json(TEMPLATE_FILE, service_templates)
                    st.rerun()
    else:
        st.warning("Enter valid PIN to manage templates.")
