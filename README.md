# Intelligent Food Delivery Agent

An offline AI course project that simulates a campus robot accepting cafeteria orders, classifying their priority, finding routes through a campus graph, and scheduling a safe multi-order delivery tour. It includes both a browser dashboard and the original Python terminal interface.

## Open the browser app on Mac

1. Extract the project ZIP and open the `intelligent_food_delivery_agent` folder in VS Code.
2. Choose **Terminal → New Terminal**.
3. Start the local app server:

   ```bash
   /usr/local/bin/python3 web_server.py
   ```

4. The app opens in your browser at `http://127.0.0.1:8000`. Keep the terminal open while using it. Press **Control + C** in the terminal to stop the server.

If your Python command is `python3`, you can also run `python3 web_server.py`. The browser app itself uses plain HTML, CSS, and JavaScript and has no third-party packages.

## Run the terminal version

In the same project folder, run:

```bash
/usr/local/bin/python3 agent.py
```

This opens the original text menu in the terminal.

## Features

- Customer order entry with cafeteria stock checks
- Food menu, sample prices, item weights, and perishability data
- Priority classification from urgency, deadline, and food sensitivity
- Campus locations and a weighted map stored in `campus_config.json`
- BFS and DFS graph traversal demonstrations
- A* least-time route search with a Manhattan-distance heuristic
- Greedy scheduling for multiple pending orders
- Battery and carrying-capacity checks, including a safe return to the cafeteria
- A simulated delivery tour and battery recharge option
- Browser dashboard with order forms, route search, map connections, and persistent local demo data

## Project files

- `index.html` contains the self-contained browser dashboard and its search and scheduling logic.
- `web_server.py` starts a local server and opens the dashboard in your browser.
- `agent.py` contains the Python agent, graph-search methods, scheduling logic, and terminal interface.
- `campus_config.json` contains the sample map, menu, robot limits, and travel times.
- `PROJECT_REPORT.md` is the written project report and four-member work plan.
- `PRESENTATION_OUTLINE.md` contains a ready-to-present slide sequence and speaking notes.

## AI methods

- **BFS** explores the campus graph level by level.
- **DFS** explores one branch of the graph before backtracking.
- **A*** chooses a least-time path using `f(n) = g(n) + h(n)`, where `g(n)` is travel time already used and `h(n)` is Manhattan distance to the destination.
- **Priority-based planning** ranks orders by a score and then considers deadline and travel time.
- **Resource constraints** prevent the planner from exceeding the robot's payload or leaving without enough battery to return.

## Sample data and assumptions

All campus locations, road times, prices, stock levels, food weights, and robot settings are sample values for demonstrating the algorithms. Edit `campus_config.json` to adapt the prototype to another campus. Road times are fixed and the map is static. The program simulates deliveries; it does not control a real robot, accept payments, use GPS, or connect to a live database.

## Suggested browser demonstration

1. Select **Load sample orders** to add the Library, Engineering Block, and Hostel examples.
2. Demonstrate BFS, DFS, and A* in the route and search section.
3. Select **Schedule delivery tour** and explain the order sequence, return path, payload, and battery calculation.
4. Add an order manually and show the priority and stock checks.

The browser app stores demo orders in that browser's local storage. Select **Reset demo data** to clear them.

## Assumptions

All campus locations, road times, menu prices, stock levels, item weights, and robot settings are sample values. Edit `campus_config.json` for the Python version. The browser version has its own matching sample data in `index.html`. Road times are fixed and the map is static. Both versions simulate deliveries; neither controls a real robot, uses GPS, accepts payments, or connects to a live database.

See `PROJECT_REPORT.md` for the algorithms, sample calculation, and group task allocation.
