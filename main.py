import time
import requests
import csv
import sys
import threading

# ==========================================
# CLI LOADING ANIMATION (Multithreading)
# ==========================================
class Spinner:
    """
    A terminal animation class that runs in the background to indicate 
    active processing without freezing the main application thread.
    """
    def __init__(self, message="Evaluating"):
        """
        Initializes the Spinner animation.

        Args:
            message (str): The text to display alongside the spinning animation.
        """
        self.spinner = ['-', '\\', '|', '/']
        self.delay = 0.1
        self.busy = False
        self.message = message

    def spin(self):
        """
        The core animation loop. Iterates through the spinner characters 
        and constantly overwrites the terminal line to create motion.
        """
        while self.busy:
            for char in self.spinner:
                if not self.busy:
                    break
                # \r overwrites the current line in the terminal
                sys.stdout.write(f'\r{CYAN}[AI] {self.message}... {char}{RESET}')
                sys.stdout.flush()
                time.sleep(self.delay)
                
        # \033[K acts as an eraser to wipe the line clean when finished
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

    def start(self):
        """Starts the spinner animation in a daemon background thread."""
        self.busy = True
        threading.Thread(target=self.spin, daemon=True).start()

    def stop(self):
        """Stops the spinner animation and cleans up the terminal line."""
        self.busy = False
        time.sleep(self.delay)

# ==========================================
# CLI COLOR CODES (ANSI Escape Sequences)
# ==========================================
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

# ==========================================
# PORT COORDINATES (Latitude & Longitude)
# ==========================================
PORT_COORDINATES = {
    "Mumbai": {"lat": 18.94, "lon": 72.83}, "Singapore": {"lat": 1.29, "lon": 103.85},
    "Shanghai": {"lat": 31.23, "lon": 121.47}, "Tokyo": {"lat": 35.67, "lon": 139.65},
    "Dubai": {"lat": 25.20, "lon": 55.27}, "Aden": {"lat": 12.79, "lon": 44.98},
    "Suez": {"lat": 29.96, "lon": 32.55}, "Cape Town": {"lat": -33.92, "lon": 18.42},
    "Gibraltar": {"lat": 36.14, "lon": -5.35}, "Rotterdam": {"lat": 51.92, "lon": 4.48},
    "Hamburg": {"lat": 53.55, "lon": 9.99}, "New York": {"lat": 40.71, "lon": -74.00},
    "Los Angeles": {"lat": 34.05, "lon": -118.24}, "Panama Canal": {"lat": 9.14, "lon": -79.72},
    "Santos": {"lat": -23.96, "lon": -46.33}
}

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
def evaluate_full_path(path):
    """
    Fetches live weather via APIs and traffic via CSV.
    Calculates safety risk using our Machine Learning formulas.
    
    Args:
        path (list): A list of port names representing the maritime route.
        
    Returns:
        tuple: (final_score, avg_wave, avg_wind, traffic_density, used_fallback)
    """
    total_wind = 0
    total_wave = 0
    successful_wind_checks = 0
    successful_wave_checks = 0

    total_traffic = 0
    successful_traffic_checks = 0
    
    # --- A. FETCH LIVE WEATHER (Open-Meteo API) ---
    for port in path:
        pt = PORT_COORDINATES[port]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={pt['lat']}&longitude={pt['lon']}&current=wind_speed_10m"
        marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={pt['lat']}&longitude={pt['lon']}&current=wave_height"
        
        try:
            # Increased timeout to 3 seconds for slower school Wi-Fi
            wind_response = requests.get(weather_url, timeout=3)
            wave_response = requests.get(marine_url, timeout=3)
            
            if wind_response.status_code == 200:
                total_wind += wind_response.json()["current"]["wind_speed_10m"]
                successful_wind_checks += 1
            if wave_response.status_code == 200:
                total_wave += wave_response.json()["current"]["wave_height"]
                successful_wave_checks += 1
        except Exception:
            pass # Skip safely if there is no internet connection

    # --- B. FETCH LOCAL TRAFFIC (CSV Database) ---
    for i in range(len(path) - 1):
        leg_start = path[i]
        leg_end = path[i+1]
        try:
            with open("traffic_data.csv", mode="r") as file:
                reader = csv.reader(file)
                next(reader) 
                for row in reader:
                    if (row[0] == leg_start and row[1] == leg_end) or (row[0] == leg_end and row[1] == leg_start):
                        total_traffic += int(row[2])
                        successful_traffic_checks += 1
                        break
        except FileNotFoundError:
            pass 

    # --- C. CALCULATE AVERAGES ---
    # BUG FIX: Only trigger the fallback warning if EVERY SINGLE port failed.
    # If even one port succeeded, we use that live data!
    if successful_wind_checks > 0:
        used_fallback = False
        wind_speed = total_wind / successful_wind_checks
    else:
        used_fallback = True
        wind_speed = 15.0
        
    if successful_wave_checks > 0:
        wave_height = total_wave / successful_wave_checks
    else:
        wave_height = 2.0
        used_fallback = True
        
    if successful_traffic_checks > 0:
        traffic_density = total_traffic / successful_traffic_checks
    else:
        traffic_density = 20 

    # --- D. APPLY MACHINE LEARNING FORMULAS ---
    weather_risk = (wave_height * 0.5107) + (wind_speed * 0.024) + 0.0105
    
    # Clamp the risk between 0.0 and 5.0
    weather_risk = max(0.0, min(5.0, weather_risk)) 
        
    # Traffic Risk (Calculated via Orange3 Linear Regression)
    traffic_risk = (traffic_density * 0.0484) + 0.0407
    
    # Clamp the risk between 0.0 and 5.0
    traffic_risk = max(0.0, min(5.0, traffic_risk))
        
    # Final Hybrid Score (65% Weather, 35% Traffic)
    final_score = (weather_risk * 0.65) + (traffic_risk * 0.35)
    
    # NEW: Returns the 'used_fallback' flag as the 5th item
    return round(final_score, 2), round(wave_height, 1), round(wind_speed, 1), int(traffic_density), used_fallback

# ==========================================
# THE PATHFINDING ALGORITHM (DFS)
# ==========================================
def find_all_paths(graph, start, end, path=None):
    """
    Finds all possible routes between the start and end ports without looping.
    
    Args:
        graph (dict): The adjacency list representing the maritime network.
        start (str): The starting port for the route.
        end (str): The destination port for the route.
        path (list, optional): The current path history to prevent cycles.
        
    Returns:
        list: A list of all valid paths connecting the start and end ports.
    """
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
    """
    Calculates the total nautical miles of a given path.
    
    Args:
        path (list): A list of port names representing a valid route.
        
    Returns:
        int: The accumulated distance of the entire journey in Nautical Miles.
    """
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
    """Clears the terminal screen by printing empty lines."""
    print("\n" * 50)

def print_logo():
    """Prints the AquaPath AI ASCII text logo to the console with colors."""
    
    print(f"{CYAN}{BOLD}***************************************************")
    print(f"* *")
    print(f"* A Q U A P A T H   A I                          *")
    print(f"* ------------------------------------           *")
    print(f"* Optimizing Maritime Routes | Smart Seas        *")
    print(f"* *")
    print(f"***************************************************{RESET}")

def main():
    """
    The main execution function of the application.
    Handles user input formatting, computes shortest physical routes, runs
    safety evaluations via the ML engine, and outputs the optimal choice.
    """
    clear_screen()
    print_logo()
    
    ports_list = list(MARITIME_NETWORK.keys())
    print(f"{CYAN}Available Global Ports:{RESET}")
    for i in range(0, len(ports_list), 3):
        col1 = ports_list[i]
        col2 = ports_list[i+1] if i+1 < len(ports_list) else ''
        col3 = ports_list[i+2] if i+2 < len(ports_list) else ''
        print(f"  {col1:<15} {col2:<15} {col3:<15}")
    
    print("\n" + "="*50)
    
    # Get User Input
    try:
        while True:
            start_port = input("Enter Starting Port: ").strip().title()

            if start_port in ports_list:
                break
            else:
                print(f"\n{RED}[!] Error: Invalid port selected. Please check spelling.{RESET}")

        while True:
            end_port = input("Enter Destination Port: ").strip().title()
        
            if end_port in ports_list:
                break
            else:
                print(f"\n{RED}[!] Error: Invalid port selected. Please check spelling.{RESET}")
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}[!] Program shutdown initiated. Shutting down AquaPath AI safely...{RESET}")
        return

    print(f"\n{CYAN}[System] Analyzing historical routes...{RESET}")
    time.sleep(1)
    
    # Find paths
    possible_routes = find_all_paths(MARITIME_NETWORK, start_port, end_port)
    
    if not possible_routes:
        print(f"\n{RED}[!] No valid maritime route found between these ports.{RESET}")
        return
        
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
    print(GREEN +"\n" + "="*50)
    print(f" 🗺️  TOP 3 SHORTEST ROUTES DISCOVERED ")
    print("="*50 + RESET)
    
    # --- SHOW THE DISCOVERED ROUTES FIRST ---
    # show the top 3 shortest routes before evaluating them
    for idx, route_data in enumerate(top_shortest_routes):
        path = route_data["path"]
        distance = route_data["distance"]
        path_string = " -> ".join(path)
        print(f"Option {idx + 1}: {path_string} | Distance: {distance} NM")
        time.sleep(0.5)
    else:
        print("\n" + "="*50)

    for idx, route_data in enumerate(top_shortest_routes):
        path = route_data["path"]
        distance = route_data["distance"]
        path_string = " -> ".join(path)
        
        # Start the animated loading spinner
        spinner = Spinner(message=f"Evaluating Option {idx + 1}")
        spinner.start()
        
        try:
            # NEW: Catches the 5th variable (used_fallback)
            avg_score, avg_wave, avg_wind, avg_traffic, used_fallback = evaluate_full_path(path)
        finally:
            spinner.stop() # Spinner erases completely here!
        
        # Save the route data
        scored_routes.append({
            "path": path, 
            "score": avg_score, 
            "string": path_string,
            "distance": distance
        })
        
        # Print the results cleanly AFTER the spinner is gone
        print(f"{GREEN}✅ Option {idx + 1} Evaluated: {path_string}{RESET}")
        
        # Print the warning if the API failed
        if used_fallback:
            print(f"   {YELLOW}[!] WARNING: Unable to fetch live data. Using fallback weather values.{RESET}")
            
        print(f"   -> Avg Weather: Waves {avg_wave}m | Wind {avg_wind}km/h")
        print(f"   -> Avg Traffic: {avg_traffic} active vessels detected")
        print(f"   -> Warning Level: {avg_score}/5.00\n")
        time.sleep(0.5)

    # Select the best route
    best_route = min(scored_routes, key=lambda x: x['score'])
    
    print(GREEN + "\n" + "="*50)
    print("✅ OPTIMAL ROUTE SELECTED")
    print("="*50 + RESET)
    print(f"Path: {best_route['string']}")
    print(f"Average Warning Level: {best_route['score']} / 5.00")
    print("Safety Status: " + (f"{GREEN}OPTIMAL{RESET}" if best_route['score'] < 2.5 else f"{YELLOW}PROCEED WITH CAUTION{RESET}" if best_route['score'] < 4.0 else f"{RED}HIGH RISK - AVOID IF POSSIBLE{RESET}"))
    
    print(f"{CYAN}\n[ ROUTE MAP ]{RESET}")
    print(f" ( {best_route['path'][0]} )")
    for port in best_route['path'][1:]:
        print("    |")
        print("    V")
        print(f" [ {port} ]")
    print(f"Total Distance: {best_route['distance']} NM")
        
    print("\nSafe travels! Thank you for using AquaPath AI.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # This catches the Ctrl+C command and hides the ugly red error text
        print(f"\n\n{YELLOW}[!] Program shutdown initiated. Shutting down AquaPath AI safely...{RESET}")
        sys.exit(0)