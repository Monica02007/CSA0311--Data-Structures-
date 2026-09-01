"""
Smart-City Emergency Vehicle Routing System (EVRS)
Module: generator.py
Description: Generates an ultra-clean, structured, easily understandable Smart City Road Network
with 5 well-spaced districts, clear coordinates, major landmarks, hospitals, fire stations,
and ring-road expressways.
"""

from __future__ import annotations
import random
from graph import CityRoadNetwork


def build_metropolis_network() -> CityRoadNetwork:
    """
    Constructs an ultra-clean, structured Smart City Road Network:
    - 120+ clearly laid out intersections arranged in intuitive districts.
    - 350+ directed road segments with realistic speed limits and connectivity.
    - 4 Major Emergency Hospitals & Trauma Centers (Cyan 🏥)
    - 4 Rapid-Response Fire Stations (Red 🚒)
    - 4 Ambulance Depots (Amber 🏢)
    - High-speed Perimeter Ring Road & Central Arterial Avenues.
    """
    net = CityRoadNetwork(name="Metropolis-SmartCity")
    
    # -------------------------------------------------------------
    # DISTRICT 1: Medical & Healthcare District (West Zone: X 10..30, Y 20..50)
    # -------------------------------------------------------------
    medical_nodes = [
        # (id, name, x, y, type)
        ("M01", "Trauma Center H1 (Metro General)", 12.0, 22.0, "hospital"),
        ("M02", "St. Jude Emergency Hospital H2", 12.0, 32.0, "hospital"),
        ("M03", "Children's Specialized Hospital H3", 12.0, 42.0, "hospital"),
        ("M04", "CardioCare Institute H4", 12.0, 52.0, "hospital"),
        ("M05", "Ambulance Station Alpha (AMB-1)", 18.0, 22.0, "depot"),
        ("M06", "Ambulance Station Beta (AMB-2)", 18.0, 32.0, "depot"),
        ("M07", "BioTech Research Hub", 18.0, 42.0, "landmark"),
        ("M08", "Paramedic Fast Response (AMB-3)", 18.0, 52.0, "depot"),
        ("M09", "West Medical Avenue Junction 1", 24.0, 22.0, "intersection"),
        ("M10", "West Medical Avenue Junction 2", 24.0, 32.0, "intersection"),
        ("M11", "University Health Campus", 24.0, 42.0, "intersection"),
        ("M12", "Southwest Health Park Crossing", 24.0, 52.0, "intersection"),
        ("M13", "Medical Corridor North Gate", 30.0, 22.0, "intersection"),
        ("M14", "LifeSciences Plaza Interchange", 30.0, 32.0, "intersection"),
        ("M15", "West Clinic Central Crossing", 30.0, 42.0, "intersection"),
        ("M16", "Emergency Express Gate South", 30.0, 52.0, "intersection"),
        ("M17", "Highland Care Crossing", 15.0, 27.0, "intersection"),
        ("M18", "Valley Medical Plaza", 15.0, 37.0, "intersection"),
        ("M19", "NeuroScience Parkway", 15.0, 47.0, "intersection"),
        ("M20", "Riverside Clinic Crossing", 27.0, 27.0, "intersection"),
        ("M21", "Hope Emergency Gate", 27.0, 37.0, "intersection"),
        ("M22", "Pharma Avenue Crossing", 27.0, 47.0, "intersection"),
        ("M23", "Northwest Medical Link", 12.0, 16.0, "intersection"),
        ("M24", "Southwest Medical Link", 12.0, 58.0, "intersection"),
    ]
    for nid, name, x, y, ntype in medical_nodes:
        net.add_intersection(nid, name, x, y, node_type=ntype, district="Medical District", elevation=15.0)

    # -------------------------------------------------------------
    # DISTRICT 2: Downtown Core & Civic Center (Central Zone: X 38..62, Y 20..52)
    # -------------------------------------------------------------
    downtown_nodes = [
        ("D01", "Central Plaza Crossing", 40.0, 22.0, "landmark"),
        ("D02", "Grand Avenue Interchange", 46.0, 22.0, "intersection"),
        ("D03", "Financial Tower Way", 52.0, 22.0, "intersection"),
        ("D04", "City Hall Square", 58.0, 22.0, "landmark"),
        ("D05", "Union Station Interchange", 40.0, 30.0, "landmark"),
        ("D06", "Metropolitan Hub", 46.0, 30.0, "intersection"),
        ("D07", "Commerce Boulevard Core", 52.0, 30.0, "intersection"),
        ("D08", "Stock Exchange Crossing", 58.0, 30.0, "intersection"),
        ("D09", "Broadway Junction", 40.0, 38.0, "intersection"),
        ("D10", "Midtown Roundabout", 46.0, 38.0, "intersection"),
        ("D11", "Liberty Parkway Center", 52.0, 38.0, "intersection"),
        ("D12", "Civic Center Junction", 58.0, 38.0, "landmark"),
        ("D13", "Market Square Crossing", 40.0, 46.0, "intersection"),
        ("D14", "Beacon Avenue Crossing", 46.0, 46.0, "intersection"),
        ("D15", "Empire Way Central", 52.0, 46.0, "intersection"),
        ("D16", "Park Avenue Split", 58.0, 46.0, "intersection"),
        ("D17", "South Downtown Terminal", 40.0, 52.0, "intersection"),
        ("D18", "Madison Junction", 46.0, 52.0, "intersection"),
        ("D19", "Central Station Terminal", 52.0, 52.0, "landmark"),
        ("D20", "Pioneer Square Interchange", 58.0, 52.0, "intersection"),
        ("D21", "Central Core Bypass North", 49.0, 16.0, "intersection"),
        ("D22", "Central Core Bypass South", 49.0, 58.0, "intersection"),
        ("D23", "Apex Tower Plaza", 43.0, 34.0, "intersection"),
        ("D24", "Trinity Intersection", 55.0, 34.0, "intersection"),
        ("D25", "Crown Plaza West", 43.0, 42.0, "intersection"),
    ]
    for nid, name, x, y, ntype in downtown_nodes:
        net.add_intersection(nid, name, x, y, node_type=ntype, district="Downtown Core", elevation=10.0)

    # -------------------------------------------------------------
    # DISTRICT 3: Industrial & Port Zone (East Zone: X 70..90, Y 20..52)
    # -------------------------------------------------------------
    industrial_nodes = [
        ("I01", "Central Fire Station FS-01", 70.0, 22.0, "fire_station"),
        ("I02", "Eastside Refinery Gate", 76.0, 22.0, "intersection"),
        ("I03", "Port Authority Terminal", 82.0, 22.0, "landmark"),
        ("I04", "Industrial Fire Station FS-02", 88.0, 22.0, "fire_station"),
        ("I05", "Chemical Logistics Hub", 70.0, 30.0, "depot"),
        ("I06", "Cargo Freight Depot", 76.0, 30.0, "intersection"),
        ("I07", "Steelworks Boulevard", 82.0, 30.0, "intersection"),
        ("I08", "Harbor Gate 3", 88.0, 30.0, "intersection"),
        ("I09", "Manufacturing Fire Station FS-03", 70.0, 38.0, "fire_station"),
        ("I10", "Warehouse Logistics Core", 76.0, 38.0, "intersection"),
        ("I11", "Container Terminal North", 82.0, 38.0, "intersection"),
        ("I12", "East River Pier Loop", 88.0, 38.0, "intersection"),
        ("I13", "Power Grid Substation", 70.0, 46.0, "intersection"),
        ("I14", "Heavy Truck Arterial East", 76.0, 46.0, "intersection"),
        ("I15", "Maritime Way Crossing", 82.0, 46.0, "intersection"),
        ("I16", "Docklands Access Loop", 88.0, 46.0, "intersection"),
        ("I17", "Logistics Fire Station FS-04", 70.0, 52.0, "fire_station"),
        ("I18", "Foundry Interchange", 76.0, 52.0, "intersection"),
        ("I19", "Freight Expressway Ramp", 82.0, 52.0, "intersection"),
        ("I20", "Port Maritime Terminal 2", 88.0, 52.0, "landmark"),
        ("I21", "Northeast Industrial Gate", 88.0, 16.0, "intersection"),
        ("I22", "Southeast Industrial Gate", 88.0, 58.0, "intersection"),
        ("I23", "Hazmat Emergency Center", 73.0, 34.0, "depot"),
        ("I24", "Petrochemical Bypass", 85.0, 34.0, "intersection"),
    ]
    for nid, name, x, y, ntype in industrial_nodes:
        net.add_intersection(nid, name, x, y, node_type=ntype, district="Industrial Zone", elevation=5.0)

    # -------------------------------------------------------------
    # DISTRICT 4: North Suburbs & Hills (North Zone: X 15..85, Y 5..14)
    # -------------------------------------------------------------
    suburb_nodes = [
        ("R01", "Northwest Ridge Gate", 15.0, 8.0, "intersection"),
        ("R02", "Sunset Hills Avenue", 23.0, 8.0, "intersection"),
        ("R03", "Greenwood Ridge Crossing", 31.0, 8.0, "intersection"),
        ("R04", "Oakridge Community Hub", 39.0, 8.0, "landmark"),
        ("R05", "Suburban Fire Station FS-05", 47.0, 8.0, "fire_station"),
        ("R06", "Pinecrest Community Clinic", 55.0, 8.0, "hospital"),
        ("R07", "Maplewood Boulevard", 63.0, 8.0, "intersection"),
        ("R08", "Silverlake Corner", 71.0, 8.0, "intersection"),
        ("R09", "Hilltop Viewpoint Interchange", 79.0, 8.0, "intersection"),
        ("R10", "Northeast Ridge Gate", 85.0, 8.0, "intersection"),
        ("R11", "Falcon Ridge Loop", 20.0, 14.0, "intersection"),
        ("R12", "Meadowbrook Crossing", 35.0, 14.0, "intersection"),
        ("R13", "Willow Creek Drive", 45.0, 14.0, "intersection"),
        ("R14", "Highland Park Gate", 58.0, 14.0, "intersection"),
        ("R15", "Sunnyvale Junction", 68.0, 14.0, "intersection"),
        ("R16", "Briarwood Court Crossing", 78.0, 14.0, "intersection"),
        ("R17", "Westlake Roundabout", 27.0, 12.0, "intersection"),
        ("R18", "Valley Stream Way", 50.0, 12.0, "intersection"),
        ("R19", "Summit Circle", 74.0, 12.0, "intersection"),
        ("R20", "North Hills Emergency Hub", 62.0, 12.0, "depot"),
    ]
    for nid, name, x, y, ntype in suburb_nodes:
        net.add_intersection(nid, name, x, y, node_type=ntype, district="Suburbs", elevation=35.0)

    # -------------------------------------------------------------
    # DISTRICT 5: South Tech & Airport Corridor (South Zone: X 15..85, Y 60..68)
    # -------------------------------------------------------------
    tech_nodes = [
        ("T01", "Southwest Tech Gate", 15.0, 64.0, "intersection"),
        ("T02", "Innovation Campus West", 23.0, 64.0, "intersection"),
        ("T03", "Autonomous Mobility Lab", 31.0, 64.0, "landmark"),
        ("T04", "Silicon Boulevard Crossing", 39.0, 64.0, "intersection"),
        ("T05", "Airport Transit Terminal Gate", 47.0, 64.0, "landmark"),
        ("T06", "Metro Airport Trauma Center H5", 55.0, 64.0, "hospital"),
        ("T07", "Aerospace Logistics Hub", 63.0, 64.0, "depot"),
        ("T08", "Digital City Center", 71.0, 64.0, "intersection"),
        ("T09", "Cybernetics Research Center", 79.0, 64.0, "intersection"),
        ("T10", "Southeast Tech Gate", 85.0, 64.0, "intersection"),
        ("T11", "Software Park Boulevard", 20.0, 59.0, "intersection"),
        ("T12", "Cloudway Junction", 35.0, 59.0, "intersection"),
        ("T13", "Airport Expressway Exit 1", 45.0, 59.0, "intersection"),
        ("T14", "Airport Expressway Exit 2", 58.0, 59.0, "intersection"),
        ("T15", "Satellite Highway Link", 68.0, 59.0, "intersection"),
        ("T16", "High-Tech Corridor East", 78.0, 59.0, "intersection"),
        ("T17", "Quantum Way Crossing", 27.0, 61.0, "intersection"),
        ("T18", "Data Corridor Central", 50.0, 61.0, "intersection"),
        ("T19", "Venture Parkway", 74.0, 61.0, "intersection"),
        ("T20", "Airport Emergency Response Post", 52.0, 66.0, "depot"),
    ]
    for nid, name, x, y, ntype in tech_nodes:
        net.add_intersection(nid, name, x, y, node_type=ntype, district="Airport & Tech Corridor", elevation=12.0)

    # -------------------------------------------------------------
    # CONNECT ROADS (EDGES) - Structured Avenues & Corridors
    # -------------------------------------------------------------
    def connect_chain(node_ids: list[str], speed: float = 55.0, rtype: str = "arterial", lanes: int = 2):
        for i in range(len(node_ids) - 1):
            u, v = node_ids[i], node_ids[i + 1]
            if u in net.nodes and v in net.nodes and not net.get_edge(u, v):
                net.add_road(u, v, speed_limit_kmh=speed, road_type=rtype, lanes=lanes)

    # 1. West-to-East Horizontal Avenues Across the Metropolis
    avenues = [
        # Ave 1 (Y ~ 22)
        ["M01", "M05", "M09", "M13", "D01", "D02", "D03", "D04", "I01", "I02", "I03", "I04"],
        # Ave 2 (Y ~ 30..32)
        ["M02", "M06", "M10", "M14", "D05", "D06", "D07", "D08", "I05", "I06", "I07", "I08"],
        # Ave 3 (Y ~ 38..42)
        ["M03", "M07", "M11", "M15", "D09", "D10", "D11", "D12", "I09", "I10", "I11", "I12"],
        # Ave 4 (Y ~ 46..52)
        ["M04", "M08", "M12", "M16", "D13", "D14", "D15", "D16", "I13", "I14", "I15", "I16"],
        # Ave 5 (Y ~ 52)
        ["M16", "M24", "D17", "D18", "D19", "D20", "D22", "I17", "I18", "I19", "I20", "I22"],
        # North Suburb Avenue (Y ~ 8)
        ["R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10"],
        # South Expressway Corridor (Y ~ 64)
        ["T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10"],
    ]
    for ave in avenues:
        connect_chain(ave, speed=60.0, rtype="arterial", lanes=3)

    # 2. North-to-South Vertical Boulevards
    boulevards = [
        # Medical Boulevards
        ["R01", "M23", "M01", "M02", "M03", "M04", "M24", "T01"],
        ["R02", "M17", "M05", "M06", "M07", "M08", "T02"],
        ["R03", "M09", "M10", "M11", "M12", "T03"],
        ["R04", "M13", "M14", "M15", "M16", "T04"],
        # Downtown Boulevards
        ["R04", "D21", "D01", "D05", "D09", "D13", "D17", "T04"],
        ["R05", "D02", "D06", "D10", "D14", "D18", "T05"],
        ["R06", "D03", "D07", "D11", "D15", "D19", "D22", "T06"],
        ["R07", "D04", "D08", "D12", "D16", "D20", "T07"],
        # Industrial Boulevards
        ["R07", "I01", "I05", "I09", "I13", "I17", "T07"],
        ["R08", "I02", "I06", "I10", "I14", "I18", "T08"],
        ["R09", "I03", "I07", "I11", "I15", "I19", "T09"],
        ["R10", "I21", "I04", "I08", "I12", "I16", "I20", "I22", "T10"],
    ]
    for bvd in boulevards:
        connect_chain(bvd, speed=55.0, rtype="arterial", lanes=2)

    # 3. Inter-District Dedicated Emergency Express Corridors
    emergency_expressways = [
        ("M01", "D05", 75.0, "emergency_lane"),  # Trauma H1 directly to Downtown Union Station
        ("M02", "D10", 75.0, "emergency_lane"),  # Hospital H2 directly to Midtown Core
        ("M03", "D19", 80.0, "emergency_lane"),  # Hospital H3 to Central Station
        ("I01", "D04", 75.0, "emergency_lane"),  # Fire Station FS-01 to City Hall
        ("I04", "D08", 75.0, "emergency_lane"),  # Fire Station FS-02 to Financial Towers
        ("I09", "D16", 75.0, "emergency_lane"),  # Fire Station FS-03 to Park Avenue
        ("R05", "D02", 70.0, "emergency_lane"),  # North Fire Station to Grand Ave
        ("T05", "D19", 85.0, "emergency_lane"),  # Airport Transit to Central Station
        ("T06", "I17", 80.0, "emergency_lane"),  # Airport Trauma to Logistics Station
    ]
    for u, v, spd, rtype in emergency_expressways:
        if u in net.nodes and v in net.nodes and not net.get_edge(u, v):
            net.add_road(u, v, speed_limit_kmh=spd, road_type=rtype, lanes=3)

    # 4. Secondary Local Connectors for Complete District Mesh
    secondary_links = [
        # Medical local mesh
        ("M17", "M01"), ("M17", "M05"), ("M18", "M02"), ("M18", "M06"),
        ("M19", "M03"), ("M19", "M07"), ("M20", "M09"), ("M20", "M13"),
        ("M21", "M10"), ("M21", "M14"), ("M22", "M11"), ("M22", "M15"), ("M22", "M12"), ("M22", "M16"),
        ("M23", "M01"), ("M24", "M04"),
        # Downtown local mesh
        ("D23", "D05"), ("D23", "D09"), ("D23", "D06"),
        ("D24", "D07"), ("D24", "D08"), ("D24", "D11"), ("D24", "D12"),
        ("D25", "D09"), ("D25", "D13"), ("D25", "D10"), ("D25", "D14"),
        ("D21", "D01"), ("D21", "D02"), ("D22", "D19"), ("D22", "D20"),
        # Industrial local mesh
        ("I23", "I05"), ("I23", "I09"), ("I23", "I06"), ("I23", "I10"),
        ("I24", "I07"), ("I24", "I08"), ("I24", "I11"), ("I24", "I12"),
        ("I21", "I04"), ("I22", "I20"),
        # Suburbs local mesh
        ("R11", "R01"), ("R11", "R02"), ("R12", "R03"), ("R12", "R04"),
        ("R13", "R05"), ("R13", "R06"), ("R14", "R06"), ("R14", "R07"),
        ("R15", "R07"), ("R15", "R08"), ("R16", "R09"), ("R16", "R10"),
        ("R17", "R02"), ("R17", "R03"), ("R18", "R05"), ("R18", "R06"),
        ("R19", "R08"), ("R19", "R09"), ("R20", "R07"), ("R20", "R14"),
        # Tech local mesh
        ("T11", "T01"), ("T11", "T02"), ("T12", "T03"), ("T12", "T04"),
        ("T13", "T04"), ("T13", "T05"), ("T14", "T06"), ("T14", "T07"),
        ("T15", "T07"), ("T15", "T08"), ("T16", "T09"), ("T16", "T10"),
        ("T17", "T02"), ("T17", "T03"), ("T18", "T05"), ("T18", "T06"),
        ("T19", "T08"), ("T19", "T09"), ("T20", "T05"), ("T20", "T06"),
    ]
    for u, v in secondary_links:
        if u in net.nodes and v in net.nodes and not net.get_edge(u, v):
            net.add_road(u, v, speed_limit_kmh=45.0, road_type="local", lanes=2)

    # 4. Outer Ring Road Highway (Speed Limit 95 km/h, 4 Lanes)
    outer_ring = [
        "R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10",
        "I21", "I04", "I08", "I12", "I16", "I20", "I22",
        "T10", "T09", "T08", "T07", "T06", "T05", "T04", "T03", "T02", "T01",
        "M24", "M04", "M03", "M02", "M01", "M23", "R01"
    ]
    connect_chain(outer_ring, speed=95.0, rtype="highway", lanes=4)

    # Initial realistic traffic distribution
    random.seed(42)
    for u, neighbors in net.adjacency.items():
        for v, road in neighbors.items():
            if road.road_type == "highway":
                road.traffic_multiplier = round(random.uniform(1.0, 1.2), 2)
            elif u.startswith("D") or v.startswith("D"):
                road.traffic_multiplier = round(random.uniform(1.3, 2.2), 2)
            else:
                road.traffic_multiplier = round(random.uniform(1.0, 1.4), 2)

    return net


class ProceduralCityGenerator:
    """
    Generates synthetic smart-city networks for scaling tests.
    """
    @staticmethod
    def generate(num_nodes: int = 150, seed: int = 42) -> CityRoadNetwork:
        random.seed(seed)
        net = CityRoadNetwork(name=f"Procedural-City-{num_nodes}")

        grid_cols = int(num_nodes ** 0.5 * 1.3)
        grid_rows = int(num_nodes / grid_cols) + 1

        node_ids = []
        for r in range(grid_rows):
            for c in range(grid_cols):
                if len(node_ids) >= num_nodes:
                    break
                idx = len(node_ids) + 1
                nid = f"N{idx:03d}"
                x = 10.0 + c * 5.5 + random.uniform(-0.4, 0.4)
                y = 10.0 + r * 5.0 + random.uniform(-0.4, 0.4)
                
                ntype = "hospital" if idx % 25 == 1 else ("fire_station" if idx % 25 == 12 else "intersection")
                net.add_intersection(nid, f"Intersection-{nid}", round(x, 1), round(y, 1), node_type=ntype, district=f"Sector-{(idx%5)+1}")
                node_ids.append(nid)

        # Connect grid
        for i, u_id in enumerate(node_ids):
            u_node = net.nodes[u_id]
            for j, v_id in enumerate(node_ids):
                if i < j:
                    v_node = net.nodes[v_id]
                    dist = u_node.distance_to(v_node)
                    if dist < 7.5:
                        net.add_road(u_id, v_id, speed_limit_kmh=60.0, road_type="arterial")

        return net
