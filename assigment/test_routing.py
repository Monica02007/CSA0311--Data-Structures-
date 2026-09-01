"""
Smart-City Emergency Vehicle Routing System (EVRS)
Module: test_routing.py
Description: Automated unit & integration tests verifying graph construction,
algorithm optimality, sub-200ms latency SLA, dynamic traffic updates, and Flask REST APIs.
"""

import unittest
import time
import json
import os
import sys

# Ensure current package directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import CityRoadNetwork
from algorithms import DijkstraRouter, AStarRouter, MultiDepotDispatcher
from generator import build_metropolis_network, ProceduralCityGenerator
from app import app


class TestEmergencyVehicleRoutingSystem(unittest.TestCase):
    def setUp(self):
        self.net = build_metropolis_network()
        self.dijkstra = DijkstraRouter(self.net)
        self.astar = AStarRouter(self.net)
        self.dispatcher = MultiDepotDispatcher(self.net)
        self.client = app.test_client()

    def test_network_scale_constraints(self):
        """Validates network satisfies constraints (>100 intersections, >200 roads)."""
        print(f"\n[Test] Intersections: {self.net.num_nodes}, Directed Roads: {self.net.num_edges}")
        self.assertGreater(self.net.num_nodes, 100, "Network must contain > 100 intersections")
        self.assertGreater(self.net.num_edges, 200, "Network must contain > 200 roads")

    def test_algorithm_optimality_equivalence(self):
        """Verifies that Dijkstra and A* produce identical optimal path costs."""
        test_pairs = [("M01", "D19"), ("I01", "T10"), ("R05", "M22"), ("D01", "I15"), ("M06", "R20")]
        for u, v in test_pairs:
            res_d = self.dijkstra.find_shortest_path(u, v, vehicle_type="ambulance", criterion="time")
            res_a = self.astar.find_shortest_path(u, v, vehicle_type="ambulance", criterion="time")
            
            self.assertTrue(res_d.found, f"Dijkstra failed to find path from {u} to {v}")
            self.assertTrue(res_a.found, f"A* failed to find path from {u} to {v}")
            self.assertAlmostEqual(
                res_d.total_cost, res_a.total_cost, delta=1e-3,
                msg=f"Optimality mismatch between Dijkstra ({res_d.total_cost}) and A* ({res_a.total_cost})"
            )

    def test_sub_200ms_latency_sla(self):
        """Verifies that route queries execute well under 200 ms (typically < 2 ms)."""
        for _ in range(25):
            res_d = self.dijkstra.find_shortest_path("M01", "T10", vehicle_type="fire_engine", criterion="time")
            res_a = self.astar.find_shortest_path("M01", "T10", vehicle_type="fire_engine", criterion="time")
            self.assertLess(res_d.execution_time_ms, 200.0, "Dijkstra exceeded 200ms SLA")
            self.assertLess(res_a.execution_time_ms, 200.0, "A* exceeded 200ms SLA")
            self.assertTrue(res_d.sla_met)
            self.assertTrue(res_a.sla_met)

    def test_dynamic_traffic_update_o1(self):
        """Verifies O(1) dynamic traffic multiplier mutation and cost adjustment."""
        # Test on arterial multi-hop route
        res_before = self.dijkstra.find_shortest_path("M01", "T10", vehicle_type="normal", criterion="time")
        
        # Inject gridlock on an edge along the path
        if len(res_before.path) >= 2:
            u, v = res_before.path[0], res_before.path[1]
            success = self.net.update_traffic(u, v, traffic_multiplier=5.0, bidirectional=True)
            self.assertTrue(success)
            
            # Recompute
            res_after = self.dijkstra.find_shortest_path("M01", "T10", vehicle_type="normal", criterion="time")
            self.assertGreater(res_after.total_time_seconds, res_before.total_time_seconds)

    def test_roadblock_and_rerouting(self):
        """Verifies that closing a road forces the router to find an alternative bypass."""
        res_orig = self.dijkstra.find_shortest_path("M01", "D19")
        if len(res_orig.path) >= 2:
            u, v = res_orig.path[0], res_orig.path[1]
            # Block the direct road
            self.net.set_road_block(u, v, is_blocked=True, bidirectional=True)
            
            res_bypass = self.dijkstra.find_shortest_path("M01", "D19")
            self.assertTrue(res_bypass.found)
            self.assertGreater(len(res_bypass.path), 2, "Should take alternative multi-hop path")
            # Ensure the blocked edge is NOT in the new path
            edges_in_new_path = list(zip(res_bypass.path[:-1], res_bypass.path[1:]))
            self.assertNotIn((u, v), edges_in_new_path)
            self.assertNotIn((v, u), edges_in_new_path)

    def test_multi_depot_dispatch(self):
        """Tests many-to-one closest emergency unit dispatch."""
        depots = ["M01", "M06", "I01", "R05"]
        dispatch_res = self.dispatcher.find_fastest_dispatch(depots, "T20", vehicle_type="ambulance")
        self.assertIsNotNone(dispatch_res["best_unit"])
        self.assertTrue(dispatch_res["sla_met"])
        self.assertEqual(len(dispatch_res["all_candidates"]), len(depots))

    def test_flask_rest_api_endpoints(self):
        """Tests all REST endpoints."""
        # 1. Network API
        r1 = self.client.get("/api/network")
        self.assertEqual(r1.status_code, 200)
        data = r1.get_json()["data"]
        self.assertGreater(data["num_nodes"], 100)

        # 2. Route API
        r2 = self.client.post("/api/route", json={"start": "M01", "target": "D19", "algorithm": "both"})
        self.assertEqual(r2.status_code, 200)
        route_data = r2.get_json()["data"]
        self.assertIn("dijkstra", route_data)
        self.assertIn("astar", route_data)
        self.assertIn("comparison", route_data)

        # 3. Trace API
        r3 = self.client.post("/api/trace", json={"start": "M01", "target": "D19"})
        self.assertEqual(r3.status_code, 200)
        trace_data = r3.get_json()["data"]
        self.assertIn("dijkstra", trace_data)
        self.assertIn("astar", trace_data)

        # 4. Traffic Update API
        r4 = self.client.post("/api/traffic/update", json={"u": "M01", "v": "M02", "multiplier": 3.0})
        self.assertEqual(r4.status_code, 200)


if __name__ == "__main__":
    unittest.main()
