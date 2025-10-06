"""
MCP Chatbot - Streamlit Version
A beautiful chatbot interface that connects to your LangChain MCP server
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Fuse Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background-image: linear-gradient(135deg, #f8f9fa 0%, #e2e6ea 100%);
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e2e6ea;
        color: #222;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f8f9fa;
        color: #222;
        margin-right: 20%;
    }
    .error-message {
        background-color: #c53030;
        color: white;
    }
    .message-time {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.5rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #e2e6ea;
        color: #222;
    }
    .connection-status {
        padding: 0.5rem;
        border-radius: 0.25rem;
        text-align: center;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .status-connected {
        background-color: #38a169;
        color: white;
    }
    .status-error {
        background-color: #c53030;
        color: white;
    }
    .status-unknown {
        background-color: #718096;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session-{int(time.time() * 1000)}"
if 'connection_status' not in st.session_state:
    st.session_state.connection_status = 'unknown'
if 'debug_logs' not in st.session_state:
    st.session_state.debug_logs = []

# Helper functions
def add_debug_log(message, log_type='info'):
    """Add a debug log entry"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    st.session_state.debug_logs.append({
        'time': timestamp,
        'type': log_type,
        'message': message
    })
    print(f"[{log_type.upper()}] {message}")

def call_mcp_tool(server_url, tool_name, arguments):
    """Call an MCP tool on the server"""
    try:
        request_body = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        add_debug_log(f"Calling tool: {tool_name}", 'info')
        add_debug_log(f"Request: {json.dumps(request_body, indent=2)}", 'info')
        
        response = requests.post(
            server_url,
            json=request_body,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        add_debug_log(f"Response status: {response.status_code}", 'info')
        add_debug_log(f"Response: {response.text}", 'info')
        
        data = response.json()
        
        if 'error' in data:
            raise Exception(data['error'].get('message', str(data['error'])))
        
        return data['result']
    
    except requests.exceptions.Timeout:
        raise Exception("Request timed out. The server took too long to respond.")
    except requests.exceptions.ConnectionError:
        raise Exception("Connection failed. Check your server URL.")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

def test_connection(server_url):
    """Test connection to MCP server"""
    try:
        add_debug_log(f"Testing connection to: {server_url}", 'info')
        
        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = requests.post(
            server_url,
            json=request_body,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        add_debug_log(f"Response status: {response.status_code}", 'info')
        data = response.json()
        
        if 'error' in data:
            add_debug_log(f"Server error: {json.dumps(data['error'])}", 'error')
            return False, f"Server error: {data['error'].get('message', 'Unknown error')}"
        
        if 'result' in data:
            server_name = data['result'].get('serverInfo', {}).get('name', 'Unknown')
            add_debug_log(f"✓ Connection successful! Server: {server_name}", 'success')
            return True, f"Connected to {server_name}"
        
        return False, "Unexpected response format"
    
    except Exception as e:
        add_debug_log(f"Connection failed: {str(e)}", 'error')
        return False, str(e)

# Sidebar configuration
with st.sidebar:
    st.title("⚙️ Settings")
    
    # Server configuration
    st.subheader("MCP Server")
    server_url = st.text_input(
        "Server URL",
        value=st.session_state.get('server_url', ''),
        placeholder="https://your-api-gateway-url.com/prod",
        help="Your AWS API Gateway endpoint"
    )
    st.session_state.server_url = server_url
    
    if st.button("🔌 Test Connection"):
        if server_url:
            with st.spinner("Testing connection..."):
                success, message = test_connection(server_url)
                if success:
                    st.session_state.connection_status = 'connected'
                    st.success(message)
                else:
                    st.session_state.connection_status = 'error'
                    st.error(message)
        else:
            st.warning("Please enter a server URL first")
    
    # Connection status indicator
    status = st.session_state.connection_status
    if status == 'connected':
        st.markdown('<div class="connection-status status-connected">✓ Connected</div>', 
                   unsafe_allow_html=True)
    elif status == 'error':
        st.markdown('<div class="connection-status status-error">✗ Connection Failed</div>', 
                   unsafe_allow_html=True)
    else:
        st.markdown('<div class="connection-status status-unknown">⚬ Not Tested</div>', 
                   unsafe_allow_html=True)
    
    st.divider()
    
    # LLM configuration
    st.subheader("LLM Settings")
    provider = st.selectbox(
        "Provider",
        ["openai", "anthropic"],
        help="Choose your LLM provider"
    )
    
    model = st.text_input(
        "Model",
        value="gpt-3.5-turbo" if provider == "openai" else "claude-3-sonnet-20240229",
        help="Specific model to use"
    )
    
    use_memory = st.checkbox(
        "Use Conversation Memory",
        value=True,
        help="Remember previous messages in the conversation"
    )
    
    st.divider()
    
    # Session info
    st.subheader("Session Info")
    st.text(f"Session ID: ...{st.session_state.session_id[-8:]}")
    st.text(f"Messages: {len(st.session_state.messages)}")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🔄 New Session"):
        st.session_state.messages = []
        st.session_state.session_id = f"session-{int(time.time() * 1000)}"
        st.rerun()
    
    st.divider()
    
    # Debug toggle
    show_debug = st.checkbox("Show Debug Logs", value=False)

# Main chat interface
st.title("🤖 Fuse Chatbot")

# Display chat messages
chat_container = st.container()
with chat_container:
    if len(st.session_state.messages) == 0:
        st.info("""
        👋 Welcome to the Fuse Chatbot!
        """)
    
    for message in st.session_state.messages:
        role = message['role']
        content = message['content']
        timestamp = message['timestamp']
        is_error = message.get('is_error', False)
        
        if role == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <div><strong>👤 You</strong></div>
                <div>{content}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            css_class = "error-message" if is_error else "assistant-message"
            icon = "❌" if is_error else "🤖"
            st.markdown(f"""
            <div class="chat-message {css_class}">
                <div><strong>{icon} Assistant</strong></div>
                <div>{content}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    if not server_url:
        st.error("⚠️ Please configure your MCP Server URL in the sidebar first!")
    else:
        # Add user message
        timestamp = datetime.now().strftime('%I:%M %p')
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input,
            'timestamp': timestamp
        })
        
        # Get bot response
        with st.spinner("🤔 Thinking..."):
            try:
                # Choose tool based on memory setting
                if use_memory:
                    tool_name = "conversation_with_memory"
                    arguments = {
                        "message": user_input,
                        "sessionId": st.session_state.session_id,
                        "provider": provider
                    }
                else:
                    tool_name = "chat"
                    arguments = {
                        "message": user_input,
                        "provider": provider,
                        "model": model
                    }
                
                # Call MCP tool
                result = call_mcp_tool(server_url, tool_name, arguments)
                
                # Extract response
                response_text = result['content'][0]['text']
                
                # Add assistant message
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': response_text,
                    'timestamp': datetime.now().strftime('%I:%M %p'),
                    'is_error': False
                })
                
            except Exception as e:
                # Add error message
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': f"Error: {str(e)}\n\nPlease check your server URL and API keys.",
                    'timestamp': datetime.now().strftime('%I:%M %p'),
                    'is_error': True
                })
        
        # Rerun to display new messages
        st.rerun()

# Debug logs (if enabled)
if show_debug and len(st.session_state.debug_logs) > 0:
    st.divider()
    st.subheader("🐛 Debug Logs")
    
    if st.button("Clear Debug Logs"):
        st.session_state.debug_logs = []
        st.rerun()
    
    for log in st.session_state.debug_logs[-20:]:  # Show last 20 logs
        log_color = {
            'error': '🔴',
            'success': '🟢',
            'info': '🔵'
        }.get(log['type'], '⚪')
        
        st.text(f"{log_color} [{log['time']}] {log['message']}")