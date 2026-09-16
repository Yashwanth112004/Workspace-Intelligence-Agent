"""
Workspace Intelligence Agent (WIA) - Streamlit Frontend

AI-powered multi-agent platform that centralizes workplace knowledge,
automates workflows, and provides context-aware assistance.
"""

import streamlit as st
import requests
import json
from datetime import datetime
import uuid

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Workspace Intelligence Agent",
    page_icon="����",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f3e5f5;
        margin-right: 20%;
    }
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton > button {
        width: 100%;
    }
    .document-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .task-card {
        border-left: 4px solid #667eea;
        padding: 0.75rem;
        background-color: #fafafa;
        margin-bottom: 0.5rem;
        border-radius: 4px;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-pending { background-color: #fff3e0; color: #e65100; }
    .status-in-progress { background-color: #e3f2fd; color: #1565c0; }
    .status-completed { background-color: #e8f5e9; color: #2e7d32; }
    .status-failed { background-color: #ffebee; color: #c62828; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents" not in st.session_state:
    st.session_state.documents = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "Chat"
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


def call_api(endpoint: str, method: str = "GET", data: dict | None = None) -> dict:
    """Make API call to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=60)
        else:
            return {"error": "Unsupported method"}

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code} - {response.text}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Make sure the API server is running on port 8000."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except Exception as e:
        return {"error": str(e)}


def render_sidebar():
    """Render the sidebar navigation"""
    with st.sidebar:
        st.markdown("""
        <div class="main-header">
            <h2>���� Workspace Intelligence Agent</h2>
            <p>AI-powered workspace assistant</p>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        pages = ["���� Chat", "���� Document Search", "��� Task Automation", "���� Analytics", "������ Settings"]
        selected_page = st.radio("Navigation", pages, index=pages.index(f"���� {st.session_state.current_page}") if st.session_state.current_page in ["Chat", "Document Search", "Task Automation", "Analytics", "Settings"] else 0)
        st.session_state.current_page = selected_page.split(" ", 1)[1]

        st.divider()

        # Quick stats
        st.markdown("### Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", len(st.session_state.documents))
            st.metric("Active Tasks", len([t for t in st.session_state.tasks if t.get("status") == "in_progress"]))
        with col2:
            st.metric("Messages", len(st.session_state.messages))
            st.metric("Completed Tasks", len([t for t in st.session_state.tasks if t.get("status") == "completed"]))

        st.divider()

        # Backend status
        st.markdown("### Backend Status")
        health = call_api("/health")
        if "error" not in health:
            st.success("��� Connected")
        else:
            st.error("��� Disconnected")
            st.caption(health.get("error", "Unknown error"))

        st.divider()

        # Session info
        st.markdown("### Session")
        st.caption(f"ID: {st.session_state.session_id[:8]}...")
        if st.button("���� New Session"):
            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()


def render_chat_page():
    """Render the main chat interface"""
    st.markdown("""
    <div class="main-header">
        <h1>���� Chat with WIA</h1>
        <p>Ask questions, get insights, and automate tasks with natural language</p>
    </div>
    """, unsafe_allow_html=True)

    # Chat container
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>WIA:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)

                # Show sources if available
                if "sources" in message and message["sources"]:
                    with st.expander("���� Sources"):
                        for src in message["sources"]:
                            st.caption(f"• {src}")

    # Input area
    st.divider()
    col1, col2, col3 = st.columns([6, 1, 1])

    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Ask me anything about your workspace...",
            label_visibility="collapsed",
            key="chat_input"
        )

    with col2:
        send_clicked = st.button("Send", type="primary", use_container_width=True)

    with col3:
        if st.button("������� Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Handle message sending
    if send_clicked and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Call API
        with st.spinner("Thinking..."):
            response = call_api("/chat", "POST", {
                "message": user_input,
                "session_id": st.session_state.session_id
            })

        if "error" not in response:
            assistant_message = {
                "role": "assistant",
                "content": response.get("response", "No response"),
                "sources": response.get("sources", [])
            }
        else:
            assistant_message = {
                "role": "assistant",
                "content": f"��� Error: {response['error']}",
                "sources": []
            }

        st.session_state.messages.append(assistant_message)
        st.rerun()


def render_document_search_page():
    """Render the document search interface"""
    st.markdown("""
    <div class="main-header">
        <h1>���� Document Search</h1>
        <p>Search and explore your workspace knowledge base using semantic search</p>
    </div>
    """, unsafe_allow_html=True)

    # Search bar
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        search_query = st.text_input(
            "Search",
            placeholder="Enter search query...",
            label_visibility="collapsed"
        )
    with col2:
        search_type = st.selectbox("Type", ["Semantic", "Keyword", "Hybrid"], label_visibility="collapsed")
    with col3:
        search_clicked = st.button("���� Search", type="primary", use_container_width=True)

    # Filters
    with st.expander("���� Filters"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.date_input("Date Range", value=[])
        with col2:
            doc_types = st.multiselect("Document Types", ["PDF", "DOCX", "TXT", "MD", "CSV", "XLSX"])
        with col3:
            tags = st.multiselect("Tags", ["meeting", "project", "policy", "report", "code"])

    st.divider()

    # Results
    if search_clicked and search_query:
        with st.spinner("Searching..."):
            response = call_api("/search", "POST", {
                "query": search_query,
                "type": search_type.lower(),
                "filters": {
                    "doc_types": doc_types,
                    "tags": tags
                }
            })

        if "error" not in response:
            results = response.get("results", [])
            st.success(f"Found {len(results)} results")

            for i, doc in enumerate(results):
                with st.container():
                    st.markdown(f"""
                    <div class="document-card">
                        <h4>{doc.get('title', 'Untitled')}</h4>
                        <p>{doc.get('snippet', 'No preview available')}</p>
                        <small>Score: {doc.get('score', 0):.2f} | Type: {doc.get('type', 'Unknown')} |
                        Modified: {doc.get('modified', 'Unknown')}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("���� Open", key=f"open_{i}"):
                            st.info(f"Opening {doc.get('title')}...")
                    with col2:
                        if st.button("���� Copy", key=f"copy_{i}"):
                            st.toast("Copied to clipboard!")
        else:
            st.error(f"Search failed: {response['error']}")
    else:
        # Show recent documents
        st.markdown("### Recent Documents")
        if st.session_state.documents:
            for doc in st.session_state.documents[:10]:
                st.markdown(f"""
                <div class="document-card">
                    <h4>{doc.get('title', 'Untitled')}</h4>
                    <small>Type: {doc.get('type', 'Unknown')} | Modified: {doc.get('modified', 'Unknown')}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No documents indexed yet. Add documents to start searching.")


def render_task_automation_page():
    """Render the task automation interface"""
    st.markdown("""
    <div class="main-header">
        <h1>��� Task Automation</h1>
        <p>Create, manage, and monitor automated workflows</p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["���� My Tasks", "��� Create Task", "���� Workflows"])

    with tab1:
        st.markdown("### Active Tasks")

        # Filter tasks
        status_filter = st.selectbox("Filter by Status", ["All", "pending", "in_progress", "completed", "failed"])

        filtered_tasks = st.session_state.tasks
        if status_filter != "All":
            filtered_tasks = [t for t in st.session_state.tasks if t.get("status") == status_filter]

        if filtered_tasks:
            for task in filtered_tasks:
                status_class = f"status-{task.get('status', 'pending')}"
                st.markdown(f"""
                <div class="task-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{task.get('title', 'Untitled Task')}</strong>
                            <br>
                            <small>{task.get('description', 'No description')}</small>
                        </div>
                        <span class="status-badge {status_class}">{task.get('status', 'pending').replace('_', ' ').title()}</span>
                    </div>
                    <div style="margin-top: 0.5rem; display: flex; gap: 1rem; font-size: 0.8rem; color: #666;">
                        <span>Created: {task.get('created', 'Unknown')}</span>
                        <span>Assigned: {task.get('assignee', 'Unassigned')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("����� Run", key=f"run_{task.get('id')}"):
                        st.toast(f"Starting task {task.get('title')}...")
                with col2:
                    if st.button("������ Pause", key=f"pause_{task.get('id')}"):
                        st.toast("Task paused")
                with col3:
                    if st.button("���� Edit", key=f"edit_{task.get('id')}"):
                        st.session_state.editing_task = task.get('id')
                with col4:
                    if st.button("������� Delete", key=f"delete_{task.get('id')}"):
                        st.session_state.tasks = [t for t in st.session_state.tasks if t.get('id') != task.get('id')]
                        st.rerun()
        else:
            st.info("No tasks found. Create your first task!")

    with tab2:
        st.markdown("### Create New Task")

        with st.form("create_task_form"):
            col1, col2 = st.columns(2)
            with col1:
                task_title = st.text_input("Task Title*", placeholder="e.g., Generate weekly report")
                task_type = st.selectbox("Task Type", [
                    "Document Generation", "Data Analysis", "Email Automation",
                    "Meeting Summary", "Code Review", "Custom"
                ])
            with col2:
                assignee = st.text_input("Assignee", placeholder="Agent or team member")
                priority = st.select_slider("Priority", ["Low", "Medium", "High", "Critical"])

            task_description = st.text_area("Description", placeholder="Describe what this task should do...")

            # Schedule options
            st.markdown("#### Schedule")
            schedule_type = st.radio("Schedule Type", ["Manual", "Recurring", "Trigger-based"], horizontal=True)

            if schedule_type == "Recurring":
                col1, col2 = st.columns(2)
                with col1:
                    _ = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])
                with col2:
                    _ = st.time_input("Time")
            elif schedule_type == "Trigger-based":
                _ = st.text_input("Trigger Condition", placeholder="e.g., New document added to 'Reports' folder")

            # Parameters
            with st.expander("������ Advanced Parameters"):
                params = st.text_area("Parameters (JSON)", placeholder='{"key": "value"}', height=100)

            submitted = st.form_submit_button("Create Task", type="primary", use_container_width=True)

            if submitted and task_title:
                new_task = {
                    "id": str(uuid.uuid4())[:8],
                    "title": task_title,
                    "description": task_description,
                    "type": task_type,
                    "assignee": assignee or "WIA Agent",
                    "priority": priority,
                    "status": "pending",
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "schedule": schedule_type,
                    "params": json.loads(params) if params else {}
                }
                st.session_state.tasks.append(new_task)
                st.success("Task created successfully!")
                st.rerun()

    with tab3:
        st.markdown("### Workflow Templates")
        st.info("Workflow templates coming soon. This will allow you to chain multiple tasks together.")

        # Example workflows
        workflows = [
            {"name": "Weekly Report Generation", "tasks": 3, "status": "Active"},
            {"name": "Meeting Notes Processor", "tasks": 2, "status": "Active"},
            {"name": "Code Review Automation", "tasks": 4, "status": "Draft"},
        ]

        for wf in workflows:
            st.markdown(f"""
            <div class="task-card">
                <strong>{wf['name']}</strong> - {wf['tasks']} tasks -
                <span class="status-badge status-{wf['status'].lower()}">{wf['status']}</span>
            </div>
            """, unsafe_allow_html=True)


def render_analytics_page():
    """Render the analytics dashboard"""
    st.markdown("""
    <div class="main-header">
        <h1>���� Analytics Dashboard</h1>
        <p>Insights into workspace activity and agent performance</p>
    </div>
    """, unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Queries", "1,234", "+12%")
    with col2:
        st.metric("Documents Indexed", "5,678", "+234")
    with col3:
        st.metric("Tasks Automated", "89", "+5")
    with col4:
        st.metric("Time Saved", "120 hrs", "+15 hrs")

    st.divider()

    # Charts placeholder
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Query Volume (Last 30 Days)")
        # Sample data for chart
        import pandas as pd
        import numpy as np

        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        queries = np.random.randint(20, 100, 30)
        df = pd.DataFrame({"Date": dates, "Queries": queries})
        st.line_chart(df.set_index("Date"))

    with col2:
        st.markdown("### Task Completion Rate")
        completion_data = pd.DataFrame({
            "Status": ["Completed", "In Progress", "Pending", "Failed"],
            "Count": [65, 12, 8, 4]
        })
        st.bar_chart(completion_data.set_index("Status"))

    st.divider()

    # Top queries
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Top Search Queries")
        top_queries = [
            ("Q3 budget forecast", 45),
            ("Project Alpha timeline", 38),
            ("Remote work policy", 32),
            ("API documentation", 28),
            ("Security audit results", 24),
        ]
        for query, count in top_queries:
            st.markdown(f"**{query}** - {count} searches")

    with col2:
        st.markdown("### Most Active Users")
        top_users = [
            ("Sarah Chen", 156),
            ("Mike Johnson", 134),
            ("Emily Davis", 112),
            ("James Wilson", 98),
            ("Lisa Anderson", 87),
        ]
        for user, count in top_users:
            st.markdown(f"**{user}** - {count} queries")


def render_settings_page():
    """Render the settings page"""
    st.markdown("""
    <div class="main-header">
        <h1>������ Settings</h1>
        <p>Configure your Workspace Intelligence Agent</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["���� General", "���� AI Models", "���� Integrations", "���� Security"])

    with tab1:
        st.markdown("### General Settings")

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Workspace Name", value="My Workspace")
            st.selectbox("Default Language", ["English", "Spanish", "French", "German", "Japanese"])
            st.selectbox("Timezone", ["UTC", "EST", "PST", "CET", "JST"])
        with col2:
            st.toggle("Auto-save conversations", value=True)
            st.toggle("Enable notifications", value=True)
            st.toggle("Dark mode", value=False)

        st.divider()
        st.markdown("### Data Management")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("���� Export Data", use_container_width=True):
                st.toast("Export started...")
        with col2:
            if st.button("������� Clear Cache", use_container_width=True):
                st.toast("Cache cleared!")
        with col3:
            if st.button("���� Reindex", use_container_width=True):
                st.toast("Reindexing started...")

    with tab2:
        st.markdown("### AI Model Configuration")

        st.markdown("#### Primary Model")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Model Provider", ["Anthropic", "OpenAI", "Local (Ollama)"])
            st.selectbox("Model", ["Claude 3.5 Sonnet", "Claude 3 Opus", "GPT-4o", "GPT-4o-mini"])
        with col2:
            st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
            st.slider("Max Tokens", 1000, 8000, 4000, 500)

        st.divider()
        st.markdown("#### Embedding Model")
        st.selectbox("Embedding Provider", ["Voyage AI", "OpenAI", "Local (Sentence Transformers)"])
        st.selectbox("Model", ["voyage-3-large", "text-embedding-3-large", "all-MiniLM-L6-v2"])

        st.divider()
        st.markdown("#### RAG Settings")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Chunk Size", value=1000, min_value=100, max_value=5000)
            st.number_input("Chunk Overlap", value=200, min_value=0, max_value=1000)
        with col2:
            st.number_input("Top K Results", value=5, min_value=1, max_value=20)
            st.number_input("Similarity Threshold", value=0.7, min_value=0.0, max_value=1.0, step=0.05)

    with tab3:
        st.markdown("### Integrations")

        integrations = [
            {"name": "Slack", "status": "Connected", "icon": "����"},
            {"name": "Microsoft Teams", "status": "Not Connected", "icon": "����"},
            {"name": "Google Drive", "status": "Connected", "icon": "����"},
            {"name": "Notion", "status": "Not Connected", "icon": "����"},
            {"name": "GitHub", "status": "Connected", "icon": "����"},
            {"name": "Jira", "status": "Not Connected", "icon": "����"},
            {"name": "Confluence", "status": "Not Connected", "icon": "����"},
            {"name": "Salesforce", "status": "Not Connected", "icon": "�����"},
        ]

        for integration in integrations:
            col1, col2, col3 = st.columns([1, 4, 2])
            with col1:
                st.markdown(f"### {integration['icon']}")
            with col2:
                st.markdown(f"**{integration['name']}**")
                st.caption(f"Status: {integration['status']}")
            with col3:
                if integration['status'] == "Connected":
                    if st.button("Disconnect", key=f"disc_{integration['name']}"):
                        st.toast(f"Disconnected from {integration['name']}")
                else:
                    if st.button("Connect", key=f"conn_{integration['name']}", type="primary"):
                        st.toast(f"Connecting to {integration['name']}...")

    with tab4:
        st.markdown("### Security & Privacy")

        st.markdown("#### Access Control")
        col1, col2 = st.columns(2)
        with col1:
            st.toggle("Require authentication", value=True)
            st.toggle("SSO enabled", value=False)
            st.toggle("Two-factor authentication", value=True)
        with col2:
            st.selectbox("Session timeout", ["30 min", "1 hour", "4 hours", "8 hours", "Never"])
            st.selectbox("Data retention", ["30 days", "90 days", "1 year", "Custom"])

        st.divider()
        st.markdown("#### API Keys")
        st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
        st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        st.text_input("Voyage AI API Key", type="password", placeholder="pa-...")

        st.divider()
        st.markdown("#### Audit Log")
        if st.button("���� View Audit Log", use_container_width=True):
            st.info("Audit log viewer coming soon")

        st.divider()
        st.markdown("#### Danger Zone")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("������� Delete All Data", type="secondary", use_container_width=True):
                st.warning("This action cannot be undone!")
        with col2:
            if st.button("���� Reset to Defaults", type="secondary", use_container_width=True):
                st.toast("Settings reset to defaults")


# Main app
def main():
    render_sidebar()

    # Route to appropriate page
    if st.session_state.current_page == "Chat":
        render_chat_page()
    elif st.session_state.current_page == "Document Search":
        render_document_search_page()
    elif st.session_state.current_page == "Task Automation":
        render_task_automation_page()
    elif st.session_state.current_page == "Analytics":
        render_analytics_page()
    elif st.session_state.current_page == "Settings":
        render_settings_page()


if __name__ == "__main__":
    main()