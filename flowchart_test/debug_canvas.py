#!/usr/bin/env python3

import gradio as gr
from flowchart_component import FlowchartCreator

def test_simple_interaction():
    """Test the canvas with minimal setup"""
    creator = FlowchartCreator()
    
    # Simple test data
    test_data = {
        "nodes": [
            {
                "id": "1",
                "type": "start",
                "position": {"x": 50, "y": 50},
                "data": {"label": "Start"}
            },
            {
                "id": "2", 
                "type": "process",
                "position": {"x": 50, "y": 150},
                "data": {"label": "Click Me!"}
            }
        ],
        "edges": [
            {
                "id": "e1-2",
                "source": "1",
                "target": "2",
                "label": "Click This Edge!"
            }
        ]
    }
    
    def handle_action(action_data):
        print(f"🎯 ACTION RECEIVED: {action_data}")
        if action_data:
            return f"✅ Action received: {action_data}"
        return "❌ No action data received"
    
    with gr.Blocks() as demo:
        gr.Markdown("# Debug Canvas Test")
        gr.Markdown("**Instructions:** Click on nodes, edges, or background. Check browser console (F12) for detailed logs.")
        
        # Hidden action input - this is what the JavaScript will target
        canvas_action = gr.Textbox(
            value="", 
            visible=False, 
            elem_id="canvas_action",
            label="Canvas Action"
        )
        
        # Display
        flowchart_html = gr.HTML(
            value=creator.render_interactive_flowchart(test_data),
            label="Test Canvas"
        )
        
        # Debug output
        debug_output = gr.Textbox(
            label="Debug Output",
            value="Waiting for interactions...",
            lines=5,
            interactive=False
        )
        
        # Additional debug info
        input_debug = gr.Textbox(
            label="Input Debug (shows raw input)",
            value="",
            lines=2,
            interactive=False
        )
        
        # Connect the action handler - FIX: only one output
        canvas_action.change(
            handle_action,
            inputs=[canvas_action],
            outputs=[debug_output]
        )
        
        # Also show the raw input for debugging
        canvas_action.change(
            lambda x: f"Raw input: {x}",
            inputs=[canvas_action],
            outputs=[input_debug]
        )
    
    return demo

if __name__ == "__main__":
    demo = test_simple_interaction()
    demo.launch(debug=True, server_port=7861) 