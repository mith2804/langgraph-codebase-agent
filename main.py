import streamlit as st
from agent.graph import build_graph


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Codebase Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 80% 5%,
                rgba(92, 70, 180, 0.10),
                transparent 28%
            ),
            #090b10;
    }

    .main .block-container {
        max-width: 1220px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.6px;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: #0e1117;
        border-right: 1px solid #202532;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }

    .brand-logo {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background:
            linear-gradient(
                135deg,
                #6d5dfc,
                #3b82f6
            );
        box-shadow:
            0 8px 24px rgba(76, 78, 220, 0.28);
    }

    .brand-logo svg {
        width: 25px;
        height: 25px;
    }

    .brand-title {
        font-size: 1.12rem;
        font-weight: 800;
        color: #f4f6fa;
        line-height: 1.1;
    }

    .brand-subtitle {
        font-size: 0.68rem;
        color: #737d8e;
        margin-top: 4px;
    }


    /* ========================================================
       SECTION LABEL
       ======================================================== */

    .section-label {
        color: #788398;
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 1.7px;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }


    /* ========================================================
       HERO
       ======================================================== */

    .hero {
        position: relative;
        overflow: hidden;
        padding: 2.6rem 2.7rem;
        border-radius: 22px;
        border: 1px solid #272d3b;
        background:
            radial-gradient(
                circle at 90% 20%,
                rgba(98, 78, 220, 0.18),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #151923 0%,
                #10131b 55%,
                #0e1219 100%
            );
        margin-bottom: 2rem;
        box-shadow:
            0 24px 70px rgba(0, 0, 0, 0.25);
    }

    .hero-grid {
        position: absolute;
        inset: 0;
        opacity: 0.08;
        background-image:
            linear-gradient(#8b95a7 1px, transparent 1px),
            linear-gradient(90deg, #8b95a7 1px, transparent 1px);
        background-size: 34px 34px;
        mask-image: linear-gradient(
            to right,
            transparent,
            black 65%,
            transparent
        );
    }

    .hero-content {
        position: relative;
        z-index: 2;
    }

    .hero-label {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 2px;
        color: #9aa5b8;
        margin-bottom: 0.85rem;
    }

    .hero-label-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #7c6cff;
        box-shadow: 0 0 12px rgba(124,108,255,0.8);
    }

    .hero-title {
        font-size: 2.9rem;
        font-weight: 850;
        line-height: 1.08;
        margin-bottom: 0.85rem;
        color: #f5f7fb;
    }

    .hero-title span {
        background:
            linear-gradient(
                90deg,
                #ffffff,
                #a9a2ff
            );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-description {
        color: #9ba5b5;
        font-size: 1rem;
        line-height: 1.65;
        max-width: 760px;
    }

    .agent-status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-top: 1.35rem;
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        background: rgba(73, 180, 105, 0.08);
        border: 1px solid rgba(91, 210, 124, 0.22);
        color: #a5d9b2;
        font-size: 0.76rem;
        font-weight: 700;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #5bd27c;
        box-shadow: 0 0 10px rgba(91, 210, 124, 0.7);
    }


    /* ========================================================
       PROMPT CARDS
       ======================================================== */

    .prompt-card {
        height: 100%;
        background:
            linear-gradient(
                145deg,
                #141820,
                #10131a
            );
        border: 1px solid #252b38;
        border-radius: 14px;
        padding: 1rem 1.05rem;
        min-height: 92px;
        transition:
            transform 0.18s ease,
            border-color 0.18s ease,
            background 0.18s ease;
    }

    .prompt-card:hover {
        transform: translateY(-3px);
        border-color: #3b4260;
        background: #171b25;
    }

    .prompt-icon {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: #1d2130;
        color: #a59cff;
        font-size: 0.85rem;
        margin-bottom: 0.65rem;
    }

    .prompt-card-title {
        font-size: 0.82rem;
        font-weight: 750;
        color: #e1e5ec;
        margin-bottom: 0.3rem;
    }

    .prompt-card-text {
        font-size: 0.72rem;
        color: #7f8999;
        line-height: 1.45;
    }


    /* ========================================================
       WORKFLOW
       ======================================================== */

    .workflow {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
        padding: 1.25rem;
        background:
            linear-gradient(
                145deg,
                #11151d,
                #0d1016
            );
        border: 1px solid #252b37;
        border-radius: 16px;
        margin: 0.9rem 0 1.5rem 0;
        overflow-x: auto;
    }

    .workflow-step {
        display: flex;
        align-items: center;
        gap: 7px;
        padding: 0.6rem 0.8rem;
        border-radius: 9px;
        background: #181d27;
        border: 1px solid #2b3241;
        color: #c2c9d4;
        font-size: 0.73rem;
        font-weight: 700;
        white-space: nowrap;
    }

    .workflow-number {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #242a3a;
        color: #938aff;
        font-size: 0.61rem;
    }

    .workflow-arrow {
        color: #535c6d;
        font-size: 0.9rem;
    }


    /* ========================================================
       ANSWER
       ======================================================== */

    .answer-card {
        background: #11161e;
        border: 1px solid #29303d;
        border-radius: 16px;
        padding: 1.4rem 1.5rem;
        margin-top: 0.8rem;
    }

    .answer-label {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #929cad;
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 1.3px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .answer-label-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #7c6cff;
    }


    /* ========================================================
       METRIC CARDS
       ======================================================== */

    .metric-card {
        background: #11151d;
        border: 1px solid #252b37;
        border-radius: 13px;
        padding: 1rem 1.1rem;
    }

    .metric-top {
        display: flex;
        align-items: center;
        gap: 7px;
        color: #737e90;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-icon {
        color: #9188ff;
    }

    .metric-value {
        color: #edf0f5;
        font-size: 1rem;
        font-weight: 750;
        margin-top: 0.45rem;
    }


    /* ========================================================
       BUTTON
       ======================================================== */

    .stButton > button {
        border-radius: 11px;
        min-height: 3.1rem;
        font-weight: 750;
        border: 1px solid #3b4260;
        transition: all 0.18s ease;
    }

    .stButton > button:hover {
        border-color: #756bff;
        box-shadow:
            0 8px 28px rgba(89, 76, 210, 0.18);
    }


    /* ========================================================
       TEXT AREA
       ======================================================== */

    textarea {
        background: #10141b !important;
        border: 1px solid #303745 !important;
        border-radius: 13px !important;
    }

    textarea:focus {
        border-color: #6158c9 !important;
        box-shadow:
            0 0 0 1px rgba(97, 88, 201, 0.25) !important;
    }


    /* ========================================================
       ALERTS
       ======================================================== */

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }


    /* ========================================================
       SIDEBAR CAPABILITIES
       ======================================================== */

    .side-item {
        display: flex;
        align-items: center;
        gap: 9px;
        padding: 0.45rem 0;
        color: #b6becb;
        font-size: 0.79rem;
        font-weight: 600;
    }

    .side-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #6d5dfc;
    }

    .tech-item {
        margin-bottom: 0.8rem;
    }

    .tech-name {
        color: #dfe3ea;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .tech-desc {
        color: #707b8d;
        font-size: 0.68rem;
        margin-top: 2px;
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

    st.html(
        """
        <div class="brand">

            <div class="brand-logo">
                <svg viewBox="0 0 32 32" fill="none">
                    <path
                        d="M10 8L4.5 16L10 24"
                        stroke="white"
                        stroke-width="2.6"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                    <path
                        d="M22 8L27.5 16L22 24"
                        stroke="white"
                        stroke-width="2.6"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                    <path
                        d="M18.5 6L13.5 26"
                        stroke="white"
                        stroke-width="2.3"
                        stroke-linecap="round"
                    />
                </svg>
            </div>

            <div>
                <div class="brand-title">
                    Codebase Agent
                </div>
                <div class="brand-subtitle">
                    Autonomous AI Engineering
                </div>
            </div>

        </div>
        """
    )

    st.divider()

    st.html(
        '<div class="section-label">Capabilities</div>'
    )

    capabilities = [
        "Codebase Search",
        "Code Analysis",
        "Tool Selection",
        "Code Modification",
        "Test Execution",
        "Validation",
    ]

    for item in capabilities:
        st.html(
            f"""
            <div class="side-item">
                <span class="side-dot"></span>
                {item}
            </div>
            """
        )

    st.divider()

    st.html(
        '<div class="section-label">Technology Stack</div>'
    )

    technologies = [
        ("LangGraph", "Agent orchestration"),
        ("Qdrant", "Vector retrieval"),
        ("MiniLM", "Code embeddings"),
        ("Qwen", "Language model"),
    ]

    for name, description in technologies:
        st.html(
            f"""
            <div class="tech-item">
                <div class="tech-name">{name}</div>
                <div class="tech-desc">{description}</div>
            </div>
            """
        )

    st.divider()

    st.caption(
        "Autonomous AI Codebase Engineering Agent"
    )


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="hero">

        <div class="hero-grid"></div>

        <div class="hero-content">

            <div class="hero-label">
                <span class="hero-label-dot"></span>
                AUTONOMOUS AI CODEBASE ENGINEERING
            </div>

            <div class="hero-title">
                Build. Analyze.
                <span>Modify. Validate.</span>
            </div>

            <div class="hero-description">
                An autonomous LangGraph agent that understands your
                codebase, retrieves relevant code, selects tools,
                performs engineering tasks, runs tests, and validates
                the result.
            </div>

            <div class="agent-status">
                <span class="status-dot"></span>
                Agent Ready
            </div>

        </div>

    </div>
    """
)


# ============================================================
# CODEBASE INTERFACE
# ============================================================

st.html(
    '<div class="section-label">Codebase Interface</div>'
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

st.html(
    '<div class="section-label">Try an Example</div>'
)

p1, p2, p3, p4 = st.columns(4)


with p1:
    st.html(
        """
        <div class="prompt-card">

            <div class="prompt-icon">⌘</div>

            <div class="prompt-card-title">
                Analyze Code
            </div>

            <div class="prompt-card-text">
                Find functions and explain their purpose.
            </div>

        </div>
        """
    )


with p2:
    st.html(
        """
        <div class="prompt-card">

            <div class="prompt-icon">⌕</div>

            <div class="prompt-card-title">
                Search Project
            </div>

            <div class="prompt-card-text">
                Find where QdrantClient is used.
            </div>

        </div>
        """
    )


with p3:
    st.html(
        """
        <div class="prompt-card">

            <div class="prompt-icon">▶</div>

            <div class="prompt-card-title">
                Run Test
            </div>

            <div class="prompt-card-text">
                Verify that greet() returns the expected output.
            </div>

        </div>
        """
    )


with p4:
    st.html(
        """
        <div class="prompt-card">

            <div class="prompt-icon">✦</div>

            <div class="prompt-card-title">
                Modify Code
            </div>

            <div class="prompt-card-text">
                Add a comment or make a requested code change.
            </div>

        </div>
        """
    )


st.write("")


# ============================================================
# WORKFLOW
# ============================================================

st.html(
    '<div class="section-label">Agent Workflow</div>'
)

st.html(
    """
    <div class="workflow">

        <div class="workflow-step">
            <span class="workflow-number">1</span>
            Analyze
        </div>

        <div class="workflow-arrow">→</div>

        <div class="workflow-step">
            <span class="workflow-number">2</span>
            Retrieve
        </div>

        <div class="workflow-arrow">→</div>

        <div class="workflow-step">
            <span class="workflow-number">3</span>
            Select Tool
        </div>

        <div class="workflow-arrow">→</div>

        <div class="workflow-step">
            <span class="workflow-number">4</span>
            Execute
        </div>

        <div class="workflow-arrow">→</div>

        <div class="workflow-step">
            <span class="workflow-number">5</span>
            Test
        </div>

        <div class="workflow-arrow">→</div>

        <div class="workflow-step">
            <span class="workflow-number">6</span>
            Validate
        </div>

    </div>
    """
)


# ============================================================
# RUN AGENT
# ============================================================

run_agent = st.button(
    "⚡  Run Autonomous Agent",
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

    with st.spinner(
        "Agent is analyzing your codebase..."
    ):

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

    st.success(
        "Agent execution completed successfully."
    )


    # ========================================================
    # FINAL ANSWER
    # ========================================================

    st.html(
        '<div class="section-label">Agent Response</div>'
    )

    st.html(
        """
        <div class="answer-card">

            <div class="answer-label">
                <span class="answer-label-dot"></span>
                Final Answer
            </div>
        """
    )

    answer = result.get("answer", "")

    if answer:
        st.markdown(answer)
    else:
        st.info(
            "No final answer was generated."
        )

    st.html("</div>")


    # ========================================================
    # EXECUTION SUMMARY
    # ========================================================

    st.write("")

    st.html(
        '<div class="section-label">Execution Summary</div>'
    )

    c1, c2, c3, c4 = st.columns(4)


    with c1:
        st.html(
            """
            <div class="metric-card">

                <div class="metric-top">
                    <span class="metric-icon">◆</span>
                    Orchestration
                </div>

                <div class="metric-value">
                    LangGraph
                </div>

            </div>
            """
        )


    with c2:
        st.html(
            """
            <div class="metric-card">

                <div class="metric-top">
                    <span class="metric-icon">◈</span>
                    Retrieval
                </div>

                <div class="metric-value">
                    Qdrant
                </div>

            </div>
            """
        )


    with c3:
        st.html(
            """
            <div class="metric-card">

                <div class="metric-top">
                    <span class="metric-icon">✦</span>
                    LLM
                </div>

                <div class="metric-value">
                    Qwen
                </div>

            </div>
            """
        )


    with c4:
        st.html(
            """
            <div class="metric-card">

                <div class="metric-top">
                    <span class="metric-icon">✓</span>
                    Status
                </div>

                <div class="metric-value">
                    Validated
                </div>

            </div>
            """
        )


    # ========================================================
    # EXECUTION DETAILS
    # ========================================================

    st.write("")

    with st.expander(
        "View Full Agent Execution"
    ):
        st.json(result)


# ============================================================
# INITIAL STATE
# ============================================================

else:

    st.info(
        "Enter a request above and run the autonomous agent "
        "to analyze, retrieve, execute, test, and validate."
    )