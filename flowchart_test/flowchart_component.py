import gradio as gr
import json
import requests
from bs4 import BeautifulSoup
import re


class FlowchartCreator:
    """
    Flowchart Creator using Gradio's built-in components.
    """
    
    def __init__(self):
        self.value = {"nodes": [], "edges": []}
    
    def create_interface(self):
        """Create the flowchart interface using built-in Gradio components"""
        with gr.Column() as interface:
            gr.Markdown("### Interactive Flowchart Canvas")
            
            # Add hidden components to track selection and editing state
            selected_element = gr.Textbox(value="", visible=False, elem_id="selected_element")
            edit_mode = gr.Checkbox(value=False, visible=False, elem_id="edit_mode")
            canvas_action = gr.Textbox(value="", visible=False, elem_id="canvas_action")
            
            # Visual canvas using HTML with enhanced interactivity
            flowchart_html = gr.HTML(
                value=self.render_interactive_flowchart(self.get_example_flowchart()),
                label="Interactive Flowchart Canvas",
                elem_id="flowchart_canvas"
            )
            
            # Quick edit panel that appears when something is selected
            with gr.Row(visible=False) as edit_panel:
                quick_edit_text = gr.Textbox(
                    label="Quick Edit",
                    placeholder="Edit selected element...",
                    scale=3
                )
                apply_edit_btn = gr.Button("Apply", scale=1, variant="primary")
                cancel_edit_btn = gr.Button("Cancel", scale=1)
            
            # JSON editor for manual editing
            flowchart_json = gr.JSON(
                value=self.get_example_flowchart(),
                label="Flowchart Data (JSON)"
            )
            
            with gr.Row():
                add_node_btn = gr.Button("➕ Add Node", size="sm")
                delete_selected_btn = gr.Button("🗑️ Delete Selected", size="sm", variant="stop")
                refresh_btn = gr.Button("🔄 Refresh Visualization", size="sm")
                export_btn = gr.Button("📤 Export to Mermaid", size="sm")
                clear_btn = gr.Button("🗑️ Clear All", size="sm")
            
            export_output = gr.Textbox(
                label="Mermaid Export",
                lines=5,
                visible=False
            )
            
            # Status display
            status_text = gr.Textbox(
                label="Status",
                value="Click on nodes or edges to select and edit them",
                interactive=False
            )
            
            # Connect the functionality
            
            # Handle canvas interactions
            canvas_action.change(
                self.handle_canvas_action,
                inputs=[canvas_action, flowchart_json, selected_element],
                outputs=[flowchart_json, selected_element, edit_panel, quick_edit_text, status_text]
            ).then(
                self.update_interactive_visualization,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_html]
            )
            
            # Quick edit functionality
            apply_edit_btn.click(
                self.apply_quick_edit,
                inputs=[flowchart_json, selected_element, quick_edit_text],
                outputs=[flowchart_json, status_text]
            ).then(
                lambda: (gr.update(visible=False), ""),
                outputs=[edit_panel, quick_edit_text]
            ).then(
                self.update_interactive_visualization,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_html]
            )
            
            cancel_edit_btn.click(
                lambda: (gr.update(visible=False), "", ""),
                outputs=[edit_panel, quick_edit_text, selected_element]
            ).then(
                self.update_interactive_visualization,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_html]
            )
            
            # Add node functionality
            add_node_btn.click(
                self.add_new_node,
                inputs=[flowchart_json],
                outputs=[flowchart_json, status_text]
            ).then(
                self.update_interactive_visualization,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_html]
            )
            
            # Delete selected functionality
            delete_selected_btn.click(
                self.delete_selected_element,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_json, selected_element, status_text]
            ).then(
                lambda: gr.update(visible=False),
                outputs=[edit_panel]
            ).then(
                self.update_interactive_visualization,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_html]
            )
            
            refresh_btn.click(
                self.update_interactive_visualization,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_html]
            )
            
            export_btn.click(
                self.export_to_mermaid,
                inputs=[flowchart_json],
                outputs=[export_output]
            ).then(
                lambda: gr.update(visible=True),
                outputs=[export_output]
            )
            
            clear_btn.click(
                lambda: (self.get_empty_flowchart(), "", "Canvas cleared"),
                outputs=[flowchart_json, selected_element, status_text]
            ).then(
                lambda: gr.update(visible=False),
                outputs=[edit_panel]
            ).then(
                self.update_interactive_visualization,
                inputs=[flowchart_json, selected_element],
                outputs=[flowchart_html]
            )
        
        return interface, flowchart_json, flowchart_html
    
    def get_example_flowchart(self):
        """Return example flowchart data"""
        return {
            "nodes": [
                {
                    "id": "1",
                    "type": "start",
                    "position": {"x": 150, "y": 50},
                    "data": {"label": "Start"}
                },
                {
                    "id": "2",
                    "type": "process",
                    "position": {"x": 150, "y": 150},
                    "data": {"label": "Process Step"}
                },
                {
                    "id": "3",
                    "type": "decision",
                    "position": {"x": 150, "y": 250},
                    "data": {"label": "Decision?"}
                },
                {
                    "id": "4",
                    "type": "end",
                    "position": {"x": 150, "y": 350},
                    "data": {"label": "End"}
                }
            ],
            "edges": [
                {
                    "id": "e1-2",
                    "source": "1",
                    "target": "2",
                    "label": ""
                },
                {
                    "id": "e2-3",
                    "source": "2",
                    "target": "3",
                    "label": ""
                },
                {
                    "id": "e3-4",
                    "source": "3",
                    "target": "4",
                    "label": "Yes"
                }
            ]
        }
    
    def get_empty_flowchart(self):
        """Return empty flowchart"""
        return {"nodes": [], "edges": []}
    
    def update_interactive_visualization(self, flowchart_data, selected_element=""):
        """Update the interactive visualization"""
        return self.render_interactive_flowchart(flowchart_data, selected_element)
    
    def render_interactive_flowchart(self, flowchart_data, selected_element=""):
        """Render interactive flowchart with click handlers and drag support"""
        if not flowchart_data or not isinstance(flowchart_data, dict):
            return "<div>No flowchart data available</div>"
        
        nodes = flowchart_data.get("nodes", [])
        edges = flowchart_data.get("edges", [])
        
        # Calculate SVG dimensions
        max_x = max([node.get("position", {}).get("x", 0) for node in nodes] + [400])
        max_y = max([node.get("position", {}).get("y", 0) for node in nodes] + [500])
        
        svg_width = max_x + 250
        svg_height = max_y + 150
        
        # Start building HTML
        html = f"""
        <div style="border: 2px solid #ddd; border-radius: 8px; padding: 15px; background: #f9f9f9;">
            <div style="margin-bottom: 10px; font-size: 14px; color: #666;">
                💡 Click nodes/edges to select • Drag nodes to move • Quick edit when selected
            </div>
            <div style="position: relative;">
                <svg width="{svg_width}" height="{svg_height}" 
                     style="background: white; border-radius: 4px; cursor: default;"
                     id="flowchart-svg">
                    
                    <defs>
                        <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                                refX="10" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                        </marker>
                        <filter id="selected-glow">
                            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                            <feMerge>
                                <feMergeNode in="coloredBlur"/>
                                <feMergeNode in="SourceGraphic"/>
                            </feMerge>
                        </filter>
                    </defs>
        """
        
        # Draw edges with click handlers
        for edge in edges:
            source_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            target_node = next((n for n in nodes if n["id"] == edge["target"]), None)
            
            if source_node and target_node:
                x1 = source_node["position"]["x"] + 75
                y1 = source_node["position"]["y"] + 30
                x2 = target_node["position"]["x"] + 75
                y2 = target_node["position"]["y"] + 10
                
                is_selected = selected_element == f"edge:{edge['id']}"
                edge_style = "stroke: #0066cc; stroke-width: 3;" if is_selected else "stroke: #666; stroke-width: 2;"
                
                html += f"""
                    <g class="edge" data-edge-id="{edge['id']}" style="cursor: pointer;">
                        <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                              style="{edge_style}" marker-end="url(#arrowhead)"
                              onclick="window.fcSelectElement('{edge['id']}', 'edge')" />
                """
                
                if edge.get("label"):
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2 - 8
                    html += f"""
                        <rect x="{mid_x - len(edge['label']) * 3}" y="{mid_y - 10}" 
                              width="{len(edge['label']) * 6}" height="16" 
                              fill="white" stroke="#ddd" rx="3" 
                              onclick="window.fcSelectElement('{edge['id']}', 'edge')" />
                        <text x="{mid_x}" y="{mid_y}" text-anchor="middle" 
                              fill="#333" font-size="12" font-family="Arial"
                              style="pointer-events: none;">
                            {edge['label']}
                        </text>
                    """
                
                html += "</g>"
        
        # Draw nodes with enhanced interactivity
        for node in nodes:
            x = node["position"]["x"]
            y = node["position"]["y"]
            label = node["data"]["label"]
            node_type = node.get("type", "process")
            node_id = node["id"]
            
            is_selected = selected_element == f"node:{node_id}"
            glow_filter = 'filter="url(#selected-glow)"' if is_selected else ""
            
            html += f"""
            <g class="node" data-node-id="{node_id}" transform="translate({x},{y})"
               style="cursor: move;"
               onmousedown="window.fcStartDrag(event, '{node_id}')"
               onclick="window.fcSelectElement('{node_id}', 'node')">
            """
            
            # Node shapes with selection highlighting
            if node_type in ("start", "end"):
                fill_color = "#b3e5fc" if is_selected else "#e1f5fe"
                stroke_color = "#0288d1" if is_selected else "#01579b"
                html += f"""
                    <rect x="0" y="0" width="150" height="40" rx="20" ry="20"
                          fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" {glow_filter} />
                """
            elif node_type == "decision":
                fill_color = "#ffcc80" if is_selected else "#fff3e0"
                stroke_color = "#f57c00" if is_selected else "#e65100"
                cx, cy = 75, 20
                html += f"""
                    <polygon points="{cx},0 150,{cy} {cx},40 0,{cy}"
                             fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" {glow_filter} />
                """
            else:
                fill_color = "#e1bee7" if is_selected else "#f3e5f5"
                stroke_color = "#7b1fa2" if is_selected else "#4a148c"
                html += f"""
                    <rect x="0" y="0" width="150" height="40"
                          fill="{fill_color}" stroke="{stroke_color}" stroke-width="2" {glow_filter} />
                """
            
            html += f"""
                <text x="75" y="25" text-anchor="middle" 
                      fill="#333" font-size="13" font-family="Arial, sans-serif"
                      font-weight="bold" style="pointer-events: none;">
                    {label[:20]}{'...' if len(label) > 20 else ''}
                </text>
            </g>
            """
        
        # Close SVG and add JavaScript
        html += """
                </svg>
            </div>
        </div>
        
        <script>
            (function() {
                // Prevent multiple initializations
                if (window.flowchartInitialized) return;
                window.flowchartInitialized = true;
                
                // Global state
                window.fcDragging = false;
                window.fcDragOffset = {x: 0, y: 0};
                window.fcSelectedElement = null;
                
                // Find canvas action input
                function findActionInput() {
                    const inputs = document.querySelectorAll('input, textarea');
                    for (let input of inputs) {
                        const parent = input.parentElement;
                        if (parent && parent.style.display === 'none') {
                            return input;
                        }
                    }
                    return null;
                }
                
                // Send action to backend
                function sendAction(data) {
                    const input = findActionInput();
                    if (input) {
                        input.value = JSON.stringify(data);
                        input.dispatchEvent(new Event('input', {bubbles: true}));
                        console.log('Sent action:', data);
                    }
                }
                
                // Global functions
                window.fcSelectElement = function(id, type) {
                    console.log('Selecting:', id, type);
                    sendAction({
                        type: type === 'node' ? 'select_node' : 'select_edge',
                        id: id
                    });
                    window.fcSelectedElement = id;
                };
                
                window.fcStartDrag = function(event, nodeId) {
                    console.log('Starting drag:', nodeId);
                    event.stopPropagation();
                    event.preventDefault();
                    
                    window.fcDragging = true;
                    window.fcSelectedElement = nodeId;
                    
                    const node = event.currentTarget;
                    const transform = node.getAttribute('transform') || 'translate(0,0)';
                    const match = transform.match(/translate\\(([^,]+),([^)]+)\\)/);
                    const currentX = match ? parseFloat(match[1]) : 0;
                    const currentY = match ? parseFloat(match[2]) : 0;
                    
                    const svg = document.getElementById('flowchart-svg');
                    const rect = svg.getBoundingClientRect();
                    window.fcDragOffset.x = event.clientX - rect.left - currentX;
                    window.fcDragOffset.y = event.clientY - rect.top - currentY;
                };
                
                // Mouse move handler
                document.addEventListener('mousemove', function(event) {
                    if (!window.fcDragging || !window.fcSelectedElement) return;
                    
                    const svg = document.getElementById('flowchart-svg');
                    if (!svg) return;
                    
                    const rect = svg.getBoundingClientRect();
                    const x = Math.max(0, event.clientX - rect.left - window.fcDragOffset.x);
                    const y = Math.max(0, event.clientY - rect.top - window.fcDragOffset.y);
                    
                    const node = document.querySelector(`[data-node-id="${window.fcSelectedElement}"]`);
                    if (node) {
                        node.setAttribute('transform', `translate(${x},${y})`);
                    }
                });
                
                // Mouse up handler
                document.addEventListener('mouseup', function(event) {
                    if (window.fcDragging && window.fcSelectedElement) {
                        const svg = document.getElementById('flowchart-svg');
                        if (svg) {
                            const rect = svg.getBoundingClientRect();
                            const x = Math.max(0, event.clientX - rect.left - window.fcDragOffset.x);
                            const y = Math.max(0, event.clientY - rect.top - window.fcDragOffset.y);
                            
                            sendAction({
                                type: 'move_node',
                                id: window.fcSelectedElement,
                                x: x,
                                y: y
                            });
                        }
                    }
                    window.fcDragging = false;
                });
                
                // Click outside to deselect
                const svg = document.getElementById('flowchart-svg');
                if (svg) {
                    svg.addEventListener('click', function(e) {
                        if (e.target === this) {
                            sendAction({type: 'deselect'});
                            window.fcSelectedElement = null;
                        }
                    });
                }
                
                console.log('Flowchart initialized successfully');
            })();
        </script>
        """
        
        return html
    
    def scrape_website_content(self, url):
        """Scrape and extract only relevant content from website"""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "menu"]):
                element.decompose()
            
            # Priority content extraction
            relevant_content = []
            
            # 1. Extract headings and their following content
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                heading_text = heading.get_text().strip()
                if heading_text and len(heading_text) > 3:
                    relevant_content.append(f"HEADING: {heading_text}")
                    
                    # Get the next few elements after the heading
                    next_elements = []
                    current = heading.next_sibling
                    count = 0
                    while current and count < 3:
                        if hasattr(current, 'get_text'):
                            text = current.get_text().strip()
                            if text and len(text) > 20:
                                next_elements.append(text)
                                count += 1
                        current = current.next_sibling
                    
                    if next_elements:
                        relevant_content.extend(next_elements[:2])  # Limit to 2 elements
            
            # 2. Extract ordered/unordered lists (often contain steps)
            lists = soup.find_all(['ol', 'ul'])
            for list_elem in lists:
                list_items = list_elem.find_all('li')
                if len(list_items) >= 2:  # Only include lists with multiple items
                    relevant_content.append("LIST:")
                    for li in list_items[:8]:  # Limit to 8 items
                        item_text = li.get_text().strip()
                        if item_text and len(item_text) > 10:
                            relevant_content.append(f"- {item_text}")
            
            # 3. Extract paragraphs that might contain process descriptions
            paragraphs = soup.find_all('p')
            process_keywords = ['step', 'process', 'procedure', 'method', 'how to', 'first', 'then', 'next', 'finally', 'workflow']
            
            for p in paragraphs:
                text = p.get_text().strip()
                if (text and len(text) > 50 and len(text) < 500 and 
                    any(keyword in text.lower() for keyword in process_keywords)):
                    relevant_content.append(text)
            
            # 4. Look for specific content areas
            content_selectors = [
                '.content', '.main-content', '.article-body', '.post-content',
                '#content', '#main', '.entry-content', '.page-content'
            ]
            
            for selector in content_selectors:
                content_area = soup.select_one(selector)
                if content_area:
                    text = content_area.get_text().strip()
                    if text and len(text) > 100:
                        # Extract meaningful sentences
                        sentences = text.split('.')
                        good_sentences = []
                        for sentence in sentences[:10]:  # Limit to 10 sentences
                            sentence = sentence.strip()
                            if (len(sentence) > 20 and len(sentence) < 200 and
                                any(keyword in sentence.lower() for keyword in process_keywords)):
                                good_sentences.append(sentence + '.')
                        
                        if good_sentences:
                            relevant_content.extend(good_sentences[:5])  # Limit to 5 sentences
                        break
            
            # Combine and clean content
            final_content = []
            seen_content = set()
            
            for content in relevant_content:
                # Clean and normalize
                content = re.sub(r'\s+', ' ', content).strip()
                content = re.sub(r'[^\w\s\-\.\,\:\;\!\?\(\)]', '', content)
                
                # Avoid duplicates and very short content
                if (content and len(content) > 15 and 
                    content.lower() not in seen_content and
                    len(content) < 300):  # Limit individual content length
                    seen_content.add(content.lower())
                    final_content.append(content)
            
            # Join and limit total length
            result = '\n'.join(final_content)
            
            # Final length check - limit to ~1000 characters for token efficiency
            if len(result) > 1000:
                result = result[:1000] + "..."
            
            return result if result.strip() else "No relevant content found on this website."
            
        except Exception as e:
            return f"Error scraping website: {str(e)}"
    
    def export_to_mermaid(self, flowchart_data):
        """Convert flowchart JSON to Mermaid syntax"""
        if not flowchart_data or not isinstance(flowchart_data, dict):
            return "No flowchart data available"
        
        nodes = flowchart_data.get("nodes", [])
        edges = flowchart_data.get("edges", [])
        
        mermaid_lines = ["flowchart TD"]
        
        # Add nodes
        for node in nodes:
            node_id = node.get("id", "")
            label = node.get("data", {}).get("label", "")
            node_type = node.get("type", "default")
            
            # Clean label for Mermaid
            label = re.sub(r'[^\w\s-]', '', label)
            
            if node_type == "start":
                mermaid_lines.append(f"    {node_id}([{label}])")
            elif node_type == "end":
                mermaid_lines.append(f"    {node_id}([{label}])")
            elif node_type == "decision":
                mermaid_lines.append(f"    {node_id}{{{label}}}")
            else:
                mermaid_lines.append(f"    {node_id}[{label}]")
        
        # Add edges
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            label = edge.get("label", "")
            
            if label:
                label = re.sub(r'[^\w\s-]', '', label)
                mermaid_lines.append(f"    {source} -->|{label}| {target}")
            else:
                mermaid_lines.append(f"    {source} --> {target}")
        
        return "\n".join(mermaid_lines)

    def handle_canvas_action(self, action, flowchart_data, current_selection):
        """Handle actions from canvas interactions"""
        if not action:
            return flowchart_data, current_selection, gr.update(), "", "Ready"
        
        try:
            action_data = json.loads(action)
            action_type = action_data.get("type")
            element_id = action_data.get("id")
            
            if action_type == "select_node":
                node = next((n for n in flowchart_data.get("nodes", []) 
                           if n["id"] == element_id), None)
                if node:
                    current_label = node.get("data", {}).get("label", "")
                    return (flowchart_data, f"node:{element_id}", 
                           gr.update(visible=True), current_label,
                           f"Selected node: {current_label}")
            
            elif action_type == "select_edge":
                edge = next((e for e in flowchart_data.get("edges", []) 
                           if e["id"] == element_id), None)
                if edge:
                    current_label = edge.get("label", "")
                    return (flowchart_data, f"edge:{element_id}", 
                           gr.update(visible=True), current_label,
                           f"Selected edge: {element_id}")
            
            elif action_type == "deselect":
                return (flowchart_data, "", gr.update(visible=False), "",
                       "Click on nodes or edges to select and edit them")
            
            elif action_type == "move_node":
                x = action_data.get("x", 0)
                y = action_data.get("y", 0)
                for node in flowchart_data.get("nodes", []):
                    if node["id"] == element_id:
                        node["position"] = {"x": max(0, x), "y": max(0, y)}
                        break
                return (flowchart_data, current_selection, gr.update(), "",
                       f"Moved node {element_id}")
        
        except Exception as e:
            return (flowchart_data, current_selection, gr.update(), "",
                   f"Error: {str(e)}")
        
        return flowchart_data, current_selection, gr.update(), "", "Ready"

    def apply_quick_edit(self, flowchart_data, selected_element, new_text):
        """Apply quick edit to selected element"""
        if not selected_element or not new_text:
            return flowchart_data, "No element selected or empty text"
        
        try:
            element_type, element_id = selected_element.split(":", 1)
            
            if element_type == "node":
                for node in flowchart_data.get("nodes", []):
                    if node["id"] == element_id:
                        node["data"]["label"] = new_text
                        return flowchart_data, f"Updated node {element_id}"
            
            elif element_type == "edge":
                for edge in flowchart_data.get("edges", []):
                    if edge["id"] == element_id:
                        edge["label"] = new_text
                        return flowchart_data, f"Updated edge {element_id}"
            
            return flowchart_data, "Element not found"
        
        except Exception as e:
            return flowchart_data, f"Error updating: {str(e)}"

    def add_new_node(self, flowchart_data):
        """Add a new node to the flowchart"""
        new_id = str(len(flowchart_data.get("nodes", [])) + 1)
        new_node = {
            "id": new_id,
            "type": "process",
            "position": {"x": 200, "y": 100 + len(flowchart_data.get("nodes", [])) * 80},
            "data": {"label": f"New Node {new_id}"}
        }
        
        flowchart_data["nodes"] = flowchart_data.get("nodes", []) + [new_node]
        return flowchart_data, f"Added new node {new_id}"

    def delete_selected_element(self, flowchart_data, selected_element):
        """Delete the selected element"""
        if not selected_element:
            return flowchart_data, "", "No element selected"
        
        try:
            element_type, element_id = selected_element.split(":", 1)
            
            if element_type == "node":
                # Remove node
                flowchart_data["nodes"] = [n for n in flowchart_data.get("nodes", []) 
                                         if n["id"] != element_id]
                # Remove connected edges
                flowchart_data["edges"] = [e for e in flowchart_data.get("edges", [])
                                         if e["source"] != element_id and e["target"] != element_id]
                return flowchart_data, "", f"Deleted node {element_id} and its connections"
            
            elif element_type == "edge":
                flowchart_data["edges"] = [e for e in flowchart_data.get("edges", [])
                                         if e["id"] != element_id]
                return flowchart_data, "", f"Deleted edge {element_id}"
            
            return flowchart_data, selected_element, "Element not found"
        
        except Exception as e:
            return flowchart_data, selected_element, f"Error deleting: {str(e)}" 