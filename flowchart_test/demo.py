import gradio as gr
from flowchart_component import FlowchartCreator
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from interactive_features import FlowchartEditor

# Load environment variables
load_dotenv()

# Initialize OpenRouter client using OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def generate_flowchart_from_text(text_input):
    """Generate flowchart from text input using Gemini"""
    if not text_input or not text_input.strip():
        return {
            "nodes": [
                {
                    "id": "error",
                    "type": "process",
                    "position": {"x": 150, "y": 100},
                    "data": {"label": "Please enter some text"}
                }
            ],
            "edges": []
        }
    
    try:
        response = client.chat.completions.create(
            model="openai/chatgpt-4o-latest",
            messages=[{
                "role": "system",
                "content": (
                    "Create a practical, followable flowchart from the given text. "
                    "Focus on actual steps someone would take. "
                    "Return ONLY valid JSON with 'nodes' and 'edges' arrays. "
                    "Rules: "
                    "1. Start with preparation/prerequisites "
                    "2. Break down into clear, actionable steps "
                    "3. Include measurements and timings when relevant "
                    "4. Add quality checks as decision points "
                    "5. Show alternative paths and corrections "
                    "6. End with completion criteria "
                    "Node format: {\"id\": \"1\", \"type\": \"start\", \"position\": {\"x\": 150, \"y\": 50}, \"data\": {\"label\": \"Start\"}} "
                    "Edge format: {\"id\": \"e1-2\", \"source\": \"1\", \"target\": \"2\", \"label\": \"\"} "
                    "Keep steps clear and concise."
                )
            }, {
                "role": "user",
                "content": f"Create a practical flowchart showing how to: {text_input[:600]}"
            }],
            temperature=0.4,
            max_tokens=2500,
            extra_headers={
                "HTTP-Referer": "http://localhost:7860",
                "X-Title": "AI Flowchart Creator",
            }
        )
        
        content = response.choices[0].message.content
        
        if not content or not content.strip():
            raise ValueError("Empty response from API")
        
        content = content.strip()
        print(f"Raw API response: {content[:300]}...")  # Debug output
        
        # Try to extract JSON from the response
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        
        # Clean up any remaining markdown or extra text
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Find JSON-like content if it's embedded in text
        if not content.startswith("{"):
            json_start = content.find("{")
            if json_start != -1:
                content = content[json_start:]
        
        if not content.endswith("}"):
            json_end = content.rfind("}")
            if json_end != -1:
                content = content[:json_end + 1]
        
        print(f"Cleaned content: {content[:300]}...")  # Debug output
        
        # Parse and validate the JSON
        flowchart_data = json.loads(content)
        
        # Ensure proper structure
        if "nodes" not in flowchart_data:
            flowchart_data["nodes"] = []
        if "edges" not in flowchart_data:
            flowchart_data["edges"] = []
        
        # If we got a simple flowchart (less than 4 nodes), enhance it
        if len(flowchart_data["nodes"]) < 4:
            return enhance_simple_flowchart(flowchart_data, text_input)
        
        # Validate and enhance nodes
        for i, node in enumerate(flowchart_data["nodes"]):
            if "id" not in node:
                node["id"] = str(i + 1)
            if "type" not in node:
                node["type"] = "process"
            if "position" not in node:
                # Smart positioning based on node type and flow
                if node["type"] == "start":
                    node["position"] = {"x": 150, "y": 50}
                elif node["type"] == "end":
                    node["position"] = {"x": 150, "y": 50 + len(flowchart_data["nodes"]) * 100}
                else:
                    node["position"] = {"x": 150, "y": 50 + i * 100}
            if "data" not in node:
                node["data"] = {"label": f"Step {i + 1}"}
        
        # Validate edges
        valid_edges = []
        for i, edge in enumerate(flowchart_data["edges"]):
            if "id" not in edge:
                edge["id"] = f"e{i + 1}"
            if "source" in edge and "target" in edge:
                valid_edges.append(edge)
        flowchart_data["edges"] = valid_edges
        
        return flowchart_data
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Content that failed to parse: {content if 'content' in locals() else 'No content'}")
        return create_detailed_fallback_flowchart(text_input)
    except Exception as e:
        print(f"Error generating flowchart: {e}")
        return create_detailed_fallback_flowchart(text_input)

def enhance_simple_flowchart(flowchart_data, original_text):
    """Enhance a simple flowchart by adding more detailed steps"""
    if not flowchart_data.get("nodes"):
        return create_detailed_fallback_flowchart(original_text)
    
    # Extract key action words from the original text
    words = original_text.lower().split()
    action_words = []
    for word in words:
        if len(word) > 3 and word not in ['the', 'and', 'for', 'with', 'from', 'that', 'this', 'will', 'can', 'may']:
            action_words.append(word.title())
    
    # Create enhanced nodes
    enhanced_nodes = [
        {
            "id": "1",
            "type": "start",
            "position": {"x": 150, "y": 50},
            "data": {"label": "Start Process"}
        },
        {
            "id": "2",
            "type": "process",
            "position": {"x": 150, "y": 150},
            "data": {"label": "Prepare Materials"}
        }
    ]
    
    # Add nodes for each action word
    for i, action in enumerate(action_words[:6], 3):  # Limit to 6 actions
        if i % 2 == 1:  # Add some decision points
            enhanced_nodes.append({
                "id": str(i),
                "type": "decision",
                "position": {"x": 150, "y": 50 + i * 100},
                "data": {"label": f"{action}?"}
            })
        else:
            enhanced_nodes.append({
                "id": str(i),
                "type": "process",
                "position": {"x": 150, "y": 50 + i * 100},
                "data": {"label": action[:20]}
            })
    
    # Add quality check
    quality_id = str(len(enhanced_nodes) + 1)
    enhanced_nodes.append({
        "id": quality_id,
        "type": "decision",
        "position": {"x": 150, "y": 50 + len(enhanced_nodes) * 100},
        "data": {"label": "Quality Check?"}
    })
    
    # Add end node
    end_id = str(len(enhanced_nodes) + 1)
    enhanced_nodes.append({
        "id": end_id,
        "type": "end",
        "position": {"x": 150, "y": 50 + len(enhanced_nodes) * 100},
        "data": {"label": "Complete"}
    })
    
    # Create edges
    enhanced_edges = []
    for i in range(len(enhanced_nodes) - 1):
        source_id = enhanced_nodes[i]["id"]
        target_id = enhanced_nodes[i + 1]["id"]
        
        # Add appropriate labels for decision nodes
        if enhanced_nodes[i]["type"] == "decision":
            enhanced_edges.append({
                "id": f"e{source_id}-{target_id}",
                "source": source_id,
                "target": target_id,
                "label": "Yes"
            })
            # Add a "No" path back to previous step if possible
            if i > 1:
                prev_id = enhanced_nodes[i - 1]["id"]
                enhanced_edges.append({
                    "id": f"e{source_id}-{prev_id}",
                    "source": source_id,
                    "target": prev_id,
                    "label": "No"
                })
        else:
            enhanced_edges.append({
                "id": f"e{source_id}-{target_id}",
                "source": source_id,
                "target": target_id,
                "label": ""
            })
    
    return {"nodes": enhanced_nodes, "edges": enhanced_edges}

def create_detailed_fallback_flowchart(text_input):
    """Create a detailed fallback flowchart based on text analysis"""
    # Extract meaningful words for steps
    words = text_input.split()
    meaningful_words = []
    
    for word in words[:10]:  # Take first 10 words
        clean_word = ''.join(c for c in word if c.isalnum())
        if len(clean_word) > 2:
            meaningful_words.append(clean_word.title())
    
    if not meaningful_words:
        meaningful_words = ["Prepare", "Execute", "Verify", "Complete"]
    
    nodes = [
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
            "data": {"label": "Initialize"}
        }
    ]
    
    # Add process nodes
    for i, word in enumerate(meaningful_words[:5], 3):
        nodes.append({
            "id": str(i),
            "type": "process",
            "position": {"x": 150, "y": 50 + i * 100},
            "data": {"label": word[:20]}
        })
    
    # Add a decision point
    decision_id = str(len(nodes) + 1)
    nodes.append({
        "id": decision_id,
        "type": "decision",
        "position": {"x": 150, "y": 50 + len(nodes) * 100},
        "data": {"label": "Success?"}
    })
    
    # Add end node
    end_id = str(len(nodes) + 1)
    nodes.append({
        "id": end_id,
        "type": "end",
        "position": {"x": 150, "y": 50 + len(nodes) * 100},
        "data": {"label": "Complete"}
    })
    
    # Create edges
    edges = []
    for i in range(len(nodes) - 1):
        source_id = nodes[i]["id"]
        target_id = nodes[i + 1]["id"]
        
        if nodes[i]["type"] == "decision":
            edges.append({
                "id": f"e{source_id}-{target_id}",
                "source": source_id,
                "target": target_id,
                "label": "Yes"
            })
        else:
            edges.append({
                "id": f"e{source_id}-{target_id}",
                "source": source_id,
                "target": target_id,
                "label": ""
            })
    
    return {"nodes": nodes, "edges": edges}

def create_error_flowchart(message):
    """Create a simple error flowchart"""
    return {
        "nodes": [
            {
                "id": "error",
                "type": "process",
                "position": {"x": 150, "y": 100},
                "data": {"label": message[:20] + "..."}
            }
        ],
        "edges": []
    }

def generate_flowchart_from_website(url):
    """Generate flowchart from website content"""
    if not url.strip():
        return create_error_flowchart("Please enter a valid URL")
    
    # Create flowchart creator instance to scrape website
    creator = FlowchartCreator()
    website_content = creator.scrape_website_content(url)
    
    if website_content.startswith("Error"):
        return create_error_flowchart("Website error")
    
    # Use the scraped content to generate flowchart with process-focused prompt
    enhanced_prompt = f"""
    Create a step-by-step flowchart from this content:
    
    {website_content[:800]}
    
    Focus on actionable steps and decision points that someone would follow.
    If this is a recipe or process:
    - Start with preparation/prerequisites
    - Include quality checks and decisions
    - Note important measurements or timings
    - End with completion criteria
    - Add alternative paths where relevant
    
    Make it practical and followable.
    """
    
    return generate_flowchart_from_text(enhanced_prompt)

def analyze_flowchart(flowchart_data, question):
    """Analyze flowchart based on user question"""
    if not question.strip():
        return "Please ask a specific question about the flowchart."
    
    try:
        # Simplify flowchart data for analysis
        simplified_data = {
            "nodes": [{"id": n.get("id"), "type": n.get("type"), "label": n.get("data", {}).get("label", "")} 
                     for n in flowchart_data.get("nodes", [])],
            "edges": [{"source": e.get("source"), "target": e.get("target"), "label": e.get("label", "")} 
                     for e in flowchart_data.get("edges", [])]
        }
        
        response = client.chat.completions.create(
            model="google/gemini-flash-1.5",
            messages=[{
                "role": "system",
                "content": (
                    "Analyze the flowchart comprehensively. Consider: "
                    "1. Logical flow and sequence "
                    "2. Missing steps or gaps "
                    "3. Potential improvements "
                    "4. Error handling and edge cases "
                    "5. Efficiency opportunities "
                    "6. Decision point validity "
                    "Provide specific, actionable feedback."
                )
            }, {
                "role": "user",
                "content": f"Flowchart: {json.dumps(simplified_data)}\nQuestion: {question[:300]}"
            }],
            temperature=0.7,
            max_tokens=500,  # Increased for more detailed analysis
            extra_headers={
                "HTTP-Referer": "http://localhost:7860",
                "X-Title": "AI Flowchart Creator",
            }
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error analyzing flowchart: {str(e)}"

# Create the Gradio interface
with gr.Blocks(title="AI Flowchart Creator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔄 AI Flowchart Creator")
    gr.Markdown("Create detailed, comprehensive flowcharts with AI assistance!")
    
    # Initialize editors
    flowchart_creator = FlowchartCreator()
    flowchart_editor = FlowchartEditor()
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ✨ Generate Detailed Flowchart")
            
            with gr.Tabs():
                with gr.TabItem("📝 From Text"):
                    text_input = gr.Textbox(
                        label="Describe your process in detail",
                        placeholder="e.g., Complete process for making coffee including preparation, brewing, and cleanup",
                        lines=5,
                        max_lines=8
                    )
                    generate_text_btn = gr.Button("🎯 Generate Detailed Flowchart", variant="primary")
                    
                    # Add example buttons
                    with gr.Row():
                        example_btn1 = gr.Button("☕ Coffee Example", size="sm")
                        example_btn2 = gr.Button("🏠 Home Buying", size="sm")
                        example_btn3 = gr.Button("💻 Software Deploy", size="sm")
                
                with gr.TabItem("🌐 From Website"):
                    url_input = gr.Textbox(
                        label="Website URL",
                        placeholder="e.g., https://example.com/how-to-guide",
                        lines=1
                    )
                    generate_web_btn = gr.Button("🕷️ Generate from Website", variant="primary")
            
            gr.Markdown("### 🤔 Analyze & Improve")
            question_input = gr.Textbox(
                label="Ask detailed questions about the flowchart",
                placeholder="e.g., What edge cases are missing? How can efficiency be improved?",
                lines=3,
                max_lines=4
            )
            analyze_btn = gr.Button("🔍 Detailed Analysis", variant="secondary")
            
            analysis_output = gr.Textbox(
                label="Comprehensive Analysis",
                lines=8,
                interactive=False
            )
            
            # Add editing section
            gr.Markdown("### ✏️ Edit Flowchart")
            with gr.Row():
                node_id_input = gr.Textbox(
                    label="Node ID",
                    placeholder="Enter node ID to edit"
                )
                new_label_input = gr.Textbox(
                    label="New Label",
                    placeholder="Enter new label"
                )
                edit_node_btn = gr.Button("✏️ Edit Node", size="sm")
            
            with gr.Row():
                source_id_input = gr.Textbox(
                    label="Source ID",
                    placeholder="Start node ID"
                )
                target_id_input = gr.Textbox(
                    label="Target ID",
                    placeholder="End node ID"
                )
                edge_label_input = gr.Textbox(
                    label="Edge Label",
                    placeholder="Optional edge label"
                )
                connect_btn = gr.Button("🔗 Connect Nodes", size="sm")
            
            with gr.Row():
                delete_node_input = gr.Textbox(
                    label="Delete Node",
                    placeholder="Node ID to delete"
                )
                delete_node_btn = gr.Button("🗑️ Delete Node", size="sm", variant="stop")
            
            # Add node type selector
            node_type_dropdown = gr.Dropdown(
                choices=["process", "decision", "start", "end"],
                value="process",
                label="New Node Type"
            )
            new_node_label = gr.Textbox(
                label="New Node Label",
                placeholder="Enter label for new node"
            )
            add_node_btn = gr.Button("➕ Add Node", size="sm")
        
        with gr.Column(scale=2):
            # Create the flowchart interface
            flowchart_interface, flowchart_json, flowchart_html = flowchart_creator.create_interface()
    
    # Connect the functionality
    generate_text_btn.click(
        generate_flowchart_from_text,
        inputs=[text_input],
        outputs=[flowchart_json]
    ).then(
        flowchart_creator.update_visualization,
        inputs=[flowchart_json],
        outputs=[flowchart_html]
    )
    
    # Example button functionality
    example_btn1.click(
        lambda: "Complete coffee making process: Check if coffee beans are available, grind beans to medium consistency, heat water to 195-205°F, set up coffee filter, measure 2 tablespoons coffee per 6oz water, pour hot water slowly over grounds, wait 4-5 minutes for brewing, check if strength is adequate, add milk or sugar if desired, clean equipment after use",
        outputs=[text_input]
    )
    
    example_btn2.click(
        lambda: "Home buying process: Determine budget and get pre-approved for mortgage, research neighborhoods and property types, find a real estate agent, search for properties online and schedule viewings, make offers on suitable properties, negotiate terms and price, arrange home inspection, finalize mortgage application, conduct final walkthrough, sign closing documents and transfer funds, receive keys and take possession",
        outputs=[text_input]
    )
    
    example_btn3.click(
        lambda: "Software deployment process: Review code changes and run automated tests, create deployment package and backup current version, schedule maintenance window, deploy to staging environment first, run integration tests and user acceptance testing, check system performance and logs, deploy to production environment, monitor system metrics and error rates, verify all features working correctly, update documentation and notify stakeholders, rollback if issues detected",
        outputs=[text_input]
    )
    
    generate_web_btn.click(
        generate_flowchart_from_website,
        inputs=[url_input],
        outputs=[flowchart_json]
    ).then(
        flowchart_creator.update_visualization,
        inputs=[flowchart_json],
        outputs=[flowchart_html]
    )
    
    analyze_btn.click(
        analyze_flowchart,
        inputs=[flowchart_json, question_input],
        outputs=[analysis_output]
    )
    
    # Connect editing functionality
    edit_node_btn.click(
        lambda data, id, label: flowchart_editor.edit_node(data, id, label),
        inputs=[flowchart_json, node_id_input, new_label_input],
        outputs=[flowchart_json]
    ).then(
        flowchart_creator.update_visualization,
        inputs=[flowchart_json],
        outputs=[flowchart_html]
    )
    
    connect_btn.click(
        lambda data, src, tgt, lbl: flowchart_editor.connect_nodes(data, src, tgt, lbl),
        inputs=[flowchart_json, source_id_input, target_id_input, edge_label_input],
        outputs=[flowchart_json]
    ).then(
        flowchart_creator.update_visualization,
        inputs=[flowchart_json],
        outputs=[flowchart_html]
    )
    
    delete_node_btn.click(
        lambda data, id: flowchart_editor.delete_node(data, id),
        inputs=[flowchart_json, delete_node_input],
        outputs=[flowchart_json]
    ).then(
        flowchart_creator.update_visualization,
        inputs=[flowchart_json],
        outputs=[flowchart_html]
    )
    
    add_node_btn.click(
        lambda data, type, label: flowchart_editor.add_node(data, type, label),
        inputs=[flowchart_json, node_type_dropdown, new_node_label],
        outputs=[flowchart_json]
    ).then(
        flowchart_creator.update_visualization,
        inputs=[flowchart_json],
        outputs=[flowchart_html]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    ) 