import pandas as pd
import streamlit as st


st.set_page_config(page_title="FutureRoute AI Admin", layout="wide")
st.title("FutureRoute AI Command Center")
st.caption("Executive analytics for congestion, safety, prediction confidence, and fuel savings.")

summary = {
    "Route searches": 1284,
    "Average ETA": "23.8 min",
    "Mean congestion risk": "41%",
    "Estimated fuel saved": "318.4 L",
}

cols = st.columns(4)
for col, (label, value) in zip(cols, summary.items()):
    col.metric(label, value)

traffic = pd.DataFrame(
    [
        {"corridor": "Saddar to Blue Area", "hour": "08:00", "congestion": 0.76, "confidence": 0.82},
        {"corridor": "Murree Road", "hour": "09:00", "congestion": 0.69, "confidence": 0.78},
        {"corridor": "7th Avenue", "hour": "17:00", "congestion": 0.81, "confidence": 0.84},
        {"corridor": "Islamabad Expressway", "hour": "18:00", "congestion": 0.74, "confidence": 0.79},
    ]
)

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Congestion Forecast")
    st.bar_chart(traffic, x="corridor", y="congestion", color="#00c2ff")

with right:
    st.subheader("Prediction Confidence")
    st.line_chart(traffic, x="hour", y="confidence")

st.subheader("Corridor Intelligence")
st.dataframe(traffic, use_container_width=True)

