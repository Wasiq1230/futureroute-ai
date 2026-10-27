import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MapContainer, Polyline, Popup, TileLayer, CircleMarker, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000/api/v1";
const defaultToken = process.env.REACT_APP_DEMO_TOKEN || "";

const priorities = [
  { id: "balanced", label: "Balanced" },
  { id: "fastest", label: "Fastest" },
  { id: "safest", label: "Safest" },
  { id: "fuel", label: "Fuel" },
  { id: "emergency", label: "Emergency" },
];

const demoPayload = {
  source: { lat: 33.5943, lon: 73.0502 },
  destination: { lat: 33.7294, lon: 73.0379 },
  priority: "balanced",
};

function metric(value, suffix = "") {
  if (value === undefined || value === null) return "n/a";
  return `${Number(value).toFixed(value < 1 ? 2 : 1)}${suffix}`;
}

async function ensureToken() {
  const existing = localStorage.getItem("future_route_token") || defaultToken;
  if (existing) return existing;
  const response = await fetch(`${API_BASE}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "demo@futureroute.ai", password: "demo-password" }),
  });
  if (!response.ok) return "";
  const data = await response.json();
  localStorage.setItem("future_route_token", data.access_token);
  return data.access_token;
}

async function api(path, options = {}) {
  const token = path.startsWith("/auth") ? "" : await ensureToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function parseCoordinateText(text) {
  const match = text.match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
  if (!match) return null;
  const lat = Number(match[1]);
  const lon = Number(match[2]);
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
  return { lat, lon };
}

function haversineKm(a, b) {
  const radius = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * radius * Math.asin(Math.sqrt(h));
}

function fallbackRoutes(sourcePoint, destPoint, selectedPriority) {
  const baseKm = haversineKm(sourcePoint, destPoint);
  const offsets = [0.012, -0.016, 0.024];
  const routes = offsets.map((offset, index) => {
    const mid = {
      lat: (sourcePoint.lat + destPoint.lat) / 2 + offset,
      lon: (sourcePoint.lon + destPoint.lon) / 2 - offset / 2,
    };
    const geometry = [sourcePoint, mid, destPoint];
    const distance = baseKm * (1 + Math.abs(offset) * 4 + index * 0.05);
    const congestion = Math.min(0.85, 0.32 + index * 0.11 + (selectedPriority === "fastest" ? -0.06 : 0));
    const safety = Math.min(0.72, 0.22 + index * 0.08 + (selectedPriority === "safest" ? -0.08 : 0));
    const weather = 0.18;
    const eta = (distance / (42 - congestion * 18)) * 60;
    const fuel = distance * (0.072 + congestion * 0.018);
    const score = eta * 0.45 + congestion * 22 + safety * 18 + fuel * 2.4;
    return {
      id: `local-route-${index + 1}`,
      name: `Route ${String.fromCharCode(65 + index)}`,
      geometry,
      distance_km: Number(distance.toFixed(2)),
      duration_minutes: Number(eta.toFixed(1)),
      score: {
        ai_score: Number(score.toFixed(2)),
        eta_minutes: Number(eta.toFixed(1)),
        eta_confidence: Number(Math.max(0.58, 0.9 - congestion * 0.25).toFixed(2)),
        congestion_risk: Number(congestion.toFixed(2)),
        safety_risk: Number(safety.toFixed(2)),
        weather_risk: weather,
        fuel_liters: Number(fuel.toFixed(2)),
        explanation: [
          "Local fallback route generated because backend routing was unavailable.",
          "Start the FastAPI backend for ORS-powered navigation and turn-by-turn routing.",
          "Scores use deterministic distance, congestion, safety, weather, and fuel features.",
        ],
      },
      steps: [
        { instruction: "Start from selected source", distance_m: Math.round(distance * 250), duration_s: Math.round(eta * 15) },
        { instruction: "Continue through optimized corridor", distance_m: Math.round(distance * 560), duration_s: Math.round(eta * 34) },
        { instruction: "Proceed toward destination", distance_m: Math.round(distance * 190), duration_s: Math.round(eta * 11) },
      ],
    };
  });
  const best = routes.reduce((winner, route) => (route.score.ai_score < winner.score.ai_score ? route : winner), routes[0]);
  return {
    request_id: "local-fallback",
    best_route_id: best.id,
    routes,
    traffic_heatmap: routes.flatMap((route) => route.geometry.map((point, index) => [point.lat, point.lon, route.score.congestion_risk + index * 0.03])),
    incidents: [],
  };
}

function FitRoute({ route }) {
  const map = useMap();
  useEffect(() => {
    if (!route?.geometry?.length) return;
    map.fitBounds(route.geometry.map((point) => [point.lat, point.lon]), { padding: [60, 60] });
  }, [map, route]);
  return null;
}

function SearchBox({ label, value, onChange, onSelect }) {
  const [results, setResults] = useState([]);
  useEffect(() => {
    const handle = setTimeout(async () => {
      if (value.length < 3) return setResults([]);
      try {
        setResults(await api(`/geocode/search?q=${encodeURIComponent(value)}`));
      } catch {
        setResults([]);
      }
    }, 350);
    return () => clearTimeout(handle);
  }, [value]);

  return (
    <div className="searchBox">
      <label>{label}</label>
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={`Search ${label.toLowerCase()}`} />
      <AnimatePresence>
        {results.length > 0 && (
          <motion.div className="suggestions" initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {results.slice(0, 5).map((item) => (
              <button key={`${item.lat}-${item.lon}`} onClick={() => onSelect(item)}>
                <span>{item.label}</span>
                <small>{item.category}</small>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function RouteCard({ route, selected, onClick }) {
  return (
    <motion.button className={`routeCard ${selected ? "selected" : ""}`} onClick={onClick} layout>
      <div className="routeCardTop">
        <strong>{route.name}</strong>
        <span className="score">{metric(route.score.ai_score)}</span>
      </div>
      <div className="routeMetrics">
        <span>{metric(route.score.eta_minutes, " min")}</span>
        <span>{metric(route.distance_km, " km")}</span>
        <span>{metric(route.score.fuel_liters, " L")}</span>
      </div>
      <div className="confidence">
        <span style={{ width: `${route.score.eta_confidence * 100}%` }} />
      </div>
      <small>ETA confidence {Math.round(route.score.eta_confidence * 100)}%</small>
    </motion.button>
  );
}

function RecommendationPanel({ route }) {
  if (!route) return null;
  return (
    <section className="panelSection">
      <div className="sectionTitle">AI Recommendation</div>
      <div className="riskGrid">
        <div><span>Congestion</span><strong>{Math.round(route.score.congestion_risk * 100)}%</strong></div>
        <div><span>Safety Risk</span><strong>{Math.round(route.score.safety_risk * 100)}%</strong></div>
        <div><span>Weather</span><strong>{Math.round(route.score.weather_risk * 100)}%</strong></div>
      </div>
      <ul className="explainList">
        {route.score.explanation.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </section>
  );
}

function TurnByTurn({ route }) {
  return (
    <section className="panelSection instructions">
      <div className="sectionTitle">Turn-by-turn</div>
      {(route?.steps || []).slice(0, 8).map((step, index) => (
        <div className="instruction" key={`${step.instruction}-${index}`}>
          <b>{index + 1}</b>
          <span>{step.instruction}</span>
          <small>{Math.round(step.distance_m)} m</small>
        </div>
      ))}
    </section>
  );
}

function App() {
  const [theme, setTheme] = useState("dark");
  const [sourceText, setSourceText] = useState("Saddar Rawalpindi Pakistan");
  const [destText, setDestText] = useState("Faisal Mosque Islamabad Pakistan");
  const [source, setSource] = useState(demoPayload.source);
  const [destination, setDestination] = useState(demoPayload.destination);
  const [priority, setPriority] = useState("balanced");
  const [loading, setLoading] = useState(false);
  const [routeData, setRouteData] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [trafficPulse, setTrafficPulse] = useState(null);
  const [statusMessage, setStatusMessage] = useState("Backend connecting...");

  useEffect(() => {
    ensureToken().then(() => setStatusMessage("Backend ready")).catch(() => setStatusMessage("Backend offline: local fallback active"));
  }, []);

  useEffect(() => {
    const wsBase = API_BASE.replace("http", "ws").replace("/api/v1", "");
    const socket = new WebSocket(`${wsBase}/api/v1/realtime/traffic`);
    socket.onmessage = (event) => setTrafficPulse(JSON.parse(event.data));
    return () => socket.close();
  }, []);

  const selectedRoute = useMemo(() => {
    if (!routeData) return null;
    return routeData.routes.find((route) => route.id === (selectedId || routeData.best_route_id));
  }, [routeData, selectedId]);

  async function useLocation() {
    navigator.geolocation?.getCurrentPosition((position) => {
      const coords = { lat: position.coords.latitude, lon: position.coords.longitude };
      setSource(coords);
      setSourceText(`${coords.lat.toFixed(5)}, ${coords.lon.toFixed(5)}`);
    });
  }

  async function planRoute() {
    setLoading(true);
    try {
      const parsedSource = parseCoordinateText(sourceText) || source;
      let resolvedDestination = parseCoordinateText(destText) || destination;
      if (!parseCoordinateText(destText) && destText.length > 3) {
        const places = await api(`/geocode/search?q=${encodeURIComponent(destText)}`);
        if (places[0]) {
          resolvedDestination = { lat: places[0].lat, lon: places[0].lon };
          setDestination(resolvedDestination);
        }
      }
      setSource(parsedSource);
      const data = await api("/routes/plan", {
        method: "POST",
        body: JSON.stringify({ source: parsedSource, destination: resolvedDestination, priority }),
      });
      setStatusMessage(data.request_id === "local-fallback" ? "Local fallback active" : "Backend route active");
      setRouteData(data);
      setSelectedId(data.best_route_id);
    } catch (error) {
      const parsedSource = parseCoordinateText(sourceText) || source;
      const parsedDestination = parseCoordinateText(destText) || destination;
      const fallback = fallbackRoutes(parsedSource, parsedDestination, priority);
      setStatusMessage("Backend offline: local fallback active");
      setRouteData(fallback);
      setSelectedId(fallback.best_route_id);
    } finally {
      setLoading(false);
    }
  }

  const mapCenter = selectedRoute?.geometry?.[Math.floor(selectedRoute.geometry.length / 2)] || source;

  return (
    <main className={`appShell ${theme}`}>
      <aside className="sidebar">
        <div className="brandBlock">
          <div className="brandMark">FR</div>
          <div>
            <h1>FutureRoute AI</h1>
            <p>Predictive mobility intelligence</p>
          </div>
          <button className="iconBtn" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? "Light" : "Dark"}</button>
        </div>

        <SearchBox label="Source" value={sourceText} onChange={setSourceText} onSelect={(item) => {
          setSource({ lat: item.lat, lon: item.lon });
          setSourceText(item.label);
        }} />
        <SearchBox label="Destination" value={destText} onChange={setDestText} onSelect={(item) => {
          setDestination({ lat: item.lat, lon: item.lon });
          setDestText(item.label);
        }} />

        <div className="priorityBar">
          {priorities.map((item) => (
            <button key={item.id} className={priority === item.id ? "active" : ""} onClick={() => setPriority(item.id)}>
              {item.label}
            </button>
          ))}
        </div>

        <div className="actionRow">
          <button className="secondaryBtn" onClick={useLocation}>Live location</button>
          <button className="primaryBtn" onClick={planRoute}>{loading ? "Analyzing..." : "Analyze route"}</button>
        </div>

        {loading && <div className="skeletonStack"><span /><span /><span /></div>}

        <section className="panelSection">
          <div className="sectionTitle">Route Candidates</div>
          <div className="routeList">
            {(routeData?.routes || []).map((route) => (
              <RouteCard key={route.id} route={route} selected={route.id === selectedRoute?.id} onClick={() => setSelectedId(route.id)} />
            ))}
          </div>
        </section>

        <RecommendationPanel route={selectedRoute} />
        <TurnByTurn route={selectedRoute} />
      </aside>

      <section className="mapStage">
        <div className="topHud">
          <div>
            <span>Live network</span>
            <strong>{trafficPulse ? `update #${trafficPulse.tick}` : statusMessage}</strong>
          </div>
          <div>
            <span>Best ETA</span>
            <strong>{selectedRoute ? metric(selectedRoute.score.eta_minutes, " min") : "--"}</strong>
          </div>
          <div>
            <span>Confidence</span>
            <strong>{selectedRoute ? `${Math.round(selectedRoute.score.eta_confidence * 100)}%` : "--"}</strong>
          </div>
        </div>

        <MapContainer center={[mapCenter.lat, mapCenter.lon]} zoom={12} className="mapCanvas">
          <FitRoute route={selectedRoute} />
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url={theme === "dark"
              ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"}
          />
          <CircleMarker center={[source.lat, source.lon]} radius={9} pathOptions={{ color: "#16a34a", fillColor: "#16a34a", fillOpacity: 0.9 }}>
            <Popup>Source</Popup>
          </CircleMarker>
          <CircleMarker center={[destination.lat, destination.lon]} radius={9} pathOptions={{ color: "#dc2626", fillColor: "#dc2626", fillOpacity: 0.9 }}>
            <Popup>Destination</Popup>
          </CircleMarker>
          {(routeData?.routes || []).map((route) => (
            <Polyline
              key={route.id}
              pathOptions={{ color: route.id === selectedRoute?.id ? "#00c2ff" : "#6b7280", weight: route.id === selectedRoute?.id ? 7 : 4, opacity: route.id === selectedRoute?.id ? 0.95 : 0.45 }}
              positions={route.geometry.map((point) => [point.lat, point.lon])}
            />
          ))}
          {(routeData?.traffic_heatmap || []).map(([lat, lon, intensity], index) => (
            <CircleMarker key={`${lat}-${lon}-${index}`} center={[lat, lon]} radius={5 + intensity * 14} pathOptions={{ color: "#ff9f1c", fillColor: "#ff3d00", fillOpacity: 0.18 + intensity * 0.35, weight: 1 }} />
          ))}
          {(routeData?.incidents || []).map((incident) => (
            <CircleMarker key={incident.id} center={[incident.lat, incident.lon]} radius={11} pathOptions={{ color: "#ef4444", fillColor: "#ef4444", fillOpacity: 0.45 }}>
              <Popup>{incident.description}</Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </section>
    </main>
  );
}

export default App;
