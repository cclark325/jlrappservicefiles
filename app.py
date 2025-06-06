
import streamlit as st
import json
import os

# --- Config ---
SERVICE_FILE = "service_models.json"
PARTS_FILE = "parts_catalog.json"
TEMPLATE_FILE = "service_templates.json"
CONFIG_FILE = "config.json"

# --- Utility Functions ---
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def get_part_info(part_number):
    return next((p for p in parts_catalog if p["Part Number"] == part_number), None)

def calculate_total_price(service, rate):
    parts_total = sum(get_part_info(p)["Unit Price"] for p in service.get("Parts Used", []) if get_part_info(p))
    labor_total = service.get("Labor Hours", 0.0) * rate
    return parts_total + labor_total

# --- Load Data ---
service_models = load_json(SERVICE_FILE)
parts_catalog = load_json(PARTS_FILE)
service_templates = load_json(TEMPLATE_FILE)
config = load_json(CONFIG_FILE)

labor_rate = config.get("Labor Rate", 170.0)
service_pin = config.get("Service Admin PIN", "0000")
parts_pin = config.get("Parts Admin PIN", "0000")

st.set_page_config(page_title="Service Manager", layout="wide")

# Inject custom styles for modern UI
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
}
div[data-testid="stSidebar"] {
    background-color: #f3f4f6;
}
h1, h2, h3 {
    color: #111827;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
}
.stButton>button {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    padding: 0.4em 1em;
    font-weight: 500;
}
.stButton>button:hover {
    background-color: #1d4ed8;
}
[data-testid="stExpander"] {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 8px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
}
</style>
""")
st.sidebar.markdown(
    f"<img src='https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Jaguar_Land_Rover_Logo.svg/2560px-Jaguar_Land_Rover_Logo.svg.png' width='100%' style='margin-bottom: 20px;'>",
    unsafe_allow_html=True
)
st.sidebar.title("🔧 Service System")

mode = st.sidebar.radio("Select Mode", [
    "👨‍🔧 Advisor Dashboard",
    "🔧 Vehicle Manager",
    "📦 Template Manager",
    "🧰 Parts Manager",
    "⚙️ Labor Rate Settings",
    "🔑 PIN Settings"
])

# --- Advisor Dashboard ---
if mode == "👨‍🔧 Advisor Dashboard":
    st.title("👨‍🔧 Advisor Dashboard")
    if not service_models:
        st.warning("No vehicles available.")
    else:
        names = sorted([v["Display Name"] for v in service_models])
        selected_name = st.selectbox("Select Vehicle", names)
        model = next((m for m in service_models if m["Display Name"] == selected_name), None)
        if model and model.get("Services"):
            intervals = [s["Interval"] for s in model["Services"]]
            selected_interval = st.selectbox("Select Service Interval", intervals)
            svc = next((s for s in model["Services"] if s["Interval"] == selected_interval), None)
            if svc:
                st.markdown(f"### {svc['Interval']}")
                st.write("#### Services Performed:")
                st.write(svc["What's Included"])
                st.markdown("#### Parts Used:")
                for part_num in svc.get("Parts Used", []):
                    part = get_part_info(part_num)
                    if part:
                        st.write(f"- **{part['Part Name']}** ({part['Part Number']}): ${part['Unit Price']:.2f}")
                st.write(f"**Labor Hours:** {svc.get('Labor Hours', 0.0):.1f}")
                total = calculate_total_price(svc, labor_rate)
                st.markdown(f"### 💰 Total Price: **${total:.2f}**")
        else:
            st.info("This vehicle has no defined service intervals.")

# --- Vehicle Manager ---
elif mode == "🔧 Vehicle Manager":
    st.title("🔧 Vehicle Manager")
    pin = st.text_input("Enter Service Admin PIN", type="password")
    if pin == service_pin:
        
        names = [v["Display Name"] for v in service_models]
        selected_name = st.selectbox("Select Vehicle", names)
        idx = next((i for i, v in enumerate(service_models) if v["Display Name"] == selected_name), None)
        selected_model = service_models[idx]

        st.text_input("Edit Display Name", value=selected_model["Display Name"], key="edit_display_name")

        st.markdown("### Existing Intervals")
        intervals_to_delete = []
        for i, svc in enumerate(selected_model.get("Services", [])):
            with st.expander(f"Edit: {svc['Interval']}"):
                svc["Interval"] = st.text_input(f"Interval {i}", value=svc["Interval"], key=f"int_{i}")
                svc["What's Included"] = st.text_area(f"Included Services {i}", value=svc["What's Included"], key=f"inc_{i}")
                svc["Labor Hours"] = st.number_input(f"Labor Hours {i}", value=svc["Labor Hours"], step=0.1, key=f"lh_{i}")
                valid_parts = [p["Part Number"] for p in parts_catalog]
                svc["Parts Used"] = st.multiselect(f"Parts {i}", options=valid_parts, default=[p for p in svc.get("Parts Used", []) if p in valid_parts], key=f"parts_{i}")
                if st.button(f"Delete Interval {i}", key=f"del_{i}"):
                    intervals_to_delete.append(i)

        if intervals_to_delete:
            for i in sorted(intervals_to_delete, reverse=True):
                selected_model["Services"].pop(i)
            service_models[idx] = selected_model
            save_json(SERVICE_FILE, service_models)
            st.warning("Deleted selected intervals.")
            st.experimental_rerun()

        st.markdown("### ➕ Add New Interval")
        with st.form("add_int"):
            new_int = st.text_input("Interval Name")
            template = st.selectbox("Select Template", [t["Template Name"] for t in service_templates])
            parts = st.multiselect("Select Parts", [p["Part Number"] for p in parts_catalog])
            submit = st.form_submit_button("Add")
            if submit:
                selected_template = next((t for t in service_templates if t["Template Name"] == template), {})
                labor = selected_template["Labor Hours"] if selected_template else 0.0
                selected_model["Services"].append({
                    "Interval": new_int,
                    "What's Included": template,
                    "Labor Hours": labor,
                    "Parts Used": parts
                })
                service_models[idx] = selected_model
                save_json(SERVICE_FILE, service_models)
                st.success("Interval added.")
                st.experimental_rerun()

        new_display_name = st.text_input("Display Name")
        if st.button("Add Vehicle"):
            if new_display_name and new_display_name not in names:
                service_models.append({"Display Name": new_display_name, "Services": []})
                save_json(SERVICE_FILE, service_models)
                st.success("Vehicle added.")
                st.experimental_rerun()
    else:
        st.warning("Enter correct Service Admin PIN.")

# --- Template Manager ---
elif mode == "📦 Template Manager":
    st.title("📦 Service Templates")
    pin = st.text_input("Enter Service Admin PIN", type="password", key="tpl_pin")
    if pin == service_pin:
        st.markdown("### Add Template")
        name = st.text_input("Template Name")
        labor = st.number_input("Labor Hours", min_value=0.0, step=0.1)
        if st.button("Save Template"):
            service_templates.append({
                "Template Name": name,
                "Interval": name,
                "What's Included": name,
                "Labor Hours": labor,
                "Parts Used": []
            })
            save_json(TEMPLATE_FILE, service_templates)
            st.success("Template saved.")
            st.experimental_rerun()

        st.markdown("### Existing Templates")
        for i, tpl in enumerate(service_templates):
            with st.expander(tpl["Template Name"]):
                tpl["Template Name"] = st.text_input(f"Name {i}", value=tpl["Template Name"], key=f"tpl_{i}")
                tpl["Labor Hours"] = st.number_input(f"Labor {i}", value=tpl["Labor Hours"], step=0.1, key=f"lab_{i}")
                if st.button(f"Save Template {i}", key=f"save_tpl_{i}"):
                    save_json(TEMPLATE_FILE, service_templates)
                    st.success("Saved.")
                if st.button(f"Delete Template {i}", key=f"del_tpl_{i}"):
                    service_templates.pop(i)
                    save_json(TEMPLATE_FILE, service_templates)
                    st.warning("Deleted.")
                    st.experimental_rerun()
    else:
        st.warning("Enter correct Service Admin PIN.")

# --- Parts Manager ---
elif mode == "🧰 Parts Manager":
    st.title("🧰 Parts Manager")
    pin = st.text_input("Enter Parts Admin PIN", type="password", key="parts_pin")
    if pin == parts_pin:
        for i, part in enumerate(parts_catalog):
            with st.expander(f"{part['Part Name']} ({part['Part Number']})"):
                part["Part Name"] = st.text_input(f"Name {i}", value=part["Part Name"], key=f"pn_{i}")
                part["Part Number"] = st.text_input(f"Number {i}", value=part["Part Number"], key=f"pnum_{i}")
                part["Unit Price"] = st.number_input(f"Price {i}", value=part["Unit Price"], step=0.01, key=f"price_{i}")

        st.markdown("### ➕ Add New Part")
        pname = st.text_input("Part Name")
        pnum = st.text_input("Part Number")
        pprice = st.number_input("Unit Price", min_value=0.0, step=0.01)
        if st.button("Add Part"):
            parts_catalog.append({"Part Name": pname, "Part Number": pnum, "Unit Price": pprice})
            save_json(PARTS_FILE, parts_catalog)
            st.success("Part added.")
            st.experimental_rerun()

        if st.button("Save All Parts"):
            save_json(PARTS_FILE, parts_catalog)
            st.success("All saved.")
    else:
        st.warning("Enter correct Parts Admin PIN.")

# --- Labor Rate Settings ---
elif mode == "⚙️ Labor Rate Settings":
    st.title("⚙️ Labor Rate Settings")
    pin = st.text_input("Enter Service Admin PIN", type="password", key="rate_pin")
    if pin == service_pin:
        new_rate = st.number_input("Set Labor Rate", min_value=0.0, value=labor_rate, step=1.0)
        if st.button("Update Labor Rate"):
            config["Labor Rate"] = new_rate
            save_json(CONFIG_FILE, config)
            st.success("Labor rate updated.")
    else:
        st.warning("Enter correct Service Admin PIN.")

# --- PIN Settings ---
elif mode == "🔑 PIN Settings":
    st.title("🔑 PIN Settings")
    pin = st.text_input("Enter Current Service Admin PIN", type="password", key="pin_check")
    if pin == service_pin:
        new_service = st.text_input("New Service PIN", type="password")
        new_parts = st.text_input("New Parts PIN", type="password")
        if st.button("Update PINs"):
            config["Service Admin PIN"] = new_service
            config["Parts Admin PIN"] = new_parts
            save_json(CONFIG_FILE, config)
            st.success("PINs updated.")
    else:
        st.warning("Enter correct current Service Admin PIN.")
