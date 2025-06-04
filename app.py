
import streamlit as st
import json
import os

SERVICE_FILE = "service_models.json"
PARTS_FILE = "parts_catalog.json"
CONFIG_FILE = "config.json"

# Load data
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

service_models = load_json(SERVICE_FILE)
parts_catalog = load_json(PARTS_FILE)
config = load_json(CONFIG_FILE)

labor_rate = config.get("Labor Rate", 0.0)
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

if mode == "View Service Menu":
    display_names = sorted([model["Display Name"] for model in service_models])
    selected_display = st.selectbox("Select Vehicle", display_names)

    selected_model = next((m for m in service_models if m["Display Name"] == selected_display), None)
    if selected_model:
        intervals = [svc["Interval"] for svc in selected_model["Services"]]
        selected_interval = st.selectbox("Select Service Interval", intervals)

        svc = next((s for s in selected_model["Services"] if s["Interval"] == selected_interval), None)
        if svc:
            from print_utils import generate_service_html, download_link

            parts = [get_part_info(p) for p in svc.get("Parts Used", []) if get_part_info(p)]

            html_out = generate_service_html(
                model_name=selected_model["Display Name"],
                interval=svc["Interval"],
                description=svc.get("What's Included", ""),
                parts=parts,
                labor_hours=svc.get("Labor Hours", 0.0),
                total_price=calculate_total_price(svc)
            )
            st.markdown(download_link(html_out, "Service_Interval_Printout.html"), unsafe_allow_html=True)

            st.markdown(f"### {svc['Interval']}")
            st.write(svc.get("What's Included", ""))

            st.markdown("#### Parts Used:")
            for part in parts:
                st.write(f"- **{part['Part Name']}** ({part['Part Number']}): ${part['Unit Price']:.2f}")

            st.write(f"**Labor:** {svc.get('Labor Hours', 0.0):.2f} hrs")
            st.markdown(f"### 💰 Total Price: **${calculate_total_price(svc):.2f}**")
