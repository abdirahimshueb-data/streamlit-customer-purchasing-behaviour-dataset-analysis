
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Customer Purchasing Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F7FB;
    }

    [data-testid="stSidebar"] {
        background-color: #EAF0F8;
    }

    .main-title {
        font-size: 34px;
        font-weight: 800;
        color: #16324F;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #64748B;
        font-size: 15px;
        margin-bottom: 24px;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        padding: 20px;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #16324F;
        font-weight: 800;
    }

    .section-title {
        color: #16324F;
        font-size: 22px;
        font-weight: 750;
        margin-top: 16px;
        margin-bottom: 12px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 3. EXPECTED DATASET COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "user_id",
    "age",
    "annual_income",
    "purchase_amount",
    "loyalty_score",
    "region",
    "purchase_frequency"
]

NUMERIC_COLUMNS = [
    "user_id",
    "age",
    "annual_income",
    "purchase_amount",
    "loyalty_score",
    "purchase_frequency"
]

# ============================================================
# 4. DATA LOADING
# ============================================================

@st.cache_data
def load_data(file_source):
    df = pd.read_csv(file_source)

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    # Remove accidental spaces from region names
    if "region" in df.columns:
        df["region"] = df["region"].astype("string").str.strip()

    # Convert numeric columns to numeric types
    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column], errors="coerce"
            )

    return df


def validate_data(df):
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        st.error(
            "The dataset is missing these required columns: "
            + ", ".join(missing_columns)
        )
        st.info(
            "Please upload the correct Customer Purchasing "
            "Behaviors CSV file."
        )
        st.stop()

    return df


# ============================================================
# 5. SIDEBAR AND FILE UPLOAD
# ============================================================

st.sidebar.title("🛍️ Customer Intelligence")
st.sidebar.caption("Purchasing behavior analytics")

uploaded_file = st.sidebar.file_uploader(
    "Upload your customer CSV",
    type=["csv"],
    help="Upload Customer-Purchasing-Behaviors.csv"
)

default_path = Path("Customer-Purchasing-Behaviors.csv")

try:
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        source_name = uploaded_file.name

    elif default_path.exists():
        df = load_data(str(default_path))
        source_name = default_path.name

    else:
        st.markdown(
            '<div class="main-title">'
            'Customer Purchasing Intelligence</div>',
            unsafe_allow_html=True
        )

        st.warning(
            "Upload your CSV file using the sidebar, or place "
            "Customer-Purchasing-Behaviors.csv in the same "
            "folder as app.py."
        )

        st.code(
            """
            project_folder/
                app.py
                Customer-Purchasing-Behaviors.csv
            """,
            language="text"
        )

        st.stop()

except Exception as error:
    st.error(f"Unable to read the CSV file: {error}")
    st.stop()

df = validate_data(df)

if df.empty:
    st.error("The uploaded dataset contains no records.")
    st.stop()

# ============================================================
# 6. DATA PREPARATION
# ============================================================

df = df.copy()

# Treat blank region values as missing
df["region"] = df["region"].replace("", pd.NA)

# Preserve original data for quality checks
original_row_count = len(df)

# ============================================================
# 7. DASHBOARD HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    'Customer Purchasing Intelligence</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Understand customer spending, loyalty, income, '
    'and regional purchasing patterns.</div>',
    unsafe_allow_html=True
)

st.caption(
    f"Data source: {source_name}  |  "
    f"Records loaded: {original_row_count:,}"
)

# ============================================================
# 8. DATA QUALITY OVERVIEW
# ============================================================

with st.expander("Inspect data quality and dataset structure"):

    quality_col1, quality_col2, quality_col3 = st.columns(3)

    quality_col1.metric(
        "Rows",
        f"{len(df):,}"
    )

    quality_col2.metric(
        "Columns",
        f"{df.shape[1]:,}"
    )

    quality_col3.metric(
        "Duplicate rows",
        f"{df.duplicated().sum():,}"
    )

    missing_data = pd.DataFrame({
        "Column": df.columns,
        "Missing values": df.isna().sum().values,
        "Missing percentage": (
            df.isna().mean().values * 100
        ).round(2)
    })

    st.markdown("#### Missing values")
    st.dataframe(
        missing_data,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### Descriptive statistics")
    st.dataframe(
        df.describe(include="all").transpose(),
        use_container_width=True
    )

# ============================================================
# 9. FILTER PANEL
# ============================================================

st.sidebar.divider()
st.sidebar.subheader("Filter customers")

region_values = sorted(
    df["region"].dropna().unique().tolist()
)

selected_regions = st.sidebar.multiselect(
    "Region",
    options=region_values,
    default=region_values
)

def get_numeric_range(data, column):
    values = data[column].dropna()

    if values.empty:
        return None

    minimum = float(values.min())
    maximum = float(values.max())

    return minimum, maximum


age_range = get_numeric_range(df, "age")
income_range = get_numeric_range(df, "annual_income")
purchase_range = get_numeric_range(df, "purchase_amount")
loyalty_range = get_numeric_range(df, "loyalty_score")

frequency_range = get_numeric_range(df, "purchase_frequency")


def numeric_filter(label, column, value_range, step=1.0):
    if value_range is None:
        st.sidebar.caption(
            f"{label}: no valid numeric values available"
        )
        return None

    minimum, maximum = value_range

    if minimum == maximum:
        st.sidebar.caption(
            f"{label}: {minimum:,.2f}"
        )
        return minimum, maximum

    return st.sidebar.slider(
        label,
        min_value=minimum,
        max_value=maximum,
        value=(minimum, maximum),
        step=step
    )


selected_age = numeric_filter(
    "Customer age",
    "age",
    age_range,
    1.0
)

selected_income = numeric_filter(
    "Annual income",
    "annual_income",
    income_range,
    1000.0
)

selected_purchase = numeric_filter(
    "Purchase amount",
    "purchase_amount",
    purchase_range,
    10.0
)

selected_loyalty = numeric_filter(
    "Loyalty score",
    "loyalty_score",
    loyalty_range,
    0.1
)

selected_frequency = numeric_filter(
    "Purchase frequency",
    "purchase_frequency",
    frequency_range,
    1.0
)

# ============================================================
# 10. APPLY FILTERS
# ============================================================

filtered_df = df.copy()

filtered_df = filtered_df[
    filtered_df["region"].isin(selected_regions)
]

filters = [
    ("age", selected_age),
    ("annual_income", selected_income),
    ("purchase_amount", selected_purchase),
    ("loyalty_score", selected_loyalty),
    ("purchase_frequency", selected_frequency)
]

for column, value_range in filters:
    if value_range is not None:
        filtered_df = filtered_df[
            filtered_df[column].between(
                value_range[0],
                value_range[1],
                inclusive="both"
            )
        ]

# Exclude missing values from relevant calculations
analysis_df = filtered_df.copy()

if analysis_df.empty:
    st.warning(
        "No customers match your selected filters. "
        "Adjust the filters in the sidebar."
    )
    st.stop()

# ============================================================
# 11. EXECUTIVE KPI CARDS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Executive Overview</div>',
    unsafe_allow_html=True
)

total_customers = len(analysis_df)

average_purchase = analysis_df[
    "purchase_amount"
].mean()

total_purchase_amount = analysis_df[
    "purchase_amount"
].sum()

average_income = analysis_df[
    "annual_income"
].mean()

average_loyalty = analysis_df[
    "loyalty_score"
].mean()

average_frequency = analysis_df[
    "purchase_frequency"
].mean()

total_frequency = analysis_df[
    "purchase_frequency"
].sum()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Customers",
    f"{total_customers:,}"
)

kpi2.metric(
    "Total Purchase Amount",
    f"{total_purchase_amount:,.2f}"
)

kpi3.metric(
    "Average Purchase",
    f"{average_purchase:,.2f}"
)

kpi4.metric(
    "Average Annual Income",
    f"{average_income:,.0f}"
)

kpi5, kpi6, kpi7, kpi8 = st.columns(4)

kpi5.metric(
    "Average Loyalty Score",
    f"{average_loyalty:.2f}"
)

kpi6.metric(
    "Average Purchase Frequency",
    f"{average_frequency:.2f}"
)

kpi7.metric(
    "Total Purchase Frequency",
    f"{total_frequency:,.0f}"
)

kpi8.metric(
    "Regions Represented",
    f"{analysis_df['region'].nunique():,}"
)

st.caption(
    "All KPIs reflect the currently filtered customers. "
    "Purchase frequency is the recorded frequency value, "
    "not necessarily a transaction count."
)

# ============================================================
# 12. REGIONAL PERFORMANCE
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Regional Performance</div>',
    unsafe_allow_html=True
)

region_summary = (
    analysis_df.groupby("region", dropna=False)
    .agg(
        customer_count=("user_id", "count"),
        average_purchase=("purchase_amount", "mean"),
        total_purchase_amount=("purchase_amount", "sum"),
        average_income=("annual_income", "mean"),
        average_loyalty=("loyalty_score", "mean"),
        average_frequency=("purchase_frequency", "mean")
    )
    .reset_index()
)

region_summary["region"] = (
    region_summary["region"].fillna("Unknown")
)

region_summary = region_summary.sort_values(
    "total_purchase_amount",
    ascending=False
)

region_col1, region_col2 = st.columns(2)

with region_col1:

    fig_region = px.bar(
        region_summary,
        x="region",
        y="total_purchase_amount",
        color="region",
        title="Total Purchase Amount by Region",
        labels={
            "region": "Region",
            "total_purchase_amount": "Total Purchase Amount"
        },
        template="plotly_white",
        text_auto=".2s"
    )

    fig_region.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        height=390
    )

    st.plotly_chart(
        fig_region,
        use_container_width=True
    )

with region_col2:

    fig_customers = px.pie(
        region_summary,
        names="region",
        values="customer_count",
        title="Customer Distribution by Region",
        hole=0.55,
        template="plotly_white"
    )

    fig_customers.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )

    fig_customers.update_layout(
        margin=dict(l=20, r=20, t=60, b=20),
        height=390
    )

    st.plotly_chart(
        fig_customers,
        use_container_width=True
    )

st.markdown("#### Regional summary table")

st.dataframe(
    region_summary.round(2),
    use_container_width=True,
    hide_index=True,
    column_config={
        "region": "Region",
        "customer_count": "Customer Count",
        "average_purchase": st.column_config.NumberColumn(
            "Average Purchase",
            format="%.2f"
        ),
        "total_purchase_amount": st.column_config.NumberColumn(
            "Total Purchase Amount",
            format="%.2f"
        ),
        "average_income": st.column_config.NumberColumn(
            "Average Income",
            format="%.2f"
        ),
        "average_loyalty": st.column_config.NumberColumn(
            "Average Loyalty",
            format="%.2f"
        ),
        "average_frequency": st.column_config.NumberColumn(
            "Average Frequency",
            format="%.2f"
        )
    }
)

# ============================================================
# 13. CUSTOMER SPENDING ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Customer Spending Analysis</div>',
    unsafe_allow_html=True
)

spending_col1, spending_col2 = st.columns(2)

with spending_col1:

    spending_data = analysis_df.dropna(
        subset=["annual_income", "purchase_amount"]
    )

    if not spending_data.empty:

        fig_income = px.scatter(
            spending_data,
            x="annual_income",
            y="purchase_amount",
            color="region",
            size="purchase_frequency",
            hover_data=[
                "user_id",
                "age",
                "loyalty_score"
            ],
            title="Annual Income vs Purchase Amount",
            labels={
                "annual_income": "Annual Income",
                "purchase_amount": "Purchase Amount",
                "region": "Region",
                "purchase_frequency": "Purchase Frequency"
            },
            template="plotly_white"
        )

        fig_income.update_layout(
            height=420,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig_income,
            use_container_width=True
        )
    else:
        st.info("No complete income and purchase records.")

with spending_col2:

    purchase_data = analysis_df.dropna(
        subset=["purchase_amount"]
    )

    if not purchase_data.empty:

        fig_purchase_distribution = px.histogram(
            purchase_data,
            x="purchase_amount",
            color="region",
            nbins=20,
            barmode="overlay",
            opacity=0.75,
            title="Distribution of Purchase Amounts",
            labels={
                "purchase_amount": "Purchase Amount",
                "count": "Number of Customers"
            },
            template="plotly_white"
        )

        fig_purchase_distribution.update_layout(
            height=420,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig_purchase_distribution,
            use_container_width=True
        )
    else:
        st.info("No valid purchase amounts available.")

# ============================================================
# 14. CUSTOMER AGE ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Customer Demographics</div>',
    unsafe_allow_html=True
)

age_col1, age_col2 = st.columns(2)

with age_col1:

    age_data = analysis_df.dropna(subset=["age"])

    if not age_data.empty:

        fig_age = px.histogram(
            age_data,
            x="age",
            nbins=15,
            title="Customer Age Distribution",
            labels={
                "age": "Customer Age",
                "count": "Number of Customers"
            },
            template="plotly_white"
        )

        fig_age.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig_age,
            use_container_width=True
        )
    else:
        st.info("No valid age data available.")

with age_col2:

    age_purchase_data = analysis_df.dropna(
        subset=["age", "purchase_amount"]
    )

    if not age_purchase_data.empty:

        fig_age_purchase = px.scatter(
            age_purchase_data,
            x="age",
            y="purchase_amount",
            color="region",
            hover_data=[
                "user_id",
                "annual_income",
                "loyalty_score"
            ],
            title="Age vs Purchase Amount",
            labels={
                "age": "Customer Age",
                "purchase_amount": "Purchase Amount",
                "region": "Region"
            },
            template="plotly_white"
        )

        fig_age_purchase.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig_age_purchase,
            use_container_width=True
        )
    else:
        st.info("No complete age and purchase records.")

# ============================================================
# 15. LOYALTY ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Customer Loyalty Analysis</div>',
    unsafe_allow_html=True
)

loyalty_col1, loyalty_col2 = st.columns(2)

with loyalty_col1:

    loyalty_data = analysis_df.dropna(
        subset=["loyalty_score"]
    )

    if not loyalty_data.empty:

        fig_loyalty = px.histogram(
            loyalty_data,
            x="loyalty_score",
            nbins=15,
            title="Distribution of Loyalty Scores",
            labels={
                "loyalty_score": "Loyalty Score",
                "count": "Number of Customers"
            },
            template="plotly_white"
        )

        fig_loyalty.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig_loyalty,
            use_container_width=True
        )
    else:
        st.info("No valid loyalty scores available.")

with loyalty_col2:

    loyalty_purchase_data = analysis_df.dropna(
        subset=["loyalty_score", "purchase_amount"]
    )

    if not loyalty_purchase_data.empty:

        fig_loyalty_purchase = px.scatter(
            loyalty_purchase_data,
            x="loyalty_score",
            y="purchase_amount",
            color="region",
            hover_data=[
                "user_id",
                "age",
                "annual_income"
            ],
            title="Loyalty Score vs Purchase Amount",
            labels={
                "loyalty_score": "Loyalty Score",
                "purchase_amount": "Purchase Amount",
                "region": "Region"
            },
            template="plotly_white"
        )

        fig_loyalty_purchase.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig_loyalty_purchase,
            use_container_width=True
        )
    else:
        st.info("No complete loyalty and purchase records.")

# ============================================================
# 16. CORRELATION ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Relationship Between Numeric Variables</div>',
    unsafe_allow_html=True
)

correlation_columns = [
    "age",
    "annual_income",
    "purchase_amount",
    "loyalty_score",
    "purchase_frequency"
]

correlation_data = analysis_df[
    correlation_columns
].dropna(how="all")

if not correlation_data.empty:

    correlation_matrix = correlation_data.corr(
        method="pearson",
        min_periods=2
    )

    fig_corr = px.imshow(
        correlation_matrix,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        origin="lower",
        title="Pearson Correlation Matrix",
        labels={
            "color": "Correlation"
        }
    )

    fig_corr.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig_corr,
        use_container_width=True
    )

    st.caption(
        "Correlation measures linear association, not causation. "
        "Values closer to 1 indicate positive association, "
        "values closer to minus 1 indicate negative association, "
        "and values near 0 indicate weak linear association."
    )

else:
    st.info("Insufficient numeric data for correlation analysis.")

# ============================================================
# 17. CUSTOMER SEGMENTATION
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Customer Segmentation</div>',
    unsafe_allow_html=True
)

segment_df = analysis_df.copy()

def assign_purchase_segment(value):
    if pd.isna(value):
        return "Unknown"
    elif value < 200:
        return "Low Spending"
    elif value < 400:
        return "Moderate Spending"
    else:
        return "High Spending"


def assign_loyalty_segment(value):
    if pd.isna(value):
        return "Unknown"
    elif value < 4:
        return "Low Loyalty"
    elif value < 7:
        return "Moderate Loyalty"
    else:
        return "High Loyalty"


segment_df["purchase_segment"] = (
    segment_df["purchase_amount"].apply(
        assign_purchase_segment
    )
)

segment_df["loyalty_segment"] = (
    segment_df["loyalty_score"].apply(
        assign_loyalty_segment
    )
)

segment_col1, segment_col2 = st.columns(2)

with segment_col1:

    purchase_segment_summary = (
        segment_df.groupby("purchase_segment")
        .agg(
            customers=("user_id", "count"),
            average_purchase=("purchase_amount", "mean"),
            total_purchase=("purchase_amount", "sum")
        )
        .reset_index()
    )

    fig_segments = px.bar(
        purchase_segment_summary,
        x="purchase_segment",
        y="customers",
        color="purchase_segment",
        title="Customers by Spending Segment",
        labels={
            "purchase_segment": "Spending Segment",
            "customers": "Customer Count"
        },
        template="plotly_white",
        text_auto=True
    )

    fig_segments.update_layout(
        showlegend=False,
        height=380,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig_segments,
        use_container_width=True
    )

with segment_col2:

    loyalty_segment_summary = (
        segment_df.groupby("loyalty_segment")
        .agg(
            customers=("user_id", "count"),
            average_loyalty=("loyalty_score", "mean"),
            average_purchase=("purchase_amount", "mean")
        )
        .reset_index()
    )

    fig_loyalty_segments = px.bar(
        loyalty_segment_summary,
        x="loyalty_segment",
        y="customers",
        color="loyalty_segment",
        title="Customers by Loyalty Segment",
        labels={
            "loyalty_segment": "Loyalty Segment",
            "customers": "Customer Count"
        },
        template="plotly_white",
        text_auto=True
    )

    fig_loyalty_segments.update_layout(
        showlegend=False,
        height=380,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig_loyalty_segments,
        use_container_width=True
    )

st.markdown("#### Spending segment summary")

st.dataframe(
    purchase_segment_summary.round(2),
    use_container_width=True,
    hide_index=True
)

st.markdown("#### Loyalty segment summary")

st.dataframe(
    loyalty_segment_summary.round(2),
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Spending thresholds are illustrative business rules, "
    "not statistically derived customer segments. "
    "Adjust them to suit your business context."
)

# ============================================================
# 18. TOP CUSTOMERS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Top Customers</div>',
    unsafe_allow_html=True
)

top_count = st.selectbox(
    "Number of customers to display",
    options=[5, 10, 20, 50],
    index=1
)

top_customers = (
    analysis_df.dropna(subset=["purchase_amount"])
    .sort_values(
        "purchase_amount",
        ascending=False
    )
    .head(top_count)
)

st.dataframe(
    top_customers[
        REQUIRED_COLUMNS
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "user_id": "Customer ID",
        "age": "Age",
        "annual_income": st.column_config.NumberColumn(
            "Annual Income",
            format="%.0f"
        ),
        "purchase_amount": st.column_config.NumberColumn(
            "Purchase Amount",
            format="%.2f"
        ),
        "loyalty_score": st.column_config.NumberColumn(
            "Loyalty Score",
            format="%.2f"
        ),
        "region": "Region",
        "purchase_frequency": "Purchase Frequency"
    }
)

# ============================================================
# 19. FULL FILTERED CUSTOMER TABLE
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Customer Records Explorer</div>',
    unsafe_allow_html=True
)

search_term = st.text_input(
    "Search by customer ID or region",
    placeholder="For example, 12 or North"
)

table_df = analysis_df.copy()

if search_term.strip():

    term = search_term.strip().lower()

    id_match = (
        table_df["user_id"]
        .astype("string")
        .str.lower()
        .str.contains(term, na=False)
    )

    region_match = (
        table_df["region"]
        .astype("string")
        .str.lower()
        .str.contains(term, na=False)
    )

    table_df = table_df[
        id_match | region_match
    ]

st.write(
    f"Showing {len(table_df):,} customer records"
)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    height=400
)

# ============================================================
# 20. DOWNLOAD FILTERED DATA
# ============================================================

st.markdown("#### Export your analysis")

csv_data = table_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download filtered customers as CSV",
    data=csv_data,
    file_name="filtered_customer_analysis.csv",
    mime="text/csv",
    use_container_width=True
)

# ============================================================
# 21. AUTOMATIC BUSINESS INSIGHTS
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Business Insights</div>',
    unsafe_allow_html=True
)

insight_col1, insight_col2 = st.columns(2)

with insight_col1:

    st.markdown("#### Purchasing insights")

    valid_purchases = analysis_df.dropna(
        subset=["purchase_amount"]
    )

    if not valid_purchases.empty:

        highest_purchase = valid_purchases.loc[
            valid_purchases["purchase_amount"].idxmax()
        ]

        lowest_purchase = valid_purchases.loc[
            valid_purchases["purchase_amount"].idxmin()
        ]

        st.write(
            f"**Highest individual purchase:** "
            f"{highest_purchase['purchase_amount']:,.2f}"
        )

        st.write(
            f"**Customer ID with highest purchase:** "
            f"{highest_purchase['user_id']}"
        )

        st.write(
            f"**Lowest individual purchase:** "
            f"{lowest_purchase['purchase_amount']:,.2f}"
        )

        st.write(
            f"**Median purchase amount:** "
            f"{valid_purchases['purchase_amount'].median():,.2f}"
        )

        st.write(
            f"**Purchase amount standard deviation:** "
            f"{valid_purchases['purchase_amount'].std():,.2f}"
        )

    else:
        st.info("No valid purchase data available.")

with insight_col2:

    st.markdown("#### Regional insights")

    valid_regions = region_summary[
        region_summary["region"] != "Unknown"
    ]

    if not valid_regions.empty:

        leading_region = valid_regions.iloc[0]

        st.write(
            f"**Region with highest total purchase amount:** "
            f"{leading_region['region']}"
        )

        st.write(
            f"**Regional total purchase amount:** "
            f"{leading_region['total_purchase_amount']:,.2f}"
        )

        largest_customer_region = (
            region_summary.sort_values(
                "customer_count",
                ascending=False
            ).iloc[0]
        )

        st.write(
            f"**Region with most customer records:** "
            f"{largest_customer_region['region']}"
        )

        st.write(
            f"**Customer records in that region:** "
            f"{largest_customer_region['customer_count']:,}"
        )

    else:
        st.info("No valid regional data available.")

# ============================================================
# 22. FOOTER
# ============================================================

st.divider()

st.caption(
    "Customer Purchasing Intelligence Dashboard | "
    "Built with Python, Pandas, Streamlit, and Plotly"
)
