"""Q-SHIELD - PQC Migration Readiness Analyzer."""
from __future__ import annotations

import json
import pandas as pd
import streamlit as st
from models.migration import AssetInventoryItem, MigrationReportSummary
from services.migration_service import (
    assess_asset,
    assess_inventory,
    export_report_to_json,
    export_report_to_markdown,
    load_inventory_from_json,
)

st.set_page_config(page_title="Migration Analyzer · Q-SHIELD", page_icon="🧭", layout="wide")

try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown(
    """
    <div class="hero-banner">
        <h1>🧭 PQC Migration Readiness Analyzer</h1>
        <p>Assess organizational cryptographic inventory against quantum vulnerability. Uses Mosca's theorem and Harvest-Now-Decrypt-Later (HNDL) risk models to prioritize legacy algorithm migration toward NIST FIPS 203 / 204 standards.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Inventory source selection
col_src1, col_src2 = st.columns([2, 1])
with col_src1:
    up_inv = st.file_uploader("Upload Cryptographic Inventory JSON", type=["json"], key="inv_upload")
with col_src2:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("📁 Load Enterprise Sample Inventory", type="primary"):
        with open("sample-data/crypto-inventory.json", "r", encoding="utf-8") as f:
            st.session_state["inventory_json"] = f.read()
        st.success("Loaded sample enterprise inventory (7 cryptographic assets).")

if up_inv:
    st.session_state["inventory_json"] = up_inv.getvalue().decode("utf-8")

if "inventory_json" not in st.session_state:
    with open("sample-data/crypto-inventory.json", "r", encoding="utf-8") as f:
        st.session_state["inventory_json"] = f.read()

try:
    items = load_inventory_from_json(st.session_state["inventory_json"])
    summary: MigrationReportSummary = assess_inventory(items)
except Exception as e:
    st.error(f"Error parsing inventory JSON: {e}")
    st.stop()

# Overall Posture Header
score_color = "#10b981" if summary.overall_posture_score >= 80 else ("#f59e0b" if summary.overall_posture_score >= 50 else "#ef4444")
st.markdown(
    f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:#0f172a; padding:1.2rem 1.6rem; border:1px solid #1e293b; border-radius:12px; margin-bottom:1.2rem;">
        <div>
            <h3 style="margin:0 0 0.3rem 0;">Enterprise Quantum Safety Posture</h3>
            <p style="margin:0; color:#94a3b8;">Based on Mosca's Theorem (X + Y > Z) and HNDL vulnerability analysis.</p>
        </div>
        <div style="text-align:right;">
            <span style="font-size:2.4rem; font-weight:800; color:{score_color};">{summary.overall_posture_score}</span>
            <span style="font-size:1.1rem; color:#64748b;"> / 100</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# KPI Cards
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total Assets", summary.total_assets)
with k2:
    st.metric("Quantum Vulnerable", summary.quantum_vulnerable_count, f"{summary.quantum_vulnerable_count/summary.total_assets*100:.0f}% of estate")
with k3:
    st.metric("HNDL Exposed", summary.hndl_vulnerable_count, "Immediate Key Threat")
with k4:
    st.metric("Critical Urgency", summary.critical_priority_count, "Immediate Plan Needed")
with k5:
    st.metric("PQC-Ready Assets", summary.pqc_ready_count, "Protected")

st.markdown("---")

tab_inventory, tab_single, tab_export = st.tabs(["📋 Assessed Asset Inventory", "🧪 Interactive Asset Evaluator", "📤 Export Migration Report"])

with tab_inventory:
    st.markdown("### Organizational Cryptographic Inventory Assessment")
    records = []
    for a in summary.assets:
        records.append({
            "Asset ID": a.asset_id,
            "Application": a.application_name,
            "Current Algorithm": a.current_algorithm,
            "Risk Level": a.risk_level,
            "HNDL Exposed": "YES" if a.hndl_exposed else "NO",
            "Mosca Breach": "YES" if a.mosca_breach else "NO",
            "Urgency": a.migration_urgency,
            "Recommended Replacement": a.recommended_replacement,
        })
    st.dataframe(pd.DataFrame(records), hide_index=True, width="stretch")

    st.markdown("#### Technical Migration Rationales & Sizing Impact")
    for a in summary.assets:
        with st.expander(f"{a.asset_id} — {a.application_name} [{a.risk_level}]", expanded=(a.risk_level == "CRITICAL")):
            st.markdown(f"**Current Algorithm:** `{a.current_algorithm}`")
            st.markdown(f"**Recommended Replacement:** `{a.recommended_replacement}`")
            st.markdown(f"**Quantum Vulnerability Mechanism:** {a.vulnerability_threat}")
            st.markdown(f"**Size Expansion Impact:** {a.size_expansion_impact}")
            st.info(a.technical_rationale)

with tab_single:
    st.markdown("### Evaluate Custom Cryptographic Configuration")
    with st.form("custom_asset_form"):
        f_app = st.text_input("Application Name", "Internal Microservice Auth")
        f_alg = st.selectbox("Current Cryptographic Algorithm", ["RSA-2048", "RSA-4096", "ECDSA (P-256)", "ECDH (X25519)", "Ed25519", "AES-128", "AES-256-GCM", "3DES", "Hybrid (X25519 + ML-KEM-768)", "ML-DSA-65"])
        f_cat = st.selectbox("Cryptographic Role", ["Key Exchange", "Digital Signature", "Symmetric Encryption"])
        f_exp = st.selectbox("Network Exposure", ["Public Internet", "Internal Network", "Air-gapped"])
        f_life = st.slider("Confidentiality Requirement Lifetime (Years)", min_value=1, max_value=50, value=15)
        assess_submit = st.form_submit_button("Assess Asset", type="primary")

    if assess_submit:
        custom_item = AssetInventoryItem(
            id="CUSTOM-EVAL",
            application_name=f_app,
            current_algorithm=f_alg,
            category=f_cat,
            key_size=256,
            usage_type="Custom Evaluation",
            data_classification="User Specified",
            confidentiality_lifetime_years=f_life,
            network_exposure=f_exp,
        )
        c_res = assess_asset(custom_item)
        st.markdown(
            f"""
            <div class="card" style="margin-top:1rem;">
                <h4>Assessment Outcome for {c_res.application_name}</h4>
                <div class="kv-row"><span>Risk Priority</span><span class="badge {'badge-critical' if c_res.risk_level=='CRITICAL' else ('badge-warn' if c_res.risk_level=='HIGH' else 'badge-ok')}">{c_res.risk_level}</span></div>
                <div class="kv-row"><span>Migration Urgency</span><span>{c_res.migration_urgency}</span></div>
                <div class="kv-row"><span>Recommended Replacement</span><span class="mono">{c_res.recommended_replacement}</span></div>
                <div class="kv-row"><span>Mosca's Condition</span><span>{'Triggered (X + Y > Z)' if c_res.mosca_breach else 'Not Triggered'}</span></div>
                <div class="kv-row"><span>HNDL Vulnerability</span><span>{'EXPOSED' if c_res.hndl_exposed else 'NOT EXPOSED'}</span></div>
                <div class="kv-row"><span>Size & Bandwidth Impact</span><span>{c_res.size_expansion_impact}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(c_res.technical_rationale)

with tab_export:
    st.markdown("### Export Assessment Findings")
    c_exp1, c_exp2 = st.columns(2)
    with c_exp1:
        json_report = export_report_to_json(summary)
        st.download_button(
            label="⬇ Download Assessment JSON",
            data=json_report,
            file_name="qshield_migration_assessment.json",
            mime="application/json",
            type="primary",
        )
    with c_exp2:
        md_report = export_report_to_markdown(summary)
        st.download_button(
            label="⬇ Download Executive Markdown Report",
            data=md_report,
            file_name="qshield_migration_report.md",
            mime="text/markdown",
            type="primary",
        )
