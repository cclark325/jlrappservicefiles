
import base64

def generate_service_html(model_name, interval, description, parts, labor_hours, total_price):
    parts_rows = "".join(
        f"<tr><td>{p['Part Name']}</td><td>{p['Part Number']}</td><td>${p['Unit Price']:.2f}</td></tr>" for p in parts
    )
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='UTF-8'>
        <title>Service Interval Printout</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            h1 {{ font-size: 24px; margin-bottom: 10px; }}
            h2 {{ font-size: 20px; margin-top: 30px; }}
            .section {{ margin-bottom: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        </style>
        <script>
            window.onload = function() {{
                window.print();
            }};
        </script>
    </head>
    <body>
        <h1>{model_name} - {interval}</h1>
        <div class="section">
            <h2>What's Included</h2>
            <p>{description}</p>
        </div>
        <div class="section">
            <h2>Parts Used</h2>
            <table>
                <tr><th>Part Name</th><th>Part Number</th><th>Price</th></tr>
                {parts_rows}
            </table>
        </div>
        <div class="section">
            <h2>Labor</h2>
            <p>{labor_hours} hours</p>
        </div>
        <h2>Total Price: ${total_price:.2f}</h2>
    </body>
    </html>
    """
    return html_template

def download_link(content, filename, label="Download as HTML"):
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}">{label}</a>'
    return href
