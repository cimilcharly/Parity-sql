"""Topological dependency ordering engine."""

from collections import defaultdict, deque
from typing import Dict, List, Set
from parity.lineage.models import LineagePlan, SQLObject


def order_dependencies(objects: List[SQLObject]) -> LineagePlan:
    """
    Sorts SQL objects topologically so that base tables/views are converted
    and migrated before dependent downstream views and queries.
    """
    if not objects:
        return LineagePlan(ordered_objects=[])

    # Index objects by name (lowercased)
    obj_by_name: Dict[str, SQLObject] = {obj.name.lower(): obj for obj in objects}

    # Build dependency graph
    # in_degree counts how many known objects an object depends on
    in_degree: Dict[str, int] = defaultdict(int)
    graph: Dict[str, Set[str]] = defaultdict(set)

    for obj in objects:
        o_name = obj.name.lower()
        if o_name not in in_degree:
            in_degree[o_name] = 0

        for dep in obj.dependencies:
            dep_clean = dep.lower()
            if dep_clean in obj_by_name and dep_clean != o_name:
                # dep_clean must be processed BEFORE o_name
                graph[dep_clean].add(o_name)
                in_degree[o_name] += 1

    # Kahn's algorithm
    queue = deque([name for name, deg in in_degree.items() if deg == 0])
    ordered_names: List[str] = []

    while queue:
        current = queue.popleft()
        ordered_names.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycles
    has_cycles = len(ordered_names) < len(in_degree)
    cycle_nodes = []
    if has_cycles:
        cycle_nodes = [name for name, deg in in_degree.items() if deg > 0]
        # Append remaining nodes to order
        for node in in_degree:
            if node not in ordered_names:
                ordered_names.append(node)

    ordered_objects = [obj_by_name[name] for name in ordered_names if name in obj_by_name]
    avg_complexity = (
        sum(o.complexity_score for o in ordered_objects) / len(ordered_objects)
        if ordered_objects
        else 1.0
    )

    return LineagePlan(
        ordered_objects=ordered_objects,
        has_cycles=has_cycles,
        cycle_nodes=cycle_nodes,
        average_complexity=round(avg_complexity, 2),
    )
