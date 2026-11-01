"""Q-SHIELD - Authenticated File Protection."""
from __future__ import annotations

import time
import streamlit as st
import qs_crypto as qc
from services.file_service import protect_file, recover_file

st.set_page_config(page_title="File Protection · Q-SHIELD", page_icon="📁", layout="wide")

try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown(
    """
    <div class="hero-banner">
        <h1>📁 Post-Quantum File Protection</h1>
        <p>Encrypt files using NIST FIPS 203 (ML-KEM-768), X25519, or Defense-in-Depth Hybrid modes with AES-256-GCM authenticated encryption. Any tampering with headers, filenames, or ciphertext bytes is rejected.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "ident" not in st.session_state:
    st.session_state["ident"] = qc.generate_identity("Local File Vault")

ident: qc.Identity = st.session_state["ident"]

tab_enc, tab_dec, tab_keystore = st.tabs(["🔒 Protect a File", "🔓 Decrypt a File", "🔑 Keystore Backup / Restore"])

with tab_enc:
    mode_options = {
        "Post-Quantum (ML-KEM-768 + AES-256-GCM)": "pqc",
        "Hybrid (X25519 ‖ ML-KEM-768 + AES-256-GCM)": "hybrid",
        "Classical (X25519 + AES-256-GCM)": "classical",
    }
    mode_label = st.radio("Key Establishment Mode", list(mode_options.keys()), horizontal=True)
    mode = mode_options[mode_label]

    uploaded_file = st.file_uploader("Select file to protect", key="file_enc_upload")

    if uploaded_file and st.button("🔒 Encrypt File", type="primary"):
        file_bytes = uploaded_file.getvalue()
        filename = uploaded_file.name
        t0 = time.perf_counter()
        blob = protect_file(file_bytes, filename, mode, ident.public())
        duration_ms = (time.perf_counter() - t0) * 1000

        st.session_state["protected_blob"] = blob
        st.session_state["protected_meta"] = {
            "filename": filename,
            "original_size": len(file_bytes),
            "container_size": len(blob),
            "mode": mode,
            "duration_ms": duration_ms,
        }

    meta = st.session_state.get("protected_meta")
    blob = st.session_state.get("protected_blob")
    if meta and blob:
        st.markdown('<span class="badge badge-ok">ENCRYPTED & AUTHENTICATED</span>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="card" style="margin-top:0.8rem;">
                <div class="kv-row"><span>Original Filename</span><span class="mono">{meta['filename']}</span></div>
                <div class="kv-row"><span>Original Size</span><span class="mono">{meta['original_size']:,} bytes</span></div>
                <div class="kv-row"><span>Encrypted Container Size</span><span class="mono">{meta['container_size']:,} bytes</span></div>
                <div class="kv-row"><span>Container Overhead</span><span class="mono">{meta['container_size'] - meta['original_size']:,} bytes</span></div>
                <div class="kv-row"><span>Encryption Duration</span><span class="mono">{meta['duration_ms']:.2f} ms</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="⬇ Download Protected Container (.qsh)",
            data=blob,
            file_name=f"{meta['filename']}.qsh",
            mime="application/octet-stream",
            type="primary",
        )

with tab_dec:
    req_mode_label = st.radio("Enforce Algorithm Mode", list(mode_options.keys()), horizontal=True, key="dec_mode")
    req_mode = mode_options[req_mode_label]

    up_enc = st.file_uploader("Upload encrypted container (.qsh)", key="file_dec_upload")
    corrupt_box = st.checkbox("Simulate File Corruption: Flip one bit inside ciphertext")

    if up_enc and st.button("🔓 Decrypt & Verify File", type="primary"):
        container_data = up_enc.getvalue()
        if corrupt_box:
            # Flip one bit in payload
            bad_data = bytearray(container_data)
            bad_data[-10] ^= 0x01
            container_data = bytes(bad_data)

        t0 = time.perf_counter()
        try:
            pt, hdr = recover_file(container_data, ident, expected_mode=req_mode)
            dur = (time.perf_counter() - t0) * 1000
            st.markdown('<span class="badge badge-ok">INTEGRITY VERIFIED</span>', unsafe_allow_html=True)
            recovered_name = hdr.get("filename") or "recovered_file.bin"
            st.success(f"Successfully decrypted **{recovered_name}** ({len(pt):,} bytes) in {dur:.2f} ms using **{hdr['mode']}** mode.")
            st.download_button(
                label=f"⬇ Download Restored {recovered_name}",
                data=pt,
                file_name=recovered_name,
                mime="application/octet-stream",
                type="primary",
            )
        except qc.IntegrityError as ie:
            st.markdown('<span class="badge badge-critical">AUTHENTICATION FAILURE</span>', unsafe_allow_html=True)
            st.error(f"Decryption Rejected: {ie}")
        except qc.ModeMismatchError as mme:
            st.markdown('<span class="badge badge-warn">DOWNGRADE REJECTED</span>', unsafe_allow_html=True)
            st.error(f"Security Policy Rejection: {mme}")
        except Exception as e:
            st.error(f"Error: {e}")

with tab_keystore:
    st.markdown("#### 🔑 Identity Keystore Backup")
    st.caption("Because encryption keys are held in memory, back up your keystore using a passphrase to decrypt files after application restart.")

    pw = st.text_input("Enter Passphrase (min 8 characters)", type="password", key="ks_pass")
    if pw and len(pw) >= 8:
        ks_bytes = qc.export_keystore(ident, pw)
        st.download_button(
            label="⬇ Export Encrypted Keystore (.qsk)",
            data=ks_bytes,
            file_name="qshield_identity.qsk",
            mime="application/octet-stream",
        )

    st.markdown("---")
    st.markdown("#### 🔄 Restore Keystore")
    restore_file = st.file_uploader("Upload Keystore (.qsk)", key="ks_restore_file")
    if restore_file and pw and st.button("Restore Identity from Keystore"):
        try:
            restored = qc.import_keystore(restore_file.getvalue(), pw)
            st.session_state["ident"] = restored
            st.success(f"Identity '{restored.name}' restored successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to restore keystore: {e}")

