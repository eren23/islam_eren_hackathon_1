#!/usr/bin/env python3

import gradio as gr


def test_basic_communication():
    """Test basic JavaScript to Python communication"""
    
    def handle_test_action(action_data):
        print(f"🎯 PYTHON RECEIVED: {action_data}")
        return f"✅ Python got: {action_data}"
    
    with gr.Blocks(head="""
    <script>
    // Define functions in head section to ensure they load
    function sendTestMessage() {
        console.log('🔥 Button clicked!');
        
        // Find the actual textarea inside the test_input div
        let input = null;
        const testInputDiv = document.getElementById('test_input');
        
        if (testInputDiv) {
            // Look for textarea inside the div
            input = testInputDiv.querySelector('textarea');
            console.log('📍 Found textarea in test_input div:', input);
        }
        
        if (!input) {
            // Fallback: get first available textarea
            const allTextareas = document.querySelectorAll('textarea');
            input = allTextareas[0];
            console.log('📍 Using fallback textarea:', input);
        }
        
        if (input) {
            const data = JSON.stringify({
                type: 'test_click',
                message: 'Hello from JavaScript!',
                timestamp: new Date().toISOString()
            });
            
            // Set the value
            input.value = data;
            console.log('📝 Set textarea value to:', input.value);
            
            // Dispatch events that Gradio listens for
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
            
            // Trigger focus/blur to ensure Gradio notices
            input.focus();
            input.blur();
            
            console.log('🚀 Events dispatched on textarea');
        } else {
            console.error('❌ Could not find any textarea element');
            console.log('Available textareas:', document.querySelectorAll('textarea'));
        }
    }
    
    // Test function to check what's available
    function debugInputs() {
        console.log('🔍 Debugging inputs...');
        const testInputDiv = document.getElementById('test_input');
        console.log('test_input div:', testInputDiv);
        if (testInputDiv) {
            console.log('textarea inside test_input:', testInputDiv.querySelector('textarea'));
        }
        console.log('All textareas:', document.querySelectorAll('textarea'));
    }
    
    // Run debug after page loads
    window.addEventListener('load', function() {
        setTimeout(debugInputs, 1000);
    });
    </script>
    """) as demo:
        gr.Markdown("# Simple Communication Test")
        
        # Hidden input for JavaScript to target
        test_input = gr.Textbox(
            value="", 
            visible=False, 
            elem_id="test_input"
        )
        
        # Simple HTML with buttons
        gr.HTML(
            value="""
            <div style="border: 2px solid #007acc; padding: 20px; 
                        border-radius: 8px; margin: 10px 0;">
                <h3>Communication Test</h3>
                <button onclick="sendTestMessage()" 
                        style="padding: 10px 20px; font-size: 16px; 
                               cursor: pointer; margin: 5px;">
                    🚀 Send Test Message
                </button>
                <button onclick="debugInputs()" 
                        style="padding: 10px 20px; font-size: 16px; 
                               cursor: pointer; margin: 5px;">
                    🔍 Debug Inputs
                </button>
                <p><strong>Instructions:</strong></p>
                <ol>
                    <li>Open browser console (F12)</li>
                    <li>Click "Debug Inputs" to see what's available</li>
                    <li>Click "Send Test Message" to test communication</li>
                    <li>Check if the output below updates</li>
                </ol>
            </div>
            """,
            elem_id="test_html"
        )
        
        # Output display
        output_display = gr.Textbox(
            label="Output",
            value="Waiting for test...",
            interactive=False,
            lines=3
        )
        
        # Raw input display for debugging
        raw_input_display = gr.Textbox(
            label="Raw Input (for debugging)",
            value="",
            interactive=False,
            lines=2
        )
        
        # Connect the handler
        test_input.change(
            handle_test_action,
            inputs=[test_input],
            outputs=[output_display]
        )
        
        # Also show raw input changes
        test_input.change(
            lambda x: f"Raw: {x}",
            inputs=[test_input],
            outputs=[raw_input_display]
        )
    
    return demo


if __name__ == "__main__":
    demo = test_basic_communication()
    demo.launch(debug=True, server_port=7862, show_error=True) 