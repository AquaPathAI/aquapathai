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
        self.spinner = ['-', '\\', '|', '/'] # The classic spinner characters
        self.delay = 0.1 # Delay between spinner updates (in seconds)
        self.busy = False # Flag to control the spinner loop
        self.message = message # Custom message to show next to the spinner

    def spin(self):
        """
        The core animation loop. Iterates through the spinner characters 
        and constantly overwrites the terminal line to create motion.
        """
        while self.busy:
            for char in self.spinner:
                if not self.busy:
                    # If the busy flag was turned off during the sleep, we want to exit immediately
                    break
                # \r overwrites the current line in the terminal
                sys.stdout.write(f'\r{CLI_COLORS["CYAN"]}[AI] {self.message}... {char}{CLI_COLORS["RESET"]}')
                sys.stdout.flush()
                time.sleep(self.delay)
                
        # \033[K acts as an eraser to wipe the line clean when finished
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

    def start(self):
        """Starts the spinner animation in a daemon background thread."""
        self.busy = True
        # A daemon thread runs in the background and automatically exits when the main program ends
        threading.Thread(target=self.spin, daemon=True).start()

    def stop(self):
        """Stops the spinner animation and cleans up the terminal line."""
        self.busy = False
        time.sleep(self.delay)

# ==========================================
# CLI COLOR CODES (ANSI Escape Sequences)
# ==========================================
CLI_COLORS = {
    "BOLD": "\033[1m",
    "CYAN": "\033[36m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "RED": "\033[31m",
    "RESET": "\033[0m"
}

# ==========================================
# PORT COORDINATES (Latitude & Longitude)
# ==========================================
PORT_COORDINATES = {
    # --- ASIA & MIDDLE EAST ---
    "Mumbai": {"lat": 18.94, "lon": 72.83}, "Singapore": {"lat": 1.29, "lon": 103.85},
    "Shanghai": {"lat": 31.23, "lon": 121.47}, "Tokyo": {"lat": 35.67, "lon": 139.65},
    "Dubai": {"lat": 25.20, "lon": 55.27}, 
    # --- AFRICA & CHOKEPOINTS ---
    "Aden": {"lat": 12.79, "lon": 44.98}, "Suez": {"lat": 29.96, "lon": 32.55}, 
    "Cape Town": {"lat": -33.92, "lon": 18.42},
    # --- EUROPE ---
    "Gibraltar": {"lat": 36.14, "lon": -5.35}, "Rotterdam": {"lat": 51.92, "lon": 4.48},
    "Hamburg": {"lat": 53.55, "lon": 9.99}, 
    # --- THE AMERICAS ---
    "New York": {"lat": 40.71, "lon": -74.00}, "Los Angeles": {"lat": 34.05, "lon": -118.24}, 
    "Panama Canal": {"lat": 9.14, "lon": -79.72}, "Santos": {"lat": -23.96, "lon": -46.33}
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
    # Initialize accumulators and counters for averaging
    total_wind = 0
    total_wave = 0
    successful_wind_checks = 0
    successful_wave_checks = 0

    # Traffic data is only available for legs between ports, so we count those separately
    total_traffic = 0
    successful_traffic_checks = 0
    
    # --- FETCH LIVE WEATHER (Open-Meteo API) ---
    for port in path:
        pt = PORT_COORDINATES[port]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={pt['lat']}&longitude={pt['lon']}&current=wind_speed_10m"
        marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={pt['lat']}&longitude={pt['lon']}&current=wave_height"
        
        try:
            # Timeout of 3 seconds to prevent hanging if the API is unreachable
            wind_response = requests.get(weather_url, timeout=3)
            wave_response = requests.get(marine_url, timeout=3)
            
            if wind_response.status_code == 200:
                # We only add to the total if we got a valid response, and we count how many successful checks we had for averaging later
                total_wind += wind_response.json()["current"]["wind_speed_10m"]
                successful_wind_checks += 1
            if wave_response.status_code == 200:
                # Same for wave height - only add if we got a valid response, and count successful checks
                total_wave += wave_response.json()["current"]["wave_height"]
                successful_wave_checks += 1
        except Exception:
            pass # Skip safely if there is no internet connection

    # --- FETCH LOCAL TRAFFIC (CSV Database) ---
    for i in range(len(path) - 1):
        # Each leg of the journey is between two ports, so we check the traffic data for each leg separately. 
        # This allows us to average traffic across the entire route.
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

    # --- CALCULATE AVERAGES ---
    # Only trigger the fallback warning if EVERY SINGLE port failed.
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

    # --- APPLY MACHINE LEARNING FORMULAS ---
    # Weather Risk (Calculated via Orange3 Linear Regression)
    weather_risk = (wave_height * 0.5107) + (wind_speed * 0.024) + 0.0105
    
    # Clamp the risk between 0.0 and 5.0
    weather_risk = max(0.0, min(5.0, weather_risk)) 
        
    # Traffic Risk (Calculated via Orange3 Linear Regression)
    traffic_risk = (traffic_density * 0.0484) + 0.0407
    
    # Clamp the risk between 0.0 and 5.0
    traffic_risk = max(0.0, min(5.0, traffic_risk))
        
    # Final Hybrid Score (65% Weather, 35% Traffic)
    # Uses custom weights to balance the importance of weather and traffic
    final_score = (weather_risk * 0.65) + (traffic_risk * 0.35)
    
    # Returns the final safety score, the average wave height, average wind speed, traffic density, and whether we had to use fallback values for weather
    return round(final_score, 2), round(wave_height, 1), round(wind_speed, 1), int(traffic_density), used_fallback


def find_best_route(scored_routes, tolerance=0.25):
    """
    Selects the best route based on the lowest safety score, with a tie-breaker for distance if scores are close.
    
    Args:
        scored_routes (list): A list of dictionaries containing route paths, scores, and distances.
        tolerance (float): The acceptable difference in safety scores to consider routes as tied.
    Returns:
        dict: The dictionary representing the best route with keys 'path', 'score', 'string', and 'distance'.
    """
    # We start by assuming the first route in our list is the best one
    best_route = scored_routes[0]

    # Loop through the rest of the evaluated routes to find the true optimal choice
    for route in scored_routes[1:]:
        # Condition A: If this route is strictly safer than our current best, select it
        if route['score'] < best_route['score']:
            # Tie-breaker Check: Is the old route's score within the tolerance of this new route?
            # And is the old route physically shorter? If so, keep the shorter one!
            if abs(best_route['score'] - route['score']) <= tolerance and best_route['distance'] < route['distance']:
                continue  # Skip updating; stick with the shorter route
            best_route = route
            
        # Condition B: If the safety scores are practically a tie (within the tolerance of each other)
        elif abs(route['score'] - best_route['score']) <= tolerance:
            # If the alternative route is physically shorter, pick it as the tie-breaker
            if route['distance'] < best_route['distance']:
                best_route = route

    return best_route

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

    # Initialize the path list on the first call 
    if path is None:
        path = []
    
    # Add the current port to the path history. This prevents us from visiting the same port twice and creating loops.
    path = path + [start]
    
    # Base Case: If the start and end ports are the same, we have found a valid path. Return it as a single-item list.
    if start == end:
        return [path]

    # If the starting port is not in the graph, it means there are no routes from this port. Return an empty list to indicate failure.        
    if start not in graph:
        return []
    
    # Recursive Case: Explore each neighboring port (connected via an edge) and continue searching for valid paths to the destination.
    paths = []
    for node in graph[start]:
        # Only continue down this path if we haven't already visited this port in our current path history. This ensures we don't create cycles.
        if node not in path:
            # For each valid neighboring port, we make a recursive call to find all paths from that neighbor to the destination. 
            # We also pass along the current path history so that it can be updated in deeper recursive calls.
            newpaths = find_all_paths(graph, node, end, path)
            # Add any new valid paths found from this neighbor to our overall list of paths. 
            # This builds up the complete list of valid routes from the start to the end port.
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
    # Initialize a distance accumulator to sum up the distances between each pair of ports in the path
    total_distance = 0
    # We loop through the path list, taking pairs of consecutive ports (port_a and port_b) and looking up the distance between them in our MARITIME_NETWORK graph.
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
    
    print(f"{CLI_COLORS['CYAN']}{CLI_COLORS['BOLD']}***************************************************")
    print(f"* *")
    print(f"* A Q U A P A T H   A I                          *")
    print(f"* ------------------------------------           *")
    print(f"* Optimizing Maritime Routes | Smart Seas        *")
    print(f"* *")
    print(f"***************************************************{CLI_COLORS['RESET']}")

def main():
    """
    The main execution function of the application.
    Handles user input formatting, computes shortest physical routes, runs
    safety evaluations via the ML engine, and outputs the optimal choice.
    """
    # Initial UI Setup
    clear_screen()
    print_logo()
    
    # Show Available Ports
    ports_list = list(MARITIME_NETWORK.keys())
    print(f"{CLI_COLORS['CYAN']}Available Global Ports:{CLI_COLORS['RESET']}")
    for i in range(0, len(ports_list), 3):
        col1 = ports_list[i]
        col2 = ports_list[i+1] if i+1 < len(ports_list) else ''
        col3 = ports_list[i+2] if i+2 < len(ports_list) else ''
        print(f"  {col1:<15} {col2:<15} {col3:<15}")
    
    # A visual separator to distinguish the port list from the user input section
    print("\n" + "="*50)
    
    # Get User Input
    try:
        # We use a loop to continuously prompt the user until they provide valid input for both the starting and destination ports.
        while True:
            start_port = input("Enter Starting Port: ").strip().title()

            # Check if the entered port is in our list of valid ports. 
            # If it is, we break out of the loop and move on to the next input. 
            # If not, we show an error message and prompt again.
            if start_port in ports_list:
                break
            else:
                print(f"\n{CLI_COLORS['RED']}[!] Error: Invalid port selected. Please check spelling.{CLI_COLORS['RESET']}")

        # We repeat the same process for the destination port, ensuring that the user selects valid ports from our predefined list.
        while True:
            end_port = input("Enter Destination Port: ").strip().title()
        
            if end_port in ports_list:
                break
            else:
                print(f"\n{CLI_COLORS['RED']}[!] Error: Invalid port selected. Please check spelling.{CLI_COLORS['RESET']}")
    except KeyboardInterrupt:
        # This allows the user to exit gracefully if they decide to cancel the input process (e.g., by pressing Ctrl+C).
        print(f"\n\n{CLI_COLORS['YELLOW']}[!] Program shutdown initiated. Shutting down AquaPath AI safely...{CLI_COLORS['RESET']}")
        return

    # Show a loading message while we compute the possible routes.
    print(f"\n{CLI_COLORS['CYAN']}[System] Analyzing historical routes...{CLI_COLORS['RESET']}")
    time.sleep(1)
    
    # Find paths
    possible_routes = find_all_paths(MARITIME_NETWORK, start_port, end_port)
    
    # If there are no valid routes found between the selected ports, we inform the user and exit the program gracefully.
    if not possible_routes:
        print(f"\n{CLI_COLORS['RED']}[!] No valid maritime route found between these ports.{CLI_COLORS['RESET']}")
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

    # Evaluate routes
    scored_routes = []
    print(CLI_COLORS['GREEN'] +"\n" + "="*50)
    print(f" 🗺️  TOP 3 SHORTEST ROUTES DISCOVERED ")
    print("="*50 + CLI_COLORS['RESET'])
    
    # Show the top 3 shortest routes before evaluating them
    for idx, route_data in enumerate(top_shortest_routes):
        path = route_data["path"]
        distance = route_data["distance"]
        path_string = " -> ".join(path)
        print(f"Option {idx + 1}: {path_string} | Distance: {distance} NM")
        time.sleep(0.5)
    
    # A visual separator to distinguish the route discovery phase from the safety evaluation phase
    print("\n" + "="*50)

    # Run the safety evaluation for each of the top 3 shortest routes, 
    # Showing an animated spinner while we fetch live data and compute the scores.
    for idx, route_data in enumerate(top_shortest_routes):
        path = route_data["path"]
        distance = route_data["distance"]
        path_string = " -> ".join(path)
        
        # Start the animated loading spinner
        spinner = Spinner(message=f"Evaluating Option {idx + 1}")
        spinner.start()
        
        try:
            # This function call will fetch live weather and traffic data, apply our ML formulas, and return the average safety score along with the raw data for waves, wind, and traffic.
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
        print(f"{CLI_COLORS['GREEN']}✅ Option {idx + 1} Evaluated: {path_string}{CLI_COLORS['RESET']}")
        
        # Print the warning if the API failed
        if used_fallback:
            print(f"   {CLI_COLORS['YELLOW']}[!] WARNING: Unable to fetch live data. Using fallback weather values.{CLI_COLORS['RESET']}")
        
        # Print the average conditions and the calculated warning level for this route, giving the user insight into why the score is what it is.
        print(f"   -> Avg Weather: Waves {avg_wave}m | Wind {avg_wind}km/h")
        print(f"   -> Avg Traffic: {avg_traffic} active vessels detected")
        print(f"   -> Warning Level: {avg_score}/5.00\n")
        time.sleep(0.5)

    # Find the best route based on the lowest safety score, 
    # with a tie-breaker for distance if scores are close
    best_route = find_best_route(scored_routes)
    
    # Final Output: Show the optimal route with its safety score, a color-coded safety status, and a visual map of the ports along the route.
    print(CLI_COLORS['GREEN'] + "\n" + "="*50)
    print("✅ OPTIMAL ROUTE SELECTED")
    print("="*50 + CLI_COLORS['RESET'])
    print(f"Path: {best_route['string']}")
    print(f"Average Warning Level: {best_route['score']} / 5.00")
    print("Safety Status: " + (f"{CLI_COLORS['GREEN']}OPTIMAL{CLI_COLORS['RESET']}" if best_route['score'] < 2.5 else f"{CLI_COLORS['YELLOW']}PROCEED WITH CAUTION{CLI_COLORS['RESET']}" if best_route['score'] < 4.0 else f"{CLI_COLORS['RED']}HIGH RISK - AVOID IF POSSIBLE{CLI_COLORS['RESET']}"))
    
    # A visual representation of the route map, showing the ports in a vertical flow with arrows indicating the direction of travel. 
    print(f"{CLI_COLORS['CYAN']}\n[ ROUTE MAP ]{CLI_COLORS['RESET']}")
    for port in best_route['path']:
        print(f" [ {port} ]")
        if port != best_route['path'][-1]: # Don't print an arrow after the last port
            print("    |")
            print("    V")
    print(f"Total Distance: {best_route['distance']} NM")
        
    print("\nSafe travels! Thank you for using AquaPath AI.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # This catches the Ctrl+C command and hides the ugly red error text
        print(f"\n\n{CLI_COLORS['YELLOW']}[!] Program shutdown initiated. Shutting down AquaPath AI safely...{CLI_COLORS['RESET']}")
        sys.exit(0)