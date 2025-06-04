import streamlit as st
import json
import os
import pdfkit

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

st.set_page_config(page_title="Printable Service Sheet", layout="centered")
st.title("Generate Service Sheet PDF")

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
    else:
        st.warning("Service interval not found.")
