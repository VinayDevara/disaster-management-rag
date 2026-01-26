import { useEffect, useState } from "react";
import Map, { Marker, Popup } from "react-map-gl/mapbox"; // ✅ FIX
import "mapbox-gl/dist/mapbox-gl.css"; // ✅ IMPORTANT for proper styling
import { api } from "../api/client";

const MAPBOX_TOKEN = "pk.eyJ1IjoidmlkeWFkaXNhc3RlciIsImEiOiJjbWtzN21oNTAxNXdqM3BzOWEzZWNvaHl6In0.zu0n7yNlJKkkh62deq6HsQ";

export default function FlightsMap({
  center = { lat: 12.9141, lon: 74.8560 }, // Mangalore
  radiusKm = 150,
}) {
  const [rows, setRows] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    (async () => {
      const res = await api.get("/viz/flights/near", {
        params: {
          lat: center.lat,
          lon: center.lon,
          radius_km: radiusKm,
          limit: 300,
        },
      });
      setRows(res.data?.rows || []);
    })();
  }, [center.lat, center.lon, radiusKm]);

  return (
    <Map
      mapboxAccessToken={MAPBOX_TOKEN}
      initialViewState={{
        latitude: center.lat,
        longitude: center.lon,
        zoom: 7,
      }}
      style={{ width: "100%", height: "100%" }}
      mapStyle="mapbox://styles/mapbox/dark-v11"
    >
      {rows.map((f, i) => {
        if (!f.aircraft__lat || !f.aircraft__lon) return null;

        return (
          <Marker
            key={i}
            latitude={f.aircraft__lat}
            longitude={f.aircraft__lon}
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setSelected(f);
            }}
          >
            ✈️
          </Marker>
        );
      })}

      {selected && (
        <Popup
          latitude={selected.aircraft__lat}
          longitude={selected.aircraft__lon}
          onClose={() => setSelected(null)}
          closeOnClick={false}
        >
          <div style={{ fontSize: 12 }}>
            <b>{selected.aircraft__flight || "Unknown Flight"}</b><br />
            Hex: {selected.aircraft__hex}<br />
            Alt: {selected.aircraft__alt_baro ?? "N/A"} ft<br />
            Speed: {selected.aircraft__gs ?? "N/A"} kt
          </div>
        </Popup>
      )}
    </Map>
  );
}
