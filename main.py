import streamlit as st
from agent.graph import build_graph


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Autonomous AI Codebase Agent",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #0b0d12;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.5px;
    }


    /* ---------- SIDEBAR ---------- */

    section[data-testid="stSidebar"] {
        background: #11141b;
        border-right: 1px solid #242936;
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 1.45rem;
    }


    /* ---------- HERO ---------- */

    .hero {
        padding: 2.2rem 2.4rem;
        border-radius: 18px;
        border: 1px solid #252b38;
        background:
            linear-gradient(
                135deg,
                #151923 0%,
                #0f1219 55%,
                #10151d 100%
            );
        margin-bottom: 1.8rem;
    }

    .hero-label {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 2px;
        color: #8b95a7;
        margin-bottom: 0.7rem;
    }

    .hero-title {
        font-size: 2.7rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.8rem;
        color: #f4f6fa;
    }

    .hero-description {
        color: #9ba5b5;
        font-size: 1rem;
        line-height: 1.6;
        max-width: 760px;
    }

    .online {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        margin-top: 1.2rem;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: #151c18;
        border: 1px solid #27352c;
        color: #9fd3ad;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .online-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #5bd27c;
        display: inline-block;
    }


    /* ---------- SECTION LABEL ---------- */

    .section-label {
        color: #7f8999;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }


    /* ---------- PROMPT CARDS ---------- */

    .prompt-card {
        background: #12161e;
        border: 1px solid #252b37;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        min-height: 78px;
    }

    .prompt-card-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #dce1e9;
        margin-bottom: 0.35rem;
    }

    .prompt-card-text {
        font-size: 0.74rem;
        color: #7f8999;
        line-height: 1.45;
    }


    /* ---------- WORKFLOW ---------- */

    .workflow {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 1.3rem;
        background: #10141b;
        border: 1px solid #252b37;
        border-radius: 14px;
        margin: 1rem 0 1.5rem 0;
        overflow-x: auto;
    }

    .workflow-step {
        padding: 0.55rem 0.8rem;
        border-radius: 8px;
        background: #181d26;
        border: 1px solid #2a303d;
        color: #b7bfcc;
        font-size: 0.76rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .workflow-arrow {
        color: #596272;
        font-size: 0.9rem;
    }


    /* ---------- ANSWER ---------- */

    .answer-card {
        background: #11161e;
        border: 1px solid #29303d;
        border-radius: 15px;
        padding: 1.4rem 1.5rem;
        margin-top: 0.8rem;
    }

    .answer-label {
        color: #8993a4;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1.3px;
        text-transform: uppercase;
        margin-bottom: 0.8rem;
    }


    /* ---------- METRIC CARDS ---------- */

    .metric-card {
        background: #11151d;
        border: 1px solid #252b37;
        border-radius: 12px;
        padding: 1rem 1.1rem;
    }

    .metric-label {
        color: #7e8797;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-value {
        color: #edf0f5;
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 0.25rem;
    }


    /* ---------- BUTTON ---------- */

    .stButton > button {
        border-radius: 10px;
        min-height: 3rem;
        font-weight: 700;
        border: 1px solid #343b49;
    }


    /* ---------- TEXT AREA ---------- */

    textarea {
        background: #11151d !important;
        border: 1px solid #303745 !important;
        border-radius: 12px !important;
    }


    /* ---------- INFO BOX ---------- */

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD AGENT
# ============================================================

@st.cache_resource
def load_agent():
    return build_graph()


app = load_agent()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Codebase Agent")

    st.caption("Autonomous AI Engineering")

    st.divider()

    st.markdown(
        '<div class="section-label">Capabilities</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        **Codebase Search**

        **Code Analysis**

        **Tool Selection**

        **Code Modification**

        **Test Execution**

        **Validation**
        """
    )

    st.divider()

    st.markdown(
        '<div class="section-label">Technology Stack</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        **LangGraph**  
        Agent orchestration

        **Qdrant**  
        Vector retrieval

        **MiniLM**  
        Code embeddings

        **Qwen**  
        Language model
        """
    )

    st.divider()

    st.caption("Autonomous AI Codebase Engineering Agent")


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-label">
            AUTONOMOUS AI CODEBASE ENGINEERING
        </div>

        <div class="hero-title">
            Build. Analyze. Modify. Validate.
        </div>

        <div class="hero-description">
            An autonomous LangGraph agent that understands your
            codebase, retrieves relevant code, selects tools,
            performs engineering tasks, runs tests, and validates
            the result.
        </div>

        <div class="online">
            <span class="online-dot"></span>
            Agent Ready
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ASK CODEBASE
# ============================================================

st.markdown(
    '<div class="section-label">Codebase Interface</div>',
    unsafe_allow_html=True,
)

st.subheader("Ask Your Codebase")

question = st.text_area(
    "Enter your request",
    placeholder=(
        "Ask about your codebase...\n\n"
        "Example: Why is QdrantClient used in this project?"
    ),
    height=140,
    label_visibility="collapsed",
)


# ============================================================
# EXAMPLE PROMPTS
# ============================================================

st.markdown(
    '<div class="section-label">Try an Example</div>',
    unsafe_allow_html=True,
)

p1, p2, p3, p4 = st.columns(4)

with p1:
    st.markdown(
        """
        <div class="prompt-card">
            <div class="prompt-card-title">Analyze Code</div>
            <div class="prompt-card-text">
                Find functions and explain their purpose.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with p2:
    st.markdown(
        """
        <div class="prompt-card">
            <div class="prompt-card-title">Search Project</div>
            <div class="prompt-card-text">
                Find where QdrantClient is used.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with p3:
    st.markdown(
        """
        <div class="prompt-card">
            <div class="prompt-card-title">Run Test</div>
            <div class="prompt-card-text">
                Verify that greet() returns the expected output.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with p4:
    st.markdown(
        """
        <div class="prompt-card">
            <div class="prompt-card-title">Modify Code</div>
            <div class="prompt-card-text">
                Add a comment or make a requested code change.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")


# ============================================================
# WORKFLOW
# ============================================================

st.markdown(
    '<div class="section-label">Agent Workflow</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="workflow">

        <div class="workflow-step">Analyze</div>
        <div class="workflow-arrow">→</div>

        <div class="workflow-step">Retrieve</div>
        <div class="workflow-arrow">→</div>

        <div class="workflow-step">Select Tool</div>
        <div class="workflow-arrow">→</div>

        <div class="workflow-step">Execute</div>
        <div class="workflow-arrow">→</div>

        <div class="workflow-step">Test</div>
        <div class="workflow-arrow">→</div>

        <div class="workflow-step">Validate</div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# RUN AGENT
# ============================================================

run_agent = st.button(
    "Run Autonomous Agent",
    type="primary",
    use_container_width=True,
)


if run_agent:

    if not question.strip():

        st.warning("Please enter a request first.")
        st.stop()


    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    with st.spinner("Agent is analyzing your codebase..."):

        result = app.invoke(
            {
                "question": question,
                "plan": [],
                "current_task": "",
                "answer": "",
            }
        )


    # ========================================================
    # STATUS
    # ========================================================

    st.success("Agent execution completed successfully.")


    # ========================================================
    # FINAL ANSWER
    # ========================================================

    st.markdown(
        '<div class="section-label">Agent Response</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="answer-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="answer-label">Final Answer</div>',
        unsafe_allow_html=True,
    )

    answer = result.get("answer", "")

    if answer:
        st.markdown(answer)
    else:
        st.info("No final answer was generated.")

    st.markdown("</div>", unsafe_allow_html=True)


    # ========================================================
    # EXECUTION SUMMARY
    # ========================================================

    st.write("")

    st.markdown(
        '<div class="section-label">Execution Summary</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Orchestration</div>
                <div class="metric-value">LangGraph</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Retrieval</div>
                <div class="metric-value">Qdrant</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">LLM</div>
                <div class="metric-value">Qwen</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Status</div>
                <div class="metric-value">Validated</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    # ========================================================
    # EXECUTION DETAILS
    # ========================================================

    st.write("")

    with st.expander("View Full Agent Execution"):

        st.json(result)


# ============================================================
# INITIAL STATE
# ============================================================

else:

    st.info(
        "Enter a request above and run the autonomous agent "
        "to analyze, retrieve, execute, test, and validate."
    )