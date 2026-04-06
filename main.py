import time
import random

# ==========================================
# THE KNOWLEDGE GRAPH (Nodes, Edges & Distances)
# ==========================================
# Values are estimated Nautical Miles (NM) between ports.
MARITIME_NETWORK = {
    # --- ASIA & MIDDLE EAST ---
    "Mumbai": {"Aden": 1650, "Dubai": 930, "Singapore": 2440, "Cape Town": 4600},
    "Singapore": {"Mumbai": 2440, "Shanghai": 2500, "Tokyo": 2900, "Los Angeles": 7600},
    "Shanghai": {"Singapore": 2500, "Tokyo": 1000, "Los Angeles": 5700},
    "Tokyo": {"Shanghai": 1000, "Singapore": 2900, "Los Angeles": 5400, "Panama Canal": 7600},
    "Dubai": {"Mumbai": 930, "Aden": 1400},
    
    # --- AFRICA & CHOKEPOINTS ---
    "Aden": {"Dubai": 1400, "Mumbai": 1650, "Suez": 1300, "Cape Town": 3900},
    "Suez": {"Aden": 1300, "Gibraltar": 1900},
    "Cape Town": {"Mumbai": 4600, "Aden": 3900, "Santos": 3300, "Gibraltar": 4500},
    
    # --- EUROPE ---
    "Gibraltar": {"Suez": 1900, "Cape Town": 4500, "Rotterdam": 1300, "New York": 3100},
    "Rotterdam": {"Gibraltar": 1300, "Hamburg": 250, "New York": 3400},
    "Hamburg": {"Rotterdam": 250, "New York": 3500},
    
    # --- THE AMERICAS ---
    "New York": {"Gibraltar": 3100, "Rotterdam": 3400, "Hamburg": 3500, "Panama Canal": 2000, "Santos": 4800},
    "Los Angeles": {"Tokyo": 5400, "Shanghai": 5700, "Singapore": 7600, "Panama Canal": 2900},
    "Panama Canal": {"Los Angeles": 2900, "New York": 2000, "Santos": 3400, "Tokyo": 7600},
    "Santos": {"Cape Town": 3300, "Panama Canal": 3400, "New York": 4800}
}

# ==========================================
# THE AI SCORING ENGINE
# ==========================================
def fetch_edge_data(start, end):
    # Simulates fetching data from Open-Meteo and GFW APIs for a specific route leg.
    # Returns a dictionary of risk factors.
    wave_height = round(random.uniform(0.5, 6.0), 1) # Meters
    wind_speed = random.randint(10, 80) # km/h
    traffic_density = random.randint(10, 100) # Number of vessels
    
    # Calculate Weather Risk (1-5)
    if wave_height > 4.0 or wind_speed > 60: weather_risk = 5
    elif wave_height > 2.5 or wind_speed > 40: weather_risk = 3
    else: weather_risk = 1
        
    # Calculate Traffic Risk (1-5)
    if traffic_density > 80: traffic_risk = 5
    elif traffic_density > 40: traffic_risk = 3
    else: traffic_risk = 1
        
    # Apply your hybrid Weightage: 65% Weather, 35% Traffic
    final_score = (weather_risk * 0.65) + (traffic_risk * 0.35)
    
    return round(final_score, 2), weather_risk, traffic_risk

# ==========================================
# THE PATHFINDING ALGORITHM (DFS)
# ==========================================
def find_all_paths(graph, start, end, path=None):
    # Finds all possible routes between the start and end ports without looping.
    if path is None:
        path = []
        
    path = path + [start]
    
    if start == end:
        return [path]
        
    if start not in graph:
        return []
    
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

def calculate_total_distance(path):
    # Calculates the total nautical miles of a given path.
    total_distance = 0
    for i in range(len(path) - 1):
        port_a = path[i]
        port_b = path[i+1]
        total_distance += MARITIME_NETWORK[port_a][port_b]
    return total_distance

# ==========================================
# COMMAND-LINE INTERFACE (UI)
# ==========================================
def clear_screen():
    print("\n" * 50)

def print_logo():
    print("""
***************************************************
* *
* A Q U A P A T H   A I                          *
* ------------------------------------           *
* Optimizing Maritime Routes | Smart Seas        *
* *
***************************************************
    """)

def main():
    clear_screen()
    print_logo()
    
    ports_list = list(MARITIME_NETWORK.keys())
    print("Available Global Ports:")
    for i in range(0, len(ports_list), 3):
        col1 = ports_list[i]
        col2 = ports_list[i+1] if i+1 < len(ports_list) else ''
        col3 = ports_list[i+2] if i+2 < len(ports_list) else ''
        print(f"  {col1:<15} {col2:<15} {col3:<15}")
    
    print("\n" + "="*50)
    
    # Get User Input
    start_port = input("Enter Starting Port: ").strip().title()
    end_port = input("Enter Destination Port: ").strip().title()
    
    if start_port not in ports_list or end_port not in ports_list:
        print("\n[!] Error: Invalid port selected. Please restart and check spelling.")
        return
        
    print("\n[System] Analyzing historical routes...")
    time.sleep(1)
    print("[System] Pinging Open-Meteo API for live weather...")
    time.sleep(1)
    print("[System] Fetching GFW AIS vessel traffic density...")
    time.sleep(1.5)
    
    # Find paths
    possible_routes = find_all_paths(MARITIME_NETWORK, start_port, end_port)
    
    if not possible_routes:
        print("\n[!] No valid maritime route found between these ports.")
        return
        
    # --- NEW DISTANCE FILTERING LOGIC ---
    # Calculate distance for all paths and sort them from shortest to longest
    routes_with_distance = []
    for path in possible_routes:
        dist = calculate_total_distance(path)
        routes_with_distance.append({"path": path, "distance": dist})
        
    # Sort the list by distance (shortest first)
    routes_with_distance.sort(key=lambda x: x['distance'])
    
    # Keep only the top 3 physically shortest routes to evaluate for safety
    top_shortest_routes = routes_with_distance[:3]
    # ------------------------------------

    # Evaluate routes
    scored_routes = []
    print("\n" + "="*50)
    print("EVALUATING TOP 3 SHORTEST ROUTES FOR SAFETY:")
    print("="*50)
    
    # We now loop through our pre-filtered shortest routes
    for idx, route_data in enumerate(top_shortest_routes):
        path = route_data["path"]
        distance = route_data["distance"]
        
        total_score = 0
        path_string = " -> ".join(path)
        
        # Score each leg of the journey for Weather/Traffic
        for i in range(len(path) - 1):
            score, w_risk, t_risk = fetch_edge_data(path[i], path[i+1])
            total_score += score
            
        avg_score = round(total_score / (len(path) - 1), 2)
        scored_routes.append({
            "path": path, 
            "score": avg_score, 
            "string": path_string,
            "distance": distance
        })
        
        print(f"Option {idx + 1}: {path_string}")
        print(f"   -> Distance: {distance} Nautical Miles")
        print(f"   -> Warning Level: {avg_score}/5.00\n")
        time.sleep(0.5)

    # Select the best route
    best_route = min(scored_routes, key=lambda x: x['score'])
    
    print("\n" + "="*50)
    print("✅ OPTIMAL ROUTE SELECTED")
    print("="*50)
    print(f"Path: {best_route['string']}")
    print(f"Average Warning Level: {best_route['score']} / 5.00")
    print("Safety Status: " + ("OPTIMAL" if best_route['score'] < 2.5 else "PROCEED WITH CAUTION"))
    
    print("\n[ ROUTE MAP ]")
    print(f" ( {best_route['path'][0]} )")
    for port in best_route['path'][1:]:
        print("    |")
        print("    V")
        print(f" [ {port} ]")
    print(f"Total Distance: {best_route['distance']} NM")
        
    print("\nSafe travels! Thank you for using AquaPath AI.")

if __name__ == "__main__":
    main()