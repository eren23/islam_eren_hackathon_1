from gradio.components.base import Component
from gradio.events import Events
import json
from gradio.events import Dependency

class FlowchartCreator(Component):
    """A custom Gradio component for creating and editing flowcharts"""
    
    EVENTS = [
        Events.change,  # For flowchart data changes
        Events.select,  # For node/edge selection
        Events.edit,    # For editing nodes/edges
        Events.clear    # For clearing the flowchart
    ]
    
    def __init__(
        self,
        value=None,
        *,
        label=None,
        every=None,
        show_label=True,
        interactive=True,
        visible=True,
        elem_id=None,
        **kwargs,
    ):
        """Initialize the flowchart component"""
        super().__init__(
            label=label,
            every=every,
            show_label=show_label,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            **kwargs,
        )
        self.value = value if value is not None else {"nodes": [], "edges": []}
    
    def create_interface(self):
        """Create the flowchart interface with editing capabilities"""
        with gr.Column() as interface:
            gr.Markdown("### Interactive Flowchart")
            
            # Visual canvas using HTML
            flowchart_html = gr.HTML(
                value=self.render_flowchart_html(self.get_example_flowchart()),
                label="Flowchart Visualization"
            )
            
            # Add editing controls
            with gr.Row():
                edit_text = gr.Textbox(
                    label="Edit Node/Edge",
                    placeholder="Enter text to edit selected element..."
                )
                edit_btn = gr.Button("✏️ Apply Edit")
            
            with gr.Row():
                add_node_text = gr.Textbox(
                    label="Add Node",
                    placeholder="Enter node text..."
                )
                add_node_btn = gr.Button("➕ Add Node")
            
            with gr.Row():
                connect_nodes = gr.Textbox(
                    label="Connect Nodes",
                    placeholder="node1,node2,label (e.g., 1,2,Yes)"
                )
                connect_btn = gr.Button("🔗 Connect")
            
            # JSON editor for advanced editing
            flowchart_json = gr.JSON(
                value=self.get_example_flowchart(),
                label="Flowchart Data (JSON)"
            )
            
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh", size="sm")
                export_btn = gr.Button("📤 Export", size="sm")
                clear_btn = gr.Button("🗑️ Clear", size="sm")
            
            # Connect the functionality
            edit_btn.click(
                self.edit_element,
                inputs=[flowchart_json, edit_text],
                outputs=[flowchart_json, flowchart_html]
            )
            
            add_node_btn.click(
                self.add_node,
                inputs=[flowchart_json, add_node_text],
                outputs=[flowchart_json, flowchart_html]
            )
            
            connect_btn.click(
                self.connect_nodes,
                inputs=[flowchart_json, connect_nodes],
                outputs=[flowchart_json, flowchart_html]
            )
            
            refresh_btn.click(
                self.update_visualization,
                inputs=[flowchart_json],
                outputs=[flowchart_html]
            )
            
            clear_btn.click(
                lambda: (self.get_empty_flowchart(), self.render_flowchart_html(self.get_empty_flowchart())),
                outputs=[flowchart_json, flowchart_html]
            )
        
        return interface, flowchart_json, flowchart_html
    
    def example_inputs(self) -> dict:
        """Return example input for the component"""
        return {
            "nodes": [
                {
                    "id": "1",
                    "type": "start",
                    "position": {"x": 100, "y": 100},
                    "data": {"label": "Start"}
                },
                {
                    "id": "2",
                    "type": "process",
                    "position": {"x": 100, "y": 200},
                    "data": {"label": "Process"}
                },
                {
                    "id": "3",
                    "type": "end",
                    "position": {"x": 100, "y": 300},
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
                }
            ]
        }

    def example_payload(self) -> str:
        """Return example payload for the component"""
        return json.dumps(self.example_inputs())

    def get_example_flowchart(self) -> dict:
        """Return example flowchart data"""
        return self.example_inputs()

    def get_empty_flowchart(self) -> dict:
        """Return empty flowchart data"""
        return {"nodes": [], "edges": []}

    def update_visualization(self, flowchart_data: dict) -> str:
        """Update the flowchart visualization"""
        return self.render_flowchart_html(flowchart_data)

    def render_flowchart_html(self, flowchart_data: dict) -> str:
        """Render flowchart as HTML/CSS visualization"""
        if not flowchart_data or not isinstance(flowchart_data, dict):
            return "<div>No flowchart data available</div>"
        
        nodes = flowchart_data.get("nodes", [])
        edges = flowchart_data.get("edges", [])
        
        # Calculate SVG dimensions
        max_x = max([node.get("position", {}).get("x", 0) for node in nodes] + [300])
        max_y = max([node.get("position", {}).get("y", 0) for node in nodes] + [400])
        
        svg_width = max_x + 200
        svg_height = max_y + 100
        
        html = [
            '<div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #f9f9f9;">',
            f'<svg width="{svg_width}" height="{svg_height}" style="background: white; border-radius: 4px;">',
            '<defs>',
            '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">',
            '<polygon points="0 0, 10 3.5, 0 7" fill="#666" />',
            '</marker>',
            '</defs>'
        ]
        
        # Draw edges first
        for edge in edges:
            source_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            target_node = next((n for n in nodes if n["id"] == edge["target"]), None)
            
            if source_node and target_node:
                x1 = source_node["position"]["x"] + 75
                y1 = source_node["position"]["y"] + 30
                x2 = target_node["position"]["x"] + 75
                y2 = target_node["position"]["y"] + 10
                
                html.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    'stroke="#666" stroke-width="2" marker-end="url(#arrowhead)" />'
                )
                
                label = edge.get("label", "")
                if label:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2 - 5
                    html.append(
                        f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" '
                        f'fill="#333" font-size="12" font-family="Arial">{label}</text>'
                    )
        
        # Draw nodes
        for node in nodes:
            x = node["position"]["x"]
            y = node["position"]["y"]
            label = node["data"]["label"]
            node_type = node.get("type", "process")
            
            if node_type in ("start", "end"):
                html.append(
                    f'<rect x="{x}" y="{y}" width="150" height="40" rx="20" ry="20" '
                    'fill="#e1f5fe" stroke="#01579b" stroke-width="2" />'
                )
            elif node_type == "decision":
                cx, cy = x + 75, y + 20
                html.append(
                    f'<polygon points="{cx},{y} {x+150},{cy} {cx},{y+40} {x},{cy}" '
                    'fill="#fff3e0" stroke="#e65100" stroke-width="2" />'
                )
            else:
                html.append(
                    f'<rect x="{x}" y="{y}" width="150" height="40" '
                    'fill="#f3e5f5" stroke="#4a148c" stroke-width="2" />'
                )
            
            text_x = x + 75
            text_y = y + 25
            html.append(
                f'<text x="{text_x}" y="{text_y}" text-anchor="middle" '
                f'fill="#333" font-size="14" font-family="Arial, sans-serif" '
                f'font-weight="bold">{label}</text>'
            )
        
        html.extend(['</svg>', '</div>'])
        return '\n'.join(html)
    
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

    def edit_element(self, flowchart_data, edit_text):
        """Edit the selected node or edge"""
        # Implementation for editing elements
        if not flowchart_data or not edit_text:
            return flowchart_data, self.render_flowchart_html(flowchart_data)
            
        # Add logic to edit selected element
        # This is a placeholder - you'll need to track selection state
        return flowchart_data, self.render_flowchart_html(flowchart_data)

    def add_node(self, flowchart_data, node_text):
        """Add a new node to the flowchart"""
        if not flowchart_data or not node_text:
            return flowchart_data, self.render_flowchart_html(flowchart_data)
            
        new_id = str(len(flowchart_data.get("nodes", [])) + 1)
        new_node = {
            "id": new_id,
            "type": "process",
            "position": {"x": 150, "y": 50 + len(flowchart_data.get("nodes", [])) * 100},
            "data": {"label": node_text}
        }
        
        flowchart_data["nodes"] = flowchart_data.get("nodes", []) + [new_node]
        return flowchart_data, self.render_flowchart_html(flowchart_data)

    def connect_nodes(self, flowchart_data, connection_text):
        """Connect two nodes with an edge"""
        if not flowchart_data or not connection_text:
            return flowchart_data, self.render_flowchart_html(flowchart_data)
            
        try:
            source, target, label = connection_text.split(",")
            new_edge = {
                "id": f"e{source}-{target}",
                "source": source.strip(),
                "target": target.strip(),
                "label": label.strip()
            }
            
            flowchart_data["edges"] = flowchart_data.get("edges", []) + [new_edge]
            return flowchart_data, self.render_flowchart_html(flowchart_data)
        except:
            return flowchart_data, self.render_flowchart_html(flowchart_data)

    def preprocess(self, payload):
        """Convert from frontend format to Python"""
        if payload is None:
            return {"nodes": [], "edges": []}
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except:
                return {"nodes": [], "edges": []}
        return payload

    def postprocess(self, value):
        """Convert from Python to frontend format"""
        if value is None:
            return json.dumps({"nodes": [], "edges": []})
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def api_info(self):
        """Return API info for the component"""
        return {
            "type": "object",
            "description": "Flowchart data containing nodes and edges",
            "example_data": self.get_example_flowchart()
        }
    from typing import Callable, Literal, Sequence, Any, TYPE_CHECKING
    from gradio.blocks import Block
    if TYPE_CHECKING:
        from gradio.components import Timer
        from gradio.components.base import Component

    
    def change(self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | None = None,
        api_name: str | None | Literal[False] = None,
        scroll_to_output: bool = False,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        show_progress_on: Component | Sequence[Component] | None = None,
        queue: bool | None = None,
        batch: bool = False,
        max_batch_size: int = 4,
        preprocess: bool = True,
        postprocess: bool = True,
        cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
        every: Timer | float | None = None,
        trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
        js: str | Literal[True] | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_api: bool = True,
    
        ) -> Dependency:
        """
        Parameters:
            fn: the function to call when this event is triggered. Often a machine learning model's prediction function. Each parameter of the function corresponds to one input component, and the function should return a single value or a tuple of values, with each element in the tuple corresponding to one output component.
            inputs: list of gradio.components to use as inputs. If the function takes no inputs, this should be an empty list.
            outputs: list of gradio.components to use as outputs. If the function returns no outputs, this should be an empty list.
            api_name: defines how the endpoint appears in the API docs. Can be a string, None, or False. If False, the endpoint will not be exposed in the api docs. If set to None, will use the functions name as the endpoint route. If set to a string, the endpoint will be exposed in the api docs with the given name.
            scroll_to_output: if True, will scroll to output component on completion
            show_progress: how to show the progress animation while event is running: "full" shows a spinner which covers the output component area as well as a runtime display in the upper right corner, "minimal" only shows the runtime display, "hidden" shows no progress animation at all
            show_progress_on: Component or list of components to show the progress animation on. If None, will show the progress animation on all of the output components.
            queue: if True, will place the request on the queue, if the queue has been enabled. If False, will not put this event on the queue, even if the queue has been enabled. If None, will use the queue setting of the gradio app.
            batch: if True, then the function should process a batch of inputs, meaning that it should accept a list of input values for each parameter. The lists should be of equal length (and be up to length `max_batch_size`). The function is then *required* to return a tuple of lists (even if there is only 1 output component), with each list in the tuple corresponding to one output component.
            max_batch_size: maximum number of inputs to batch together if this is called from the queue (only relevant if batch=True)
            preprocess: if False, will not run preprocessing of component data before running 'fn' (e.g. leaving it as a base64 string if this method is called with the `Image` component).
            postprocess: if False, will not run postprocessing of component data before returning 'fn' output to the browser.
            cancels: a list of other events to cancel when this listener is triggered. For example, setting cancels=[click_event] will cancel the click_event, where click_event is the return value of another components .click method. Functions that have not yet run (or generators that are iterating) will be cancelled, but functions that are currently running will be allowed to finish.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            trigger_mode: if "once" (default for all events except `.change()`) would not allow any submissions while an event is pending. If set to "multiple", unlimited submissions are allowed while pending, and "always_last" (default for `.change()` and `.key_up()` events) would allow a second submission after the pending event is complete.
            js: optional frontend js method to run before running 'fn'. Input arguments for js method are values of 'inputs' and 'outputs', return should be a list of values for output components.
            concurrency_limit: if set, this is the maximum number of this event that can be running simultaneously. Can be set to None to mean no concurrency_limit (any number of this event can be running simultaneously). Set to "default" to use the default concurrency limit (defined by the `default_concurrency_limit` parameter in `Blocks.queue()`, which itself is 1 by default).
            concurrency_id: if set, this is the id of the concurrency group. Events with the same concurrency_id will be limited by the lowest set concurrency_limit.
            show_api: whether to show this event in the "view API" page of the Gradio app, or in the ".view_api()" method of the Gradio clients. Unlike setting api_name to False, setting show_api to False will still allow downstream apps as well as the Clients to use this event. If fn is None, show_api will automatically be set to False.
        
        """
        ...
    
    def select(self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | None = None,
        api_name: str | None | Literal[False] = None,
        scroll_to_output: bool = False,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        show_progress_on: Component | Sequence[Component] | None = None,
        queue: bool | None = None,
        batch: bool = False,
        max_batch_size: int = 4,
        preprocess: bool = True,
        postprocess: bool = True,
        cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
        every: Timer | float | None = None,
        trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
        js: str | Literal[True] | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_api: bool = True,
    
        ) -> Dependency:
        """
        Parameters:
            fn: the function to call when this event is triggered. Often a machine learning model's prediction function. Each parameter of the function corresponds to one input component, and the function should return a single value or a tuple of values, with each element in the tuple corresponding to one output component.
            inputs: list of gradio.components to use as inputs. If the function takes no inputs, this should be an empty list.
            outputs: list of gradio.components to use as outputs. If the function returns no outputs, this should be an empty list.
            api_name: defines how the endpoint appears in the API docs. Can be a string, None, or False. If False, the endpoint will not be exposed in the api docs. If set to None, will use the functions name as the endpoint route. If set to a string, the endpoint will be exposed in the api docs with the given name.
            scroll_to_output: if True, will scroll to output component on completion
            show_progress: how to show the progress animation while event is running: "full" shows a spinner which covers the output component area as well as a runtime display in the upper right corner, "minimal" only shows the runtime display, "hidden" shows no progress animation at all
            show_progress_on: Component or list of components to show the progress animation on. If None, will show the progress animation on all of the output components.
            queue: if True, will place the request on the queue, if the queue has been enabled. If False, will not put this event on the queue, even if the queue has been enabled. If None, will use the queue setting of the gradio app.
            batch: if True, then the function should process a batch of inputs, meaning that it should accept a list of input values for each parameter. The lists should be of equal length (and be up to length `max_batch_size`). The function is then *required* to return a tuple of lists (even if there is only 1 output component), with each list in the tuple corresponding to one output component.
            max_batch_size: maximum number of inputs to batch together if this is called from the queue (only relevant if batch=True)
            preprocess: if False, will not run preprocessing of component data before running 'fn' (e.g. leaving it as a base64 string if this method is called with the `Image` component).
            postprocess: if False, will not run postprocessing of component data before returning 'fn' output to the browser.
            cancels: a list of other events to cancel when this listener is triggered. For example, setting cancels=[click_event] will cancel the click_event, where click_event is the return value of another components .click method. Functions that have not yet run (or generators that are iterating) will be cancelled, but functions that are currently running will be allowed to finish.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            trigger_mode: if "once" (default for all events except `.change()`) would not allow any submissions while an event is pending. If set to "multiple", unlimited submissions are allowed while pending, and "always_last" (default for `.change()` and `.key_up()` events) would allow a second submission after the pending event is complete.
            js: optional frontend js method to run before running 'fn'. Input arguments for js method are values of 'inputs' and 'outputs', return should be a list of values for output components.
            concurrency_limit: if set, this is the maximum number of this event that can be running simultaneously. Can be set to None to mean no concurrency_limit (any number of this event can be running simultaneously). Set to "default" to use the default concurrency limit (defined by the `default_concurrency_limit` parameter in `Blocks.queue()`, which itself is 1 by default).
            concurrency_id: if set, this is the id of the concurrency group. Events with the same concurrency_id will be limited by the lowest set concurrency_limit.
            show_api: whether to show this event in the "view API" page of the Gradio app, or in the ".view_api()" method of the Gradio clients. Unlike setting api_name to False, setting show_api to False will still allow downstream apps as well as the Clients to use this event. If fn is None, show_api will automatically be set to False.
        
        """
        ...
    
    def edit(self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | None = None,
        api_name: str | None | Literal[False] = None,
        scroll_to_output: bool = False,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        show_progress_on: Component | Sequence[Component] | None = None,
        queue: bool | None = None,
        batch: bool = False,
        max_batch_size: int = 4,
        preprocess: bool = True,
        postprocess: bool = True,
        cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
        every: Timer | float | None = None,
        trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
        js: str | Literal[True] | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_api: bool = True,
    
        ) -> Dependency:
        """
        Parameters:
            fn: the function to call when this event is triggered. Often a machine learning model's prediction function. Each parameter of the function corresponds to one input component, and the function should return a single value or a tuple of values, with each element in the tuple corresponding to one output component.
            inputs: list of gradio.components to use as inputs. If the function takes no inputs, this should be an empty list.
            outputs: list of gradio.components to use as outputs. If the function returns no outputs, this should be an empty list.
            api_name: defines how the endpoint appears in the API docs. Can be a string, None, or False. If False, the endpoint will not be exposed in the api docs. If set to None, will use the functions name as the endpoint route. If set to a string, the endpoint will be exposed in the api docs with the given name.
            scroll_to_output: if True, will scroll to output component on completion
            show_progress: how to show the progress animation while event is running: "full" shows a spinner which covers the output component area as well as a runtime display in the upper right corner, "minimal" only shows the runtime display, "hidden" shows no progress animation at all
            show_progress_on: Component or list of components to show the progress animation on. If None, will show the progress animation on all of the output components.
            queue: if True, will place the request on the queue, if the queue has been enabled. If False, will not put this event on the queue, even if the queue has been enabled. If None, will use the queue setting of the gradio app.
            batch: if True, then the function should process a batch of inputs, meaning that it should accept a list of input values for each parameter. The lists should be of equal length (and be up to length `max_batch_size`). The function is then *required* to return a tuple of lists (even if there is only 1 output component), with each list in the tuple corresponding to one output component.
            max_batch_size: maximum number of inputs to batch together if this is called from the queue (only relevant if batch=True)
            preprocess: if False, will not run preprocessing of component data before running 'fn' (e.g. leaving it as a base64 string if this method is called with the `Image` component).
            postprocess: if False, will not run postprocessing of component data before returning 'fn' output to the browser.
            cancels: a list of other events to cancel when this listener is triggered. For example, setting cancels=[click_event] will cancel the click_event, where click_event is the return value of another components .click method. Functions that have not yet run (or generators that are iterating) will be cancelled, but functions that are currently running will be allowed to finish.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            trigger_mode: if "once" (default for all events except `.change()`) would not allow any submissions while an event is pending. If set to "multiple", unlimited submissions are allowed while pending, and "always_last" (default for `.change()` and `.key_up()` events) would allow a second submission after the pending event is complete.
            js: optional frontend js method to run before running 'fn'. Input arguments for js method are values of 'inputs' and 'outputs', return should be a list of values for output components.
            concurrency_limit: if set, this is the maximum number of this event that can be running simultaneously. Can be set to None to mean no concurrency_limit (any number of this event can be running simultaneously). Set to "default" to use the default concurrency limit (defined by the `default_concurrency_limit` parameter in `Blocks.queue()`, which itself is 1 by default).
            concurrency_id: if set, this is the id of the concurrency group. Events with the same concurrency_id will be limited by the lowest set concurrency_limit.
            show_api: whether to show this event in the "view API" page of the Gradio app, or in the ".view_api()" method of the Gradio clients. Unlike setting api_name to False, setting show_api to False will still allow downstream apps as well as the Clients to use this event. If fn is None, show_api will automatically be set to False.
        
        """
        ...
    
    def clear(self,
        fn: Callable[..., Any] | None = None,
        inputs: Block | Sequence[Block] | set[Block] | None = None,
        outputs: Block | Sequence[Block] | None = None,
        api_name: str | None | Literal[False] = None,
        scroll_to_output: bool = False,
        show_progress: Literal["full", "minimal", "hidden"] = "full",
        show_progress_on: Component | Sequence[Component] | None = None,
        queue: bool | None = None,
        batch: bool = False,
        max_batch_size: int = 4,
        preprocess: bool = True,
        postprocess: bool = True,
        cancels: dict[str, Any] | list[dict[str, Any]] | None = None,
        every: Timer | float | None = None,
        trigger_mode: Literal["once", "multiple", "always_last"] | None = None,
        js: str | Literal[True] | None = None,
        concurrency_limit: int | None | Literal["default"] = "default",
        concurrency_id: str | None = None,
        show_api: bool = True,
    
        ) -> Dependency:
        """
        Parameters:
            fn: the function to call when this event is triggered. Often a machine learning model's prediction function. Each parameter of the function corresponds to one input component, and the function should return a single value or a tuple of values, with each element in the tuple corresponding to one output component.
            inputs: list of gradio.components to use as inputs. If the function takes no inputs, this should be an empty list.
            outputs: list of gradio.components to use as outputs. If the function returns no outputs, this should be an empty list.
            api_name: defines how the endpoint appears in the API docs. Can be a string, None, or False. If False, the endpoint will not be exposed in the api docs. If set to None, will use the functions name as the endpoint route. If set to a string, the endpoint will be exposed in the api docs with the given name.
            scroll_to_output: if True, will scroll to output component on completion
            show_progress: how to show the progress animation while event is running: "full" shows a spinner which covers the output component area as well as a runtime display in the upper right corner, "minimal" only shows the runtime display, "hidden" shows no progress animation at all
            show_progress_on: Component or list of components to show the progress animation on. If None, will show the progress animation on all of the output components.
            queue: if True, will place the request on the queue, if the queue has been enabled. If False, will not put this event on the queue, even if the queue has been enabled. If None, will use the queue setting of the gradio app.
            batch: if True, then the function should process a batch of inputs, meaning that it should accept a list of input values for each parameter. The lists should be of equal length (and be up to length `max_batch_size`). The function is then *required* to return a tuple of lists (even if there is only 1 output component), with each list in the tuple corresponding to one output component.
            max_batch_size: maximum number of inputs to batch together if this is called from the queue (only relevant if batch=True)
            preprocess: if False, will not run preprocessing of component data before running 'fn' (e.g. leaving it as a base64 string if this method is called with the `Image` component).
            postprocess: if False, will not run postprocessing of component data before returning 'fn' output to the browser.
            cancels: a list of other events to cancel when this listener is triggered. For example, setting cancels=[click_event] will cancel the click_event, where click_event is the return value of another components .click method. Functions that have not yet run (or generators that are iterating) will be cancelled, but functions that are currently running will be allowed to finish.
            every: continously calls `value` to recalculate it if `value` is a function (has no effect otherwise). Can provide a Timer whose tick resets `value`, or a float that provides the regular interval for the reset Timer.
            trigger_mode: if "once" (default for all events except `.change()`) would not allow any submissions while an event is pending. If set to "multiple", unlimited submissions are allowed while pending, and "always_last" (default for `.change()` and `.key_up()` events) would allow a second submission after the pending event is complete.
            js: optional frontend js method to run before running 'fn'. Input arguments for js method are values of 'inputs' and 'outputs', return should be a list of values for output components.
            concurrency_limit: if set, this is the maximum number of this event that can be running simultaneously. Can be set to None to mean no concurrency_limit (any number of this event can be running simultaneously). Set to "default" to use the default concurrency limit (defined by the `default_concurrency_limit` parameter in `Blocks.queue()`, which itself is 1 by default).
            concurrency_id: if set, this is the id of the concurrency group. Events with the same concurrency_id will be limited by the lowest set concurrency_limit.
            show_api: whether to show this event in the "view API" page of the Gradio app, or in the ".view_api()" method of the Gradio clients. Unlike setting api_name to False, setting show_api to False will still allow downstream apps as well as the Clients to use this event. If fn is None, show_api will automatically be set to False.
        
        """
        ... 