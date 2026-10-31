# Presentation Outline

Suggested 8-slide presentation for a four-member group. Replace the member labels with the group's names.

## Slide 1: Intelligent Food Delivery Agent

- AI course project
- Group member names and course details
- One-sentence goal: simulate a campus agent that schedules cafeteria deliveries

**Speaker:** Member 1

## Slide 2: Problem and Objectives

- Several students or departments may order at the same time.
- The agent must choose routes and delivery order.
- It must check deadlines, food priority, robot battery, and carrying capacity.

**Speaker:** Member 1

## Slide 3: Campus Map and Agent Information

- Show the locations and road connections from `campus_config.json`.
- Explain that locations are graph nodes and roads are weighted edges.
- Show the PEAS summary from the project report.

**Speaker:** Member 2

## Slide 4: BFS and DFS

- BFS explores neighboring locations in layers using a queue.
- DFS follows one branch using a stack before backtracking.
- Use the program's traversal option to show the visitation order.

**Speaker:** Member 2

## Slide 5: A* Route Planning

- Explain `f(n) = g(n) + h(n)`.
- `g(n)` is travel time so far; `h(n)` is Manhattan distance to the goal.
- Show one A* path and its estimated travel time.

**Speaker:** Member 3

## Slide 6: Order Priority and Robot Limits

- Priority score uses requested urgency, deadline, and perishable food.
- The carrying limit checks the total weight loaded for the tour.
- Battery checks include the remaining route back to the cafeteria.

**Speaker:** Member 3

## Slide 7: Browser Dashboard and Multi-order Demonstration

- Use the browser dashboard to enter orders for Library, Engineering Block, and Hostel.
- Run the scheduler and show the chosen order sequence.
- Explain the route time, estimated battery use, and any orders left pending.

**Speaker:** Member 4, with one short comment from each module owner

## Slide 8: Result, Limits, and Conclusion

- The prototype demonstrates an AI search and planning workflow.
- It uses sample static campus data and simulates delivery.
- Possible extensions: GUI, live location, dynamic obstacles, persistent data, and multiple robots.

**Speaker:** Member 4
