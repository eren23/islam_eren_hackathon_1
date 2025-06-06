from openai import OpenAI
import json
import os
from typing import Dict, List, Tuple, Optional
import re

class FlowchartNLP:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def parse_edit_command(self, flowchart_data: dict, command: str) -> Tuple[dict, str]:
        """Parse natural language command to edit flowchart"""
        try:
            response = self.client.chat.completions.create(
                model="openai/chatgpt-4o-latest",
                messages=[{
                    "role": "system",
                    "content": (
                        "You are a flowchart editing assistant. Parse the command "
                        "and return ONLY a JSON object that matches this schema:\n"
                        "{\n"
                        '  "operation": "add_node|edit_node|delete_node|'
                        'connect_nodes|delete_edge",\n'
                        '  "node": {  // for add_node\n'
                        '    "id": "string",\n'
                        '    "type": "process|decision|start|end",\n'
                        '    "position": {"x": number, "y": number},\n'
                        '    "data": {"label": "string"}\n'
                        '  },\n'
                        '  "node_id": "string",  // for edit_node/delete_node\n'
                        '  "new_label": "string",  // for edit_node\n'
                        '  "edge": {  // for connect_nodes\n'
                        '    "id": "string",\n'
                        '    "source": "string",\n'
                        '    "target": "string",\n'
                        '    "label": "string"\n'
                        '  },\n'
                        '  "edge_id": "string"  // for delete_edge\n'
                        "}\n"
                        'Example: {"operation": "add_node", '
                        '"node": {"id": "3", "type": "decision", '
                        '"position": {"x": 150, "y": 250}, '
                        '"data": {"label": "Check temperature"}}}'
                    )
                }, {
                    "role": "user",
                    "content": (f"Current flowchart: {json.dumps(flowchart_data)}\n\n"
                               f"Command: {command}")
                }],
                temperature=0.1,
                max_tokens=500,
                extra_headers={
                    "HTTP-Referer": "http://localhost:7860", 
                    "X-Title": "AI Flowchart Creator"
                }
            )

            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response if it's embedded in text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            try:
                edit_operation = json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to create a basic operation
                words = command.lower().split()
                if any(word in words for word in ['add', 'create', 'new']):
                    new_id = str(len(flowchart_data.get("nodes", [])) + 1)
                    edit_operation = {
                        "operation": "add_node",
                        "node": {
                            "id": new_id,
                            "type": "process",
                            "position": {"x": 150, "y": 150},
                            "data": {"label": command}
                        }
                    }
                elif any(word in words for word in ['edit', 'change', 'modify']):
                    edit_operation = {
                        "operation": "edit_node",
                        "node_id": "1",
                        "new_label": command
                    }
                else:
                    raise ValueError("Could not parse command into valid operation")

            return self.apply_edit_operation(flowchart_data, edit_operation)
        except Exception as e:
            print(f"Error in parse_edit_command: {str(e)}")
            print(f"Response content: {content if 'content' in locals() else 'No content'}")
            return flowchart_data, f"Error parsing command: {str(e)}"

    def apply_edit_operation(self, flowchart_data: dict, operation: dict) -> Tuple[dict, str]:
        """Apply the parsed edit operation to the flowchart"""
        try:
            op_type = operation.get("operation", "").lower()
            
            if op_type == "add_node":
                node = operation.get("node", {})
                if not node:
                    # Create default node if not provided
                    new_id = str(len(flowchart_data.get("nodes", [])) + 1)
                    y_pos = 50 + (len(flowchart_data.get("nodes", [])) * 100)
                    node = {
                        "id": new_id,
                        "type": "process",
                        "position": {"x": 150, "y": y_pos},
                        "data": {"label": "New Node"}
                    }
                
                flowchart_data["nodes"] = flowchart_data.get("nodes", []) + [node]
                return (flowchart_data, 
                       f"Added new {node['type']} node: {node['data']['label']}")

            elif op_type == "edit_node":
                node_id = operation.get("node_id")
                new_label = operation.get("new_label")
                
                for node in flowchart_data.get("nodes", []):
                    if node["id"] == node_id:
                        old_label = node["data"]["label"]
                        node["data"]["label"] = new_label
                        return (flowchart_data, 
                               f"Updated node {node_id} from '{old_label}' "
                               f"to '{new_label}'")
                
                return flowchart_data, f"Node {node_id} not found"

            elif op_type == "delete_node":
                node_id = operation.get("node_id")
                nodes = flowchart_data.get("nodes", [])
                edges = flowchart_data.get("edges", [])
                
                # Find node to delete
                node_to_delete = next((n for n in nodes if n["id"] == node_id), 
                                    None)
                if not node_to_delete:
                    return flowchart_data, f"Node {node_id} not found"
                
                # Remove node and connected edges
                flowchart_data["nodes"] = [n for n in nodes 
                                         if n["id"] != node_id]
                flowchart_data["edges"] = [
                    e for e in edges 
                    if e["source"] != node_id and e["target"] != node_id
                ]
                
                return (flowchart_data, 
                       f"Deleted node {node_id} and its connections")

            elif op_type == "connect_nodes":
                edge = operation.get("edge", {})
                if not edge:
                    return flowchart_data, "No edge information provided"
                
                source_id = edge.get("source")
                target_id = edge.get("target")
                label = edge.get("label", "")
                
                # Verify nodes exist
                nodes = flowchart_data.get("nodes", [])
                source_exists = any(n["id"] == source_id for n in nodes)
                target_exists = any(n["id"] == target_id for n in nodes)
                
                if not (source_exists and target_exists):
                    return flowchart_data, "One or both nodes not found"
                
                edge_id = edge.get("id", f"e{source_id}-{target_id}")
                new_edge = {
                    "id": edge_id,
                    "source": source_id,
                    "target": target_id,
                    "label": label
                }
                flowchart_data["edges"] = (flowchart_data.get("edges", []) + 
                                          [new_edge])
                return (flowchart_data, 
                       f"Connected node {source_id} to node {target_id}")

            elif op_type == "delete_edge":
                edge_id = operation.get("edge_id")
                if not edge_id:
                    return flowchart_data, "No edge ID provided"
                
                original_edges = flowchart_data.get("edges", [])
                flowchart_data["edges"] = [e for e in original_edges 
                                         if e["id"] != edge_id]
                
                if len(flowchart_data["edges"]) < len(original_edges):
                    return flowchart_data, f"Deleted edge {edge_id}"
                return flowchart_data, f"Edge {edge_id} not found"

            return flowchart_data, f"Unknown operation type: {op_type}"
            
        except Exception as e:
            print(f"Error in apply_edit_operation: {str(e)}")
            return flowchart_data, f"Error applying edit: {str(e)}"

    def suggest_improvements(self, flowchart_data: dict) -> List[str]:
        """Suggest potential improvements for the flowchart"""
        try:
            response = self.client.chat.completions.create(
                model="openai/chatgpt-4o-latest",
                messages=[{
                    "role": "system",
                    "content": (
                        "Analyze the flowchart and suggest specific improvements. "
                        "Consider:\n"
                        "1. Missing decision points or error handling\n"
                        "2. Unclear or ambiguous steps\n"
                        "3. Potential parallel processes\n"
                        "4. Missing connections or feedback loops\n"
                        "5. Optimization opportunities\n"
                        "Return a numbered list of specific, actionable suggestions."
                    )
                }, {
                    "role": "user",
                    "content": f"Analyze this flowchart: {json.dumps(flowchart_data)}"
                }],
                temperature=0.4,
                max_tokens=500,
                extra_headers={
                    "HTTP-Referer": "http://localhost:7860",
                    "X-Title": "AI Flowchart Creator"
                }
            )

            suggestions = response.choices[0].message.content.split("\n")
            return [s.strip() for s in suggestions if s.strip()]
        except Exception as e:
            print(f"Error in suggest_improvements: {str(e)}")
            return [f"Error generating suggestions: {str(e)}"] 