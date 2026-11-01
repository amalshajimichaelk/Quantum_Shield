"""Q-SHIELD - Quantum Threat Laboratory (Shor's Factoring Algorithm using Qiskit Aer)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import quantum as qm
from services.quantum_service import run_quantum_threat_experiment

st.set_page_config(page_title="Quantum Threat Lab · Q-SHIELD", page_icon="⚛️", layout="wide")

try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown(
    """
    <div class="hero-banner">
        <h1>⚛️ Quantum Threat Laboratory</h1>
        <p>Explore how quantum algorithms challenge conventional public-key cryptography. Demonstrating Shor's Factoring Algorithm and Quantum Phase Estimation on the local Qiskit Aer simulator.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.warning(
    "⚠️ **Important Engineering Disclaimer:** This experiment demonstrates Shor's algorithm on a small composite integer (N=15) "
    "using a high-performance quantum simulator (Qiskit Aer). It proves the theoretical polynomial-time threat model to RSA and discrete-log "
    "cryptography, but does NOT demonstrate the current physical ability to factor RSA-2048 or ECC-256 keys, which require millions of physical fault-tolerant qubits."
)

st.markdown("### 🎛️ Experiment Configuration")
cfg1, cfg2, cfg3, cfg4 = st.columns([1, 1, 2, 1])
with cfg1:
    target_N = st.selectbox("Target Integer N", [15], index=0, help="N=15 (3 × 5) canonical demonstration integer")
with cfg2:
    selected_a = st.selectbox("Coprime Base a", [2, 7, 8, 11, 13], index=0, help="Must satisfy gcd(a, N) = 1")
with cfg3:
    shots = st.slider("Measurement Shots", min_value=256, max_value=4096, value=1024, step=256)
with cfg4:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    execute_btn = st.button("⚛️ Execute Quantum Circuit", type="primary")

# Visual Workflow Pipeline
st.markdown("### 🔄 Shor's Algorithm Execution Pipeline")
st.markdown(
    """
    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:1.5rem;">
        <span class="badge badge-info">1. Target N=15, a=2</span> →
        <span class="badge badge-info">2. Superposition (Hadamards)</span> →
        <span class="badge badge-info">3. Modular Exponentiation (CSWAP/U)</span> →
        <span class="badge badge-info">4. Inverse QFT</span> →
        <span class="badge badge-info">5. Measurement</span> →
        <span class="badge badge-info">6. Continued Fractions</span> →
        <span class="badge badge-ok">7. Verified Factorization</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if execute_btn:
    with st.spinner(f"Building circuit, transpiling, and simulating {shots} shots on Qiskit Aer..."):
        result = run_quantum_threat_experiment(N=target_N, a=selected_a, shots=shots)
        st.session_state["shor_result"] = result

if "shor_result" not in st.session_state:
    st.info("Click **⚛️ Execute Quantum Circuit** above to construct the 8-qubit QPE circuit, transpile it for AerSimulator, and factor N=15.")
    circ = qm.build_shor_circuit(N=target_N, a=selected_a, num_counting_qubits=4)
    st.markdown("### 🔌 Circuit Architecture Preview (8 Qubits)")
    st.caption("Theoretical Quantum Phase Estimation circuit constructed with Qiskit 2.x.")
    with st.expander("Expand ASCII Circuit Diagram", expanded=True):
        st.code(qm.circuit_to_ascii(circ), language=None)
else:
    res: qm.ShorResult = st.session_state["shor_result"]

    # Status Banner
    if res.success and res.verified_factorization:
        p, q = res.verified_factorization
        st.markdown(
            f"""
            <div style="padding:1.2rem; border-radius:12px; background:rgba(16, 185, 129, 0.15); border:1px solid #10b981; margin-bottom:1.2rem;">
                <h3 style="margin:0 0 0.4rem 0; color:#10b981;">🎉 Quantum Factorization Succeeded: {res.target_number} = {p} × {q}</h3>
                <p style="margin:0; color:#94a3b8; font-size:0.95rem;">{res.explanation}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.error(f"Factorization Outcome: {res.explanation}")

    # Circuit Telemetry Metrics
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total Qubits", f"{res.num_qubits} Qubits", "4 Count + 4 Work")
    with k2:
        st.metric("Circuit Depth", f"{res.circuit_depth}", "Pre-transpilation")
    with k3:
        st.metric("Transpiled Depth", f"{res.transpiled_circuit_metadata.get('transpiled_depth', 'N/A')}", "Aer Native")
    with k4:
        st.metric("Simulation Time", f"{res.execution_time_ms:.2f} ms", f"{res.measurement_shots} shots")
    with k5:
        st.metric("Recovered Order r", f"r = {res.estimated_order}", f"{res.selected_base}^{res.estimated_order} ≡ 1 mod {res.target_number}")

    st.markdown("---")

    col_hist, col_diag = st.columns([3, 2])

    with col_hist:
        st.markdown("### 📊 Quantum Measurement Histogram")
        st.caption("Distribution of measured states in the counting register over all shots. Peaks correspond to fractional phase eigenvalues.")

        counts_data = [
            {"Bitstring": k, "Decimal": int(k, 2), "Shots": v, "Probability": v / res.measurement_shots}
            for k, v in res.measurement_counts.items()
        ]
        df_counts = pd.DataFrame(counts_data).sort_values("Decimal")

        fig = px.bar(
            df_counts,
            x="Bitstring",
            y="Shots",
            hover_data=["Decimal", "Probability"],
            text="Shots",
            title=f"AerSimulator Measurement Distribution (N={res.target_number}, a={res.selected_base})",
            template="plotly_dark",
            color="Shots",
            color_continuous_scale="teal",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Measured Counting Bitstring", yaxis_title="Shot Frequency")
        st.plotly_chart(fig, width="stretch")

    with col_diag:
        st.markdown("### 🔌 Real Quantum Circuit Diagram")
        st.caption("Generated directly from Qiskit QuantumCircuit data structures.")
        with st.expander("Expand ASCII Circuit Diagram", expanded=True):
            st.code(res.circuit_ascii, language=None)

    st.markdown("---")
    st.markdown("### 🧮 Classical Post-Processing: Step-by-Step Continued Fractions Breakdown")
    st.caption("How quantum measurement outcomes map to phase estimations, fraction approximations, and factor extraction.")

    records = []
    for d in res.detailed_measurements:
        records.append({
            "Bitstring": d["bitstring"],
            "Value": d["integer_value"],
            "Count": d["count"],
            "Phase (θ)": f"{d['phase']:.4f}",
            "Fraction (s/r)": d["fraction"],
            "Candidate r": d["candidate_r"],
            "Valid Order?": "YES" if d["order_valid"] else "NO",
            "Recovered Factors": str(d["verified_factors"]) if d["verified_factors"] else "None",
            "Note": d["status_note"],
        })

    st.dataframe(pd.DataFrame(records), hide_index=True, width="stretch")

st.markdown("---")
st.markdown("### 📖 Educational Deep-Dive: Why Shor's Algorithm Breaks RSA")
e1, e2, e3 = st.columns(3)
with e1:
    st.markdown("""
    #### 1. Factoring as Order-Finding
    RSA security depends on the hardness of factoring $N = p \\cdot q$.
    Euler's totient theorem states that for any coprime $a$:
    $$a^r \\equiv 1 \\pmod N$$
    If we can efficiently find the order $r$, and $r$ is even, then:
    $$(a^{r/2} - 1)(a^{r/2} + 1) = a^r - 1 \\equiv 0 \\pmod N$$
    At least one of $\\gcd(a^{r/2} \\pm 1, N)$ yields a non-trivial factor!
    """)
with e2:
    st.markdown("""
    #### 2. The Quantum Phase Estimation
    Classical algorithms take exponential / sub-exponential time ($e^{\\sqrt[3]{\\ln N}}$ with Number Field Sieve) to find $r$.
    Quantum Phase Estimation uses a counting register in superposition:
    $$\\frac{1}{\\sqrt{2^t}} \\sum_{x=0}^{2^t-1} |x\\rangle |1\\rangle \\xrightarrow{U^{2^j}} \\frac{1}{\\sqrt{2^t}} \\sum_{x=0}^{2^t-1} |x\\rangle |a^x \\bmod N\\rangle$$
    This creates constructive interference at phase states $\\theta = s / r$.
    """)
with e3:
    st.markdown("""
    #### 3. Why PQC is Immune
    Post-Quantum Cryptography algorithms like **ML-KEM** and **ML-DSA** do not rely on abelian hidden subgroup problems or discrete logarithms.
    They are built on the geometry of high-dimensional lattices (Module Learning with Errors). No quantum algorithm (including Shor's) provides a polynomial-time solution for lattice shortest vector problems.
    """)

