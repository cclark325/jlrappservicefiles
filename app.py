
import streamlit as st
import json
import os
import pdfkit

SERVICE_FILE = "service_models.json"
PARTS_FILE = "parts_catalog.json"
CONFIG_FILE = "config.json"

# Load and save helpers
def load_json(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"Error loading {file_path}: file is corrupted.")
    return []

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

service_models = load_json(SERVICE_FILE)
parts_catalog = load_json(PARTS_FILE)
config = load_json(CONFIG_FILE) or {}

labor_rate = config.get("Labor Rate", 100.0)
service_pin = config.get("Service Admin PIN", "0000")
parts_pin = config.get("Parts Admin PIN", "0000")

def get_part_info(part_number):
    return next((p for p in parts_catalog if p["Part Number"] == part_number), None)

def calculate_total_price(service):
    parts_total = sum(get_part_info(p)["Unit Price"] for p in service.get("Parts Used", []) if get_part_info(p))
    labor_total = service.get("Labor Hours", 0.0) * labor_rate
    return parts_total + labor_total

def generate_service_html(model_name, interval, description, parts, labor_hours, total_price):
    part_rows = "".join(
        f"<tr><td>{p['Part Name']}</td><td>{p['Part Number']}</td><td>${p['Unit Price']:.2f}</td></tr>"
        for p in parts
    )
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1, h2 {{ color: #2E3B4E; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .total {{ font-weight: bold; font-size: 1.2em; }}
        </style>
    </head>
    <body>
        <h1>Service Sheet</h1>
        <h2>{model_name} - {interval}</h2>
        <p>{description}</p>
        <h3>Parts Used</h3>
        <table>
            <tr><th>Part Name</th><th>Part Number</th><th>Unit Price</th></tr>
            {part_rows}
        </table>
        <p><strong>Labor Hours:</strong> {labor_hours:.2f}</p>
        <p class="total">Total Price: ${total_price:.2f}</p>
    </body>
    </html>
    """
    return html

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
            parts = [get_part_info(p) for p in svc.get("Parts Used", []) if get_part_info(p)]
            html = generate_service_html(
                model_name=selected_model["Display Name"],
                interval=svc["Interval"],
                description=svc.get("What's Included", ""),
                parts=parts,
                labor_hours=svc.get("Labor Hours", 0.0),
                total_price=calculate_total_price(svc)
            )
            pdf_file = "service_sheet.pdf"
            try:
                pdfkit.from_string(html, pdf_file)
                with open(pdf_file, "rb") as f:
                    st.download_button("📄 Download Service Sheet PDF", f, file_name=pdf_file)
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
            st.markdown("---")
            st.components.v1.html(html, height=600, scrolling=True)

elif mode == "Admin Panel 🔐":
    st.subheader("Service Admin Panel")
    pin = st.text_input("Enter Service Admin PIN", type="password")
    if pin == service_pin:
        st.success("Access granted.")
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

            st.markdown("### Edit Service Intervals")
            for i, svc in enumerate(selected_model["Services"]):
                with st.expander(f"Edit: {svc['Interval']}"):
                    svc["Interval"] = st.text_input(f"Interval {i+1}", value=svc["Interval"], key=f"int_{i}")
                    svc["What's Included"] = st.text_area(f"What's Included {i+1}", value=svc.get("What's Included", ""), key=f"desc_{i}")
                    svc["Labor Hours"] = st.number_input(f"Labor Hours {i+1}", value=svc.get("Labor Hours", 0.0), step=0.1, key=f"lh_{i}")
                    current_parts = svc.get("Parts Used", [])
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

            if st.button("💾 Save All Changes"):
                save_json(SERVICE_FILE, service_models)
                st.success("All changes saved.")
    else:
        st.warning("Enter correct Service Admin PIN.")

elif mode == "Parts Manager 🧰":
    st.subheader("Parts Catalog Editor")
    pin = st.text_input("Enter Parts Admin PIN", type="password", key="parts_pin")
    if pin == parts_pin:
        st.success("Access granted.")
        for i, part in enumerate(parts_catalog):
            with st.expander(f"{part['Part Name']} ({part['Part Number']})"):
                part["Part Name"] = st.text_input(f"Part Name {i}", value=part["Part Name"], key=f"name_{i}")
                part["Part Number"] = st.text_input(f"Part Number {i}", value=part["Part Number"], key=f"num_{i}")
                part["Unit Price"] = st.number_input(f"Unit Price {i}", value=part["Unit Price"], key=f"price_{i}")

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
        st.warning("Enter correct Parts Admin PIN.")

elif mode == "Labor Rate Settings ⚙️":
    st.subheader("Set Global Labor Rate")
    pin = st.text_input("Enter Service Admin PIN", type="password", key="rate_pin")
    if pin == service_pin:
        st.success("Access granted.")
        with st.form("update_labor_rate_form"):
            new_rate = st.number_input("Set Labor Rate ($/hr)", min_value=0.0, value=labor_rate, step=1.0)
            update = st.form_submit_button("💾 Update Labor Rate")
            if update:
                config["Labor Rate"] = new_rate
                save_json(CONFIG_FILE, config)
                st.success("Labor rate updated. Please refresh the app to apply.")
    elif pin:
        st.error("Incorrect PIN.")
    else:
        st.info("Enter PIN to continue.")

elif mode == "PIN Settings 🔑":
    st.subheader("Update Admin PINs")
    pin = st.text_input("Enter Current Service Admin PIN", type="password", key="pin_pin")
    if pin == service_pin:
        st.success("Access granted.")
        new_service_pin = st.text_input("New Service Admin PIN", type="password")
        new_parts_pin = st.text_input("New Parts Admin PIN", type="password")
        if st.button("Update Admin PINs"):
            config["Service Admin PIN"] = new_service_pin
            config["Parts Admin PIN"] = new_parts_pin
            save_json(CONFIG_FILE, config)
            st.success("Admin PINs updated.")
    else:
        st.warning("Enter correct current Service Admin PIN.")
