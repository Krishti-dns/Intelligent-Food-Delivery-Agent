"""Campus cafeteria delivery agent: an offline AI course-project prototype."""

from __future__ import annotations

import heapq
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class FoodItem:
    item_id: str
    name: str
    price_inr: float
    weight_kg: float
    stock: int
    perishable: bool


@dataclass
class Order:
    order_id: str
    customer_name: str
    items: Dict[str, int]
    delivery_location: str
    requested_urgency: str
    deadline_minutes: int
    priority_score: int
    priority_level: str
    status: str = "Pending"

    def total_weight(self, menu: Dict[str, FoodItem]) -> float:
        return sum(menu[item_id].weight_kg * quantity for item_id, quantity in self.items.items())

    def total_price(self, menu: Dict[str, FoodItem]) -> float:
        return sum(menu[item_id].price_inr * quantity for item_id, quantity in self.items.items())


@dataclass
class ScheduledStop:
    order: Order
    path: List[str]
    travel_minutes: float
    estimated_arrival_minute: float


@dataclass
class TourResult:
    stops: List[ScheduledStop]
    return_path: List[str]
    return_minutes: float
    total_minutes: float
    battery_before: float
    battery_after: float
    remaining_orders: List[Tuple[Order, str]]


class CampusMap:
    """Undirected, weighted campus graph with BFS, DFS, and A* search."""

    def __init__(self, locations: dict, roads: list):
        self.locations = locations
        self.graph: Dict[str, Dict[str, float]] = {name: {} for name in locations}
        for road in roads:
            start = road["from"]
            end = road["to"]
            minutes = float(road["minutes"])
            if start not in self.graph or end not in self.graph:
                raise ValueError("Every road must connect two locations in the map.")
            if minutes <= 0:
                raise ValueError("Road travel times must be positive.")
            self.graph[start][end] = minutes
            self.graph[end][start] = minutes

    def _check_location(self, location: str) -> None:
        if location not in self.graph:
            raise ValueError("Unknown campus location: " + location)

    def bfs(self, start: str) -> List[str]:
        """Return locations in breadth-first visitation order."""
        self._check_location(start)
        queue = [start]
        visited = {start}
        order = []
        while queue:
            current = queue.pop(0)
            order.append(current)
            for neighbor in sorted(self.graph[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return order

    def dfs(self, start: str) -> List[str]:
        """Return locations in depth-first visitation order."""
        self._check_location(start)
        stack = [start]
        visited = set()
        order = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            order.append(current)
            # Reverse the push order so the alphabetically first neighbor is
            # visited first. The ordering is deterministic for classroom demos.
            for neighbor in sorted(self.graph[current], reverse=True):
                if neighbor not in visited:
                    stack.append(neighbor)
        return order

    def _heuristic(self, current: str, goal: str) -> float:
        """Manhattan distance in minutes for the sample grid campus map."""
        here = self.locations[current]
        target = self.locations[goal]
        return float(abs(here["x"] - target["x"]) + abs(here["y"] - target["y"]))

    def a_star(self, start: str, goal: str) -> Tuple[List[str], float]:
        """Return a least-time path and its cost using A*."""
        self._check_location(start)
        self._check_location(goal)
        frontier = [(self._heuristic(start, goal), 0.0, start)]
        came_from: Dict[str, Optional[str]] = {start: None}
        best_cost = {start: 0.0}

        while frontier:
            _, cost_so_far, current = heapq.heappop(frontier)
            if cost_so_far > best_cost.get(current, float("inf")):
                continue
            if current == goal:
                path = []
                node: Optional[str] = goal
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path, cost_so_far

            for neighbor, travel_time in self.graph[current].items():
                new_cost = cost_so_far + travel_time
                if new_cost < best_cost.get(neighbor, float("inf")):
                    best_cost[neighbor] = new_cost
                    came_from[neighbor] = current
                    estimate = new_cost + self._heuristic(neighbor, goal)
                    heapq.heappush(frontier, (estimate, new_cost, neighbor))

        return [], float("inf")


class FoodDeliveryAgent:
    """Coordinates orders, route search, tour scheduling, and robot limits."""

    def __init__(self, config: dict):
        self.cafeteria = config["cafeteria"]
        self.map = CampusMap(config["locations"], config["roads"])
        self.menu = {
            row["id"]: FoodItem(
                item_id=row["id"],
                name=row["name"],
                price_inr=float(row["price_inr"]),
                weight_kg=float(row["weight_kg"]),
                stock=int(row["stock"]),
                perishable=bool(row["perishable"]),
            )
            for row in config["menu"]
        }
        robot = config["robot"]
        self.battery_percent = float(robot["battery_percent"])
        self.battery_percent_per_minute = float(robot["battery_percent_per_minute"])
        self.carrying_capacity_kg = float(robot["carrying_capacity_kg"])
        self.orders: List[Order] = []
        self.order_number = 1

    @staticmethod
    def classify_priority(urgency: str, deadline_minutes: int, has_perishable_food: bool) -> Tuple[int, str]:
        """Combine requested urgency, deadline, and food sensitivity."""
        urgency_points = {"urgent": 3, "normal": 1, "low": 0}
        if urgency not in urgency_points:
            raise ValueError("Urgency must be urgent, normal, or low.")
        deadline_points = 2 if deadline_minutes <= 10 else 1 if deadline_minutes <= 20 else 0
        food_points = 1 if has_perishable_food else 0
        score = urgency_points[urgency] + deadline_points + food_points
        level = "High" if score >= 5 else "Medium" if score >= 3 else "Low"
        return score, level

    def place_order(
        self,
        customer_name: str,
        items: Dict[str, int],
        delivery_location: str,
        urgency: str,
        deadline_minutes: int,
    ) -> Order:
        if not customer_name.strip():
            raise ValueError("Customer name cannot be empty.")
        if delivery_location == self.cafeteria or delivery_location not in self.map.graph:
            raise ValueError("Choose a valid campus delivery location.")
        if not items:
            raise ValueError("An order must contain at least one food item.")
        if deadline_minutes <= 0:
            raise ValueError("Deadline must be a positive number of minutes.")
        for item_id, quantity in items.items():
            if item_id not in self.menu:
                raise ValueError("Unknown menu item: " + item_id)
            if quantity <= 0:
                raise ValueError("Each item quantity must be at least one.")
            if quantity > self.menu[item_id].stock:
                raise ValueError("Not enough stock for " + self.menu[item_id].name + ".")

        has_perishable = any(self.menu[item_id].perishable for item_id in items)
        score, level = self.classify_priority(urgency, deadline_minutes, has_perishable)
        order = Order(
            order_id="O" + str(self.order_number).zfill(3),
            customer_name=customer_name.strip(),
            items=dict(items),
            delivery_location=delivery_location,
            requested_urgency=urgency,
            deadline_minutes=deadline_minutes,
            priority_score=score,
            priority_level=level,
        )
        for item_id, quantity in items.items():
            self.menu[item_id].stock -= quantity
        self.order_number += 1
        self.orders.append(order)
        return order

    def pending_orders(self) -> List[Order]:
        return [order for order in self.orders if order.status == "Pending"]

    def plan_and_simulate_tour(self) -> TourResult:
        """Greedily schedule safe pending deliveries, then simulate the tour."""
        battery_before = self.battery_percent
        available_orders = self.pending_orders()
        current = self.cafeteria
        elapsed = 0.0
        used_minutes = 0.0
        loaded_weight = 0.0
        stops: List[ScheduledStop] = []

        while available_orders:
            choices = []
            for order in available_orders:
                order_weight = order.total_weight(self.menu)
                if order_weight > self.carrying_capacity_kg:
                    continue
                if loaded_weight + order_weight > self.carrying_capacity_kg:
                    continue
                outward_path, outward_minutes = self.map.a_star(current, order.delivery_location)
                return_path, return_minutes = self.map.a_star(order.delivery_location, self.cafeteria)
                if not outward_path or not return_path:
                    continue
                complete_tour_minutes = used_minutes + outward_minutes + return_minutes
                energy_needed = complete_tour_minutes * self.battery_percent_per_minute
                if energy_needed > battery_before + 1e-9:
                    continue
                eta = elapsed + outward_minutes
                late_minutes = max(0.0, eta - order.deadline_minutes)
                # Priority dominates the choice; the planner then favors an
                # earlier deadline and a short next leg.
                rank = (
                    order.priority_score * 100 - late_minutes * 5 - outward_minutes,
                    -order.deadline_minutes,
                    -outward_minutes,
                    order.order_id,
                )
                choices.append((rank, order, outward_path, outward_minutes, eta))

            if not choices:
                break
            choices.sort(key=lambda item: item[0], reverse=True)
            _, chosen, path, travel_minutes, eta = choices[0]
            stops.append(ScheduledStop(chosen, path, travel_minutes, eta))
            available_orders.remove(chosen)
            loaded_weight += chosen.total_weight(self.menu)
            current = chosen.delivery_location
            elapsed += travel_minutes
            used_minutes += travel_minutes

        if not stops:
            remaining = []
            for order in available_orders:
                if order.total_weight(self.menu) > self.carrying_capacity_kg:
                    reason = "order is heavier than the robot's full carrying capacity"
                elif order.total_weight(self.menu) > self.carrying_capacity_kg - loaded_weight:
                    reason = "payload limit for this tour"
                else:
                    reason = "battery reserve is too low for a safe round trip"
                remaining.append((order, reason))
            return TourResult([], [], 0.0, 0.0, battery_before, battery_before, remaining)

        return_path, return_minutes = self.map.a_star(current, self.cafeteria)
        total_minutes = used_minutes + return_minutes
        energy_used = total_minutes * self.battery_percent_per_minute
        self.battery_percent = max(0.0, battery_before - energy_used)
        for stop in stops:
            stop.order.status = "Delivered (simulated)"

        remaining = []
        for order in available_orders:
            order_weight = order.total_weight(self.menu)
            if order_weight > self.carrying_capacity_kg:
                reason = "order is heavier than the robot's full carrying capacity"
            elif order_weight + loaded_weight > self.carrying_capacity_kg:
                reason = "payload limit for this tour"
            else:
                reason = "battery reserve is too low for a safe round trip"
            remaining.append((order, reason))
        return TourResult(stops, return_path, return_minutes, total_minutes, battery_before, self.battery_percent, remaining)

    def recharge(self) -> None:
        self.battery_percent = 100.0


def load_config() -> dict:
    config_path = Path(__file__).with_name("campus_config.json")
    with config_path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


def print_menu(agent: FoodDeliveryAgent) -> None:
    print("\nCAMPUS CAFETERIA MENU")
    print("ID         FOOD                         PRICE     WEIGHT     STOCK")
    for item in agent.menu.values():
        print(
            "{:<10} {:<28} Rs {:<5.0f}   {:<7.2f} kg {:>3}".format(
                item.item_id, item.name, item.price_inr, item.weight_kg, item.stock
            )
        )


def print_locations(agent: FoodDeliveryAgent) -> None:
    print("\nCAMPUS LOCATIONS")
    for name in agent.map.locations:
        marker = " (cafeteria)" if name == agent.cafeteria else ""
        print("- " + name + marker)
    print("\nCONNECTED PATHS AND SAMPLE TRAVEL TIME")
    printed = set()
    for start, neighbors in agent.map.graph.items():
        for end, minutes in neighbors.items():
            edge = tuple(sorted((start, end)))
            if edge not in printed:
                print("- {} <-> {} : {} min".format(edge[0], edge[1], int(minutes)))
                printed.add(edge)


def print_orders(agent: FoodDeliveryAgent) -> None:
    if not agent.orders:
        print("No orders have been entered.")
        return
    print("\nORDERS")
    for order in agent.orders:
        item_text = ", ".join(
            "{} x{}".format(agent.menu[item_id].name, quantity)
            for item_id, quantity in order.items.items()
        )
        print(
            "{} | {} | {} | {} | {} priority (score {}) | due in {} min | {:.2f} kg | Rs {:.0f} | {}".format(
                order.order_id,
                order.customer_name,
                order.delivery_location,
                item_text,
                order.priority_level,
                order.priority_score,
                order.deadline_minutes,
                order.total_weight(agent.menu),
                order.total_price(agent.menu),
                order.status,
            )
        )


def ask_integer(prompt: str, minimum: int = 0) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
            if value < minimum:
                print("Enter a number greater than or equal to {}.".format(minimum))
                continue
            return value
        except ValueError:
            print("Enter a whole number.")


def choose_location(agent: FoodDeliveryAgent, prompt: str, include_cafeteria: bool) -> str:
    names = [name for name in agent.map.locations if include_cafeteria or name != agent.cafeteria]
    for index, name in enumerate(names, start=1):
        print("{}. {}".format(index, name))
    while True:
        choice = ask_integer(prompt, 1)
        if choice <= len(names):
            return names[choice - 1]
        print("Choose a listed location number.")


def add_order_flow(agent: FoodDeliveryAgent) -> None:
    print_menu(agent)
    customer = input("Customer name: ").strip()
    destination = choose_location(agent, "Delivery location number: ", include_cafeteria=False)
    items: Dict[str, int] = {}
    for item in agent.menu.values():
        quantity = ask_integer("Quantity of {} (0 to skip): ".format(item.name), 0)
        if quantity > 0:
            items[item.item_id] = quantity
    print("Urgency: 1 = urgent, 2 = normal, 3 = low")
    urgency_choice = ask_integer("Choose urgency: ", 1)
    urgency_names = {1: "urgent", 2: "normal", 3: "low"}
    if urgency_choice not in urgency_names:
        print("Urgency must be 1, 2, or 3. Order was not placed.")
        return
    deadline = ask_integer("Delivery deadline in minutes: ", 1)
    try:
        order = agent.place_order(customer, items, destination, urgency_names[urgency_choice], deadline)
    except ValueError as error:
        print("Order not placed: {}".format(error))
        return
    print(
        "Placed {} for {}. Priority: {} (score {}). Total: Rs {:.0f}, {:.2f} kg.".format(
            order.order_id,
            order.customer_name,
            order.priority_level,
            order.priority_score,
            order.total_price(agent.menu),
            order.total_weight(agent.menu),
        )
    )


def search_demo(agent: FoodDeliveryAgent) -> None:
    start = choose_location(agent, "Start location number: ", include_cafeteria=True)
    print("BFS visitation order: " + " -> ".join(agent.map.bfs(start)))
    print("DFS visitation order: " + " -> ".join(agent.map.dfs(start)))
    print("BFS and DFS show graph traversal. They do not minimize the weighted travel time.")


def route_demo(agent: FoodDeliveryAgent) -> None:
    start = choose_location(agent, "Start location number: ", include_cafeteria=True)
    goal = choose_location(agent, "Destination number: ", include_cafeteria=True)
    path, minutes = agent.map.a_star(start, goal)
    if path:
        print("A* least-time route: " + " -> ".join(path))
        print("Estimated travel time: {} minutes".format(int(minutes)))
    else:
        print("No route connects those locations.")


def run_tour_flow(agent: FoodDeliveryAgent) -> None:
    if not agent.pending_orders():
        print("There are no pending orders. Add orders first.")
        return
    if agent.battery_percent <= 0:
        print("Battery is empty. Recharge the robot at the cafeteria first.")
        return
    print("Planning a delivery tour from {}...".format(agent.cafeteria))
    result = agent.plan_and_simulate_tour()
    if not result.stops:
        print("No safe delivery tour fits the current battery and carrying limits.")
    else:
        print("\nSIMULATED TOUR")
        for index, stop in enumerate(result.stops, start=1):
            print(
                "{}. {} for {}: {} | leg {} min | ETA {} min | {} priority".format(
                    index,
                    stop.order.order_id,
                    stop.order.customer_name,
                    " -> ".join(stop.path),
                    int(stop.travel_minutes),
                    int(stop.estimated_arrival_minute),
                    stop.order.priority_level,
                )
            )
        print("Return to cafeteria: " + " -> ".join(result.return_path))
        print("Tour time: {} min".format(int(result.total_minutes)))
        print(
            "Battery: {:.1f}% before, {:.1f}% after ({}% per travel minute).".format(
                result.battery_before,
                result.battery_after,
                agent.battery_percent_per_minute,
            )
        )
        print("Delivered statuses are simulation results; no physical robot is controlled.")
    if result.remaining_orders:
        print("\nOrders left pending:")
        for order, reason in result.remaining_orders:
            print("- {} for {}: {}".format(order.order_id, order.customer_name, reason))


def show_status(agent: FoodDeliveryAgent) -> None:
    print("\nAGENT STATUS")
    print("Current location after each simulated tour: {}".format(agent.cafeteria))
    print("Battery: {:.1f}%".format(agent.battery_percent))
    print("Maximum carrying capacity: {:.2f} kg".format(agent.carrying_capacity_kg))
    print("Pending orders: {}".format(len(agent.pending_orders())))
    print_orders(agent)


def main() -> None:
    try:
        agent = FoodDeliveryAgent(load_config())
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        print("Could not load campus_config.json: {}".format(error))
        return

    print("Intelligent Food Delivery Agent")
    print("AI course project | campus delivery simulation")
    while True:
        print(
            "\n1. Add customer order\n"
            "2. Show food menu and stock\n"
            "3. Show campus map and locations\n"
            "4. Demonstrate BFS and DFS\n"
            "5. Find a least-time route with A*\n"
            "6. Schedule and simulate deliveries\n"
            "7. Show order and robot status\n"
            "8. Recharge at cafeteria\n"
            "0. Exit"
        )
        choice = input("Select an option: ").strip()
        if choice == "1":
            add_order_flow(agent)
        elif choice == "2":
            print_menu(agent)
        elif choice == "3":
            print_locations(agent)
        elif choice == "4":
            search_demo(agent)
        elif choice == "5":
            route_demo(agent)
        elif choice == "6":
            run_tour_flow(agent)
        elif choice == "7":
            show_status(agent)
        elif choice == "8":
            agent.recharge()
            print("Robot recharged to 100% at the cafeteria.")
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Choose one of the listed options.")


if __name__ == "__main__":
    main()
