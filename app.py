from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Over-Ear Headphone ANC & Audio Matrix",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "headphones.csv"


@st.cache_data
def load_headphone_data() -> pd.DataFrame:
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH)
    # Fallback embedded dataset if CSV is missing
    return pd.DataFrame(
        {
            "Model": [
                "Sony WH-1000XM6", "Bose QC Ultra", "Apple AirPods Max",
                "Sony WH-1000XM5", "JBL Live 780NC", "Bose QuietComfort",
                "JBL Live 770NC", "Sony ULT Wear", "Sennheiser Accentum Plus",
                "Sennheiser Momentum 4", "Sony WH-1000XM4",
                "Anker Soundcore Space One", "QCY H3", "Sony WH-CH720N",
                "Anker Soundcore Q20i", "JLab JBuds Lux ANC", "Ugreen HiTune Max5c",
            ],
            "Brand": [
                "Sony", "Bose", "Apple", "Sony", "JBL", "Bose", "JBL", "Sony",
                "Sennheiser", "Sennheiser", "Sony", "Anker", "QCY", "Sony",
                "Anker", "JLab", "Ugreen",
            ],
            "Price_GBP": [350, 450, 499, 279, 142, 300, 89, 99, 170, 250, 200, 69, 46, 70, 32, 60, 23],
            "ANC_dB": [33, 32, 31, 31, 29, 29, 29, 28, 27, 27, 27, 24, 22, 21, 20, 18, 18],
            "Sound_Quality": [9.2, 8.8, 9.0, 8.9, 7.8, 8.5, 7.5, 7.2, 8.2, 9.4, 8.5, 7.0, 6.0, 7.2, 6.5, 6.8, 5.5],
            "Bass_Intensity": [8.5, 8.0, 7.5, 8.2, 8.5, 7.8, 8.0, 10.0, 7.5, 8.2, 8.8, 7.5, 7.0, 7.0, 8.0, 7.5, 6.5],
            "Durability": [8.5, 8.5, 9.8, 8.0, 8.0, 8.5, 7.5, 7.5, 8.0, 8.5, 7.8, 7.0, 6.5, 7.0, 6.5, 7.0, 6.0],
            "Earcup_Fit": ["Large Over-Ear"] * 17,
            "Tier": [
                "Flagship", "Flagship", "Flagship", "Flagship", "Premium",
                "Premium", "Premium", "Premium", "Premium", "Premium",
                "Premium", "Everyday", "Everyday", "Everyday", "Everyday",
                "Basic", "Basic",
            ],
        }
    )


df = load_headphone_data()

METRIC_CONFIG = {
    "Active Noise Cancellation (dB)": {
        "col": "ANC_dB",
        "unit": " dB",
        "desc": "Real-world average attenuation across low and mid frequencies.",
    },
    "Sound Quality (1-10)": {
        "col": "Sound_Quality",
        "unit": "/10",
        "desc": "Acoustic balance, soundstage width, and driver resolution.",
    },
    "Bass Punch (1-10)": {
        "col": "Bass_Intensity",
        "unit": "/10",
        "desc": "Sub-bass extension, punch, and low-end impact.",
    },
    "Durability & Build (1-10)": {
        "col": "Durability",
        "unit": "/10",
        "desc": "Chassis rigidity, hinge quality, and material longevity.",
    },
}

# Sidebar Controls
st.sidebar.title("🎛️ Filter & Axes")

selected_metric_label = st.sidebar.selectbox(
    "Select Dynamic Y-Axis Metric",
    options=list(METRIC_CONFIG.keys()),
    index=0,
)
active_metric = METRIC_CONFIG[selected_metric_label]

min_price = int(df["Price_GBP"].min())
max_price = int(df["Price_GBP"].max())

price_range = st.sidebar.slider(
    "Price Range (£ GBP)",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price),
    step=5,
)

available_brands = sorted(df["Brand"].unique().tolist())
selected_brands = st.sidebar.multiselect(
    "Filter by Brand",
    options=available_brands,
    default=available_brands,
)

available_tiers = sorted(df["Tier"].unique().tolist())
selected_tiers = st.sidebar.multiselect(
    "Filter by Performance Tier",
    options=available_tiers,
    default=available_tiers,
)

# Data Filtering
filtered_df = df[
    (df["Price_GBP"] >= price_range[0])
    & (df["Price_GBP"] <= price_range[1])
    & (df["Brand"].isin(selected_brands))
    & (df["Tier"].isin(selected_tiers))
].copy()

# Header Section
st.title("🎧 Over-Ear Headphone Benchmark Matrix")
st.caption(f"Analyzing {len(filtered_df)} over-ear models | {active_metric['desc']}")

# Top KPI Summary Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
if not filtered_df.empty:
    top_performer = filtered_df.loc[filtered_df[active_metric["col"]].idxmax()]
    best_value = filtered_df.copy()
    best_value["Value_Ratio"] = (
        best_value[active_metric["col"]] / best_value["Price_GBP"]
    )
    top_value_model = best_value.loc[best_value["Value_Ratio"].idxmax()]

    kpi1.metric("Selected Models", len(filtered_df))
    kpi2.metric("Average Price", f"£{filtered_df['Price_GBP'].mean():.2f}")
    kpi3.metric(
        f"Top {selected_metric_label.split()[0]}",
        f"{top_performer['Model']}",
        f"{top_performer[active_metric['col']]}{active_metric['unit']}",
    )
    kpi4.metric(
        "Best Value Pick",
        f"{top_value_model['Model']}",
        f"£{top_value_model['Price_GBP']}",
    )

st.markdown("---")

# Main Interactive Chart
if filtered_df.empty:
    st.warning("No headphones match your selected filter criteria. Adjust the sidebar filters.")
else:
    fig = px.scatter(
        filtered_df,
        x="Price_GBP",
        y=active_metric["col"],
        color="Tier",
        hover_name="Model",
        text="Model",
        hover_data={
            "Price_GBP": ":.2f",
            active_metric["col"]: True,
            "Tier": True,
            "Brand": True,
        },
        labels={
            "Price_GBP": "Typical Retail Price (£ GBP)",
            active_metric["col"]: selected_metric_label,
        },
        template="plotly_dark",
        height=620,
    )

    fig.update_traces(
        marker=dict(size=14, line=dict(width=1.5, color="#FFFFFF"), opacity=0.9),
        textposition="top center",
        textfont=dict(size=10, color="#E2E8F0"),
    )

    fig.update_layout(
        xaxis=dict(tickprefix="£", showgrid=True, gridcolor="#334155"),
        yaxis=dict(ticksuffix=active_metric["unit"], showgrid=True, gridcolor="#334155"),
        legend=dict(
            title="Performance Tier",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

# Expandable Data Explorer
with st.expander("📊 View Detailed Data Table & Export", expanded=False):
    display_df = filtered_df[
        [
            "Model",
            "Brand",
            "Price_GBP",
            "ANC_dB",
            "Sound_Quality",
            "Bass_Intensity",
            "Durability",
            "Tier",
        ]
    ].rename(
        columns={
            "Price_GBP": "Price (£)",
            "ANC_dB": "ANC (dB)",
            "Sound_Quality": "Sound (1-10)",
            "Bass_Intensity": "Bass (1-10)",
            "Durability": "Durability (1-10)",
        }
    )
    st.dataframe(display_df.sort_values(by="Price (£)"), use_container_width=True)

    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_data,
        file_name="headphone_matrix_export.csv",
        mime="text/csv",
    )
