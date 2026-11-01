"""Q-SHIELD - Cryptographic Performance Benchmarking Laboratory."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import bench

st.set_page_config(page_title="Benchmark Lab · Q-SHIELD", page_icon="⚡", layout="wide")

try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

COLORS = {
    "Classical": "#94a3b8",
    "ML-KEM-768": "#f59e0b",
    "ML-DSA-65": "#a855f7",
    "Hybrid": "#06b6d4",
}

st.markdown(
    """
    <div class="hero-banner">
        <h1>⚡ Cryptographic Benchmark Laboratory</h1>
        <p>Real wall-clock execution timings and exact serialized byte sizes measured on this host. Evaluates computational overhead, latency, and bandwidth impacts between classical and post-quantum algorithms.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c_cfg1, c_cfg2 = st.columns([2, 1])
with c_cfg1:
    iterations = st.slider("Measurement Iterations per Primitive", min_value=10, max_value=200, value=30, step=10)
with c_cfg2:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    run_btn = st.button("▶ Run Full Benchmark Suite", type="primary")

if run_btn:
    with st.spinner(f"Executing {iterations} iterations across all primitives..."):
        timings_df = bench.run_timings(iterations=iterations)
        sizes_df = bench.measure_sizes()
        meta = bench.get_system_metadata(iterations=iterations)
        st.session_state["bench_timings"] = timings_df
        st.session_state["bench_sizes"] = sizes_df
        st.session_state["bench_meta"] = meta
        st.success("Benchmark completed successfully!")

if "bench_timings" not in st.session_state:
    st.info("Click **Run Full Benchmark Suite** above to execute live measurements on this system.")
    sizes_df = bench.measure_sizes()
    st.markdown("#### 📏 Baseline Serialized Byte Dimensions")
    st.dataframe(sizes_df, hide_index=True, width="stretch")
else:
    timings: pd.DataFrame = st.session_state["bench_timings"]
    sizes: pd.DataFrame = st.session_state["bench_sizes"]
    meta = st.session_state["bench_meta"]

    st.markdown(
        f"""
        <div class="card" style="margin-bottom:1.2rem;">
            <div class="kv-row"><span>Host Platform</span><span class="mono">{meta['platform']}</span></div>
            <div class="kv-row"><span>Python Runtime</span><span class="mono">{meta['python_version']} ({meta['cpu_count']} CPUs available)</span></div>
            <div class="kv-row"><span>Cryptographic Libraries</span><span class="mono">cryptography {meta['cryptography_version']} · pqcrypto {meta['pqcrypto_version']}</span></div>
            <div class="kv-row"><span>Timestamp</span><span class="mono">{meta['timestamp']} ({meta['iterations']} iterations)</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    log_scale = st.checkbox("Logarithmic scale (recommended: X25519 runs in microseconds while ML-DSA runs in milliseconds)", value=True)

    # Tabs for different operational domains
    tab_overview, tab_keygen, tab_kem, tab_sig, tab_sizes, tab_raw = st.tabs([
        "📊 Overview", "🔑 Key Generation", "🤝 Key Establishment", "✍️ Digital Signatures", "📏 Memory & Transmission Sizes", "📋 Raw Data & Export"
    ])

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            fig_kg = px.bar(
                timings[timings["operation"].str.startswith("Key generation")],
                x="operation",
                y="median_ms",
                color="group",
                color_discrete_map=COLORS,
                title="Key Generation Latency (Median ms)",
                template="plotly_dark",
            )
            fig_kg.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="ms")
            if log_scale:
                fig_kg.update_yaxes(type="log")
            st.plotly_chart(fig_kg, width="stretch")

        with c2:
            fig_kem = px.bar(
                timings[timings["operation"].str.startswith("Key establishment (sender")],
                x="group",
                y="median_ms",
                color="group",
                color_discrete_map=COLORS,
                title="Full Key Establishment Sender (incl. HKDF)",
                template="plotly_dark",
            )
            fig_kem.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="ms")
            st.plotly_chart(fig_kem, width="stretch")

    with tab_keygen:
        kg_df = timings[timings["operation"].str.startswith("Key generation")]
        st.dataframe(kg_df[["group", "operation", "median_ms", "mean_ms", "min_ms", "max_ms", "p95_ms", "stdev_ms"]].round(4), hide_index=True, width="stretch")

    with tab_kem:
        kem_df = timings[timings["operation"].str.contains("Key establishment|Key recovery|Encapsulation|Decapsulation|X25519 shared")]
        st.dataframe(kem_df[["group", "operation", "median_ms", "mean_ms", "min_ms", "max_ms", "p95_ms", "stdev_ms"]].round(4), hide_index=True, width="stretch")

    with tab_sig:
        sig_df = timings[timings["operation"].str.contains("Sign|Verify")]
        fig_sig = px.bar(
            sig_df,
            x="operation",
            y="median_ms",
            color="group",
            barmode="group",
            color_discrete_map=COLORS,
            title="Digital Signatures Latency: Ed25519 vs ML-DSA-65",
            template="plotly_dark",
        )
        fig_sig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="ms")
        st.plotly_chart(fig_sig, width="stretch")
        st.dataframe(sig_df[["group", "operation", "median_ms", "mean_ms", "min_ms", "max_ms", "p95_ms", "stdev_ms"]].round(4), hide_index=True, width="stretch")

    with tab_sizes:
        c1, c2 = st.columns(2)
        with c1:
            fig_pks = px.bar(
                sizes[sizes["metric"].str.contains("Public key")],
                x="metric",
                y="bytes",
                color="group",
                color_discrete_map=COLORS,
                title="Public Key Sizes (Bytes)",
                template="plotly_dark",
            )
            fig_pks.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="Bytes")
            st.plotly_chart(fig_pks, width="stretch")
        with c2:
            fig_xfer = px.bar(
                sizes[sizes["metric"].isin(["Key-exchange data sent (ciphertext)", "Signature", "Signature (Ed25519)"])],
                x="metric",
                y="bytes",
                color="group",
                color_discrete_map=COLORS,
                title="Ciphertext & Signature Wire Transmission Sizes",
                template="plotly_dark",
            )
            fig_xfer.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="Bytes")
            st.plotly_chart(fig_xfer, width="stretch")

    with tab_raw:
        st.markdown("#### Complete Benchmarking Dataset")
        st.dataframe(timings.round(4), hide_index=True, width="stretch")
        csv_data = timings.to_csv(index=False)
        st.download_button(
            label="⬇ Download Benchmark CSV",
            data=csv_data,
            file_name="qshield_benchmark_measurements.csv",
            mime="text/csv",
            type="primary",
        )

