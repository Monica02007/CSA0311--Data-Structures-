"""
Smart-City Emergency Vehicle Routing System (EVRS)
Module: traffic_engine.py
Description: Dynamic Smart-City Traffic Management Engine with real-time O(1)
congestion mutations, stochastic incident triggers, roadblock injections, and green corridor controls.
"""

from __future__ import annotations
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from graph import CityRoadNetwork, RoadSegment


class DynamicTrafficEngine:
    """
    Simulates dynamic real-time urban traffic conditions and handles emergency incident injections.
    """
    def __init__(self, network: CityRoadNetwork):
        self.network = network
        self.active_incidents: List[Dict[str, Any]] = []
        self.last_tick_time = time.time()

    def inject_incident(
        self,
        u: str,
        v: str,
        incident_type: str = "Major Multi-Vehicle Accident",
        block_road: bool = True,
        traffic_surge: float = 4.5
    ) -> Dict[str, Any]:
        """
        Injects a critical incident on road segment (u, v) in O(1).
        If block_road is True, completely blocks road.
        Otherwise creates massive congestion bottleneck (traffic_surge).
        """
        incident_record = {
            "id": f"INC-{int(time.time()*1000)%100000}",
            "u": u,
            "v": v,
            "u_name": self.network.nodes[u].name if u in self.network.nodes else u,
            "v_name": self.network.nodes[v].name if v in self.network.nodes else v,
            "type": incident_type,
            "blocked": block_road,
            "multiplier": traffic_surge,
            "timestamp": time.time()
        }

        if block_road:
            self.network.set_road_block(u, v, is_blocked=True, incident_description=incident_type, bidirectional=True)
        else:
            self.network.update_traffic(u, v, traffic_multiplier=traffic_surge, bidirectional=True)

        self.active_incidents.append(incident_record)
        return incident_record

    def clear_incident(self, u: str, v: str) -> bool:
        """Clears an active incident on road (u, v) in O(1)."""
        self.network.set_road_block(u, v, is_blocked=False, incident_description=None, bidirectional=True)
        self.network.update_traffic(u, v, traffic_multiplier=1.2, bidirectional=True)
        
        # Remove from active records
        self.active_incidents = [
            inc for inc in self.active_incidents
            if not ((inc["u"] == u and inc["v"] == v) or (inc["u"] == v and inc["v"] == u))
        ]
        return True

    def clear_all_incidents(self) -> int:
        """Reopens all blocked roads and clears incidents."""
        count = len(self.active_incidents)
        for inc in list(self.active_incidents):
            self.clear_incident(inc["u"], inc["v"])
        self.active_incidents.clear()
        return count

    def simulate_rush_hour_surge(self, severity: float = 2.5) -> int:
        """
        Simulates sudden rush hour congestion in Downtown and Arterial corridors.
        """
        affected = 0
        for u, neighbors in self.network.adjacency.items():
            for v, road in neighbors.items():
                if road.road_type in ("arterial", "local") and (u.startswith("D") or v.startswith("D") or u.startswith("T")):
                    surge = round(random.uniform(1.8, severity), 2)
                    road.traffic_multiplier = surge
                    affected += 1
                elif road.road_type == "highway":
                    road.traffic_multiplier = round(random.uniform(1.2, 1.8), 2)
        return affected

    def reset_to_free_flow(self) -> None:
        """Resets all road segments to normal free-flow conditions (multiplier = 1.0)."""
        self.clear_all_incidents()
        for u, neighbors in self.network.adjacency.items():
            for v, road in neighbors.items():
                road.traffic_multiplier = 1.0
                road.is_blocked = False

    def random_stochastic_fluctuation(self) -> Dict[str, Any]:
        """
        Applies a smooth micro-fluctuation across city roads to mimic real-world traffic telemetry.
        """
        updated_roads = []
        for u, neighbors in self.network.adjacency.items():
            for v, road in neighbors.items():
                if not road.is_blocked and u < v:  # mutate once per undirected edge
                    delta = random.uniform(-0.15, 0.15)
                    new_val = max(1.0, min(3.5, road.traffic_multiplier + delta))
                    road.traffic_multiplier = round(new_val, 2)
                    road.last_updated = time.time()
                    updated_roads.append({"u": u, "v": v, "traffic": road.traffic_multiplier})

        # 10% chance of random minor incident trigger
        if random.random() < 0.1 and not self.active_incidents:
            # Pick a random edge
            all_edges = []
            for u, neighbors in self.network.adjacency.items():
                for v in neighbors:
                    if u < v:
                        all_edges.append((u, v))
            if all_edges:
                rand_u, rand_v = random.choice(all_edges)
                self.inject_incident(rand_u, rand_v, incident_type="Stalled Vehicle / Lane Hazard", block_road=False, traffic_surge=3.2)

        return {
            "timestamp": time.time(),
            "updated_count": len(updated_roads),
            "active_incidents": self.active_incidents
        }
