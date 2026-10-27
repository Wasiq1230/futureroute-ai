import streamlit as st
import folium
import openrouteservice
import pandas as pd
import requests
import numpy as np
import re
import os
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from streamlit_js_eval import get_geolocation

ORS_API_KEY = os.getenv("ORS_API_KEY", "")

st.set_page_config(page_title="FutureRoute AI", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 1rem; }
[data-testid="stSidebar"] { background-color: #1f2430; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 FutureRoute AI")
st.caption("AI Smart Route Intelligence System")

if "source_text" not in st.session_state:
    st.session_state.source_text = "Saddar Rawalpindi Pakistan"

if "destination_text" not in st.session_state:
    st.session_state.destination_text = "Faisal Mosque Islamabad Pakistan"

if "source_coords" not in st.session_state:
    st.session_state.source_coords = None

if "destination_coords" not in st.session_state:
    st.session_state.destination_coords = None

if "routes_data" not in st.session_state:
    st.session_state.routes_data = None


def parse_coords(text):
    nums = re.findall(r"-?\d+(?:\.\d+)?", text)
    if len(nums) >= 2:
        lat = float(nums[0])
        lon = float(nums[1])
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return [lon, lat]
    return None


@st.cache_data(ttl=300)
def search_places(query):
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip()

    if "pakistan" not in q.lower():
        q = q + ", Pakistan"

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": q,
        "format": "json",
        "limit": 5,
        "addressdetails": 1,
        "countrycodes": "pk"
    }

    headers = {"User-Agent": "FutureRouteAIStudentProject/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        results = []
        for item in data:
            results.append({
                "name": item.get("display_name", "Unknown place"),
                "lat": float(item["lat"]),
                "lon": float(item["lon"])
            })

        return results
    except:
        return []


def get_coordinates(text, saved_coords):
    if saved_coords:
        return saved_coords

    coords = parse_coords(text)
    if coords:
        return coords

    results = search_places(text)
    if results:
        return [results[0]["lon"], results[0]["lat"]]

    return None


def get_weather_risk(lat, lon):
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,precipitation,rain,wind_speed_10m"
        )
        data = requests.get(url, timeout=8).json()["current"]

        risk = 2
        if data.get("rain", 0) > 0 or data.get("precipitation", 0) > 0:
            risk += 4
        if data.get("wind_speed_10m", 0) > 25:
            risk += 2

        return min(risk, 10)
    except:
        return 2


def calculate_score(distance, duration, weather, priority, index):
    traffic = min(duration / 8, 10)
    safety = [3, 4, 5][index % 3]
    fuel = min(distance / 4, 10)

    weights = {
        "Balanced": (0.35, 0.25, 0.20, 0.20),
        "Fastest": (0.55, 0.15, 0.10, 0.20),
        "Safest": (0.20, 0.50, 0.15, 0.15),
        "Fuel Efficient": (0.25, 0.15, 0.10, 0.50),
        "Emergency": (0.70, 0.15, 0.05, 0.10),
    }

    wt, ws, ww, wf = weights[priority]

    ai_score = wt * traffic + ws * safety + ww * weather + wf * fuel

    future = min(traffic + 1.2, 10)
    future_label = "High" if future >= 7 else "Medium" if future >= 4 else "Low"

    return {
        "traffic": round(traffic, 2),
        "safety": safety,
        "weather": weather,
        "fuel": round(fuel, 2),
        "future_label": future_label,
        "ai_score": round(ai_score, 2)
    }


def get_routes(start, end):
    client = openrouteservice.Client(key=ORS_API_KEY)

    try:
        result = client.directions(
            coordinates=[start, end],
            profile="driving-car",
            format="geojson",
            alternative_routes={
                "target_count": 3,
                "share_factor": 0.7,
                "weight_factor": 1.6
            }
        )
    except:
        result = client.directions(
            coordinates=[start, end],
            profile="driving-car",
            format="geojson"
        )

    return result["features"]


with st.sidebar:
    st.header("🧭 Route Control Panel")

    if st.button("📍 Use My Live Location"):
        loc = get_geolocation()

        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]

            st.session_state.source_coords = [lon, lat]
            st.session_state.source_text = f"{lat}, {lon}"
            st.success("Live location added.")
        else:
            st.warning("Browser location permission allow karo, phir dobara press karo.")

    st.text_input("Source", key="source_text")

    source_suggestions = search_places(st.session_state.source_text)

    if source_suggestions:
        st.write("Source Suggestions")
        for i, place in enumerate(source_suggestions[:4]):
            label = place["name"][:60] + "..."
            if st.button(label, key=f"source_btn_{i}"):
                st.session_state.source_coords = [place["lon"], place["lat"]]
                st.success("Source selected successfully.")

    st.text_input("Destination", key="destination_text")

    destination_suggestions = search_places(st.session_state.destination_text)

    if destination_suggestions:
        st.write("Destination Suggestions")
        for i, place in enumerate(destination_suggestions[:4]):
            label = place["name"][:60] + "..."
            if st.button(label, key=f"dest_btn_{i}"):
                st.session_state.destination_coords = [place["lon"], place["lat"]]
                st.success("Destination selected successfully.")

    priority = st.selectbox(
        "AI Priority Mode",
        ["Balanced", "Fastest", "Safest", "Fuel Efficient", "Emergency"]
    )

    show_heatmap = st.checkbox("Traffic Heatmap", False)
    show_risk = st.checkbox("Risk Zones", True)
    show_congestion = st.checkbox("Congestion Zones", True)

    analyze = st.button("🚀 Analyze Smart Route")


if analyze:
    start = get_coordinates(
        st.session_state.source_text,
        st.session_state.source_coords
    )

    end = get_coordinates(
        st.session_state.destination_text,
        st.session_state.destination_coords
    )

    if start is None or end is None:
        st.error("Location not found. Full name likho ya suggestion select karo.")
    else:
        try:
            weather = get_weather_risk(end[1], end[0])
            features = get_routes(start, end)

            routes = []

            for i, feature in enumerate(features[:3]):
                summary = feature["properties"]["summary"]
                coords = feature["geometry"]["coordinates"]

                distance = round(summary["distance"] / 1000, 2)
                duration = round(summary["duration"] / 60, 2)

                scores = calculate_score(distance, duration, weather, priority, i)

                routes.append({
                    "name": f"Route {chr(65+i)}",
                    "coords": coords,
                    "distance": distance,
                    "duration": duration,
                    **scores
                })

            best = min(routes, key=lambda x: x["ai_score"])

            st.session_state.routes_data = {
                "start": start,
                "end": end,
                "routes": routes,
                "best": best
            }

        except Exception as e:
            st.error(f"Route error: {e}")


data = st.session_state.routes_data

if data is None:
    st.info("Source/Destination type karo, suggestion select karo, phir Analyze Smart Route press karo.")

    m = folium.Map(
        location=[33.6844, 73.0479],
        zoom_start=12,
        tiles="CartoDB positron",
        control_scale=True
    )

    st_folium(
        m,
        width="100%",
        height=720,
        returned_objects=[],
        key="default_map"
    )

else:
    start = data["start"]
    end = data["end"]
    routes = data["routes"]
    best = data["best"]

    st.success(f"✅ Best Route: {best['name']} | AI Score: {best['ai_score']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distance", f"{best['distance']} km")
    c2.metric("Time", f"{best['duration']} min")
    c3.metric("Future Traffic", best["future_label"])
    c4.metric("Weather Risk", f"{best['weather']}/10")

    st.subheader("🤖 AI Suggestions")

    if best["future_label"] == "High":
        st.warning("AI predicts congestion may increase in the next 30 minutes.")
    else:
        st.info("Traffic condition is acceptable for this route.")

    if best["fuel"] > 6:
        st.warning("Fuel usage is high. Try Fuel Efficient mode.")
    else:
        st.info("Fuel usage looks efficient.")

    if best["safety"] > 5:
        st.warning("Safety risk detected. Use Safest mode at night.")
    else:
        st.info("Safety risk is acceptable.")

    st.subheader("📊 Route Comparison")

    df = pd.DataFrame([
        {
            "Route": r["name"],
            "Distance": r["distance"],
            "Time": r["duration"],
            "Traffic": r["traffic"],
            "Safety": r["safety"],
            "Weather": r["weather"],
            "Fuel": r["fuel"],
            "Future Traffic": r["future_label"],
            "AI Score": r["ai_score"]
        }
        for r in routes
    ])

    st.dataframe(df, use_container_width=True)

    st.subheader("🗺️ Smart Map View")

    m = folium.Map(
        location=[start[1], start[0]],
        zoom_start=13,
        tiles="CartoDB positron",
        control_scale=True
    )

    colors = ["#2563eb", "#16a34a", "#f97316"]
    all_bounds = []

    for i, route in enumerate(routes):
        points = [[lat, lon] for lon, lat in route["coords"]]
        all_bounds.extend(points)

        folium.PolyLine(
            points,
            color=colors[i % 3],
            weight=7 if route["name"] == best["name"] else 4,
            opacity=0.95 if route["name"] == best["name"] else 0.45,
            tooltip=f"{route['name']} | Score {route['ai_score']}"
        ).add_to(m)

    folium.Marker(
        [start[1], start[0]],
        tooltip="Source",
        popup="Source",
        icon=folium.Icon(color="green")
    ).add_to(m)

    folium.Marker(
        [end[1], end[0]],
        tooltip="Destination",
        popup="Destination",
        icon=folium.Icon(color="red")
    ).add_to(m)

    center_lat = (start[1] + end[1]) / 2
    center_lon = (start[0] + end[0]) / 2

    if show_heatmap:
        heat_points = [
            [
                center_lat + np.random.uniform(-0.01, 0.01),
                center_lon + np.random.uniform(-0.01, 0.01),
                np.random.uniform(0.2, 0.6)
            ]
            for _ in range(18)
        ]

        HeatMap(
            heat_points,
            radius=16,
            blur=20,
            min_opacity=0.2
        ).add_to(m)

    if show_risk:
        risky_areas = [
            [center_lat + 0.006, center_lon + 0.006, "Accident-Prone Zone"],
            [center_lat - 0.006, center_lon - 0.006, "Unsafe Area Risk"],
        ]

        for lat, lon, label in risky_areas:
            folium.CircleMarker(
                [lat, lon],
                radius=8,
                color="#dc2626",
                fill=True,
                fill_opacity=0.5,
                tooltip=label,
                popup=label
            ).add_to(m)

    if show_congestion:
        folium.Circle(
            [center_lat, center_lon],
            radius=400,
            color="#f97316",
            fill=True,
            fill_opacity=0.18,
            tooltip="Predicted Congestion Zone",
            popup="Predicted Congestion Zone"
        ).add_to(m)

    if all_bounds:
        m.fit_bounds(all_bounds)

    st_folium(
        m,
        width="100%",
        height=750,
        returned_objects=[],
        key="main_map"
    )

    st.subheader("📄 Export Report")

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Route Intelligence Report",
        data=csv,
        file_name="future_route_ai_report.csv",
        mime="text/csv"
    )
