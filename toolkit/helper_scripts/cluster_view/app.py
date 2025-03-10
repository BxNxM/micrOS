from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    # Provided nodes_info data
    nodes_info = {
        "node1": {"address": "192.168.1.1", "intercon": ["node2", "node4"], "network": "STA", "IRQ": ["irq1", "cron"], "app_modules": ["system"], "rssi": "GOOD"},
        "node2": {"address": "192.168.1.2", "intercon": [], "network": "STA", "IRQ": [], "app_modules": ["rgb", "cct"], "rssi": "GOOD"},
        "node3": {"address": "192.168.1.3", "intercon": [], "network": "STA", "IRQ": ["irq1", "irq3"], "app_modules": [], "rssi": "GOOD"},
        "node4": {"address": "192.168.1.4", "intercon": ["node1"], "network": "STA", "IRQ": ["timirq"], "app_modules": ["roboarm"], "rssi": "GOOD"}
    }
    
    nodes = []
    edges = []
    router_needed = False
    
    # Process nodes_info to create nodes and edges
    for node, info in nodes_info.items():
        # Create a node object with the node id and label, then update with all provided info
        node_entry = {"id": node, "label": node}
        node_entry.update(info)
        nodes.append(node_entry)
        
        # Create edges based on "intercon" list
        for target in info.get("intercon", []):
            edges.append({
                "from": node,
                "to": target
            })
        # For nodes with network "STA", add an edge to the router (green color)
        if info.get("network") == "STA":
            router_needed = True
            edges.append({
                "from": node,
                "to": "router",
                "color": "green"
            })
            
    # Add a router node if any STA nodes exist; style it with a distinct color.
    if router_needed:
        nodes.append({
            "id": "router",
            "label": "Router",
            "address": "N/A",
            "network": "Router",
            "color": {"background": "red", "border": "black", "highlight": {"background": "orange"}}
        })
    
    return render_template("index.html", nodes=nodes, edges=edges)

if __name__ == '__main__':
    app.run(debug=True)

