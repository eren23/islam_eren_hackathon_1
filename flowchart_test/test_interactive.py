#!/usr/bin/env python3

import json
from flowchart_component import FlowchartCreator

def test_canvas_creation():
    """Test basic canvas creation and interaction setup"""
    creator = FlowchartCreator()
    
    # Test basic initialization
    interface, flowchart_json, flowchart_html = creator.create_interface()
    print("✅ Interface created successfully")
    
    # Test flowchart rendering
    test_data = creator.get_example_flowchart()
    html_output = creator.render_interactive_flowchart(test_data)
    
    # Check if essential JavaScript functions are present
    required_functions = [
        "fcSelectElement_",
        "fcQuickEdit_", 
        "fcStartDrag_",
        "addEventListener"
    ]
    
    for func in required_functions:
        if func in html_output:
            print(f"✅ {func} found in generated HTML")
        else:
            print(f"❌ {func} missing from generated HTML")
    
    # Check for proper canvas ID generation
    if "flowchart-container-" in html_output:
        print("✅ Unique canvas ID generated")
    else:
        print("❌ Canvas ID generation failed")
    
    # Check for event delegation classes
    if "fc-node-" in html_output and "fc-edge-" in html_output:
        print("✅ Event delegation classes found")
    else:
        print("❌ Event delegation classes missing")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_canvas_creation() 