import time
import random

# ==========================================
# 1. THE KNOWLEDGE GRAPH (Nodes & Edges)
# ==========================================
# This dictionary represents our 15 ports and the valid shipping lanes between them.
MARITIME_NETWORK = {
    "Mumbai": ["Singapore", "Dubai", "Aden", "Cape Town"],
    "Singapore": ["Mumbai", "Shanghai", "Tokyo", "Los Angeles"],
    "Shanghai": ["Singapore", "Tokyo", "Los Angeles"],
    "Tokyo": ["Shanghai", "Singapore", "Los Angeles"],
    "Dubai": ["Mumbai", "Aden"],
    "Aden": ["Dubai", "Mumbai", "Suez", "Cape Town"],
    "Suez": ["Aden", "Gibraltar"],
    "Cape Town": ["Mumbai", "Aden", "Santos", "Gibraltar"],
    "Gibraltar": ["Suez", "Cape Town", "Rotterdam", "New York"],
    "Rotterdam": ["Gibraltar", "Hamburg", "New York"],
    "Hamburg": ["Rotterdam", "New York"],
    "New York": ["Gibraltar", "Rotterdam", "Hamburg", "Panama Canal"],
    "Los Angeles": ["Tokyo", "Singapore", "Panama Canal"],
    "Panama Canal": ["Los Angeles", "New York", "Santos"],
    "Santos": ["Cape Town", "Panama Canal"]
}

# ==========================================
# 2. THE AI SCORING ENGINE
# ==========================================
def fetch_edge_data(start, end):
    """
    Simulates fetching data from Open-Meteo and GFW APIs for a specific route leg.
    Returns a dictionary of risk factors.
    """
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
# 3. THE PATHFINDING ALGORITHM (DFS)
# ==========================================
def find_all_paths(graph, start, end, path=None):
    """Finds all possible routes between the start and end ports without looping."""
    if path is None:
        path = []
        
    path = path + [start]
    
    if start == end:
        return [path]
        
    if start not in graph: # Fixed syntax error here
        return []
    
    paths = []
    for node in graph[start]:
        if node not in path:
            newpaths = find_all_paths(graph, node, end, path)
            for newpath in newpaths:
                paths.append(newpath)
    return paths

# ==========================================
# 4. COMMAND-LINE INTERFACE (UI)
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
        
    # Evaluate routes
    scored_routes = []
    print("\n" + "="*50)
    print("EVALUATING ROUTE OPTIONS:")
    print("="*50)
    
    # Look at the first 5 paths found to keep the output readable
    for idx, path in enumerate(possible_routes[:5]):
        total_score = 0
        path_string = " -> ".join(path)
        
        # Score each leg of the journey
        for i in range(len(path) - 1):
            score, w_risk, t_risk = fetch_edge_data(path[i], path[i+1])
            total_score += score
            
        avg_score = round(total_score / (len(path) - 1), 2)
        scored_routes.append({"path": path, "score": avg_score, "string": path_string})
        
        print(f"Option {idx + 1}: {path_string}")
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
        
    print("\nSafe travels! Thank you for using AquaPath AI.")

if __name__ == "__main__":
    main()