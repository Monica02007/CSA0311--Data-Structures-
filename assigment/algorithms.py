"""
Smart-City Emergency Vehicle Routing System (EVRS)
Module: algorithms.py
Description: Implementation of Dijkstra's Algorithm (with Min-Heap Priority Queue)
and A* Search Algorithm (with Admissible Euclidean Heuristic), featuring step-by-step
state tracers, microsecond-level benchmarking, and multi-depot emergency dispatch.
"""

from __future__ import annotations
import heapq
import time
import math
import sys
from collections import deque
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from graph import CityRoadNetwork, Intersection, RoadSegment


@dataclass
class PathResult:
    """Detailed output and telemetry for a computed route."""
    algorithm: str
    found: bool
    path: List[str]
    path_names: List[str]
    total_cost: float
    total_distance_km: float
    total_time_seconds: float
    nodes_explored: int
    nodes_evaluated: int
    heap_operations: int
    execution_time_ms: float
    memory_kb: float
    sla_met: bool
    visited_nodes_order: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "found": self.found,
            "path": self.path,
            "path_names": self.path_names,
            "total_cost": round(self.total_cost, 2),
            "total_distance_km": round(self.total_distance_km, 2),
            "total_time_seconds": round(self.total_time_seconds, 1),
            "total_time_minutes": round(self.total_time_seconds / 60.0, 2),
            "nodes_explored": self.nodes_explored,
            "nodes_evaluated": self.nodes_evaluated,
            "heap_operations": self.heap_operations,
            "execution_time_ms": round(self.execution_time_ms, 3),
            "memory_kb": round(self.memory_kb, 2),
            "sla_met": self.sla_met,
            "visited_nodes_order": self.visited_nodes_order
        }


@dataclass
class AlgorithmStep:
    """Snapshot of the search state at an individual step for live UI visualization."""
    step_index: int
    current_node: str
    current_cost: float
    frontier: List[Tuple[float, str]]  # list of [priority, node_id]
    visited: List[str]
    distances: Dict[str, float]
    relaxed_edges: List[Tuple[str, str, float]]  # (u, v, new_dist)
    heuristic_values: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_index,
            "current_node": self.current_node,
            "current_cost": round(self.current_cost, 2),
            "frontier": [{"cost": round(p, 2), "id": nid} for p, nid in self.frontier[:15]],
            "visited": self.visited,
            "distances": {k: round(v, 2) for k, v in self.distances.items()},
            "relaxed_edges": self.relaxed_edges,
            "heuristics": {k: round(v, 2) for k, v in self.heuristic_values.items()}
        }


class DijkstraRouter:
    """
    Dijkstra's Shortest Path Algorithm using a Min-Heap (heapq) Priority Queue.
    Time Complexity: O((V + E) * log V)
    Space Complexity: O(V)
    Visited Tracking: HashSet for O(1) membership checks.
    """
    def __init__(self, network: CityRoadNetwork):
        self.network = network

    def find_shortest_path(
        self,
        start_id: str,
        target_id: str,
        vehicle_type: str = "ambulance",
        criterion: str = "time"
    ) -> PathResult:
        """
        Calculates optimal path from start_id to target_id using Min-Heap Dijkstra.
        Returns complete telemetry metrics and path.
        """
        start_time = time.perf_counter()

        if start_id not in self.network.nodes or target_id not in self.network.nodes:
            return PathResult(
                algorithm="Dijkstra (Min-Heap)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=0,
                nodes_evaluated=0,
                heap_operations=0,
                execution_time_ms=0.0,
                memory_kb=0.0,
                sla_met=True,
                visited_nodes_order=[]
            )

        # Priority queue min-heap storing tuples: (current_cost, node_id)
        # Python heapq is a binary min-heap
        priority_queue: List[Tuple[float, str]] = []
        heapq.heappush(priority_queue, (0.0, start_id))
        heap_ops = 1

        # Distance table: HashMap[node_id -> min_cost]
        distances: Dict[str, float] = {start_id: 0.0}
        
        # Parent pointer table for path reconstruction: HashMap[node_id -> parent_node_id]
        parents: Dict[str, Optional[str]] = {start_id: None}
        
        # Visited HashSet for O(1) lookup
        visited: Set[str] = set()
        visited_order: List[str] = []

        nodes_explored = 0
        nodes_evaluated = 0

        while priority_queue:
            current_dist, current_node = heapq.heappop(priority_queue)
            heap_ops += 1

            if current_node in visited:
                continue

            visited.add(current_node)
            visited_order.append(current_node)
            nodes_explored += 1

            # Early termination when target is popped from min-heap (guarantees optimal shortest distance)
            if current_node == target_id:
                break

            # Explore outgoing road segments in O(degree)
            for neighbor_id, road in self.network.get_neighbors(current_node).items():
                if neighbor_id in visited or road.is_blocked:
                    continue

                nodes_evaluated += 1
                edge_weight = self.network.get_weight(
                    current_node, neighbor_id,
                    vehicle_type=vehicle_type,
                    criterion=criterion
                )
                
                if math.isinf(edge_weight):
                    continue

                new_dist = current_dist + edge_weight

                if new_dist < distances.get(neighbor_id, float('inf')):
                    distances[neighbor_id] = new_dist
                    parents[neighbor_id] = current_node
                    heapq.heappush(priority_queue, (new_dist, neighbor_id))
                    heap_ops += 1

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        # Memory estimation (distances dict + parents dict + visited set + heap)
        memory_kb = (
            sys.getsizeof(distances) +
            sys.getsizeof(parents) +
            sys.getsizeof(visited) +
            sys.getsizeof(priority_queue)
        ) / 1024.0

        if target_id not in distances or (target_id != start_id and parents.get(target_id) is None):
            return PathResult(
                algorithm="Dijkstra (Min-Heap)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=nodes_explored,
                nodes_evaluated=nodes_evaluated,
                heap_operations=heap_ops,
                execution_time_ms=exec_time_ms,
                memory_kb=memory_kb,
                sla_met=(exec_time_ms < 200.0),
                visited_nodes_order=visited_order
            )

        # Path reconstruction
        path: List[str] = []
        curr: Optional[str] = target_id
        while curr is not None:
            path.append(curr)
            curr = parents.get(curr)
        path.reverse()

        # Calculate exact distance and travel time along path
        total_dist_km = 0.0
        total_time_s = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self.network.get_edge(u, v)
            if edge:
                total_dist_km += edge.distance_km
                total_time_s += edge.calculate_travel_time_seconds(
                    vehicle_type=vehicle_type,
                    weather_factor=self.network.weather_factor * self.network.global_congestion_factor,
                    green_corridor_active=self.network.green_corridor_active
                )

        path_names = [self.network.nodes[nid].name for nid in path]

        return PathResult(
            algorithm="Dijkstra (Min-Heap)",
            found=True,
            path=path,
            path_names=path_names,
            total_cost=distances[target_id],
            total_distance_km=total_dist_km,
            total_time_seconds=total_time_s,
            nodes_explored=nodes_explored,
            nodes_evaluated=nodes_evaluated,
            heap_operations=heap_ops,
            execution_time_ms=exec_time_ms,
            memory_kb=memory_kb,
            sla_met=(exec_time_ms < 200.0),
            visited_nodes_order=visited_order
        )

    def trace_search_steps(
        self,
        start_id: str,
        target_id: str,
        vehicle_type: str = "ambulance",
        criterion: str = "time",
        max_steps: int = 250
    ) -> Tuple[PathResult, List[AlgorithmStep]]:
        """
        Executes Dijkstra and records granular step snapshots for the live UI visualizer.
        """
        priority_queue: List[Tuple[float, str]] = []
        heapq.heappush(priority_queue, (0.0, start_id))
        distances: Dict[str, float] = {start_id: 0.0}
        parents: Dict[str, Optional[str]] = {start_id: None}
        visited: Set[str] = set()
        visited_order: List[str] = []
        steps: List[AlgorithmStep] = []
        step_idx = 0

        while priority_queue and step_idx < max_steps:
            current_dist, current_node = heapq.heappop(priority_queue)

            if current_node in visited:
                continue

            visited.add(current_node)
            visited_order.append(current_node)
            step_idx += 1

            relaxed: List[Tuple[str, str, float]] = []

            if current_node == target_id:
                steps.append(AlgorithmStep(
                    step_index=step_idx,
                    current_node=current_node,
                    current_cost=current_dist,
                    frontier=list(priority_queue),
                    visited=list(visited_order),
                    distances=dict(distances),
                    relaxed_edges=[]
                ))
                break

            for neighbor_id, road in self.network.get_neighbors(current_node).items():
                if neighbor_id in visited or road.is_blocked:
                    continue

                edge_weight = self.network.get_weight(
                    current_node, neighbor_id,
                    vehicle_type=vehicle_type,
                    criterion=criterion
                )
                if math.isinf(edge_weight):
                    continue

                new_dist = current_dist + edge_weight
                if new_dist < distances.get(neighbor_id, float('inf')):
                    distances[neighbor_id] = new_dist
                    parents[neighbor_id] = current_node
                    heapq.heappush(priority_queue, (new_dist, neighbor_id))
                    relaxed.append((current_node, neighbor_id, new_dist))

            steps.append(AlgorithmStep(
                step_index=step_idx,
                current_node=current_node,
                current_cost=current_dist,
                frontier=list(priority_queue),
                visited=list(visited_order),
                distances=dict(distances),
                relaxed_edges=relaxed
            ))

        final_res = self.find_shortest_path(start_id, target_id, vehicle_type, criterion)
        return final_res, steps


class AStarRouter:
    """
    A* Search Algorithm with an Admissible & Consistent Heuristic.
    Cost Function: f(n) = g(n) + h(n)
      - g(n): Exact cost from start to node n.
      - h(n): Admissible Euclidean/Time heuristic from n to target.
    Time Complexity: O((V + E) * log V), with directional pruning significantly reducing explored nodes.
    Space Complexity: O(V)
    """
    def __init__(self, network: CityRoadNetwork):
        self.network = network

    def calculate_heuristic(
        self,
        node_id: str,
        target_id: str,
        criterion: str = "time"
    ) -> float:
        """
        Admissible heuristic function:
        - If criterion is 'distance': Euclidean distance in km (never overestimates real road distance).
        - If criterion is 'time': Euclidean distance / Max Highway Speed (e.g. 100 km/h) * 3600 seconds.
          Because actual road path >= straight line, and speed <= max speed, this is strictly admissible
          and consistent (monotonic), guaranteeing mathematical optimality.
        """
        u = self.network.nodes.get(node_id)
        v = self.network.nodes.get(target_id)
        if not u or not v:
            return 0.0

        euclidean_dist = u.distance_to(v)

        if criterion == "distance":
            return euclidean_dist

        # Maximum conceivable theoretical speed on city network (100 km/h)
        max_possible_speed_kmh = 100.0
        # Time in seconds under maximum possible speed across straight line
        return (euclidean_dist / max_possible_speed_kmh) * 3600.0

    def find_shortest_path(
        self,
        start_id: str,
        target_id: str,
        vehicle_type: str = "ambulance",
        criterion: str = "time"
    ) -> PathResult:
        """
        Calculates optimal shortest path from start_id to target_id using A* with Min-Heap.
        """
        start_time = time.perf_counter()

        if start_id not in self.network.nodes or target_id not in self.network.nodes:
            return PathResult(
                algorithm="A* Search (Heuristic)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=0,
                nodes_evaluated=0,
                heap_operations=0,
                execution_time_ms=0.0,
                memory_kb=0.0,
                sla_met=True,
                visited_nodes_order=[]
            )

        # Min-Heap stores tuples: (f_score, g_score, node_id)
        h_start = self.calculate_heuristic(start_id, target_id, criterion)
        priority_queue: List[Tuple[float, float, str]] = []
        heapq.heappush(priority_queue, (h_start, 0.0, start_id))
        heap_ops = 1

        # g_score table: HashMap[node_id -> actual_cost_from_start]
        g_scores: Dict[str, float] = {start_id: 0.0}
        
        # Parent table for reconstruction
        parents: Dict[str, Optional[str]] = {start_id: None}
        
        # Closed set (visited)
        visited: Set[str] = set()
        visited_order: List[str] = []

        nodes_explored = 0
        nodes_evaluated = 0

        while priority_queue:
            f_curr, g_curr, current_node = heapq.heappop(priority_queue)
            heap_ops += 1

            if current_node in visited:
                continue

            visited.add(current_node)
            visited_order.append(current_node)
            nodes_explored += 1

            # Early exit on goal
            if current_node == target_id:
                break

            for neighbor_id, road in self.network.get_neighbors(current_node).items():
                if neighbor_id in visited or road.is_blocked:
                    continue

                nodes_evaluated += 1
                edge_weight = self.network.get_weight(
                    current_node, neighbor_id,
                    vehicle_type=vehicle_type,
                    criterion=criterion
                )
                if math.isinf(edge_weight):
                    continue

                tentative_g = g_curr + edge_weight

                if tentative_g < g_scores.get(neighbor_id, float('inf')):
                    g_scores[neighbor_id] = tentative_g
                    parents[neighbor_id] = current_node
                    
                    h_val = self.calculate_heuristic(neighbor_id, target_id, criterion)
                    f_val = tentative_g + h_val
                    heapq.heappush(priority_queue, (f_val, tentative_g, neighbor_id))
                    heap_ops += 1

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        memory_kb = (
            sys.getsizeof(g_scores) +
            sys.getsizeof(parents) +
            sys.getsizeof(visited) +
            sys.getsizeof(priority_queue)
        ) / 1024.0

        if target_id not in g_scores or (target_id != start_id and parents.get(target_id) is None):
            return PathResult(
                algorithm="A* Search (Heuristic)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=nodes_explored,
                nodes_evaluated=nodes_evaluated,
                heap_operations=heap_ops,
                execution_time_ms=exec_time_ms,
                memory_kb=memory_kb,
                sla_met=(exec_time_ms < 200.0),
                visited_nodes_order=visited_order
            )

        # Path reconstruction
        path: List[str] = []
        curr: Optional[str] = target_id
        while curr is not None:
            path.append(curr)
            curr = parents.get(curr)
        path.reverse()

        total_dist_km = 0.0
        total_time_s = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self.network.get_edge(u, v)
            if edge:
                total_dist_km += edge.distance_km
                total_time_s += edge.calculate_travel_time_seconds(
                    vehicle_type=vehicle_type,
                    weather_factor=self.network.weather_factor * self.network.global_congestion_factor,
                    green_corridor_active=self.network.green_corridor_active
                )

        path_names = [self.network.nodes[nid].name for nid in path]

        return PathResult(
            algorithm="A* Search (Heuristic)",
            found=True,
            path=path,
            path_names=path_names,
            total_cost=g_scores[target_id],
            total_distance_km=total_dist_km,
            total_time_seconds=total_time_s,
            nodes_explored=nodes_explored,
            nodes_evaluated=nodes_evaluated,
            heap_operations=heap_ops,
            execution_time_ms=exec_time_ms,
            memory_kb=memory_kb,
            sla_met=(exec_time_ms < 200.0),
            visited_nodes_order=visited_order
        )

    def trace_search_steps(
        self,
        start_id: str,
        target_id: str,
        vehicle_type: str = "ambulance",
        criterion: str = "time",
        max_steps: int = 250
    ) -> Tuple[PathResult, List[AlgorithmStep]]:
        """
        Executes A* and captures step-by-step state frames for side-by-side animation.
        """
        h_start = self.calculate_heuristic(start_id, target_id, criterion)
        priority_queue: List[Tuple[float, float, str]] = []
        heapq.heappush(priority_queue, (h_start, 0.0, start_id))
        g_scores: Dict[str, float] = {start_id: 0.0}
        parents: Dict[str, Optional[str]] = {start_id: None}
        visited: Set[str] = set()
        visited_order: List[str] = []
        steps: List[AlgorithmStep] = []
        heuristics_map: Dict[str, float] = {start_id: h_start}
        step_idx = 0

        while priority_queue and step_idx < max_steps:
            f_curr, g_curr, current_node = heapq.heappop(priority_queue)

            if current_node in visited:
                continue

            visited.add(current_node)
            visited_order.append(current_node)
            step_idx += 1

            relaxed: List[Tuple[str, str, float]] = []

            if current_node == target_id:
                steps.append(AlgorithmStep(
                    step_index=step_idx,
                    current_node=current_node,
                    current_cost=g_curr,
                    frontier=[(p[0], p[2]) for p in priority_queue],
                    visited=list(visited_order),
                    distances=dict(g_scores),
                    relaxed_edges=[],
                    heuristic_values=dict(heuristics_map)
                ))
                break

            for neighbor_id, road in self.network.get_neighbors(current_node).items():
                if neighbor_id in visited or road.is_blocked:
                    continue

                edge_weight = self.network.get_weight(
                    current_node, neighbor_id,
                    vehicle_type=vehicle_type,
                    criterion=criterion
                )
                if math.isinf(edge_weight):
                    continue

                tentative_g = g_curr + edge_weight
                if tentative_g < g_scores.get(neighbor_id, float('inf')):
                    g_scores[neighbor_id] = tentative_g
                    parents[neighbor_id] = current_node

                    h_val = self.calculate_heuristic(neighbor_id, target_id, criterion)
                    heuristics_map[neighbor_id] = h_val
                    f_val = tentative_g + h_val
                    heapq.heappush(priority_queue, (f_val, tentative_g, neighbor_id))
                    relaxed.append((current_node, neighbor_id, tentative_g))

            steps.append(AlgorithmStep(
                step_index=step_idx,
                current_node=current_node,
                current_cost=g_curr,
                frontier=[(p[0], p[2]) for p in priority_queue],
                visited=list(visited_order),
                distances=dict(g_scores),
                relaxed_edges=relaxed,
                heuristic_values=dict(heuristics_map)
            ))

        final_res = self.find_shortest_path(start_id, target_id, vehicle_type, criterion)
        return final_res, steps


class MultiDepotDispatcher:
    """
    Solves many-to-one emergency dispatch queries.
    Given an incident location, searches all candidate emergency depots (e.g. fire stations or ambulances)
    and computes the fastest responding unit using A* or Dijkstra.
    """
    def __init__(self, network: CityRoadNetwork):
        self.network = network
        self.dijkstra = DijkstraRouter(network)
        self.astar = AStarRouter(network)

    def find_fastest_dispatch(
        self,
        depot_ids: List[str],
        incident_id: str,
        vehicle_type: str = "ambulance",
        algorithm_choice: str = "astar"
    ) -> Dict[str, Any]:
        """
        Evaluates all candidate depots and returns rankings + winning route.
        """
        router = self.astar if algorithm_choice == "astar" else self.dijkstra
        candidates_results = []

        total_dispatch_start = time.perf_counter()

        for depot_id in depot_ids:
            if depot_id not in self.network.nodes:
                continue
            res = router.find_shortest_path(depot_id, incident_id, vehicle_type=vehicle_type, criterion="time")
            if res.found:
                candidates_results.append({
                    "depot_id": depot_id,
                    "depot_name": self.network.nodes[depot_id].name,
                    "travel_time_seconds": res.total_time_seconds,
                    "travel_time_minutes": round(res.total_time_seconds / 60.0, 2),
                    "distance_km": res.total_distance_km,
                    "path": res.path,
                    "path_names": res.path_names,
                    "nodes_explored": res.nodes_explored,
                    "execution_time_ms": res.execution_time_ms
                })

        total_dispatch_ms = (time.perf_counter() - total_dispatch_start) * 1000.0

        # Sort by travel time ascending
        candidates_results.sort(key=lambda x: x["travel_time_seconds"])

        best_option = candidates_results[0] if candidates_results else None

        return {
            "incident_id": incident_id,
            "incident_name": self.network.nodes[incident_id].name if incident_id in self.network.nodes else incident_id,
            "total_candidates_evaluated": len(depot_ids),
            "total_dispatch_time_ms": round(total_dispatch_ms, 3),
            "sla_met": (total_dispatch_ms < 200.0),
            "best_unit": best_option,
            "all_candidates": candidates_results
        }


class FloydWarshallRouter:
    """
    Floyd-Warshall All-Pairs Shortest Path Algorithm (Dynamic Programming Matrix).
    Time Complexity: O(V^3)
    Space Complexity: O(V^2)
    Computes all-pairs shortest paths and maintains a predecessor matrix for O(L) path reconstruction.
    """
    def __init__(self, network: CityRoadNetwork):
        self.network = network
        self._node_list: List[str] = []
        self._node_to_idx: Dict[str, int] = {}
        self._dist_matrix: List[List[float]] = []
        self._next_matrix: List[List[Optional[int]]] = []
        self._is_computed = False
        self._compute_time_ms = 0.0

    def compute_all_pairs(
        self,
        vehicle_type: str = "ambulance",
        criterion: str = "time"
    ) -> float:
        """
        Runs the O(V^3) Floyd-Warshall dynamic programming algorithm to compute all-pairs shortest paths.
        """
        start_time = time.perf_counter()

        self._node_list = list(self.network.nodes.keys())
        n = len(self._node_list)
        self._node_to_idx = {nid: i for i, nid in enumerate(self._node_list)}

        # Initialize V x V distance and predecessor matrices
        self._dist_matrix = [[float('inf')] * n for _ in range(n)]
        self._next_matrix = [[None] * n for _ in range(n)]

        for i in range(n):
            self._dist_matrix[i][i] = 0.0
            self._next_matrix[i][i] = i

        # Populate direct edges
        for u_id, neighbors in self.network.adjacency.items():
            if u_id not in self._node_to_idx:
                continue
            u_idx = self._node_to_idx[u_id]
            for v_id, road in neighbors.items():
                if v_id not in self._node_to_idx or road.is_blocked:
                    continue
                v_idx = self._node_to_idx[v_id]
                weight = self.network.get_weight(u_id, v_id, vehicle_type=vehicle_type, criterion=criterion)
                if not math.isinf(weight):
                    self._dist_matrix[u_idx][v_idx] = weight
                    self._next_matrix[u_idx][v_idx] = v_idx

        # Floyd-Warshall Triple Nested DP Loop: D^(k)[i][j] = min(D^(k-1)[i][j], D^(k-1)[i][k] + D^(k-1)[k][j])
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if self._dist_matrix[i][k] + self._dist_matrix[k][j] < self._dist_matrix[i][j]:
                        self._dist_matrix[i][j] = self._dist_matrix[i][k] + self._dist_matrix[k][j]
                        self._next_matrix[i][j] = self._next_matrix[i][k]

        self._compute_time_ms = (time.perf_counter() - start_time) * 1000.0
        self._is_computed = True
        return self._compute_time_ms

    def find_shortest_path(
        self,
        start_id: str,
        target_id: str,
        vehicle_type: str = "ambulance",
        criterion: str = "time",
        recompute_if_needed: bool = True
    ) -> PathResult:
        """
        Queries precomputed Floyd-Warshall matrix or computes on-demand.
        """
        query_start = time.perf_counter()

        if not self._is_computed and recompute_if_needed:
            self.compute_all_pairs(vehicle_type, criterion)

        if start_id not in self._node_to_idx or target_id not in self._node_to_idx:
            return PathResult(
                algorithm="Floyd-Warshall (All-Pairs DP)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=len(self._node_list),
                nodes_evaluated=len(self._node_list) ** 3,
                heap_operations=0,
                execution_time_ms=self._compute_time_ms,
                memory_kb=(len(self._node_list) ** 2 * 16) / 1024.0,
                sla_met=(self._compute_time_ms < 200.0),
                visited_nodes_order=self._node_list
            )

        u_idx = self._node_to_idx[start_id]
        v_idx = self._node_to_idx[target_id]

        if math.isinf(self._dist_matrix[u_idx][v_idx]):
            return PathResult(
                algorithm="Floyd-Warshall (All-Pairs DP)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=len(self._node_list),
                nodes_evaluated=len(self._node_list) ** 3,
                heap_operations=0,
                execution_time_ms=self._compute_time_ms,
                memory_kb=(len(self._node_list) ** 2 * 16) / 1024.0,
                sla_met=(self._compute_time_ms < 200.0),
                visited_nodes_order=self._node_list
            )

        # Path reconstruction from next_node matrix
        path: List[str] = [start_id]
        curr = u_idx
        while curr != v_idx:
            curr = self._next_matrix[curr][v_idx]
            if curr is None:
                break
            path.append(self._node_list[curr])

        # Distance & Time metrics
        total_dist_km = 0.0
        total_time_s = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self.network.get_edge(u, v)
            if edge:
                total_dist_km += edge.distance_km
                total_time_s += edge.calculate_travel_time_seconds(
                    vehicle_type=vehicle_type,
                    weather_factor=self.network.weather_factor * self.network.global_congestion_factor,
                    green_corridor_active=self.network.green_corridor_active
                )

        path_names = [self.network.nodes[nid].name for nid in path]
        n_nodes = len(self._node_list)

        return PathResult(
            algorithm="Floyd-Warshall (All-Pairs DP)",
            found=True,
            path=path,
            path_names=path_names,
            total_cost=self._dist_matrix[u_idx][v_idx],
            total_distance_km=total_dist_km,
            total_time_seconds=total_time_s,
            nodes_explored=n_nodes,
            nodes_evaluated=n_nodes ** 3,
            heap_operations=0,
            execution_time_ms=self._compute_time_ms,
            memory_kb=(n_nodes ** 2 * 16) / 1024.0,
            sla_met=(self._compute_time_ms < 200.0),
            visited_nodes_order=self._node_list
        )


class BFSRouter:
    """
    Breadth-First Search (BFS) for Unweighted Shortest Path (Hop Count).
    Time Complexity: O(V + E)
    Space Complexity: O(V)
    Finds shortest path by fewest number of intersection hops (ignoring road distance & traffic).
    """
    def __init__(self, network: CityRoadNetwork):
        self.network = network

    def find_shortest_path(
        self,
        start_id: str,
        target_id: str,
        vehicle_type: str = "ambulance",
        criterion: str = "hops"
    ) -> PathResult:
        start_time = time.perf_counter()

        if start_id not in self.network.nodes or target_id not in self.network.nodes:
            return PathResult(
                algorithm="Breadth-First Search (BFS)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=0,
                nodes_evaluated=0,
                heap_operations=0,
                execution_time_ms=0.0,
                memory_kb=0.0,
                sla_met=True,
                visited_nodes_order=[]
            )

        queue = deque([start_id])
        visited: Set[str] = {start_id}
        visited_order: List[str] = [start_id]
        parents: Dict[str, Optional[str]] = {start_id: None}
        hops: Dict[str, int] = {start_id: 0}

        nodes_explored = 0
        nodes_evaluated = 0

        found = False
        while queue:
            curr = queue.popleft()
            nodes_explored += 1

            if curr == target_id:
                found = True
                break

            for neighbor_id, road in self.network.get_neighbors(curr).items():
                if road.is_blocked or neighbor_id in visited:
                    continue

                nodes_evaluated += 1
                visited.add(neighbor_id)
                visited_order.append(neighbor_id)
                parents[neighbor_id] = curr
                hops[neighbor_id] = hops[curr] + 1
                queue.append(neighbor_id)

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        if not found:
            return PathResult(
                algorithm="Breadth-First Search (BFS)",
                found=False,
                path=[],
                path_names=[],
                total_cost=float('inf'),
                total_distance_km=0.0,
                total_time_seconds=0.0,
                nodes_explored=nodes_explored,
                nodes_evaluated=nodes_evaluated,
                heap_operations=0,
                execution_time_ms=exec_time_ms,
                memory_kb=(sys.getsizeof(visited) + sys.getsizeof(parents) + sys.getsizeof(queue)) / 1024.0,
                sla_met=(exec_time_ms < 200.0),
                visited_nodes_order=visited_order
            )

        # Path reconstruction
        path = []
        curr_node = target_id
        while curr_node is not None:
            path.append(curr_node)
            curr_node = parents.get(curr_node)
        path.reverse()

        total_dist_km = 0.0
        total_time_s = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self.network.get_edge(u, v)
            if edge:
                total_dist_km += edge.distance_km
                total_time_s += edge.calculate_travel_time_seconds(
                    vehicle_type=vehicle_type,
                    weather_factor=self.network.weather_factor * self.network.global_congestion_factor,
                    green_corridor_active=self.network.green_corridor_active
                )

        path_names = [self.network.nodes[nid].name for nid in path]

        return PathResult(
            algorithm="Breadth-First Search (BFS)",
            found=True,
            path=path,
            path_names=path_names,
            total_cost=float(hops[target_id]),
            total_distance_km=total_dist_km,
            total_time_seconds=total_time_s,
            nodes_explored=nodes_explored,
            nodes_evaluated=nodes_evaluated,
            heap_operations=0,
            execution_time_ms=exec_time_ms,
            memory_kb=(sys.getsizeof(visited) + sys.getsizeof(parents) + sys.getsizeof(queue)) / 1024.0,
            sla_met=(exec_time_ms < 200.0),
            visited_nodes_order=visited_order
        )
