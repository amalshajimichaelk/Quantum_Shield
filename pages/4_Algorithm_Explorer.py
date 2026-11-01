"""Q-SHIELD - Algorithm Explorer and Cryptographic Specifications."""
from __future__ import annotations

import pandas as pd
import streamlit as st
from utils.metadata import ALGORITHM_CATALOG

st.set_page_config(page_title="Algorithm Explorer · Q-SHIELD", page_icon="🔍", layout="wide")

try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown(
    """
    <div class="hero-banner">
        <h1>🔍 Cryptographic Algorithm Explorer</h1>
        <p>Comprehensive reference and deep-dive into NIST post-quantum standards (FIPS 203, FIPS 204), classical baselines (X25519, Ed25519, AES-256-GCM), mathematical hardness assumptions, and quantum vulnerability profiles.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_alg = st.selectbox("Select Algorithm to Inspect", list(ALGORITHM_CATALOG.keys()))
meta = ALGORITHM_CATALOG[selected_alg]

c1, c2 = st.columns([3, 2])
with c1:
    st.markdown(f"### {meta['name']}")
    st.markdown(f"**Standard / Specification:** `{meta['standard']}`")
    st.markdown(f"**Category:** `{meta['category']}`")
    st.markdown(f"**Security Level:** {meta['security_level']}")
    st.markdown(f"**Mathematical Hardness:** {meta['hardness_assumption']}")
    st.info(meta["description"])

with c2:
    st.markdown("### 📏 Parameter Dimensions")
    st.markdown(
        f"""
        <div class="card">
            <div class="kv-row"><span>Public Key Size</span><span class="mono">{meta['public_key_size_bytes']:,} bytes</span></div>
            <div class="kv-row"><span>Private Key Size</span><span class="mono">{meta['private_key_size_bytes']:,} bytes</span></div>
            <div class="kv-row"><span>Transmission Size</span><span class="mono">{meta.get('ciphertext_size_bytes', meta.get('signature_size_bytes', meta.get('tag_size_bytes', 0))):,} bytes</span></div>
            <div class="kv-row"><span>Quantum Vulnerability</span><span class="badge {'badge-critical' if 'Shor' in meta['quantum_threat'] and 'Resistant' not in meta['quantum_threat'] else 'badge-ok'}">{'VULNERABLE' if 'Shor' in meta['quantum_threat'] and 'Resistant' not in meta['quantum_threat'] else 'QUANTUM-SAFE'}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.markdown("### ⚖️ Side-by-Side Algorithm Comparison Matrix")

matrix_rows = []
for k, v in ALGORITHM_CATALOG.items():
    matrix_rows.append({
        "Algorithm": k,
        "Standard": v["standard"].split("(")[0].strip(),
        "Role": v["category"].split("(")[0].strip(),
        "Public Key (B)": v["public_key_size_bytes"],
        "Private Key (B)": v["private_key_size_bytes"],
        "Payload (B)": v.get("ciphertext_size_bytes", v.get("signature_size_bytes", v.get("tag_size_bytes", 0))),
        "Quantum Status": "VULNERABLE (Shor)" if "Shor" in v["quantum_threat"] and "Resistant" not in v["quantum_threat"] else "QUANTUM-SAFE",
    })

st.dataframe(pd.DataFrame(matrix_rows), hide_index=True, width="stretch")

st.markdown("---")
st.markdown("### 🧠 The Mathematical Foundations")

m1, m2 = st.columns(2)
with m1:
    st.markdown("""
    #### Module Learning with Errors (M-LWE)
    ML-KEM is built on the hardness of solving linear equations with small added noise over polynomial rings:
    $$\\mathbf{A} \\cdot \\mathbf{s} + \\mathbf{e} = \\mathbf{t} \\pmod q$$
    - Given matrix $\\mathbf{A}$ and vector $\\mathbf{t}$, finding secret $\\mathbf{s}$ is believed to be computationally intractable for both classical and quantum computers.
    - Unlike factoring or discrete logarithms, no polynomial-time quantum algorithm is known to solve lattice shortest-vector problems.
    """)

with m2:
    st.markdown("""
    #### Shor vs. Grover Speedup
    - **Shor's Algorithm (Exponential Speedup):** Solves hidden subgroup problems in polynomial time $O((\\log N)^3)$, reducing RSA-2048 and Curve25519 from billions of years to mere hours on a fault-tolerant machine.
    - **Grover's Algorithm (Quadratic Speedup):** Performs unstructured search in $O(\\sqrt{N})$. It effectively halves symmetric key lengths (AES-256 provides $2^{128}$ quantum security), making AES-256 permanently quantum-safe.
    """)

