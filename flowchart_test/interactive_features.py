import gradio as gr
import json
from flowchart_nlp import FlowchartNLP

class FlowchartEditor:
    def __init__(self):
        self.selected_node = None
        self.selected_edge = None
        self.nlp_editor = FlowchartNLP()
    
    def edit_node(self, flowchart_data, node_id, new_label):
        """Edit node label"""
        data = json.loads(flowchart_data) if isinstance(flowchart_data, str) else flowchart_data
        
        for node in data.get("nodes", []):
            if node["id"] == node_id:
                node["data"]["label"] = new_label
                break
                
        return data
    
    def add_node(self, flowchart_data, node_type, label, x=150, y=150):
        """Add new node"""
        data = json.loads(flowchart_data) if isinstance(flowchart_data, str) else flowchart_data
        
        new_id = str(len(data.get("nodes", [])) + 1)
        new_node = {
            "id": new_id,
            "type": node_type,
            "position": {"x": x, "y": y},
            "data": {"label": label}
        }
        
        data["nodes"] = data.get("nodes", []) + [new_node]
        return data
    
    def connect_nodes(self, flowchart_data, source_id, target_id, label=""):
        """Connect two nodes with an edge"""
        data = json.loads(flowchart_data) if isinstance(flowchart_data, str) else flowchart_data
        
        new_edge = {
            "id": f"e{source_id}-{target_id}",
            "source": source_id,
            "target": target_id,
            "label": label
        }
        
        data["edges"] = data.get("edges", []) + [new_edge]
        return data
    
    def delete_node(self, flowchart_data, node_id):
        """Delete node and its connected edges"""
        data = json.loads(flowchart_data) if isinstance(flowchart_data, str) else flowchart_data
        
        # Remove node
        data["nodes"] = [n for n in data.get("nodes", []) if n["id"] != node_id]
        
        # Remove connected edges
        data["edges"] = [e for e in data.get("edges", []) 
                        if e["source"] != node_id and e["target"] != node_id]
        
        return data
    
    def delete_edge(self, flowchart_data, edge_id):
        """Delete edge"""
        data = json.loads(flowchart_data) if isinstance(flowchart_data, str) else flowchart_data
        data["edges"] = [e for e in data.get("edges", []) if e["id"] != edge_id]
        return data 

    def edit_with_natural_language(self, flowchart_data, command):
        """Edit flowchart using natural language command"""
        data = json.loads(flowchart_data) if isinstance(flowchart_data, str) else flowchart_data
        updated_data, message = self.nlp_editor.parse_edit_command(data, command)
        return updated_data, message

    def get_improvement_suggestions(self, flowchart_data):
        """Get AI-powered improvement suggestions"""
        data = json.loads(flowchart_data) if isinstance(flowchart_data, str) else flowchart_data
        return self.nlp_editor.suggest_improvements(data) 