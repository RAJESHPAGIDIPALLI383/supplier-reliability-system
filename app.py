
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Supplier Reliability System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = Path(__file__).parent / "database" / "supplier_reliability.db"


# =====================================================
# PROFESSIONAL UI STYLING
# =====================================================

st.markdown("""
<style>
    .stApp {
        background: #f4f7fb;
    }

    [data-testid="stHeader"] {
        background: rgba(244,247,251,0.95);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101d36 0%, #1c3558 100%);
    }

    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 7px 10px;
        border-radius: 7px;
    }

    .main-title {
        color: #142b4a;
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 3px;
    }

    .subtitle {
        color: #718096;
        font-size: 14px;
        margin-bottom: 24px;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5eaf2;
        border-radius: 13px;
        padding: 17px 14px;
        min-width: 0;
        box-shadow: 0 4px 14px rgba(20,43,74,0.05);
    }

    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-size: 13px;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #1769aa;
        font-size: clamp(17px, 1.7vw, 25px) !important;
        font-weight: 800;
        white-space: nowrap !important;
        overflow: visible !important;
        letter-spacing: -0.7px;
    }

    [data-testid="stMetricValue"] div {
        overflow: visible !important;
        white-space: nowrap !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #e3e9f2;
        border-radius: 10px;
    }

    div.stButton > button {
        background: #1769aa;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background: #104d80;
        color: white;
        border: none;
    }

    div[data-testid="stDownloadButton"] button {
        border-radius: 8px;
    }

    hr {
        border-color: #e1e7f0;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE FUNCTIONS - READ ONLY
# =====================================================

def get_connection():
    return sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True
    )


@st.cache_data(ttl=30)
def load_data(query):
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


@st.cache_data(ttl=30)
def get_tables():
    conn = get_connection()
    try:
        result = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """,
            conn
        )
        return result["name"].tolist()
    finally:
        conn.close()


@st.cache_data(ttl=30)
def get_dashboard_data():

    suppliers = load_data("""
        SELECT
            s.*,
            sc.final_score,
            sc.rating,
            sc.data_coverage,
            sc.delivery_score,
            sc.quality_score,
            sc.cost_score,
            sc.capacity_score,
            sc.compliance_score,
            sc.disruption_score,
            sc.scoring_period
        FROM suppliers s
        LEFT JOIN supplier_scores sc
        ON s.supplier_id = sc.supplier_id
    """)

    risks = load_data("""
        SELECT *
        FROM risk_signals
        ORDER BY observed_at DESC
    """)

    exceptions = load_data("""
        SELECT *
        FROM data_quality_exceptions
    """)

    return suppliers, risks, exceptions


# =====================================================
# DATABASE CHECK
# =====================================================

if not DB_PATH.exists():
    st.error("Database not found. Check the database folder.")
    st.stop()

try:
    suppliers, risks, exceptions = get_dashboard_data()
except Exception as error:
    st.error(f"Database connection error: {error}")
    st.stop()


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

with st.sidebar:

    st.markdown("## 📊 SUPPLIER 360")
    st.caption("RELIABILITY INTELLIGENCE")
    st.divider()

    page = st.radio(
        "MAIN MENU",
        [
            "Overview",
            "Suppliers",
            "Risk & Anomalies",
            "Data Explorer"
        ],
        label_visibility="visible"
    )

    st.divider()

    st.markdown("### SYSTEM STATUS")
    st.success("Database Connected")

    st.caption("SQLite Database")
    st.caption("Supplier Reliability System")
    st.caption("Version 1.0")


# =====================================================
# COMMON HEADER
# =====================================================

st.markdown(
    '<div class="main-title">Supplier Reliability System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Enterprise Supplier Performance | Risk Intelligence | Data Quality Monitoring</div>',
    unsafe_allow_html=True
)

st.divider()


# =====================================================
# OVERVIEW DASHBOARD
# =====================================================

if page == "Overview":

    st.markdown("## Business Overview")

    total_suppliers = len(suppliers)

    avg_score = suppliers["final_score"].mean()
    avg_coverage = suppliers["data_coverage"].mean()

    total_risks = len(risks)
    total_exceptions = len(exceptions)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Suppliers",
        f"{total_suppliers:,}"
    )

    col2.metric(
        "Average Score",
        f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A"
    )

    col3.metric(
        "Data Coverage",
        f"{avg_coverage:.2f}%" if pd.notna(avg_coverage) else "N/A"
    )

    col4.metric(
        "Risk Signals",
        f"{total_risks:,}"
    )

    st.write("")

    col5, col6, col7 = st.columns(3)

    col5.metric("Data Exceptions", f"{total_exceptions:,}")

    excellent = (suppliers["rating"] == "EXCELLENT").sum()
    good = (suppliers["rating"] == "GOOD").sum()
    moderate = (suppliers["rating"] == "MODERATE").sum()

    col6.metric("Excellent Suppliers", f"{excellent:,}")
    col7.metric("Good Suppliers", f"{good:,}")

    st.divider()

    left, right = st.columns(2)

    with left:

        st.markdown("### Supplier Rating Distribution")

        rating_data = (
            suppliers["rating"]
            .fillna("NOT SCORED")
            .value_counts()
            .reset_index()
        )

        rating_data.columns = ["Rating", "Suppliers"]

        fig = px.pie(
            rating_data,
            names="Rating",
            values="Suppliers",
            hole=0.55,
            color="Rating",
            color_discrete_map={
                "EXCELLENT": "#16865c",
                "GOOD": "#2476c7",
                "MODERATE": "#f0a12b",
                "NOT SCORED": "#9ca3af"
            }
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=25, b=20, l=10, r=10),
            legend_title_text=""
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:

        st.markdown("### Average Performance by Dimension")

        dimensions = [
            "delivery_score",
            "quality_score",
            "cost_score",
            "capacity_score",
            "compliance_score",
            "disruption_score"
        ]

        dimension_data = (
            suppliers[dimensions]
            .mean()
            .reset_index()
        )

        dimension_data.columns = ["Dimension", "Average Score"]

        dimension_data["Dimension"] = (
            dimension_data["Dimension"]
            .str.replace("_score", "", regex=False)
            .str.title()
        )

        fig = px.bar(
            dimension_data,
            x="Dimension",
            y="Average Score",
            range_y=[0, 100],
            text_auto=".1f"
        )

        fig.update_traces(
            marker_color="#2476c7",
            textposition="outside"
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(t=25, b=20, l=10, r=10),
            yaxis_title="Average Score",
            xaxis_title=""
        )

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.markdown("### 🏆 Top 10 Performing Suppliers")

    top_suppliers = suppliers.nlargest(
        10,
        "final_score"
    )[
        [
            "supplier_id",
            "supplier_name",
            "country",
            "category",
            "final_score",
            "rating"
        ]
    ]

    st.dataframe(
        top_suppliers,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.markdown("### Supplier Performance Summary")

    summary = pd.DataFrame({
        "Rating": ["EXCELLENT", "GOOD", "MODERATE"],
        "Supplier Count": [excellent, good, moderate]
    })

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )


# =====================================================
# SUPPLIER DIRECTORY
# =====================================================

elif page == "Suppliers":

    st.markdown("## Supplier Directory")

    st.caption(
        "Search, filter and analyze individual supplier performance."
    )

    search = st.text_input(
        "🔍 Search Supplier",
        placeholder="Enter supplier name or supplier ID..."
    )

    countries = ["All"] + sorted(
        suppliers["country"].dropna().astype(str).unique().tolist()
    )

    categories = ["All"] + sorted(
        suppliers["category"].dropna().astype(str).unique().tolist()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_country = st.selectbox("Country", countries)

    with col2:
        selected_category = st.selectbox("Category", categories)

    with col3:
        selected_rating = st.selectbox(
            "Rating",
            ["All", "EXCELLENT", "GOOD", "MODERATE"]
        )

    filtered = suppliers.copy()

    if search:
        filtered = filtered[
            filtered["supplier_name"].astype(str).str.contains(
                search, case=False, na=False
            )
            |
            filtered["supplier_id"].astype(str).str.contains(
                search, case=False, na=False
            )
        ]

    if selected_country != "All":
        filtered = filtered[filtered["country"] == selected_country]

    if selected_category != "All":
        filtered = filtered[filtered["category"] == selected_category]

    if selected_rating != "All":
        filtered = filtered[filtered["rating"] == selected_rating]

    st.write(f"**{len(filtered):,} suppliers found**")

    display_columns = [
        "supplier_id",
        "supplier_name",
        "country",
        "category",
        "status",
        "final_score",
        "rating",
        "data_coverage"
    ]

    st.dataframe(
        filtered[display_columns].sort_values(
            "final_score",
            ascending=False,
            na_position="last"
        ),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇ Download Supplier Report",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="supplier_report.csv",
        mime="text/csv"
    )

    st.divider()

    st.markdown("### Individual Supplier Profile")

    if not filtered.empty:

        supplier_options = filtered["supplier_id"].astype(str).tolist()

        selected_supplier = st.selectbox(
            "Select Supplier ID",
            supplier_options
        )

        detail = filtered[
            filtered["supplier_id"].astype(str) == selected_supplier
        ].iloc[0]

        st.markdown(f"### {detail['supplier_name']}")

        a, b, c, d = st.columns(4)

        a.metric("Supplier ID", str(detail["supplier_id"]))

        b.metric(
            "Final Score",
            f"{detail['final_score']:.2f}"
            if pd.notna(detail["final_score"]) else "N/A"
        )

        c.metric("Rating", str(detail["rating"]))

        d.metric(
            "Data Coverage",
            f"{detail['data_coverage']:.2f}%"
            if pd.notna(detail["data_coverage"]) else "N/A"
        )

        score_columns = [
            "delivery_score",
            "quality_score",
            "cost_score",
            "capacity_score",
            "compliance_score",
            "disruption_score"
        ]

        score_data = pd.DataFrame({
            "Dimension": [
                item.replace("_score", "").title()
                for item in score_columns
            ],
            "Score": [
                detail[item]
                for item in score_columns
            ]
        }).dropna()

        st.markdown("#### Performance Breakdown")

        fig = px.bar(
            score_data,
            x="Dimension",
            y="Score",
            range_y=[0, 100],
            text_auto=".1f"
        )

        fig.update_traces(
            marker_color="#2476c7",
            textposition="outside"
        )

        fig.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Supplier Information")

        info_columns = [
            "supplier_id",
            "supplier_name",
            "country",
            "category",
            "status",
            "registration_date",
            "monthly_capacity_units"
        ]

        st.dataframe(
            detail[info_columns].to_frame(name="Value"),
            use_container_width=True
        )

    else:
        st.warning("No suppliers match the selected filters.")


# =====================================================
# RISK AND ANOMALY MONITORING
# =====================================================

elif page == "Risk & Anomalies":

    st.markdown("## Risk & Anomaly Monitoring")

    st.caption(
        "Monitor supplier risk signals and quarantined data records."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Risk Signals", f"{len(risks):,}")
    col2.metric("Data Exceptions", f"{len(exceptions):,}")

    high_risks = (
        risks["severity"].astype(str).str.upper()
        .isin(["HIGH", "CRITICAL"]).sum()
    ) if not risks.empty else 0

    col3.metric("High / Critical Signals", f"{high_risks:,}")

    st.divider()

    if not risks.empty:

        left, right = st.columns(2)

        with left:

            st.markdown("### Risk Severity Distribution")

            severity_data = (
                risks["severity"]
                .fillna("UNKNOWN")
                .value_counts()
                .reset_index()
            )

            severity_data.columns = ["Severity", "Count"]

            fig = px.pie(
                severity_data,
                names="Severity",
                values="Count",
                hole=0.45,
                color="Severity",
                color_discrete_map={
                    "LOW": "#2ca879",
                    "MEDIUM": "#e5aa32",
                    "HIGH": "#e87835",
                    "CRITICAL": "#d94343",
                    "UNKNOWN": "#9ca3af"
                }
            )

            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white"
            )

            st.plotly_chart(fig, use_container_width=True)

        with right:

            st.markdown("### Risk Type Analysis")

            risk_type_data = (
                risks["risk_type"]
                .fillna("UNKNOWN")
                .value_counts()
                .reset_index()
            )

            risk_type_data.columns = ["Risk Type", "Count"]

            fig = px.bar(
                risk_type_data,
                x="Risk Type",
                y="Count",
                text_auto=True
            )

            fig.update_traces(marker_color="#2476c7")

            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.markdown("### Risk Signal Records")

        severity_options = ["All"] + sorted(
            risks["severity"].dropna().astype(str).unique().tolist()
        )

        selected_severity = st.selectbox(
            "Filter by Risk Severity",
            severity_options
        )

        filtered_risks = risks.copy()

        if selected_severity != "All":
            filtered_risks = filtered_risks[
                filtered_risks["severity"] == selected_severity
            ]

        st.dataframe(
            filtered_risks,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Risk Report",
            data=filtered_risks.to_csv(index=False).encode("utf-8"),
            file_name="supplier_risk_report.csv",
            mime="text/csv"
        )

    else:
        st.info("No risk signals found.")

    st.divider()

    st.markdown("### Data Quality Exceptions")

    if not exceptions.empty:

        st.warning(
            f"{len(exceptions)} records are stored as data quality exceptions."
        )

        st.dataframe(
            exceptions,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success("No data quality exceptions found.")


# =====================================================
# DATABASE EXPLORER
# =====================================================

elif page == "Data Explorer":

    st.markdown("## Database Explorer")

    st.caption(
        "Explore records from the Supplier Reliability SQLite database."
    )

    allowed_tables = [
        "suppliers",
        "sites",
        "contracts",
        "purchase_orders",
        "po_lines",
        "shipments",
        "shipment_lines",
        "delivery_events",
        "inspections",
        "invoices",
        "risk_signals",
        "supplier_scores",
        "supplier_score_history",
        "data_quality_exceptions"
    ]

    available_tables = [
        table for table in get_tables()
        if table in allowed_tables
    ]

    selected_table = st.selectbox(
        "Select Database Table",
        available_tables
    )

    limit = st.selectbox(
        "Records to Display",
        [100, 250, 500, 1000],
        index=0
    )

    if selected_table:

        table_data = load_data(
            f'SELECT * FROM "{selected_table}" LIMIT {int(limit)}'
        )

        col1, col2 = st.columns(2)

        col1.metric("Records Displayed", f"{len(table_data):,}")
        col2.metric("Columns", f"{len(table_data.columns):,}")

        st.divider()

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Table as CSV",
            data=table_data.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_table}.csv",
            mime="text/csv"
        )


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#8190a5; padding:15px;">
        <b>Supplier Reliability System</b><br>
        Enterprise Supplier Performance & Risk Intelligence<br>
        Backend: Python | Database: SQLite | Frontend: Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
