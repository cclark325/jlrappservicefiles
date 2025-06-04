
import streamlit as st
import json

# Load service data
with open("service_intervals.json", "r") as f:
    services = json.load(f)

# Get unique models
models = sorted(set(item["Model"] for item in services))

st.title("Land Rover / Jaguar Service Menu")

# Model selection
selected_model = st.selectbox("Select Vehicle Model", models)

# Filter by model
filtered = [item for item in services if item["Model"] == selected_model]

# Display intervals
for item in filtered:
    st.markdown(f"### {item['Interval']}")
    st.write(item["What’s Included"])
    st.markdown(f"**Price: ${item['Price']:.2f}**")
    st.markdown("---")
