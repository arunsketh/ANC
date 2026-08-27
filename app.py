from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Over-Ear Headphone Benchmarks",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "data" / "headphones.csv"

# Bass text-to-score mapping dictionary
BASS_SCORE_MAP = {
    "Neutral": 6.0,
    "Balanced": 7.5,
    "Bass-Heavy": 9.2,
}


@st.cache_data
def load_and_clean_data() -> pd.DataFrame:
    raw_df = pd.read_csv(DATA_PATH)

    # Clean numeric casts
    raw_df["Price_GBP"] = pd.to_numeric(raw_df["Price_GBP"], errors="coerce")
    raw_df["ANC_dB"] = pd.to_numeric(raw_df["ANC_dB"], errors="coerce")
    raw_df["Sound_Quality"] = pd.to_numeric(raw_df["Sound_Quality"], errors="coerce")
    raw_df["Durability"] = pd.to_numeric(raw_df["Durability"], errors="coerce")

    # Clean text columns and map Bass to numerical score
    raw_df["Bass_Profile"] = raw_df["Bass_Intensity"].astype(str).str.strip()
    raw_df["Bass_Score"] = (
        raw_df["Bass_Profile"].map(BASS_SCORE_MAP).fillna(7.5)
    )

    return raw_df.dropna(subset=["Price_GBP", "ANC_dB", "Sound_Quality"])


df = load_and_clean_data()

# Numerical metrics available for Y-Axis plotting & averaging
NUMERICAL_METRICS = {
    "ANC Attenuation (dB)": "ANC_dB",
    "Sound Quality (1-10)": "Sound_Quality",
    "Bass Score (Numeric 1-10)": "Bass_Score",
    "Durability (1-10)": "Durability",
    "Price (£ GBP)": "Price_GBP",
}

# ----------------- SIDEBAR -----------------
st.sidebar.title("🎛️ Dashboard Controls")

view_mode = st.sidebar.radio(
    "Select Visualization Mode",
    options=[
        "1. Dynamic 2D Explorer (Multi-Y Average)",
        "2. Multi-Metric 2x2 Grid",
        "3. Categorical Distributions",
        "4. Head-to-Head Comparison",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Global Filters")

min_p, max_p = int(df["Price_GBP"].min()), int(df["Price_GBP"].max())
price_range = st.sidebar.slider(
    "Price Range (£ GBP)", min_p, max_p, (min_p, max_p), step=10
)

all_brands = sorted(df["Brand"].unique().tolist())
selected_brands = st.sidebar.multiselect("Brand", all_brands, default=all_brands)

all_fits = sorted(df["Earcup_Fit"].unique().tolist())
selected_fits = st.sidebar.multiselect("Earcup Fit", all_fits, default=all_fits)

all_bass = sorted(df["Bass_Profile"].unique().tolist())
selected_bass = st.sidebar.multiselect("Bass Profile", all_bass, default=all_bass)

all_tiers = sorted(df["Tier"].unique().tolist())
selected_tiers = st.sidebar.multiselect("Tier", all_tiers, default=all_tiers)

# Filter Dataframe
fdf = df[
    (df["Price_GBP"] >= price_range[0])
    & (df["Price_GBP"] <= price_range[1])
    & (df["Brand"].isin(selected_brands))
    & (df["Earcup_Fit"].isin(selected_fits))
    & (df["Bass_Profile"].isin(selected_bass))
    & (df["Tier"].isin(selected_tiers))
].copy()

# ----------------- TOP METRICS -----------------
st.title("🎧 Over-Ear Headphone Benchmarks")

if fdf.empty:
    st.warning("No headphones match your filter criteria. Adjust the sidebar filters.")
    st.stop()

col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
col_kpi1.metric("Filtered Models", len(fdf))
col_kpi2.metric("Avg Price", f"£{fdf['Price_GBP'].mean():.1f}")
col_kpi3.metric("Peak ANC", f"{fdf['ANC_dB'].max()} dB")
col_kpi4.metric("Top Sound Score", f"{fdf['Sound_Quality'].max()}/10")
col_kpi5.metric("Top Bass Score", f"{fdf['Bass_Score'].max()}/10")

st.markdown("---")

# ----------------- VIEW 1: DYNAMIC 2D EXPLORER (MULTI-Y AVERAGE) -----------------
if view_mode == "1. Dynamic 2D Explorer (Multi-Y Average)":
    st.subheader("📈 Dynamic 2D Matrix Explorer (Multi-Y Averaging)")
    st.markdown(
        "Select **multiple Y-axis metrics** below. The app will calculate the **arithmetic average** across your chosen metrics for every headphone and plot the composite score on the Y-axis."
    )

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        selected_y_labels = st.multiselect(
            "Select Y-Axis Metric(s) to Average:",
            options=list(NUMERICAL_METRICS.keys()),
            default=["ANC Attenuation (dB)"],
        )
    with c2:
        color_label = st.selectbox(
            "Color Grouping", ["Tier", "Bass_Profile", "Earcup_Fit", "Brand"], index=0
        )
    with c3:
        x_axis_label = st.selectbox(
            "X-Axis Metric", options=list(NUMERICAL_METRICS.keys()), index=4
        )

    if not selected_y_labels:
        st.warning("Please select at least one Y-axis metric.")
    else:
        # Calculate average if multiple Y metrics are chosen
        y_cols = [NUMERICAL_METRICS[label] for label in selected_y_labels]
        if len(y_cols) == 1:
            fdf["Composite_Y"] = fdf[y_cols[0]]
            y_axis_title = selected_y_labels[0]
        else:
            fdf["Composite_Y"] = fdf[y_cols].mean(axis=1)
            y_axis_title = f"Average of ({', '.})" if False else f"Averaged Metric ({len(y_cols)} selected)"

        x_col = NUMERICAL_METRICS[x_axis_label]

        fig = px.scatter(
            fdf,
            x=x_col,
            y="Composite_Y",
            color=color_label,
            hover_name="Model",
            text="Model",
            hover_data={
                "Price_GBP": ":.2f",
                "ANC_dB": True,
                "Sound_Quality": True,
                "Bass_Score": True,
                "Durability": True,
                "Composite_Y": ":.2f",
                x_col: False,
            },
            template="plotly_dark",
            height=650,
        )

        fig.update_traces(
            textposition="top center",
            textfont=dict(size=9, color="#CBD5E1"),
            marker=dict(size=11, line=dict(width=1, color="#FFFFFF")),
        )

        fig.update_layout(
            xaxis_title=x_axis_label,
            yaxis_title=y_axis_title,
            legend_title=color_label,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

# ----------------- VIEW 2: MULTI-METRIC 2x2 GRID -----------------
elif view_mode == "2. Multi-Metric 2x2 Grid":
    st.subheader("📊 4-Way Multi-Metric Benchmark vs. Price")

    g1, g2 = st.columns(2)
    with g1:
        fig_anc = px.scatter(
            fdf,
            x="Price_GBP",
            y="ANC_dB",
            color="Tier",
            hover_name="Model",
            title="ANC Attenuation (dB) vs. Price (£)",
            template="plotly_dark",
            height=400,
        )
        fig_anc.update_traces(marker=dict(size=8))
        st.plotly_chart(fig_anc, use_container_width=True)

        fig_bass = px.scatter(
            fdf,
            x="Price_GBP",
            y="Bass_Score",
            color="Bass_Profile",
            hover_name="Model",
            title="Bass Score (Numeric) vs. Price (£)",
            template="plotly_dark",
            height=400,
        )
        fig_bass.update_traces(marker=dict(size=8))
        st.plotly_chart(fig_bass, use_container_width=True)

    with g2:
        fig_sq = px.scatter(
            fdf,
            x="Price_GBP",
            y="Sound_Quality",
            color="Tier",
            hover_name="Model",
            title="Sound Quality (1-10) vs. Price (£)",
            template="plotly_dark",
            height=400,
        )
        fig_sq.update_traces(marker=dict(size=8))
        st.plotly_chart(fig_sq, use_container_width=True)

        fig_dur = px.scatter(
            fdf,
            x="Price_GBP",
            y="Durability",
            color="Tier",
            hover_name="Model",
            title="Durability (1-10) vs. Price (£)",
            template="plotly_dark",
            height=400,
        )
        fig_dur.update_traces(marker=dict(size=8))
        st.plotly_chart(fig_dur, use_container_width=True)

# ----------------- VIEW 3: CATEGORICAL DISTRIBUTIONS -----------------
elif view_mode == "3. Categorical Distributions":
    st.subheader("📦 Distribution Analysis by Profile, Fit, and Tier")

    d1, d2 = st.columns(2)
    with d1:
        cat_group = st.selectbox(
            "Categorical Grouping", ["Bass_Profile", "Earcup_Fit", "Tier"]
        )
        num_target = st.selectbox(
            "Metric to Inspect",
            ["ANC_dB", "Sound_Quality", "Bass_Score", "Price_GBP", "Durability"],
        )

        fig_box = px.box(
            fdf,
            x=cat_group,
            y=num_target,
            color=cat_group,
            points="all",
            hover_name="Model",
            template="plotly_dark",
            title=f"{num_target} Distribution grouped by {cat_group}",
            height=500,
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with d2:
        fig_bar = px.histogram(
            fdf,
            x=cat_group,
            color="Tier",
            barmode="group",
            template="plotly_dark",
            title=f"Headphone Count by {cat_group} & Tier",
            height=500,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ----------------- VIEW 4: HEAD-TO-HEAD COMPARISON -----------------
elif view_mode == "4. Head-to-Head Comparison":
    st.subheader("⚔️ Head-to-Head Model Comparator")

    selected_models = st.multiselect(
        "Choose 2 to 5 models to compare directly:",
        options=fdf["Model"].tolist(),
        default=fdf["Model"].tolist()[:3] if len(fdf) >= 3 else fdf["Model"].tolist(),
    )

    if len(selected_models) < 2:
        st.info("Select at least 2 models to render the comparison.")
    else:
        comp_df = fdf[fdf["Model"].isin(selected_models)]

        r1, r2 = st.columns([1, 1])

        with r1:
            radar_categories = [
                "ANC (Norm)",
                "Sound Quality",
                "Bass Score",
                "Durability",
                "Value (Score/£)",
            ]
            fig_radar = go.Figure()

            for _, row in comp_df.iterrows():
                anc_norm = (row["ANC_dB"] / 40.0) * 10.0
                val_norm = min(10.0, (row["Sound_Quality"] / row["Price_GBP"]) * 200.0)

                scores = [
                    anc_norm,
                    row["Sound_Quality"],
                    row["Bass_Score"],
                    row["Durability"],
                    val_norm,
                ]
                scores.append(scores[0])

                fig_radar.add_trace(
                    go.Scatterpolar(
                        r=scores,
                        theta=radar_categories + [radar_categories[0]],
                        fill="toself",
                        name=row["Model"],
                    )
                )

            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 10], color="#94A3B8")
                ),
                template="plotly_dark",
                title="Performance Radar (Normalized 0-10 Scale)",
                height=480,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with r2:
            st.write("#### Metric Breakdown")
            summary_table = comp_df[
                [
                    "Model",
                    "Brand",
                    "Price_GBP",
                    "ANC_dB",
                    "Sound_Quality",
                    "Bass_Score",
                    "Bass_Profile",
                    "Durability",
                    "Earcup_Fit",
                    "Tier",
                ]
            ].set_index("Model")
            st.dataframe(summary_table.T, use_container_width=True)

# ----------------- EXPANDABLE DATA EXPLORER & EXPORT -----------------
with st.expander("📥 Filtered Data Table & CSV Export"):
    st.dataframe(fdf.sort_values(by="Price_GBP"), use_container_width=True)
    csv_bytes = fdf.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Filtered CSV",
        data=csv_bytes,
        file_name="headphones_filtered.csv",
        mime="text/csv",
    )
