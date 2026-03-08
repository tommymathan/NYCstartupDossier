"""
NYC AI Startup Map Generator
Uses Folium + OpenStreetMap (CartoDB) — 100% free, no API key needed.
"""
import json
import math
import random
import folium
from folium.plugins import MarkerCluster, Search, Fullscreen, MiniMap

# NYC startup hubs — weighted by real AI startup density
NYC_HUBS = [
    ((40.7411, -73.9897), 30),  # Flatiron / Silicon Alley
    ((40.7359, -73.9906), 20),  # Union Square
    ((40.7549, -73.9840), 15),  # Midtown East
    ((40.7465, -74.0014), 10),  # Chelsea
    ((40.7243, -74.0018), 8),   # SoHo / NoHo
    ((40.7267, -74.0071), 5),   # Hudson Square
    ((40.7075, -74.0021), 5),   # Financial District
    ((40.7033, -73.9881), 4),   # DUMBO, Brooklyn
    ((40.7081, -73.9571), 3),   # Williamsburg
]

SOURCE_COLORS = {
    "Y Combinator": "orange",
    "Techstars NYC": "red",
    "ERA NYC": "purple",
    "Betaworks": "darkblue",
    "Built In NYC": "green",
}

SOURCE_EMOJI = {
    "Y Combinator": "🚀",
    "Techstars NYC": "⭐",
    "ERA NYC": "🔵",
    "Betaworks": "⚡",
    "Built In NYC": "🏙️",
}

SOURCE_HEX = {
    "Y Combinator": "#FF6600",
    "Techstars NYC": "#E53E3E",
    "ERA NYC": "#805AD5",
    "Betaworks": "#2B6CB0",
    "Built In NYC": "#00AA44",
}


def weighted_random_hub():
    hubs, weights = zip(*NYC_HUBS)
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for hub, w in zip(hubs, weights):
        cumulative += w
        if r <= cumulative:
            return hub
    return hubs[0]


def scatter_coords(base_lat, base_lng, radius_km=0.6):
    """Add random scatter within radius_km of a base point."""
    # Convert km to degrees (approximate)
    lat_delta = (radius_km / 111.0) * random.uniform(-1, 1)
    lng_delta = (radius_km / (111.0 * math.cos(math.radians(base_lat)))) * random.uniform(-1, 1)
    return base_lat + lat_delta, base_lng + lng_delta


def make_popup_html(company):
    name = company.get("name", "Unknown")
    desc = company.get("description", "")
    if len(desc) > 220:
        desc = desc[:220] + "…"
    source = company.get("source", "")
    batch = company.get("batch", "")
    stage = company.get("stage", "")
    url = company.get("url") or company.get("website", "")

    source_hex = SOURCE_HEX.get(source, "#888")
    emoji = SOURCE_EMOJI.get(source, "📍")

    batch_badge = (
        f'<span style="background:#FF6600;color:#fff;padding:1px 6px;'
        f'border-radius:3px;font-size:10px;margin-left:4px;">{batch}</span>'
        if batch else ""
    )

    link_btn = (
        f'<a href="{url}" target="_blank" style="display:inline-block;margin-top:8px;'
        f'padding:4px 10px;background:{source_hex};color:#fff;border-radius:4px;'
        f'font-size:11px;text-decoration:none;">Visit →</a>'
        if url else ""
    )

    return f"""
<div style="font-family:'Segoe UI',Arial,sans-serif;min-width:230px;max-width:300px;padding:2px;">
  <h4 style="margin:0 0 5px 0;font-size:14px;color:#1a1a1a;">{name}</h4>
  <div style="margin-bottom:7px;">
    <span style="background:{source_hex};color:#fff;padding:2px 7px;border-radius:3px;
                 font-size:10px;font-weight:600;">{emoji} {source}</span>
    {batch_badge}
  </div>
  <p style="margin:0 0 4px 0;color:#555;font-size:12px;line-height:1.45;">{desc}</p>
  {link_btn}
</div>
"""


def generate_map(data_file="startups.json", output_file="nyc_ai_startups_map.html"):
    with open(data_file) as f:
        companies = json.load(f)

    print(f"Building map for {len(companies)} companies…")

    # ── Base map ──────────────────────────────────────────────────────────────
    m = folium.Map(
        location=[40.7300, -73.9950],
        zoom_start=13,
        tiles=None,  # we'll add tiles manually
    )

    # Tile layers (all free / open)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
        name="Light (default)",
        max_zoom=20,
    ).add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; OSM &copy; CARTO',
        name="Dark Mode",
        subdomains="abcd",
        max_zoom=20,
    ).add_to(m)

    # ── Marker clusters per source ────────────────────────────────────────────
    cluster_opts = {
        "disableClusteringAtZoom": 16,
        "spiderfyOnMaxZoom": True,
        "showCoverageOnHover": False,
        "maxClusterRadius": 50,
    }

    clusters = {
        src: MarkerCluster(name=src, options=cluster_opts).add_to(m)
        for src in ["Y Combinator", "Techstars NYC", "ERA NYC", "Betaworks", "Built In NYC"]
    }
    clusters["Other"] = MarkerCluster(name="Other", options=cluster_opts).add_to(m)

    # ── Add markers ───────────────────────────────────────────────────────────
    random.seed(42)  # reproducible scatter
    for company in companies:
        hub_lat, hub_lng = weighted_random_hub()
        lat, lng = scatter_coords(hub_lat, hub_lng)
        source = company.get("source", "")
        color = SOURCE_COLORS.get(source, "purple")
        cluster = clusters.get(source, clusters["Other"])

        folium.CircleMarker(
            location=[lat, lng],
            radius=7,
            color=SOURCE_HEX.get(source, "#888"),
            fill=True,
            fill_color=SOURCE_HEX.get(source, "#888"),
            fill_opacity=0.8,
            weight=1.5,
            popup=folium.Popup(make_popup_html(company), max_width=320),
            tooltip=folium.Tooltip(
                company.get("name", ""),
                sticky=False,
            ),
        ).add_to(cluster)

    # ── Extras ────────────────────────────────────────────────────────────────
    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    # ── Legend ────────────────────────────────────────────────────────────────
    counts = {}
    for c in companies:
        counts[c.get("source", "Other")] = counts.get(c.get("source", "Other"), 0) + 1

    sources = [
        ("Y Combinator",  "#FF6600"),
        ("Techstars NYC", "#E53E3E"),
        ("ERA NYC",       "#805AD5"),
        ("Betaworks",     "#2B6CB0"),
        ("Built In NYC",  "#00AA44"),
    ]
    source_rows = "".join(
        f'<div style="margin-bottom:4px;">'
        f'<span style="color:{hex};font-size:16px;">●</span> '
        f'<b>{name}</b>'
        f'<span style="color:#888;font-size:11px;"> ({counts.get(name, 0)})</span>'
        f'</div>'
        for name, hex in sources
    )
    legend = f"""
<div id="legend" style="
    position: fixed; bottom: 40px; left: 20px; z-index: 9999;
    background: #fff; padding: 14px 18px; border-radius: 10px;
    box-shadow: 0 3px 14px rgba(0,0,0,0.18);
    font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;
    min-width: 180px;">
  <div style="font-size:15px;font-weight:700;margin-bottom:8px;">
    🗽 NYC Startups
  </div>
  <div style="color:#888;font-size:11px;margin-bottom:10px;">
    {len(companies)} companies mapped
  </div>
  {source_rows}
  <hr style="margin:8px 0;border:none;border-top:1px solid #eee;">
  <div style="color:#aaa;font-size:10px;">Click a dot to see details</div>
</div>
"""
    m.get_root().html.add_child(folium.Element(legend))

    m.save(output_file)
    print(f"Map saved → {output_file}")
    return output_file


if __name__ == "__main__":
    generate_map()
