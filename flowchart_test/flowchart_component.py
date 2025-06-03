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
            gr.Markdown("### Flowchart Canvas")
            
            # Visual canvas using HTML
            flowchart_html = gr.HTML(
                value=self.render_flowchart_html(self.get_example_flowchart()),
                label="Flowchart Visualization"
            )
            
            # JSON editor for manual editing
            flowchart_json = gr.JSON(
                value=self.get_example_flowchart(),
                label="Flowchart Data (JSON)"
            )
            
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh Visualization", size="sm")
                export_btn = gr.Button("📤 Export to Mermaid", size="sm")
                clear_btn = gr.Button("🗑️ Clear", size="sm")
            
            export_output = gr.Textbox(
                label="Mermaid Export",
                lines=5,
                visible=False
            )
            
            # Connect the functionality
            refresh_btn.click(
                self.update_visualization,
                inputs=[flowchart_json],
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
                lambda: (self.get_empty_flowchart(), self.render_flowchart_html(self.get_empty_flowchart())),
                outputs=[flowchart_json, flowchart_html]
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
    
    def update_visualization(self, flowchart_data):
        """Update the HTML visualization"""
        return self.render_flowchart_html(flowchart_data)
    
    def render_flowchart_html(self, flowchart_data):
        """Render flowchart as HTML/CSS visualization with drag-drop support"""
        if not flowchart_data or not isinstance(flowchart_data, dict):
            return "<div>No flowchart data available</div>"
        
        nodes = flowchart_data.get("nodes", [])
        edges = flowchart_data.get("edges", [])
        
        # Calculate SVG dimensions
        max_x = max([node.get("position", {}).get("x", 0) for node in nodes] + [300])
        max_y = max([node.get("position", {}).get("y", 0) for node in nodes] + [400])
        
        svg_width = max_x + 200
        svg_height = max_y + 100
        
        # Add drag-drop JavaScript
        html = f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #f9f9f9;">
            <svg width="{svg_width}" height="{svg_height}" style="background: white; border-radius: 4px;"
                 onmousedown="startDrag(event)" onmousemove="drag(event)" onmouseup="endDrag(event)">
                <script>
                    let selectedNode = null;
                    let offset = {{x: 0, y: 0}};
                    
                    function startDrag(event) {{
                        const target = event.target.closest('.node');
                        if (target) {{
                            selectedNode = target;
                            const rect = target.getBoundingClientRect();
                            offset.x = event.clientX - rect.left;
                            offset.y = event.clientY - rect.top;
                        }}
                    }}
                    
                    function drag(event) {{
                        if (selectedNode) {{
                            event.preventDefault();
                            const x = event.clientX - offset.x;
                            const y = event.clientY - offset.y;
                            selectedNode.setAttribute('transform', `translate(${{x}},${{y}})`);
                        }}
                    }}
                    
                    function endDrag(event) {{
                        selectedNode = null;
                    }}
                </script>
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                            refX="10" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                    </marker>
                </defs>
        """
        
        # Draw edges
        for edge in edges:
            source_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            target_node = next((n for n in nodes if n["id"] == edge["target"]), None)
            
            if source_node and target_node:
                x1 = source_node["position"]["x"] + 75
                y1 = source_node["position"]["y"] + 30
                x2 = target_node["position"]["x"] + 75
                y2 = target_node["position"]["y"] + 10
                
                html += f"""
                    <g class="edge" data-id="{edge['id']}">
                        <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                              stroke="#666" stroke-width="2" marker-end="url(#arrowhead)" />
                """
                
                if edge.get("label"):
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2 - 5
                    html += f"""
                        <text x="{mid_x}" y="{mid_y}" text-anchor="middle" 
                              fill="#333" font-size="12" font-family="Arial">
                            {edge['label']}
                        </text>
                    """
                
                html += "</g>"
        
        # Draw nodes with drag-drop support
        for node in nodes:
            x = node["position"]["x"]
            y = node["position"]["y"]
            label = node["data"]["label"]
            node_type = node.get("type", "process")
            
            html += f'<g class="node" data-id="{node["id"]}" transform="translate({x},{y})">'
            
            if node_type in ("start", "end"):
                html += f"""
                    <rect x="0" y="0" width="150" height="40" rx="20" ry="20"
                          fill="#e1f5fe" stroke="#01579b" stroke-width="2" />
                """
            elif node_type == "decision":
                cx, cy = 75, 20
                html += f"""
                    <polygon points="{cx},0 150,{cy} {cx},40 0,{cy}"
                             fill="#fff3e0" stroke="#e65100" stroke-width="2" />
                """
            else:
                html += f"""
                    <rect x="0" y="0" width="150" height="40"
                          fill="#f3e5f5" stroke="#4a148c" stroke-width="2" />
                """
            
            html += f"""
                <text x="75" y="25" text-anchor="middle" 
                      fill="#333" font-size="14" font-family="Arial, sans-serif"
                      font-weight="bold">
                    {label}
                </text>
            </g>
            """
        
        html += """
            </svg>
        </div>
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