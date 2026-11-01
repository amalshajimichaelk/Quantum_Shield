"""Q-SHIELD - Command Dashboard and Platform Overview."""
from __future__ import annotations

import streamlit as st
import qs_crypto as qc
from services.crypto_service import test_crypto_engine_health
from services.quantum_service import run_quantum_threat_experiment

st.set_page_config(page_title="Q-SHIELD Dashboard", page_icon="🛡️", layout="wide")

# Inject Custom Enterprise Styling
try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown(
    """
    <div class="hero-banner">
        <h1>🛡️ Q-SHIELD Security Intelligence Platform</h1>
        <p>Post-Quantum Cryptography for a Quantum-Safe Future. Modernize enterprise cryptography with NIST FIPS 203 (ML-KEM-768) and FIPS 204 (ML-DSA-65), evaluate quantum threats with Qiskit Shor's algorithm simulations, and navigate organizational migration readiness.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Core Platform KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("PQC Standard", "FIPS 203 / 204", "Finalized NIST 2024")
with kpi2:
    st.metric("Quantum Engine", "Qiskit 2.x Aer", "Shor's Factoring")
with kpi3:
    st.metric("Hybrid Protection", "X25519 ‖ ML-KEM", "Dual Security")
with kpi4:
    st.metric("Migration Risk", "Mosca & HNDL", "Automated Analyzer")

st.markdown("### 🧩 Platform Capability Status")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        """
        <div class="card">
            <h4>Classical Baseline</h4>
            <p>X25519 ECDH key exchange, Ed25519 signatures, and AES-256-GCM AEAD encryption.</p>
            <p class="mono" style="margin-top:0.8rem; color:#f87171;">Vulnerable to Shor's (O(log N)³)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="card">
            <h4>Post-Quantum KEM</h4>
            <p>NIST FIPS 203 <strong>ML-KEM-768</strong> (CRYSTALS-Kyber) lattice key encapsulation.</p>
            <p class="mono" style="margin-top:0.8rem; color:#34d399;">Resistant to Shor & Grover</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        """
        <div class="card">
            <h4>Digital Signatures</h4>
            <p>NIST FIPS 204 <strong>ML-DSA-65</strong> (CRYSTALS-Dilithium) lattice digital signatures.</p>
            <p class="mono" style="margin-top:0.8rem; color:#34d399;">Quantum Forgery Resistant</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        """
        <div class="card">
            <h4>Defense-in-Depth Hybrid</h4>
            <p>Dual-algorithm key establishment combining X25519 and ML-KEM-768 into HKDF-SHA256.</p>
            <p class="mono" style="margin-top:0.8rem; color:#38bdf8;">Hedge against single flaws</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# Live Cryptographic Engine Verification
st.markdown("### ⚡ Live Cryptographic Engine Self-Test")
st.caption("Executes real key generation, encapsulation, AES-256-GCM authenticated encryption, Ed25519, and ML-DSA-65 operations.")

if st.button("▶ Run Full Cryptographic Self-Test", type="primary"):
    with st.spinner("Testing cryptographic primitives..."):
        st.session_state["selftest_results"] = test_crypto_engine_health()

if "selftest_results" in st.session_state:
    cols = st.columns(2)
    for i, (test_name, ok, detail) in enumerate(st.session_state["selftest_results"]):
        badge = '<span class="badge badge-ok">PASS</span>' if ok else '<span class="badge badge-critical">FAIL</span>'
        col = cols[i % 2]
        col.markdown(
            f"""
            <div class="kv-row">
                <span>{badge} &nbsp; <strong>{test_name}</strong></span>
                <span class="mono">{detail}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")
st.markdown("### 🧭 Platform Modules")
st.caption("Select a module in the sidebar navigation or click below to explore:")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.info("**2. Secure Messaging**\n\nSimulate end-to-end communication between Alice and Bob with structured envelopes.")
with m2:
    st.info("**3. File Protection**\n\nProtect arbitrary files with authenticated containers and tamper rejection.")
with m3:
    st.info("**5. Benchmark Lab**\n\nCompare wall-clock timings and serialized sizes between classical and PQC algorithms.")
with m4:
    st.info("**6. Quantum Threat Lab**\n\nExecute Shor's factoring algorithm using Qiskit Aer to factor N=15 into 3 × 5.")

