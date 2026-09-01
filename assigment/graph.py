"""
Smart-City Emergency Vehicle Routing System (EVRS)
Module: graph.py
Description: Hash-based graph representation for road networks, supporting O(1)
traffic condition updates, roadblock toggles, and dynamic edge-weight calculation.
"""

from __future__ import annotations
import math
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field


@dataclass
class Intersection:
    """Represents a road intersection / landmark node in the smart city network."""
    id: str
    name: str
    x: float
    y: float
    node_type: str = "intersection"  # "hospital", "fire_station", "intersection", "depot", "landmark"
    district: str = "Downtown"
    elevation: float = 0.0
    traffic_signal_delay: float = 10.0  # seconds delay for normal vehicles at red lights
    
    def distance_to(self, other: Intersection) -> float:
        """Euclidean distance in kilometers between two intersections."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)


@dataclass
class RoadSegment:
    """Represents a directed road connecting two intersections."""
    u: str
    v: str
    distance_km: float
    speed_limit_kmh: float
    road_type: str = "arterial"  # "highway", "arterial", "local", "emergency_lane"
    lanes: int = 2
    traffic_multiplier: float = 1.0  # 1.0 = clear flow, 1.5 = moderate, 2.5 = heavy, 4.0 = gridlock
    is_blocked: bool = False
    incident_description: Optional[str] = None
    last_updated: float = field(default_factory=time.time)

    @property
    def free_flow_time_seconds(self) -> float:
        """Base travel time at speed limit in seconds."""
        if self.speed_limit_kmh <= 0:
            return float('inf')
        return (self.distance_km / self.speed_limit_kmh) * 3600.0

    def calculate_travel_time_seconds(
        self,
        vehicle_type: str = "ambulance",
        weather_factor: float = 1.0,
        green_corridor_active: bool = False
    ) -> float:
        """
        Calculates effective dynamic travel time in seconds.
        Accounts for:
        - Distance and speed limits
        - Dynamic live traffic congestion multiplier
        - Road blockage / accidents
        - Emergency vehicle siren preemption & green corridor signal bypass
        - Weather friction
        """
        if self.is_blocked:
            return float('inf')

        # Base time under speed limit
        base_time = self.free_flow_time_seconds

        # Emergency vehicle adjustment: Ambulances and Fire Engines can travel faster or bypass partial traffic
        # with sirens, reducing congestion impact by 30-40%
        effective_traffic = self.traffic_multiplier
        if vehicle_type in ("ambulance", "fire_engine"):
            if self.road_type == "emergency_lane":
                effective_traffic = 1.0  # Dedicated lane is clear
            elif green_corridor_active:
                # Green corridor clears signals and opens priority lane
                effective_traffic = max(1.0, 1.0 + (self.traffic_multiplier - 1.0) * 0.25)
            else:
                effective_traffic = max(1.0, 1.0 + (self.traffic_multiplier - 1.0) * 0.6)

        # Weather factor impact
        total_time = base_time * effective_traffic * weather_factor

        # Small penalty for road tier (highways have less turning friction than local streets)
        tier_penalty = {"highway": 0.95, "arterial": 1.0, "local": 1.15, "emergency_lane": 0.85}.get(self.road_type, 1.0)
        
        return total_time * tier_penalty


class CityRoadNetwork:
    """
    Graph representation using HashMaps (dict of dicts) for O(1) edge lookup and adjacency traversal.
    Nodes: HashMap[node_id -> Intersection]
    Edges: HashMap[u -> HashMap[v -> RoadSegment]]
    """
    def __init__(self, name: str = "SmartCity-Network"):
        self.name = name
        self.nodes: Dict[str, Intersection] = {}
        self.adjacency: Dict[str, Dict[str, RoadSegment]] = {}
        self.weather_condition: str = "Clear"
        self.weather_factor: float = 1.0
        self.global_congestion_factor: float = 1.0
        self.green_corridor_active: bool = False
        self._total_roads_count: int = 0

    def add_intersection(
        self,
        node_id: str,
        name: str,
        x: float,
        y: float,
        node_type: str = "intersection",
        district: str = "Downtown",
        elevation: float = 0.0
    ) -> Intersection:
        """Adds an intersection / landmark to the network. O(1) operation."""
        node = Intersection(
            id=node_id,
            name=name,
            x=x,
            y=y,
            node_type=node_type,
            district=district,
            elevation=elevation
        )
        self.nodes[node_id] = node
        if node_id not in self.adjacency:
            self.adjacency[node_id] = {}
        return node

    def add_road(
        self,
        u: str,
        v: str,
        distance_km: Optional[float] = None,
        speed_limit_kmh: float = 60.0,
        road_type: str = "arterial",
        lanes: int = 2,
        bidirectional: bool = True
    ) -> Tuple[RoadSegment, Optional[RoadSegment]]:
        """
        Adds a directed or bidirectional road segment. O(1) operation.
        If distance_km is not provided, calculates Euclidean distance from node coordinates.
        """
        if u not in self.nodes or v not in self.nodes:
            raise KeyError(f"Both nodes {u} and {v} must exist in the network before adding a road.")

        if distance_km is None:
            distance_km = round(self.nodes[u].distance_to(self.nodes[v]), 2)
            if distance_km == 0:
                distance_km = 0.1  # Minimum distance fallback

        road_uv = RoadSegment(
            u=u,
            v=v,
            distance_km=distance_km,
            speed_limit_kmh=speed_limit_kmh,
            road_type=road_type,
            lanes=lanes,
            traffic_multiplier=1.0,
            is_blocked=False
        )
        self.adjacency[u][v] = road_uv
        self._total_roads_count += 1

        road_vu = None
        if bidirectional:
            road_vu = RoadSegment(
                u=v,
                v=u,
                distance_km=distance_km,
                speed_limit_kmh=speed_limit_kmh,
                road_type=road_type,
                lanes=lanes,
                traffic_multiplier=1.0,
                is_blocked=False
            )
            self.adjacency[v][u] = road_vu
            self._total_roads_count += 1

        return road_uv, road_vu

    # --- O(1) Dynamic Traffic Update Methods ---

    def update_traffic(
        self,
        u: str,
        v: str,
        traffic_multiplier: float,
        bidirectional: bool = True
    ) -> bool:
        """
        O(1) update of traffic condition for road (u, v).
        traffic_multiplier: 1.0 (clear) to 5.0 (gridlock).
        """
        updated = False
        if u in self.adjacency and v in self.adjacency[u]:
            self.adjacency[u][v].traffic_multiplier = max(1.0, float(traffic_multiplier))
            self.adjacency[u][v].last_updated = time.time()
            updated = True

        if bidirectional and v in self.adjacency and u in self.adjacency[v]:
            self.adjacency[v][u].traffic_multiplier = max(1.0, float(traffic_multiplier))
            self.adjacency[v][u].last_updated = time.time()
            updated = True

        return updated

    def set_road_block(
        self,
        u: str,
        v: str,
        is_blocked: bool,
        incident_description: Optional[str] = None,
        bidirectional: bool = True
    ) -> bool:
        """O(1) road closure or reopening due to accidents, construction, or waterlogging."""
        modified = False
        if u in self.adjacency and v in self.adjacency[u]:
            self.adjacency[u][v].is_blocked = is_blocked
            self.adjacency[u][v].incident_description = incident_description if is_blocked else None
            self.adjacency[u][v].last_updated = time.time()
            modified = True

        if bidirectional and v in self.adjacency and u in self.adjacency[v]:
            self.adjacency[v][u].is_blocked = is_blocked
            self.adjacency[v][u].incident_description = incident_description if is_blocked else None
            self.adjacency[v][u].last_updated = time.time()
            modified = True

        return modified

    def set_weather(self, condition: str) -> None:
        """Updates weather and corresponding friction coefficient."""
        weather_factors = {
            "Clear": 1.0,
            "Light Rain": 1.15,
            "Heavy Rain / Flood": 1.45,
            "Fog / Low Visibility": 1.30,
            "Storm": 1.60
        }
        self.weather_condition = condition
        self.weather_factor = weather_factors.get(condition, 1.0)

    def set_green_corridor(self, active: bool) -> None:
        """Toggles smart city traffic signal preemption (Green Corridor) for emergency routes."""
        self.green_corridor_active = active

    def set_global_congestion(self, factor: float) -> None:
        """Scales overall traffic density across the city (e.g. Rush Hour surge)."""
        self.global_congestion_factor = max(0.5, min(4.0, factor))

    # --- Query Methods ---

    def get_neighbors(self, node_id: str) -> Dict[str, RoadSegment]:
        """Returns adjacent road segments for node_id. O(1) lookup."""
        return self.adjacency.get(node_id, {})

    def get_edge(self, u: str, v: str) -> Optional[RoadSegment]:
        """Returns edge (u, v) or None if no direct connection exists. O(1) lookup."""
        return self.adjacency.get(u, {}).get(v)

    def get_weight(
        self,
        u: str,
        v: str,
        vehicle_type: str = "ambulance",
        criterion: str = "time"  # "time" (fastest route) or "distance" (shortest physical distance)
    ) -> float:
        """
        Returns dynamic cost for traversing from u to v.
        Returns float('inf') if road is blocked or does not exist.
        """
        edge = self.get_edge(u, v)
        if not edge or edge.is_blocked:
            return float('inf')

        if criterion == "distance":
            return edge.distance_km

        # Default criterion is dynamic travel time (seconds)
        effective_weather = self.weather_factor
        return edge.calculate_travel_time_seconds(
            vehicle_type=vehicle_type,
            weather_factor=effective_weather * self.global_congestion_factor,
            green_corridor_active=self.green_corridor_active
        )

    def get_hospitals(self) -> List[Intersection]:
        """Returns all hospital nodes in the city."""
        return [node for node in self.nodes.values() if node.node_type == "hospital"]

    def get_fire_stations(self) -> List[Intersection]:
        """Returns all fire station nodes in the city."""
        return [node for node in self.nodes.values() if node.node_type == "fire_station"]

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return sum(len(neighbors) for neighbors in self.adjacency.values())

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph for JSON API consumption and frontend rendering."""
        nodes_data = []
        for n in self.nodes.values():
            nodes_data.append({
                "id": n.id,
                "name": n.name,
                "x": n.x,
                "y": n.y,
                "type": n.node_type,
                "district": n.district,
                "elevation": n.elevation
            })

        edges_data = []
        for u, neighbors in self.adjacency.items():
            for v, road in neighbors.items():
                edges_data.append({
                    "u": road.u,
                    "v": road.v,
                    "distance_km": road.distance_km,
                    "speed_limit_kmh": road.speed_limit_kmh,
                    "road_type": road.road_type,
                    "lanes": road.lanes,
                    "traffic_multiplier": round(road.traffic_multiplier, 2),
                    "is_blocked": road.is_blocked,
                    "incident": road.incident_description,
                    "effective_time_s": round(road.calculate_travel_time_seconds(), 1)
                })

        return {
            "name": self.name,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "weather": self.weather_condition,
            "weather_factor": self.weather_factor,
            "global_congestion": self.global_congestion_factor,
            "green_corridor": self.green_corridor_active,
            "nodes": nodes_data,
            "edges": edges_data
        }
