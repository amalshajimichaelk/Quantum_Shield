"""Q-SHIELD - Multi-Party Secure Messaging Demonstration."""
from __future__ import annotations

import streamlit as st
import qs_crypto as qc
from services.messaging_service import (
    create_participant_identities,
    send_secure_message,
    receive_secure_message,
    DecryptionFailedError,
    SignatureVerificationError,
)

st.set_page_config(page_title="Secure Messaging · Q-SHIELD", page_icon="💬", layout="wide")

try:
    with open("assets/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception:
    pass

st.markdown(
    """
    <div class="hero-banner">
        <h1>💬 Post-Quantum Secure Messaging</h1>
        <p>Local cryptographic workflow demonstration. Alice establishes shared secrets with Bob using NIST FIPS 203 (ML-KEM-768) or Hybrid modes, encrypts with AES-256-GCM, and signs the canonical envelope with NIST FIPS 204 (ML-DSA-65).</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Alice and Bob in session state if not present
if "alice_ident" not in st.session_state or "bob_ident" not in st.session_state:
    alice, bob = create_participant_identities()
    st.session_state["alice_ident"] = alice
    st.session_state["bob_ident"] = bob

alice: qc.Identity = st.session_state["alice_ident"]
bob: qc.Identity = st.session_state["bob_ident"]

# Participant Public Cards
p1, p2 = st.columns(2)
with p1:
    st.markdown("#### 👩 Alice (Sender Identity)")
    st.markdown(
        f"""
        <div class="card">
            <div class="kv-row"><span>Name</span><span>{alice.name}</span></div>
            <div class="kv-row"><span>Fingerprint</span><span class="mono">{alice.fingerprint()}</span></div>
            <div class="kv-row"><span>X25519 Public Key</span><span class="mono">{len(alice.x_pub)} B</span></div>
            <div class="kv-row"><span>ML-KEM-768 Public Key</span><span class="mono">{len(alice.kem_pk):,} B</span></div>
            <div class="kv-row"><span>ML-DSA-65 Public Key</span><span class="mono">{len(alice.dsa_pk):,} B</span></div>
            <div class="kv-row"><span>Ed25519 Public Key</span><span class="mono">{len(alice.ed_pub)} B</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with p2:
    st.markdown("#### 👨 Bob (Recipient Identity)")
    st.markdown(
        f"""
        <div class="card">
            <div class="kv-row"><span>Name</span><span>{bob.name}</span></div>
            <div class="kv-row"><span>Fingerprint</span><span class="mono">{bob.fingerprint()}</span></div>
            <div class="kv-row"><span>X25519 Public Key</span><span class="mono">{len(bob.x_pub)} B</span></div>
            <div class="kv-row"><span>ML-KEM-768 Public Key</span><span class="mono">{len(bob.kem_pk):,} B</span></div>
            <div class="kv-row"><span>ML-DSA-65 Public Key</span><span class="mono">{len(bob.dsa_pk):,} B</span></div>
            <div class="kv-row"><span>Ed25519 Public Key</span><span class="mono">{len(bob.ed_pub)} B</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.button("🔄 Regenerate Keypairs for Both Parties"):
    new_alice, new_bob = create_participant_identities()
    st.session_state["alice_ident"] = new_alice
    st.session_state["bob_ident"] = new_bob
    st.session_state.pop("msg_envelope", None)
    st.rerun()

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📤 Step 1: Alice Encrypts & Signs")
    mode_options = {
        "Post-Quantum (ML-KEM-768 + AES-256-GCM)": "pqc",
        "Hybrid (X25519 ‖ ML-KEM-768 + AES-256-GCM)": "hybrid",
        "Classical (X25519 + AES-256-GCM)": "classical",
    }
    selected_mode_label = st.selectbox("Key Establishment Mode", list(mode_options.keys()))
    mode = mode_options[selected_mode_label]

    sig_options = ["ML-DSA-65 (NIST FIPS 204 PQC)", "Ed25519 (Classical)", "None (Unauthenticated)"]
    selected_sig_label = st.selectbox("Digital Signature Scheme", sig_options)
    sig_alg = "ML-DSA-65" if "ML-DSA-65" in selected_sig_label else ("Ed25519" if "Ed25519" in selected_sig_label else "none")

    plaintext_msg = st.text_area(
        "Message to Bob",
        "Project Q-SHIELD: PQC transition protocol verified. Quantum safe keys authorized.",
        height=100,
    )

    if st.button("🔒 Encrypt & Transmit Envelope", type="primary"):
        with st.spinner("Establishing secret and encrypting..."):
            envelope = send_secure_message(
                sender=alice,
                recipient_pub=bob.public(),
                recipient_name=bob.name,
                plaintext=plaintext_msg.encode("utf-8"),
                mode=mode,
                signature_algorithm=sig_alg,
            )
            st.session_state["msg_envelope"] = envelope
            st.success("Envelope generated and transmitted to Bob!")

    envelope = st.session_state.get("msg_envelope")
    if envelope:
        st.markdown("#### 📦 Transmitted Cryptographic Envelope")
        st.markdown(
            f"""
            <div class="card">
                <div class="kv-row"><span>Message ID</span><span class="mono">{envelope.message_id}</span></div>
                <div class="kv-row"><span>Protocol Version</span><span class="mono">v{envelope.version}</span></div>
                <div class="kv-row"><span>Cryptographic Mode</span><span class="badge badge-info">{envelope.cryptographic_mode.upper()}</span></div>
                <div class="kv-row"><span>KEM Algorithm</span><span class="mono">{envelope.key_establishment_algorithm}</span></div>
                <div class="kv-row"><span>AEAD Cipher</span><span class="mono">{envelope.encryption_algorithm}</span></div>
                <div class="kv-row"><span>Signature Scheme</span><span class="mono">{envelope.signature_algorithm}</span></div>
                <div class="kv-row"><span>Timestamp</span><span class="mono">{envelope.timestamp}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Inspect Raw Canonical Envelope JSON"):
            st.json(envelope.to_dict())

with col_right:
    st.markdown("### 📥 Step 2: Bob Receives & Verifies")
    envelope = st.session_state.get("msg_envelope")

    if not envelope:
        st.info("No message envelope transmitted yet. Encrypt a message in Step 1.")
    else:
        st.markdown("#### Simulate Active Attackers")
        tamper_ct = st.checkbox("Simulate Network Attacker: Modify ciphertext byte in transit")
        tamper_meta = st.checkbox("Simulate Man-in-the-Middle: Alter recipient metadata field")

        if st.button("🔓 Authenticate & Decrypt as Bob", type="primary"):
            # Clone envelope for simulation to preserve state
            test_envelope = MessageEnvelope.from_dict(envelope.to_dict())

            if tamper_ct:
                # Corrupt base64 ciphertext
                chars = list(test_envelope.ciphertext)
                chars[10] = "X" if chars[10] != "X" else "Y"
                test_envelope.ciphertext = "".join(chars)

            if tamper_meta:
                test_envelope.recipient_identity = "Mallory (Imposter)"

            try:
                decrypted_bytes, meta = receive_secure_message(
                    recipient=bob,
                    sender_pub=alice.public(),
                    envelope=test_envelope,
                    expected_mode=envelope.cryptographic_mode,
                )
                st.markdown('<span class="badge badge-ok">AUTHENTICATION & INTEGRITY VERIFIED</span>', unsafe_allow_html=True)
                st.success(f"**Recovered Plaintext:**\n\n{decrypted_bytes.decode('utf-8', errors='replace')}")

                if meta.get("signature_valid"):
                    st.markdown(
                        f"""
                        <div class="card" style="margin-top:0.8rem;">
                            <p style="color:#34d399;"><strong>Digital Signature Valid:</strong> Verified authenticity of {envelope.sender_identity} using {envelope.signature_algorithm}.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            except SignatureVerificationError as sve:
                st.markdown('<span class="badge badge-critical">SIGNATURE FORGERY DETECTED</span>', unsafe_allow_html=True)
                st.error(f"Signature Verification Rejected: {sve}")
            except DecryptionFailedError as dfe:
                st.markdown('<span class="badge badge-critical">AEAD INTEGRITY REJECTED</span>', unsafe_allow_html=True)
                st.error(f"Decryption Rejected: {dfe}")
            except Exception as e:
                st.markdown('<span class="badge badge-critical">SECURITY ERROR</span>', unsafe_allow_html=True)
                st.error(f"Processing Error: {e}")

