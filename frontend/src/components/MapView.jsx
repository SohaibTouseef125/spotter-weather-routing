import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import { COLORS, LEVELS } from "../risk";

function FitBounds({ geometry }) {
  const map = useMap();
  useEffect(() => {
    if (geometry && geometry.length > 1) {
      map.fitBounds(L.latLngBounds(geometry), { padding: [40, 40] });
    }
  }, [geometry, map]);
  return null;
}

function endpointIcon(letter, color) {
  return L.divIcon({
    className: "endpoint-icon",
    html: `<div style="background:${color}">${letter}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

/**
 * Map showing all routes + checkpoints.
 * displayRisk(cp): current risk level for a checkpoint (ETA mode or slider mode).
 */
export default function MapView({
  plan,
  selectedRoute,
  selectedCheckpoint,
  onSelectCheckpoint,
  displayRisk,
}) {
  const route = plan.routes[selectedRoute];
  const center = plan.origin
    ? [plan.origin.lat, plan.origin.lng]
    : [32.7767, -96.797];

  return (
    <MapContainer
      center={center}
      zoom={6}
      style={{ height: "100%", width: "100%" }}
      zoomControl
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds geometry={route.geometry} />

      {plan.routes.map((r, i) => (
        <Polyline
          key={r.id}
          positions={r.geometry}
          pathOptions={{
            color: i === selectedRoute ? "#2563eb" : "#94a3b8",
            weight: i === selectedRoute ? 5 : 3,
            opacity: i === selectedRoute ? 0.95 : 0.6,
          }}
        />
      ))}

      <Marker
        position={[plan.origin.lat, plan.origin.lng]}
        icon={endpointIcon("A", "#16a34a")}
      >
        <Popup>
          <b>Origin:</b> {plan.origin.name}
        </Popup>
      </Marker>
      <Marker
        position={[plan.destination.lat, plan.destination.lng]}
        icon={endpointIcon("B", "#dc2626")}
      >
        <Popup>
          <b>Destination:</b> {plan.destination.name}
        </Popup>
      </Marker>

      {route.checkpoints.map((cp, i) => {
        const level = displayRisk(cp);
        const isSel =
          selectedCheckpoint && selectedCheckpoint.mile === cp.mile;
        return (
          <CircleMarker
            key={i}
            center={[cp.lat, cp.lng]}
            radius={isSel ? 12 : 8}
            pathOptions={{
              color: isSel ? "#0f172a" : "#ffffff",
              weight: isSel ? 3 : 2,
              fillColor: COLORS[level],
              fillOpacity: 0.95,
            }}
            eventHandlers={{ click: () => onSelectCheckpoint(cp) }}
          >
            <Popup>
              <b>Mile {cp.mile}</b> — {LEVELS[level]}
              <br />
              ETA: {new Date(cp.eta).toLocaleString([], {
                weekday: "short",
                hour: "numeric",
                minute: "2-digit",
              })}
              <br />
              Wind {cp.wind_mph} mph · Rain {cp.rain_in_hr} in/hr · Snow{" "}
              {cp.snow_in_hr} in/hr · {cp.temp_c}°C
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
