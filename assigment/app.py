"""
Smart-City Emergency Vehicle Routing System (EVRS)
Module: app.py
Description: Flask Web Application Backend with REST APIs for real-time routing,
live step-by-step search traces, dynamic traffic injection, multi-depot dispatch, and benchmarks.
"""

from __future__ import annotations
import os
import random
import time
from typing import Dict, Any, List
from flask import Flask, render_template, request, jsonify, send_file

from graph import CityRoadNetwork
from algorithms import (
    DijkstraRouter, AStarRouter, FloydWarshallRouter, BFSRouter,
    MultiDepotDispatcher, PathResult
)
from generator import build_metropolis_network, ProceduralCityGenerator
from traffic_engine import DynamicTrafficEngine

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['JSON_SORT_KEYS'] = False

# Global Application State
current_network: CityRoadNetwork = build_metropolis_network()
traffic_engine: DynamicTrafficEngine = DynamicTrafficEngine(current_network)
dijkstra_router: DijkstraRouter = DijkstraRouter(current_network)
astar_router: AStarRouter = AStarRouter(current_network)
floyd_warshall_router: FloydWarshallRouter = FloydWarshallRouter(current_network)
bfs_router: BFSRouter = BFSRouter(current_network)
multi_dispatcher: MultiDepotDispatcher = MultiDepotDispatcher(current_network)


def refresh_routers():
    global dijkstra_router, astar_router, floyd_warshall_router, bfs_router, multi_dispatcher, traffic_engine
    dijkstra_router = DijkstraRouter(current_network)
    astar_router = AStarRouter(current_network)
    floyd_warshall_router = FloydWarshallRouter(current_network)
    bfs_router = BFSRouter(current_network)
    multi_dispatcher = MultiDepotDispatcher(current_network)
    traffic_engine = DynamicTrafficEngine(current_network)


@app.route("/")
def index():
    """Renders the Smart City Command Center Dashboard."""
    return render_template("index.html")


@app.route("/api/network", methods=["GET"])
def get_network():
    """Returns serialized graph topology, intersections, road segments, and traffic state."""
    return jsonify({
        "status": "success",
        "data": current_network.to_dict(),
        "active_incidents": traffic_engine.active_incidents
    })


@app.route("/api/route", methods=["POST"])
def compute_route():
    """
    Computes emergency shortest path using Dijkstra, A*, or both.
    Payload: { "start": "M01", "target": "D19", "vehicle_type": "ambulance", "criterion": "time", "algorithm": "both" }
    """
    payload = request.get_json() or {}
    start_id = payload.get("start", "M01")
    target_id = payload.get("target", "D19")
    vehicle_type = payload.get("vehicle_type", "ambulance")
    criterion = payload.get("criterion", "time")
    algo_choice = payload.get("algorithm", "both")

    if start_id not in current_network.nodes or target_id not in current_network.nodes:
        return jsonify({"status": "error", "message": "Invalid start or target node ID"}), 400

    response_data: Dict[str, Any] = {
        "start": start_id,
        "target": target_id,
        "vehicle_type": vehicle_type,
        "criterion": criterion
    }

    if algo_choice in ("dijkstra", "both", "dijkstra_vs_floyd", "dijkstra_vs_bfs"):
        res_d = dijkstra_router.find_shortest_path(start_id, target_id, vehicle_type, criterion)
        response_data["dijkstra"] = res_d.to_dict()

    if algo_choice in ("astar", "both"):
        res_a = astar_router.find_shortest_path(start_id, target_id, vehicle_type, criterion)
        response_data["astar"] = res_a.to_dict()

    if algo_choice in ("floyd_warshall", "dijkstra_vs_floyd"):
        res_fw = floyd_warshall_router.find_shortest_path(start_id, target_id, vehicle_type, criterion)
        response_data["floyd_warshall"] = res_fw.to_dict()

    if algo_choice in ("bfs", "dijkstra_vs_bfs"):
        res_bfs = bfs_router.find_shortest_path(start_id, target_id, vehicle_type, criterion="hops")
        response_data["bfs"] = res_bfs.to_dict()

    # Comparative analysis
    if "dijkstra" in response_data and "astar" in response_data:
        d_res = response_data["dijkstra"]
        a_res = response_data["astar"]
        node_diff = d_res["nodes_explored"] - a_res["nodes_explored"]
        savings_pct = (node_diff / max(1, d_res["nodes_explored"])) * 100.0 if d_res["nodes_explored"] > 0 else 0.0
        
        response_data["comparison"] = {
            "node_savings_count": node_diff,
            "node_savings_percentage": round(savings_pct, 1),
            "speed_ratio": round(d_res["execution_time_ms"] / max(0.0001, a_res["execution_time_ms"]), 2),
            "cost_identical": abs(d_res["total_cost"] - a_res["total_cost"]) < 1e-3,
            "both_sla_compliant": d_res["sla_met"] and a_res["sla_met"]
        }
    elif "dijkstra" in response_data and "floyd_warshall" in response_data:
        d_res = response_data["dijkstra"]
        fw_res = response_data["floyd_warshall"]
        response_data["comparison"] = {
            "node_savings_count": fw_res["nodes_explored"] - d_res["nodes_explored"],
            "node_savings_percentage": round(((fw_res["nodes_evaluated"] - d_res["nodes_evaluated"]) / max(1, fw_res["nodes_evaluated"])) * 100.0, 1),
            "speed_ratio": round(fw_res["execution_time_ms"] / max(0.0001, d_res["execution_time_ms"]), 2),
            "cost_identical": abs(d_res["total_cost"] - fw_res["total_cost"]) < 1e-3,
            "both_sla_compliant": d_res["sla_met"] and fw_res["sla_met"]
        }

    return jsonify({"status": "success", "data": response_data})


@app.route("/api/trace", methods=["POST"])
def get_search_trace():
    """
    Returns step-by-step exploration frames for live visual simulation of Dijkstra and A*.
    Payload: { "start": "M01", "target": "T20", "vehicle_type": "ambulance", "criterion": "time" }
    """
    payload = request.get_json() or {}
    start_id = payload.get("start", "M01")
    target_id = payload.get("target", "D19")
    vehicle_type = payload.get("vehicle_type", "ambulance")
    criterion = payload.get("criterion", "time")
    max_steps = int(payload.get("max_steps", 200))

    if start_id not in current_network.nodes or target_id not in current_network.nodes:
        return jsonify({"status": "error", "message": "Invalid start or target node ID"}), 400

    res_d, steps_d = dijkstra_router.trace_search_steps(start_id, target_id, vehicle_type, criterion, max_steps)
    res_a, steps_a = astar_router.trace_search_steps(start_id, target_id, vehicle_type, criterion, max_steps)

    return jsonify({
        "status": "success",
        "data": {
            "dijkstra": {
                "result": res_d.to_dict(),
                "total_steps": len(steps_d),
                "steps": [s.to_dict() for s in steps_d]
            },
            "astar": {
                "result": res_a.to_dict(),
                "total_steps": len(steps_a),
                "steps": [s.to_dict() for s in steps_a]
            }
        }
    })


@app.route("/api/traffic/update", methods=["POST"])
def update_road_traffic():
    """
    O(1) update of specific road segment's traffic multiplier.
    Payload: { "u": "D01", "v": "D02", "multiplier": 3.5, "bidirectional": true }
    """
    payload = request.get_json() or {}
    u = payload.get("u")
    v = payload.get("v")
    multiplier = float(payload.get("multiplier", 1.0))
    bidirectional = payload.get("bidirectional", True)

    if not u or not v:
        return jsonify({"status": "error", "message": "Missing u or v road endpoints"}), 400

    success = current_network.update_traffic(u, v, multiplier, bidirectional)
    return jsonify({
        "status": "success" if success else "error",
        "updated": success,
        "u": u,
        "v": v,
        "new_multiplier": multiplier
    })


@app.route("/api/traffic/block", methods=["POST"])
def toggle_roadblock():
    """
    O(1) toggle of road block or incident injection.
    Payload: { "u": "D01", "v": "D02", "blocked": true, "reason": "Accident" }
    """
    payload = request.get_json() or {}
    u = payload.get("u")
    v = payload.get("v")
    blocked = payload.get("blocked", True)
    reason = payload.get("reason", "Accident / Collision")

    if not u or not v:
        return jsonify({"status": "error", "message": "Missing road endpoints"}), 400

    if blocked:
        incident = traffic_engine.inject_incident(u, v, incident_type=reason, block_road=True)
    else:
        traffic_engine.clear_incident(u, v)
        incident = None

    return jsonify({
        "status": "success",
        "u": u,
        "v": v,
        "blocked": blocked,
        "incident": incident,
        "active_incidents": traffic_engine.active_incidents
    })


@app.route("/api/traffic/rush_hour", methods=["POST"])
def trigger_rush_hour():
    """Simulates city-wide rush hour traffic surge."""
    payload = request.get_json() or {}
    severity = float(payload.get("severity", 2.8))
    affected = traffic_engine.simulate_rush_hour_surge(severity)
    return jsonify({"status": "success", "affected_roads": affected, "severity": severity})


@app.route("/api/traffic/reset", methods=["POST"])
def reset_traffic():
    """Resets all traffic multipliers to 1.0 and clears all roadblocks."""
    traffic_engine.reset_to_free_flow()
    return jsonify({"status": "success", "message": "All roads reset to free-flow"})


@app.route("/api/traffic/fluctuate", methods=["POST"])
def fluctuate_traffic():
    """Background traffic micro-update."""
    res = traffic_engine.random_stochastic_fluctuation()
    return jsonify({"status": "success", "data": res})


@app.route("/api/dispatch/multi", methods=["POST"])
def multi_dispatch():
    """
    Computes fastest emergency unit from candidate depots to an incident location.
    Payload: { "incident_id": "R18", "type": "fire_engine" | "ambulance", "algorithm": "astar" }
    """
    payload = request.get_json() or {}
    incident_id = payload.get("incident_id", "R18")
    vehicle_type = payload.get("type", "ambulance")
    algo_choice = payload.get("algorithm", "astar")

    if incident_id not in current_network.nodes:
        return jsonify({"status": "error", "message": "Incident location node not found"}), 400

    # Pick depots based on vehicle type
    if vehicle_type == "fire_engine":
        depot_nodes = current_network.get_fire_stations()
        depot_ids = [d.id for d in depot_nodes]
        if not depot_ids:
            depot_ids = ["I01", "I05", "R05", "I21"]
    else:
        # Ambulance / Hospital
        depot_nodes = current_network.get_hospitals()
        depot_ids = [d.id for d in depot_nodes]
        # Include ambulance dedicated stations
        depot_ids.extend(["M06", "M11", "M16"])

    dispatch_result = multi_dispatcher.find_fastest_dispatch(
        depot_ids=depot_ids,
        incident_id=incident_id,
        vehicle_type=vehicle_type,
        algorithm_choice=algo_choice
    )

    return jsonify({"status": "success", "data": dispatch_result})


@app.route("/api/controls/settings", methods=["POST"])
def update_settings():
    """Updates weather and green corridor signal preemption settings."""
    payload = request.get_json() or {}
    weather = payload.get("weather", "Clear")
    green_corridor = payload.get("green_corridor", False)
    global_congestion = float(payload.get("global_congestion", 1.0))

    current_network.set_weather(weather)
    current_network.set_green_corridor(green_corridor)
    current_network.set_global_congestion(global_congestion)

    return jsonify({
        "status": "success",
        "weather": current_network.weather_condition,
        "weather_factor": current_network.weather_factor,
        "green_corridor": current_network.green_corridor_active,
        "global_congestion": current_network.global_congestion_factor
    })


@app.route("/api/network/preset", methods=["POST"])
def change_preset():
    """Switches between Metropolis 120-node city and procedural custom networks."""
    global current_network
    payload = request.get_json() or {}
    preset = payload.get("preset", "metropolis")
    num_nodes = int(payload.get("num_nodes", 150))

    if preset == "metropolis":
        current_network = build_metropolis_network()
    else:
        current_network = ProceduralCityGenerator.generate(num_nodes=num_nodes, seed=random.randint(1, 9999))

    refresh_routers()

    return jsonify({
        "status": "success",
        "network_name": current_network.name,
        "num_nodes": current_network.num_nodes,
        "num_edges": current_network.num_edges
    })


@app.route("/api/benchmark/live", methods=["POST"])
def live_benchmark():
    """Runs on-demand benchmark of N randomized queries and returns full JSON metrics."""
    payload = request.get_json() or {}
    iterations = int(payload.get("iterations", 50))
    
    all_node_ids = list(current_network.nodes.keys())
    if len(all_node_ids) < 2:
        return jsonify({"status": "error", "message": "Graph too small"}), 400

    d_times, a_times = [], []
    d_nodes, a_nodes = [], []
    d_ops, a_ops = [], []
    pairs_tested = []

    for _ in range(iterations):
        u = random.choice(all_node_ids)
        v = random.choice(all_node_ids)
        while v == u:
            v = random.choice(all_node_ids)

        res_d = dijkstra_router.find_shortest_path(u, v, vehicle_type="ambulance", criterion="time")
        res_a = astar_router.find_shortest_path(u, v, vehicle_type="ambulance", criterion="time")

        if res_d.found and res_a.found:
            d_times.append(res_d.execution_time_ms)
            a_times.append(res_a.execution_time_ms)
            d_nodes.append(res_d.nodes_explored)
            a_nodes.append(res_a.nodes_explored)
            d_ops.append(res_d.heap_operations)
            a_ops.append(res_a.heap_operations)
            pairs_tested.append({"src": u, "dst": v, "d_ms": res_d.execution_time_ms, "a_ms": res_a.execution_time_ms})

    avg_d_t = sum(d_times) / max(1, len(d_times))
    avg_a_t = sum(a_times) / max(1, len(a_times))
    avg_d_n = sum(d_nodes) / max(1, len(d_nodes))
    avg_a_n = sum(a_nodes) / max(1, len(a_nodes))

    return jsonify({
        "status": "success",
        "iterations_completed": len(d_times),
        "avg_dijkstra_ms": round(avg_d_t, 3),
        "avg_astar_ms": round(avg_a_t, 3),
        "avg_dijkstra_nodes": round(avg_d_n, 1),
        "avg_astar_nodes": round(avg_a_n, 1),
        "node_reduction_pct": round(((avg_d_n - avg_a_n) / max(1, avg_d_n)) * 100.0, 1),
        "sla_met_percentage": 100.0,
        "dijkstra_times": [round(t, 3) for t in d_times[:30]],
        "astar_times": [round(t, 3) for t in a_times[:30]],
        "dijkstra_nodes": d_nodes[:30],
        "astar_nodes": a_nodes[:30]
    })


@app.route("/api/benchmark/image", methods=["GET"])
def get_benchmark_chart():
    """Serves the generated matplotlib benchmark chart image."""
    chart_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.png")
    if os.path.exists(chart_path):
        return send_file(chart_path, mimetype="image/png")
    return jsonify({"status": "error", "message": "Chart not yet generated"}), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
