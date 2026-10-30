
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
.stApp { background: #f4f7fb; }
[data-testid="stHeader"] { background: rgba(244,247,251,0.95); }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101d36 0%, #1c3558 100%);
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
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
div[data-testid="stDownloadButton"] button { border-radius: 8px; }
hr { border-color: #e1e7f0; }
footer { visibility: hidden; }
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


def csv_bytes(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8")


def safe_number(value, decimals=2):
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return f"{number:.{decimals}f}" if pd.notna(number) else "N/A"


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
            "Procurement & Logistics",
            "Quality & Inspection",
            "Risk & Anomalies",
            "Score Explainability",
            "Score History & Trends",
            "Data Quality & Validation",
            "Data Explorer"
        ],
        label_visibility="visible"
    )

    st.divider()

    st.markdown("### SYSTEM STATUS")
    st.success("Database Connected")
    st.caption("SQLite Database")
    st.caption("Supplier Reliability System")
    st.caption("Version 1.3")


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
    avg_score = pd.to_numeric(
        suppliers["final_score"], errors="coerce"
    ).mean()

    avg_coverage = pd.to_numeric(
        suppliers["data_coverage"], errors="coerce"
    ).mean()

    total_risks = len(risks)
    total_exceptions = len(exceptions)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Suppliers", f"{total_suppliers:,}")
    col2.metric(
        "Average Score",
        f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A"
    )
    col3.metric(
        "Data Coverage",
        f"{avg_coverage:.2f}%" if pd.notna(avg_coverage) else "N/A"
    )
    col4.metric("Risk Signals", f"{total_risks:,}")

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
            .apply(pd.to_numeric, errors="coerce")
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
        10, "final_score"
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

    st.dataframe(summary, use_container_width=True, hide_index=True)


# =====================================================
# SUPPLIER DIRECTORY
# =====================================================

elif page == "Suppliers":

    st.markdown("## Supplier Directory")
    st.caption("Search, filter and analyze individual supplier performance.")

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
        data=csv_bytes(filtered),
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
        b.metric("Final Score", safe_number(detail["final_score"]))
        c.metric("Rating", str(detail["rating"]))
        d.metric("Data Coverage", safe_number(detail["data_coverage"]) + "%")

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
                pd.to_numeric(
                    pd.Series([detail[item]]), errors="coerce"
                ).iloc[0]
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
# PROCUREMENT AND LOGISTICS
# =====================================================

elif page == "Procurement & Logistics":

    st.markdown("## Procurement & Logistics")
    st.caption(
        "Monitor purchase orders, shipments, delivery performance "
        "and logistics events."
    )

    procurement = load_data("""
        SELECT
            po.po_id,
            po.supplier_id,
            s.supplier_name,
            po.site_id,
            po.contract_id,
            po.order_date,
            po.required_date,
            po.currency,
            po.total_amount,
            po.status AS po_status
        FROM purchase_orders po
        LEFT JOIN suppliers s
            ON po.supplier_id = s.supplier_id
        ORDER BY po.order_date DESC
    """)

    shipment_data = load_data("""
        SELECT
            sh.shipment_id,
            sh.supplier_id,
            s.supplier_name,
            sh.po_id,
            po.required_date,
            sh.dispatch_date,
            sh.expected_delivery_date,
            sh.actual_delivery_date,
            sh.carrier_name,
            sh.status AS shipment_status,
            COALESCE(sl.shipped_quantity, 0) AS shipped_quantity,
            COALESCE(sl.line_count, 0) AS shipment_line_count
        FROM shipments sh
        LEFT JOIN suppliers s
            ON sh.supplier_id = s.supplier_id
        LEFT JOIN purchase_orders po
            ON sh.po_id = po.po_id
        LEFT JOIN (
            SELECT
                shipment_id,
                SUM(shipped_quantity) AS shipped_quantity,
                COUNT(*) AS line_count
            FROM shipment_lines
            GROUP BY shipment_id
        ) sl
            ON sh.shipment_id = sl.shipment_id
        ORDER BY sh.dispatch_date DESC
    """)

    delivery_events = load_data("""
        SELECT
            de.delivery_event_id,
            de.shipment_id,
            sh.supplier_id,
            s.supplier_name,
            de.event_type,
            de.event_timestamp,
            de.location,
            de.source
        FROM delivery_events de
        LEFT JOIN shipments sh
            ON de.shipment_id = sh.shipment_id
        LEFT JOIN suppliers s
            ON sh.supplier_id = s.supplier_id
        ORDER BY de.event_timestamp DESC
    """)

    if not shipment_data.empty:

        for date_col in [
            "expected_delivery_date",
            "actual_delivery_date",
            "dispatch_date"
        ]:
            shipment_data[date_col] = pd.to_datetime(
                shipment_data[date_col], errors="coerce"
            )

        shipment_data["delivery_performance"] = "IN TRANSIT"

        delivered = shipment_data["actual_delivery_date"].notna()
        valid_expected = shipment_data["expected_delivery_date"].notna()

        on_time = (
            delivered & valid_expected
            & (
                shipment_data["actual_delivery_date"]
                <= shipment_data["expected_delivery_date"]
            )
        )

        late = (
            delivered & valid_expected
            & (
                shipment_data["actual_delivery_date"]
                > shipment_data["expected_delivery_date"]
            )
        )

        shipment_data.loc[on_time, "delivery_performance"] = "ON TIME"
        shipment_data.loc[late, "delivery_performance"] = "LATE"

        shipment_data.loc[
            delivered & ~valid_expected,
            "delivery_performance"
        ] = "DATE MISSING"

    total_pos = len(procurement)
    total_po_value = pd.to_numeric(
        procurement["total_amount"], errors="coerce"
    ).sum()

    total_shipments = len(shipment_data)

    delivered_count = (
        shipment_data["delivery_performance"]
        .isin(["ON TIME", "LATE"]).sum()
        if not shipment_data.empty else 0
    )

    on_time_count = (
        (shipment_data["delivery_performance"] == "ON TIME").sum()
        if not shipment_data.empty else 0
    )

    late_count = (
        (shipment_data["delivery_performance"] == "LATE").sum()
        if not shipment_data.empty else 0
    )

    delivery_rate = (
        on_time_count / delivered_count * 100
        if delivered_count > 0 else 0
    )

    st.markdown("### Procurement Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Purchase Orders", f"{total_pos:,}")
    c2.metric("Total PO Value", f"₹{total_po_value:,.0f}")
    c3.metric("Total Shipments", f"{total_shipments:,}")
    c4.metric("Delivered Shipments", f"{delivered_count:,}")

    c5, c6, c7 = st.columns(3)
    c5.metric("On-Time Deliveries", f"{on_time_count:,}")
    c6.metric("Late Deliveries", f"{late_count:,}")
    c7.metric("On-Time Delivery Rate", f"{delivery_rate:.2f}%")

    st.caption(
        "On-time rate = on-time delivered shipments / "
        "all delivered shipments × 100. "
        "In-transit and missing-date shipments are excluded."
    )

    st.divider()
    st.markdown("### Delivery Performance Analysis")

    if not shipment_data.empty:

        performance_data = (
            shipment_data["delivery_performance"]
            .value_counts()
            .reset_index()
        )

        performance_data.columns = ["Performance", "Shipments"]

        left, right = st.columns(2)

        with left:
            fig = px.pie(
                performance_data,
                names="Performance",
                values="Shipments",
                hole=0.5,
                title="Shipment Delivery Status"
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            carrier_data = (
                shipment_data.groupby("carrier_name", dropna=False)
                .agg(
                    Total_Shipments=("shipment_id", "count"),
                    On_Time=(
                        "delivery_performance",
                        lambda x: (x == "ON TIME").sum()
                    ),
                    Late=(
                        "delivery_performance",
                        lambda x: (x == "LATE").sum()
                    )
                )
                .reset_index()
            )

            fig = px.bar(
                carrier_data,
                x="carrier_name",
                y=["On_Time", "Late"],
                barmode="group",
                title="Carrier Delivery Performance"
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No shipment records available.")

    st.divider()
    st.markdown("### Purchase Order Register")

    po_statuses = ["All"] + sorted(
        procurement["po_status"].dropna().astype(str).unique().tolist()
    )

    selected_po_status = st.selectbox(
        "Filter Purchase Order Status",
        po_statuses,
        key="procurement_po_status"
    )

    filtered_pos = procurement.copy()

    if selected_po_status != "All":
        filtered_pos = filtered_pos[
            filtered_pos["po_status"] == selected_po_status
        ]

    st.dataframe(filtered_pos, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇ Download Purchase Orders",
        data=csv_bytes(filtered_pos),
        file_name="purchase_orders_report.csv",
        mime="text/csv"
    )

    st.divider()
    st.markdown("### Shipment Tracking")

    if not shipment_data.empty:

        shipment_statuses = ["All"] + sorted(
            shipment_data["shipment_status"]
            .dropna().astype(str).unique().tolist()
        )

        selected_shipment_status = st.selectbox(
            "Filter Shipment Status",
            shipment_statuses,
            key="procurement_shipment_status"
        )

        filtered_shipments = shipment_data.copy()

        if selected_shipment_status != "All":
            filtered_shipments = filtered_shipments[
                filtered_shipments["shipment_status"]
                == selected_shipment_status
            ]

        display_shipments = filtered_shipments.copy()

        for column in [
            "dispatch_date",
            "expected_delivery_date",
            "actual_delivery_date"
        ]:
            display_shipments[column] = (
                display_shipments[column].dt.strftime("%Y-%m-%d")
            )

        st.dataframe(
            display_shipments,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Shipment Report",
            data=csv_bytes(display_shipments),
            file_name="shipment_tracking_report.csv",
            mime="text/csv"
        )

    else:
        st.info("No shipment records available.")

    st.divider()
    st.markdown("### Delivery Event History")

    if not delivery_events.empty:

        event_types = ["All"] + sorted(
            delivery_events["event_type"]
            .dropna().astype(str).unique().tolist()
        )

        selected_event = st.selectbox(
            "Filter Delivery Event",
            event_types,
            key="delivery_event_filter"
        )

        filtered_events = delivery_events.copy()

        if selected_event != "All":
            filtered_events = filtered_events[
                filtered_events["event_type"] == selected_event
            ]

        st.dataframe(
            filtered_events,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Delivery Events",
            data=csv_bytes(filtered_events),
            file_name="delivery_events_report.csv",
            mime="text/csv"
        )

    else:
        st.info("No delivery events available.")


# =====================================================
# QUALITY AND INSPECTION
# =====================================================

elif page == "Quality & Inspection":

    st.markdown("## Quality & Inspection")
    st.caption(
        "Track inspection outcomes, accepted and rejected quantities, "
        "defect patterns and supplier quality."
    )

    try:
        inspections = load_data("""
            SELECT
                i.inspection_id,
                i.supplier_id,
                s.supplier_name,
                i.shipment_id,
                i.po_line_id,
                i.inspection_date,
                i.inspected_quantity,
                i.accepted_quantity,
                i.rejected_quantity,
                i.defect_category,
                i.status
            FROM inspections i
            LEFT JOIN suppliers s
                ON i.supplier_id = s.supplier_id
            ORDER BY i.inspection_date DESC
        """)

    except Exception as error:
        st.error(f"Unable to load inspection records: {error}")
        inspections = pd.DataFrame()

    if inspections.empty:
        st.info("No inspection records are available in the database.")

    else:

        numeric_columns = [
            "inspected_quantity",
            "accepted_quantity",
            "rejected_quantity"
        ]

        for column in numeric_columns:
            inspections[column] = pd.to_numeric(
                inspections[column], errors="coerce"
            ).fillna(0)

        inspections["inspection_date"] = pd.to_datetime(
            inspections["inspection_date"], errors="coerce"
        )

        total_inspections = len(inspections)
        inspected_qty = inspections["inspected_quantity"].sum()
        accepted_qty = inspections["accepted_quantity"].sum()
        rejected_qty = inspections["rejected_quantity"].sum()

        defect_rate = (
            rejected_qty / inspected_qty * 100 if inspected_qty else 0
        )

        acceptance_rate = (
            accepted_qty / inspected_qty * 100 if inspected_qty else 0
        )

        suppliers_inspected = inspections["supplier_id"].nunique()

        st.markdown("### Quality Overview")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Inspections", f"{total_inspections:,}")
        k2.metric("Inspected Quantity", f"{inspected_qty:,.0f}")
        k3.metric("Accepted Quantity", f"{accepted_qty:,.0f}")
        k4.metric("Rejected Quantity", f"{rejected_qty:,.0f}")

        k5, k6, k7 = st.columns(3)
        k5.metric("Defect Rate", f"{defect_rate:.2f}%")
        k6.metric("Acceptance Rate", f"{acceptance_rate:.2f}%")
        k7.metric("Suppliers Inspected", f"{suppliers_inspected:,}")

        st.caption(
            "Defect rate = rejected quantity / inspected quantity × 100. "
            "Acceptance rate = accepted quantity / inspected quantity × 100."
        )

        st.divider()

        left, right = st.columns(2)

        with left:
            st.markdown("### Inspection Status Distribution")

            status_data = (
                inspections["status"]
                .fillna("UNKNOWN")
                .value_counts()
                .reset_index()
            )

            status_data.columns = ["Status", "Inspections"]

            fig = px.pie(
                status_data,
                names="Status",
                values="Inspections",
                hole=0.5
            )

            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white"
            )

            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.markdown("### Defect Category Analysis")

            defect_data = inspections.copy()
            defect_data["defect_category"] = (
                defect_data["defect_category"].fillna("NOT SPECIFIED")
            )

            defect_data = (
                defect_data.groupby("defect_category", as_index=False)
                .agg(
                    Rejected_Quantity=("rejected_quantity", "sum"),
                    Inspection_Count=("inspection_id", "count")
                )
                .sort_values("Rejected_Quantity", ascending=False)
            )

            fig = px.bar(
                defect_data,
                x="defect_category",
                y="Rejected_Quantity",
                text_auto=True,
                title="Rejected Quantity by Defect Category"
            )

            fig.update_traces(
                marker_color="#d97736",
                textposition="outside"
            )

            fig.update_layout(
                paper_bgcolor="white",
                plot_bgcolor="white",
                xaxis_title="Defect Category",
                yaxis_title="Rejected Quantity"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("### Supplier Quality Performance")

        supplier_quality = (
            inspections.groupby(
                ["supplier_id", "supplier_name"],
                dropna=False
            )
            .agg(
                Inspection_Count=("inspection_id", "count"),
                Inspected_Quantity=("inspected_quantity", "sum"),
                Accepted_Quantity=("accepted_quantity", "sum"),
                Rejected_Quantity=("rejected_quantity", "sum")
            )
            .reset_index()
        )

        supplier_quality["Defect_Rate_Percent"] = (
            supplier_quality["Rejected_Quantity"]
            / supplier_quality["Inspected_Quantity"].replace(0, pd.NA)
            * 100
        ).fillna(0).round(2)

        supplier_quality["Acceptance_Rate_Percent"] = (
            supplier_quality["Accepted_Quantity"]
            / supplier_quality["Inspected_Quantity"].replace(0, pd.NA)
            * 100
        ).fillna(0).round(2)

        st.dataframe(
            supplier_quality.sort_values(
                "Defect_Rate_Percent", ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Supplier Quality Report",
            data=csv_bytes(supplier_quality),
            file_name="supplier_quality_report.csv",
            mime="text/csv"
        )

        st.divider()
        st.markdown("### Monthly Inspection Trend")

        monthly = inspections.dropna(
            subset=["inspection_date"]
        ).copy()

        if not monthly.empty:

            monthly["Month"] = (
                monthly["inspection_date"].dt.to_period("M").astype(str)
            )

            monthly_summary = (
                monthly.groupby("Month", as_index=False)
                .agg(
                    Accepted=("accepted_quantity", "sum"),
                    Rejected=("rejected_quantity", "sum")
                )
                .sort_values("Month")
            )

            monthly_long = monthly_summary.melt(
                id_vars="Month",
                var_name="Inspection Outcome",
                value_name="Quantity"
            )

            fig = px.bar(
                monthly_long,
                x="Month",
                y="Quantity",
                color="Inspection Outcome",
                barmode="group",
                title="Accepted vs Rejected Quantity by Month"
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info(
                "No valid inspection dates are available for the monthly trend."
            )

        st.divider()
        st.markdown("### Inspection Records")

        search_inspection = st.text_input(
            "🔍 Search inspections",
            placeholder="Supplier ID, supplier name or shipment ID...",
            key="inspection_search"
        )

        statuses = ["All"] + sorted(
            inspections["status"].dropna().astype(str).unique().tolist()
        )

        selected_status = st.selectbox(
            "Filter Inspection Status",
            statuses,
            key="inspection_status_filter"
        )

        filtered_inspections = inspections.copy()

        if search_inspection:
            search_mask = (
                filtered_inspections["supplier_id"]
                .astype(str).str.contains(
                    search_inspection, case=False, na=False
                )
                |
                filtered_inspections["supplier_name"]
                .astype(str).str.contains(
                    search_inspection, case=False, na=False
                )
                |
                filtered_inspections["shipment_id"]
                .astype(str).str.contains(
                    search_inspection, case=False, na=False
                )
            )

            filtered_inspections = filtered_inspections[search_mask]

        if selected_status != "All":
            filtered_inspections = filtered_inspections[
                filtered_inspections["status"] == selected_status
            ]

        display_inspections = filtered_inspections.copy()

        display_inspections["inspection_date"] = (
            display_inspections["inspection_date"].dt.strftime("%Y-%m-%d")
        )

        st.write(
            f"**{len(display_inspections):,} inspection records found**"
        )

        st.dataframe(
            display_inspections,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Inspection Records",
            data=csv_bytes(display_inspections),
            file_name="inspection_records.csv",
            mime="text/csv"
        )


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
            data=csv_bytes(filtered_risks),
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
# SCORE EXPLAINABILITY
# =====================================================

elif page == "Score Explainability":

    st.markdown("## Score Explainability")

    st.caption(
        "Understand the stored supplier score components and configured "
        "scoring weights."
    )

    weights = pd.DataFrame({
        "Dimension": [
            "Delivery",
            "Quality",
            "Cost",
            "Capacity",
            "Compliance",
            "Disruption"
        ],
        "Weight (%)": [30, 25, 15, 10, 10, 10]
    })

    st.markdown("### Configured Scoring Weights")

    w1, w2 = st.columns([1, 1])

    with w1:
        st.dataframe(
            weights,
            use_container_width=True,
            hide_index=True
        )

    with w2:
        fig = px.bar(
            weights,
            x="Dimension",
            y="Weight (%)",
            text="Weight (%)",
            range_y=[0, 35]
        )
        fig.update_traces(marker_color="#2476c7")
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Configured weights: Delivery 30%, Quality 25%, Cost 15%, "
        "Capacity 10%, Compliance 10%, Disruption 10%."
    )

    st.divider()
    st.markdown("### Individual Supplier Score Explanation")

    if suppliers.empty:
        st.warning("No supplier records available.")

    else:
        supplier_options = suppliers["supplier_id"].dropna().astype(str).tolist()

        selected_id = st.selectbox(
            "Select Supplier",
            supplier_options,
            key="explain_supplier"
        )

        selected = suppliers[
            suppliers["supplier_id"].astype(str) == selected_id
        ].iloc[0]

        a, b, c = st.columns(3)
        a.metric("Final Score", safe_number(selected["final_score"]))
        b.metric("Rating", str(selected["rating"]))
        c.metric("Data Coverage", safe_number(selected["data_coverage"]) + "%")

        score_columns = {
            "Delivery": "delivery_score",
            "Quality": "quality_score",
            "Cost": "cost_score",
            "Capacity": "capacity_score",
            "Compliance": "compliance_score",
            "Disruption": "disruption_score"
        }

        score_rows = []

        for dimension, column in score_columns.items():
            value = pd.to_numeric(
                pd.Series([selected[column]]), errors="coerce"
            ).iloc[0]

            weight = weights.loc[
                weights["Dimension"] == dimension, "Weight (%)"
            ].iloc[0]

            score_rows.append({
                "Dimension": dimension,
                "Configured Weight (%)": weight,
                "Stored Component Score": value
            })

        breakdown = pd.DataFrame(score_rows)

        st.markdown("### Stored Component Scores")

        available_scores = breakdown.dropna(
            subset=["Stored Component Score"]
        )

        if not available_scores.empty:
            fig = px.bar(
                available_scores,
                x="Dimension",
                y="Stored Component Score",
                range_y=[0, 100],
                text_auto=".1f"
            )
            fig.update_traces(marker_color="#2476c7")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            breakdown,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Score Explanation",
            data=csv_bytes(breakdown),
            file_name=f"score_explanation_{selected_id}.csv",
            mime="text/csv"
        )

        st.info(
            "These are the stored score components and configured weights. "
            "Missing metrics may be excluded and the remaining weights "
            "renormalized by the scoring backend. This page displays stored "
            "values; it does not recalculate the supplier score."
        )


# =====================================================
# SCORE HISTORY AND TRENDS
# =====================================================

elif page == "Score History & Trends":

    st.markdown("## Score History & Trends")

    st.caption(
        "Explore historical supplier scores across scoring periods."
    )

    tables = get_tables()

    history_candidates = [
        "supplier_score_history",
        "supplier_scores_history",
        "score_history"
    ]

    history_table = next(
        (table for table in history_candidates if table in tables),
        None
    )

    if history_table is None:
        st.warning(
            "No recognized score history table was found in the database."
        )

    else:
        try:
            history = load_data(f'SELECT * FROM "{history_table}"')

            if history.empty:
                st.info("The score history table has no records.")

            else:
                st.success(f"History source: {history_table}")

                supplier_col = next(
                    (c for c in ["supplier_id"] if c in history.columns),
                    None
                )

                score_col = next(
                    (
                        c for c in [
                            "final_score",
                            "overall_score",
                            "reliability_score",
                            "score"
                        ]
                        if c in history.columns
                    ),
                    None
                )

                date_col = next(
                    (
                        c for c in [
                            "scoring_period",
                            "score_date",
                            "calculated_at",
                            "created_at",
                            "recorded_at"
                        ]
                        if c in history.columns
                    ),
                    None
                )

                if not supplier_col or not score_col or not date_col:
                    st.warning(
                        "The history table does not contain the expected "
                        "supplier, score and date columns."
                    )

                    st.write("Available columns:", list(history.columns))

                else:
                    history[score_col] = pd.to_numeric(
                        history[score_col], errors="coerce"
                    )

                    history[date_col] = pd.to_datetime(
                        history[date_col], errors="coerce"
                    )

                    history = history.dropna(
                        subset=[score_col, date_col]
                    )

                    supplier_options = ["All"] + sorted(
                        history[supplier_col]
                        .dropna().astype(str).unique().tolist()
                    )

                    selected_history_supplier = st.selectbox(
                        "Filter Supplier",
                        supplier_options,
                        key="history_supplier"
                    )

                    filtered_history = history.copy()

                    if selected_history_supplier != "All":
                        filtered_history = filtered_history[
                            filtered_history[supplier_col].astype(str)
                            == selected_history_supplier
                        ]

                    h1, h2, h3 = st.columns(3)

                    h1.metric(
                        "History Records",
                        f"{len(filtered_history):,}"
                    )

                    h2.metric(
                        "Average Historical Score",
                        safe_number(filtered_history[score_col].mean())
                    )

                    h3.metric(
                        "Suppliers in View",
                        f"{filtered_history[supplier_col].nunique():,}"
                    )

                    st.divider()
                    st.markdown("### Historical Score Trend")

                    if not filtered_history.empty:
                        trend = filtered_history.sort_values(date_col)

                        if selected_history_supplier == "All":
                            fig = px.line(
                                trend,
                                x=date_col,
                                y=score_col,
                                color=supplier_col,
                                markers=True,
                                title="Supplier Score History"
                            )
                        else:
                            fig = px.line(
                                trend,
                                x=date_col,
                                y=score_col,
                                markers=True,
                                title=f"Score Trend - {selected_history_supplier}"
                            )

                        fig.update_layout(
                            yaxis_title="Score",
                            xaxis_title="Scoring Date",
                            yaxis_range=[0, 100]
                        )

                        st.plotly_chart(fig, use_container_width=True)

                    else:
                        st.info("No history records match this filter.")

                    st.markdown("### Historical Score Records")

                    st.dataframe(
                        filtered_history.sort_values(
                            date_col, ascending=False
                        ),
                        use_container_width=True,
                        hide_index=True
                    )

                    st.download_button(
                        "⬇ Download Score History",
                        data=csv_bytes(filtered_history),
                        file_name="supplier_score_history.csv",
                        mime="text/csv"
                    )

        except Exception as error:
            st.error(f"Unable to load score history: {error}")


# =====================================================
# DATA QUALITY AND VALIDATION
# =====================================================

elif page == "Data Quality & Validation":

    st.markdown("## Data Quality & Validation")

    st.caption(
        "Inspect database completeness, duplicate records, "
        "foreign-key integrity and recorded exceptions."
    )

    tables = get_tables()

    st.markdown("### Database Summary")

    q1, q2, q3 = st.columns(3)

    q1.metric("Database Tables", f"{len(tables):,}")
    q2.metric("Supplier Records", f"{len(suppliers):,}")
    q3.metric("Data Quality Exceptions", f"{len(exceptions):,}")

    st.divider()
    st.markdown("### Table Inventory")

    inventory = []

    for table in tables:
        try:
            data = load_data(f'SELECT * FROM "{table}"')

            inventory.append({
                "Table": table,
                "Records": len(data),
                "Columns": len(data.columns),
                "Duplicate Rows": int(data.duplicated().sum())
            })

        except Exception as error:
            inventory.append({
                "Table": table,
                "Records": "Error",
                "Columns": "Error",
                "Duplicate Rows": str(error)
            })

    inventory_df = pd.DataFrame(inventory)

    st.dataframe(
        inventory_df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇ Download Table Inventory",
        data=csv_bytes(inventory_df),
        file_name="database_table_inventory.csv",
        mime="text/csv"
    )

    st.divider()
    st.markdown("### Column Completeness Analysis")

    if tables:
        selected_quality_table = st.selectbox(
            "Select Table for Validation",
            tables,
            key="quality_table"
        )

        quality_data = load_data(
            f'SELECT * FROM "{selected_quality_table}"'
        )

        if quality_data.empty:
            st.info("The selected table contains no records.")

        else:
            missing_rows = []

            for column in quality_data.columns:
                missing_count = int(quality_data[column].isna().sum())

                missing_rows.append({
                    "Column": column,
                    "Missing Values": missing_count,
                    "Missing Percentage": round(
                        missing_count / len(quality_data) * 100, 2
                    ),
                    "Present Values": len(quality_data) - missing_count
                })

            missing_df = pd.DataFrame(missing_rows)

            duplicate_count = int(quality_data.duplicated().sum())
            total_missing = int(quality_data.isna().sum().sum())

            a, b, c = st.columns(3)

            a.metric("Total Rows", f"{len(quality_data):,}")
            b.metric("Missing Cells", f"{total_missing:,}")
            c.metric("Duplicate Rows", f"{duplicate_count:,}")

            st.dataframe(
                missing_df,
                use_container_width=True,
                hide_index=True
            )

            fig = px.bar(
                missing_df,
                x="Column",
                y="Missing Values",
                text="Missing Values",
                title="Missing Values by Column"
            )

            fig.update_traces(marker_color="#d97736")
            st.plotly_chart(fig, use_container_width=True)

            st.download_button(
                "⬇ Download Column Validation Report",
                data=csv_bytes(missing_df),
                file_name=f"{selected_quality_table}_validation.csv",
                mime="text/csv"
            )

    st.divider()
    st.markdown("### Foreign Key Integrity Check")

    try:
        conn = get_connection()

        try:
            fk_violations = pd.read_sql_query(
                "PRAGMA foreign_key_check",
                conn
            )
        finally:
            conn.close()

        if fk_violations.empty:
            st.success("No foreign-key violations found.")

        else:
            st.error(
                f"{len(fk_violations)} foreign-key violations found."
            )

            st.dataframe(
                fk_violations,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇ Download Foreign Key Violations",
                data=csv_bytes(fk_violations),
                file_name="foreign_key_violations.csv",
                mime="text/csv"
            )

    except Exception as error:
        st.error(f"Unable to perform foreign-key check: {error}")

    st.divider()
    st.markdown("### Recorded Data Quality Exceptions")

    if not exceptions.empty:

        st.warning(
            f"{len(exceptions):,} exception records are present."
        )

        st.dataframe(
            exceptions,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Data Quality Exceptions",
            data=csv_bytes(exceptions),
            file_name="data_quality_exceptions.csv",
            mime="text/csv"
        )

    else:
        st.success("No recorded data quality exceptions.")

    st.info(
        "This page performs database-level checks on missing values, "
        "duplicate rows and foreign-key integrity. These checks are not "
        "a replacement for the project's separate anomaly-validation "
        "tests or ground-truth evaluation."
    )


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

    if not available_tables:
        st.warning("No supported database tables were found.")

    else:
        selected_table = st.selectbox(
            "Select Database Table",
            available_tables
        )

        limit = st.selectbox(
            "Records to Display",
            [100, 250, 500, 1000],
            index=0
        )

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
            data=csv_bytes(table_data),
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
