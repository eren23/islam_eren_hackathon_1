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
        self.canvas_id_counter = 0
    
    def create_interface(self):
        """Create the flowchart interface using built-in Gradio components"""
        
        # JavaScript that uses event delegation instead of inline handlers
        head_js = """
        <script>
        console.log('🚀 Flowchart interface loading with event delegation...');
        
        // Global flowchart interaction handler using event delegation
        window.flowchartHandler = {
            init: function() {
                console.log('🔧 Initializing flowchart event delegation...');
                
                // Remove any existing listeners
                document.removeEventListener('click', this.handleClick);
                document.removeEventListener('mousedown', this.handleMouseDown);
                document.removeEventListener('dblclick', this.handleDoubleClick);
                
                // Add event listeners using delegation
                document.addEventListener('click', this.handleClick.bind(this));
                document.addEventListener('mousedown', this.handleMouseDown.bind(this));
                document.addEventListener('dblclick', this.handleDoubleClick.bind(this));
                
                console.log('✅ Event delegation initialized');
            },
            
            handleClick: function(event) {
                const target = event.target.closest('[data-fc-action]');
                if (!target) return;
                
                event.preventDefault();
                event.stopPropagation();
                
                const action = target.dataset.fcAction;
                const elementId = target.dataset.fcId;
                const elementType = target.dataset.fcType;
                
                console.log('🎯 Click detected:', action, elementId, elementType);
                
                if (action === 'select') {
                    this.selectElement(elementId, elementType);
                }
            },
            
            handleMouseDown: function(event) {
                const target = event.target.closest('[data-fc-drag]');
                if (!target) return;
                
                event.preventDefault();
                
                const elementId = target.dataset.fcId;
                console.log('🚀 Drag started:', elementId);
                
                // For now, just select the element
                this.selectElement(elementId, 'node');
            },
            
            handleDoubleClick: function(event) {
                const target = event.target.closest('[data-fc-edit]');
                if (!target) return;
                
                event.preventDefault();
                
                const elementId = target.dataset.fcId;
                const elementType = target.dataset.fcType;
                
                console.log('✏️ Double-click edit:', elementId, elementType);
                this.selectElement(elementId, elementType);
            },
            
            selectElement: function(elementId, elementType) {
                console.log('🎯 Selecting element:', elementId, elementType);
                
                // Find canvas_action textarea
                let textarea = null;
                const canvasActionDiv = document.getElementById('canvas_action');
                
                if (canvasActionDiv) {
                    textarea = canvasActionDiv.querySelector('textarea');
                    console.log('📍 Found textarea in canvas_action:', textarea);
                }
                
                if (!textarea) {
                    // Fallback: find any hidden textarea
                    const allTextareas = document.querySelectorAll('textarea');
                    console.log('🔍 Looking through', allTextareas.length, 'textareas');
                    
                    for (let i = 0; i < allTextareas.length; i++) {
                        const ta = allTextareas[i];
                        const parentDiv = ta.closest('.block');
                        if (parentDiv && (parentDiv.style.display === 'none' || 
                            parentDiv.classList.contains('hidden'))) {
                            textarea = ta;
                            console.log('📍 Using fallback textarea:', textarea);
                            break;
                        }
                    }
                }
                
                if (textarea) {
                    const data = JSON.stringify({
                        type: 'select_' + elementType,
                        id: elementId,
                        elementType: elementType
                    });
                    
                    textarea.value = data;
                    textarea.dispatchEvent(new Event('input', {bubbles: true}));
                    textarea.dispatchEvent(new Event('change', {bubbles: true}));
                    textarea.focus();
                    textarea.blur();
                    
                    console.log('✅ Selection data sent:', data);
                } else {
                    console.error('❌ Could not find canvas_action textarea');
                    console.log('Available textareas:', document.querySelectorAll('textarea'));
                    console.log('canvas_action div:', document.getElementById('canvas_action'));
                }
            }
        };
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(window.flowchartHandler.init.bind(window.flowchartHandler), 500);
            });
        } else {
            setTimeout(window.flowchartHandler.init.bind(window.flowchartHandler), 500);
        }
        
        // Re-initialize periodically to handle dynamic content
        setInterval(function() {
            if (window.flowchartHandler && !window.flowchartHandler.initialized) {
                window.flowchartHandler.init();
                window.flowchartHandler.initialized = true;
            }
        }, 2000);
        
        // Debug function
        window.debugFlowchartElements = function() {
            console.log('🔍 Debugging flowchart elements:');
            console.log('canvas_action:', document.getElementById('canvas_action'));
            console.log('selected_element:', document.getElementById('selected_element'));
            console.log('All textareas:', document.querySelectorAll('textarea'));
            console.log('Event handler initialized:', !!window.flowchartHandler.initialized);
        };
        </script>
        """
        
        with gr.Blocks(head=head_js) as interface:
            gr.Markdown("### Interactive Flowchart Canvas")
            
            # Debug button for testing
            debug_btn = gr.Button("🔍 Debug Elements", size="sm")
            
            # Hidden components for state management
            selected_element = gr.Textbox(
                value="", visible=False, elem_id="selected_element"
            )
            canvas_action = gr.Textbox(
                value="", visible=False, elem_id="canvas_action"
            )
            
            # Visual canvas with enhanced interactivity
            flowchart_html = gr.HTML(
                value=self.render_interactive_flowchart(
                    self.get_example_flowchart()
                ),
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
                delete_selected_btn = gr.Button(
                    "🗑️ Delete Selected", size="sm", variant="stop"
                )
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
            
            # Debug button functionality
            debug_btn.click(
                lambda: "Debug function called - check console",
                outputs=[status_text]
            )
            
            # Enhanced canvas interaction handling
            canvas_action.change(
                self.handle_canvas_action,
                inputs=[canvas_action, flowchart_json, selected_element],
                outputs=[
                    flowchart_json, selected_element, edit_panel, 
                    quick_edit_text, status_text
                ]
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
    
    def _generate_svg(self, flowchart_data, canvas_id):
        """Generate SVG content for the flowchart using data attributes for event delegation"""
        if not flowchart_data or not isinstance(flowchart_data, dict):
            return "<div>No flowchart data available</div>"
        
        nodes = flowchart_data.get("nodes", [])
        edges = flowchart_data.get("edges", [])
        
        # Calculate canvas dimensions
        max_x = max([node.get("position", {}).get("x", 0) for node in nodes] + [400])
        max_y = max([node.get("position", {}).get("y", 0) for node in nodes] + [300])
        
        canvas_width = max_x + 200
        canvas_height = max_y + 200
        
        # Start building SVG
        svg_parts = [
            f'<svg id="{canvas_id}" width="{canvas_width}" height="{canvas_height}" '
            f'style="border: 1px solid #ccc; background: #fafafa;" '
            f'xmlns="http://www.w3.org/2000/svg">'
        ]
        
        # Add arrow marker definition
        svg_parts.append("""
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                        refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                </marker>
            </defs>
        """)
        
        # Draw edges first (so they appear behind nodes)
        for edge in edges:
            source_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            target_node = next((n for n in nodes if n["id"] == edge["target"]), None)
            
            if source_node and target_node:
                source_pos = source_node.get("position", {})
                target_pos = target_node.get("position", {})
                
                x1 = source_pos.get("x", 0) + 50  # Center of node
                y1 = source_pos.get("y", 0) + 25
                x2 = target_pos.get("x", 0) + 50
                y2 = target_pos.get("y", 0) + 25
                
                edge_id = edge.get("id", "")
                edge_label = edge.get("label", "")
                
                # Calculate label position
                label_x = (x1 + x2) / 2
                label_y = (y1 + y2) / 2 - 10
                
                # Create edge group with data attributes for event delegation
                edge_text = (f'<text x="{label_x}" y="{label_y}" '
                           f'text-anchor="middle" font-size="12" fill="#444">'
                           f'{edge_label}</text>') if edge_label else ''
                
                svg_parts.append(f'''
                    <g class="edge" 
                       data-fc-action="select" 
                       data-fc-id="{edge_id}" 
                       data-fc-type="edge"
                       style="cursor: pointer;">
                        <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                              stroke="#666" stroke-width="2" 
                              marker-end="url(#arrowhead)" />
                        {edge_text}
                    </g>
                ''')
        
        # Draw nodes
        for node in nodes:
            node_id = node.get("id", "")
            node_type = node.get("type", "default")
            position = node.get("position", {})
            label = node.get("data", {}).get("label", "")
            
            x = position.get("x", 0)
            y = position.get("y", 0)
            
            # Node styling based on type
            if node_type == "start":
                shape = (f'<ellipse cx="{x + 50}" cy="{y + 25}" rx="50" ry="25" '
                        f'fill="#4CAF50" stroke="#388E3C" stroke-width="2" />')
                text_color = "white"
            elif node_type == "end":
                shape = (f'<ellipse cx="{x + 50}" cy="{y + 25}" rx="50" ry="25" '
                        f'fill="#F44336" stroke="#D32F2F" stroke-width="2" />')
                text_color = "white"
            elif node_type == "decision":
                # Diamond shape
                points = f"{x + 50},{y} {x + 100},{y + 25} {x + 50},{y + 50} {x},{y + 25}"
                shape = (f'<polygon points="{points}" fill="#FF9800" '
                        f'stroke="#F57C00" stroke-width="2" />')
                text_color = "white"
            else:  # process
                shape = (f'<rect x="{x}" y="{y}" width="100" height="50" rx="5" '
                        f'fill="#2196F3" stroke="#1976D2" stroke-width="2" />')
                text_color = "white"
            
            # Create node group with data attributes for event delegation
            svg_parts.append(f'''
                <g class="node" 
                   data-fc-action="select" 
                   data-fc-id="{node_id}" 
                   data-fc-type="node"
                   data-fc-drag="true"
                   data-fc-edit="true"
                   style="cursor: pointer;">
                    {shape}
                    <text x="{x + 50}" y="{y + 30}" text-anchor="middle" 
                          font-size="12" fill="{text_color}" font-weight="bold">
                        {label}
                    </text>
                </g>
            ''')
        
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)

    def render_interactive_flowchart(self, flowchart_data, selected_element=""):
        """Render interactive flowchart with event delegation (no inline JavaScript needed)"""
        if not flowchart_data or not isinstance(flowchart_data, dict):
            return "<div>No flowchart data available</div>"
        
        self.canvas_id_counter += 1
        canvas_id = f"canvas_{self.canvas_id_counter}"
        
        # Generate SVG with data attributes (no JavaScript needed here)
        svg_content = self._generate_svg(flowchart_data, canvas_id)
        
        return svg_content

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
                        relevant_content.extend(next_elements[:2])
            
            # 2. Extract ordered/unordered lists
            lists = soup.find_all(['ol', 'ul'])
            for list_elem in lists:
                list_items = list_elem.find_all('li')
                if len(list_items) >= 2:
                    relevant_content.append("LIST:")
                    for li in list_items[:8]:
                        item_text = li.get_text().strip()
                        if item_text and len(item_text) > 10:
                            relevant_content.append(f"- {item_text}")
            
            # 3. Extract paragraphs that might contain process descriptions
            paragraphs = soup.find_all('p')
            process_keywords = [
                'step', 'process', 'procedure', 'method', 'how to', 
                'first', 'then', 'next', 'finally', 'workflow'
            ]
            
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
                        for sentence in sentences[:10]:
                            sentence = sentence.strip()
                            if (len(sentence) > 20 and len(sentence) < 200 and
                                any(keyword in sentence.lower() 
                                    for keyword in process_keywords)):
                                good_sentences.append(sentence + '.')
                        
                        if good_sentences:
                            relevant_content.extend(good_sentences[:5])
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
                    len(content) < 300):
                    seen_content.add(content.lower())
                    final_content.append(content)
            
            # Join and limit total length
            result = '\n'.join(final_content)
            
            # Final length check
            if len(result) > 1000:
                result = result[:1000] + "..."
            
            return result if result.strip() else "No relevant content found."
            
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
        """Handle actions from canvas interactions with improved error handling"""
        if not action:
            return (flowchart_data, current_selection, gr.update(), "", "Ready")
        
        try:
            action_data = json.loads(action)
            action_type = action_data.get("type")
            element_id = action_data.get("id")
            
            if action_type == "select_node":
                node = next((n for n in flowchart_data.get("nodes", []) 
                           if n["id"] == element_id), None)
                if node:
                    current_label = node.get("data", {}).get("label", "")
                    return (
                        flowchart_data, f"node:{element_id}", 
                        gr.update(visible=True), current_label,
                        f"Selected node: {current_label}"
                    )
            
            elif action_type == "select_edge":
                edge = next((e for e in flowchart_data.get("edges", []) 
                           if e["id"] == element_id), None)
                if edge:
                    current_label = edge.get("label", "")
                    return (
                        flowchart_data, f"edge:{element_id}", 
                        gr.update(visible=True), current_label,
                        f"Selected edge: {element_id}"
                    )
            
            elif action_type == "deselect":
                return (
                    flowchart_data, "", gr.update(visible=False), "",
                    "Click on nodes or edges to select and edit them"
                )
            
            elif action_type == "move_node":
                x = action_data.get("x", 0)
                y = action_data.get("y", 0)
                for node in flowchart_data.get("nodes", []):
                    if node["id"] == element_id:
                        node["position"] = {"x": max(0, x), "y": max(0, y)}
                        break
                return (
                    flowchart_data, current_selection, gr.update(), "",
                    f"Moved node {element_id}"
                )
            
            elif action_type == "quick_edit":
                element_type = action_data.get("elementType")
                if element_type == "node":
                    node = next((n for n in flowchart_data.get("nodes", []) 
                               if n["id"] == element_id), None)
                    if node:
                        current_label = node.get("data", {}).get("label", "")
                        return (
                            flowchart_data, f"node:{element_id}",
                            gr.update(visible=True), current_label,
                            f"Quick editing node: {element_id}"
                        )
                elif element_type == "edge":
                    edge = next((e for e in flowchart_data.get("edges", []) 
                               if e["id"] == element_id), None)
                    if edge:
                        current_label = edge.get("label", "")
                        return (
                            flowchart_data, f"edge:{element_id}",
                            gr.update(visible=True), current_label,
                            f"Quick editing edge: {element_id}"
                        )
        
        except json.JSONDecodeError as e:
            return (
                flowchart_data, current_selection, gr.update(), "",
                f"JSON Error: {str(e)}"
            )
        except Exception as e:
            return (
                flowchart_data, current_selection, gr.update(), "",
                f"Error: {str(e)}"
            )
        
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
                        node["data"]["label"] = new_text.strip()
                        return flowchart_data, f"Updated node {element_id}"
            
            elif element_type == "edge":
                for edge in flowchart_data.get("edges", []):
                    if edge["id"] == element_id:
                        edge["label"] = new_text.strip()
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
            "position": {
                "x": 200, 
                "y": 100 + len(flowchart_data.get("nodes", [])) * 80
            },
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
                flowchart_data["nodes"] = [
                    n for n in flowchart_data.get("nodes", []) 
                    if n["id"] != element_id
                ]
                # Remove connected edges
                flowchart_data["edges"] = [
                    e for e in flowchart_data.get("edges", [])
                    if e["source"] != element_id and e["target"] != element_id
                ]
                return (
                    flowchart_data, "", 
                    f"Deleted node {element_id} and its connections"
                )
            
            elif element_type == "edge":
                flowchart_data["edges"] = [
                    e for e in flowchart_data.get("edges", [])
                    if e["id"] != element_id
                ]
                return flowchart_data, "", f"Deleted edge {element_id}"
            
            return flowchart_data, selected_element, "Element not found"
        
        except Exception as e:
            return flowchart_data, selected_element, f"Error deleting: {str(e)}" 