"""Q-SHIELD - Documentation and Engineering Reference Portal."""
from __future__ import annotations

import os
import streamlit as st

st.set_page_config(page_title="Documentation · Q-SHIELD", page_icon="📚", layout="wide")

try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown(
    """
    <div class="hero-banner">
        <h1>📚 Q-SHIELD Engineering Documentation</h1>
        <p>Comprehensive technical specifications, cryptographic designs, quantum threat laboratory guides, benchmarking methodologies, and post-quantum migration frameworks.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

DOCS = {
    "Architecture Overview": "docs/architecture.md",
    "Cryptographic Design & Container Format": "docs/cryptographic-design.md",
    "Quantum Component & Shor's Algorithm": "docs/quantum-component.md",
    "Benchmarking Methodology": "docs/benchmarking-methodology.md",
    "PQC Migration Guide": "docs/migration-guide.md",
    "Implementation Audit Report": "docs/IMPLEMENTATION_AUDIT.md",
}

doc_choice = st.selectbox("Select Documentation Section", list(DOCS.keys()))
doc_path = DOCS[doc_choice]

if os.path.exists(doc_path):
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    st.markdown(content)
else:
    st.info(f"Documentation file `{doc_path}` will be generated.")

