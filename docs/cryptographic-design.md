# Cryptographic Design & Container Specifications

**Platform:** Q-SHIELD  
**Status:** Hackathon Prototype / Educational Reference Implementation  
**Standard Compliance:** NIST FIPS 203 (ML-KEM), NIST FIPS 204 (ML-DSA), RFC 7748 (X25519), RFC 8032 (Ed25519), NIST SP 800-38D (AES-256-GCM), RFC 5869 (HKDF)  

---

## 1. Cryptographic Primitives

Q-SHIELD relies exclusively on established cryptographic primitives without hand-rolled mathematical functions:

| Primitive | Standard | Role | Implementation Provider |
|---|---|---|---|
| **ML-KEM-768** | NIST FIPS 203 | Post-Quantum Key Encapsulation (PQC) | `pqcrypto` (compiled PQClean C) |
| **ML-DSA-65** | NIST FIPS 204 | Post-Quantum Digital Signatures (PQC) | `pqcrypto` (compiled PQClean C) |
| **X25519** | RFC 7748 | Classical Diffie-Hellman Key Exchange | `cryptography` (OpenSSL) |
| **Ed25519** | RFC 8032 | Classical Digital Signatures | `cryptography` (OpenSSL) |
| **AES-256-GCM** | NIST SP 800-38D | Authenticated Encryption with Associated Data | `cryptography` (OpenSSL) |
| **HKDF-SHA256** | RFC 5869 | Extract-and-Expand Key Derivation Function | `cryptography` (OpenSSL) |
| **Scrypt** | RFC 7914 | Password-Based Key Derivation for Keystores | `cryptography` (OpenSSL) |

---

## 2. Container Format (`.qsh`)

Both secure messages and encrypted files use the binary `QSH1` container format:

```
+--------------------------------------------------------------------------------+
| Magic (4 bytes) | Header Len (4 bytes) | Header JSON (N bytes) | Ciphertext + Tag |
|   b"QSH1"       |   uint32 big-endian  |   UTF-8 JSON string   | AES-256-GCM      |
+--------------------------------------------------------------------------------+
|<---------------------------- Associated Data (AAD) --------------------------->|
```

### 2.1 Authenticated Associated Data (AAD)
The first three components:
$$\text{AAD} = \text{Magic} \parallel \text{uint32}(\text{len}(\text{Header})) \parallel \text{Header}$$
are passed as the Associated Data to `AES-256-GCM`. This mathematically guarantees that:
- The mode label (`classical`, `pqc`, `hybrid`) cannot be tampered with.
- The 96-bit nonce cannot be swapped.
- The KEM ciphertext or ephemeral public key cannot be modified.
- The original filename cannot be changed.
- Any modification results in an unforgeable `InvalidTag` exception and immediate decryption rejection.

### 2.2 Header JSON Schema
```json
{
  "v": 1,
  "mode": "hybrid",
  "alg": "X25519 || ML-KEM-768 + HKDF-SHA256 + AES-256-GCM",
  "nonce": "Base64(12 bytes)",
  "filename": "document.pdf",
  "x25519_eph": "Base64(32 bytes)",
  "mlkem_ct": "Base64(1088 bytes)"
}
```

---

## 3. Defense-in-Depth Hybrid Key Derivation

The hybrid key establishment mode incorporates both classical (X25519) and post-quantum (ML-KEM-768) secrets to hedge against theoretical vulnerabilities in newly standardized lattice algorithms while preventing harvest-now-decrypt-later attacks against classical keys.

### 3.1 Unambiguous Length-Prefixed Context
To prevent canonicalization collisions, all contextual public values are length-prefixed:
$$\text{LP}(p_1, p_2, \dots) = \bigoplus_{i} \left( \text{uint32}(\text{len}(p_i)) \parallel p_i \right)$$

The context string binds all parties' public keys and ephemeral wire values:
$$\text{ctx} = \text{LP}(x_{\text{pub}}, x_{\text{eph}}, \text{kem}_{\text{pk}}, \text{kem}_{\text{ct}})$$

### 3.2 HKDF Construction
Both shared secrets are concatenated and fed into HKDF-SHA256:
$$\text{IKM} = \text{ss}_{\text{kem}} \parallel \text{ss}_{\text{x25519}}$$
$$\text{salt} = \text{"QuantumShield/v1/salt"}$$
$$\text{info} = \text{"QuantumShield/v1/aes256gcm/"} \parallel \text{mode} \parallel \text{0x00} \parallel \text{ctx}$$
$$K_{\text{AES}} = \text{HKDF-SHA256-Derive}(\text{IKM}, \text{salt}, \text{info}, 32)$$

### 3.3 Downgrade Prevention Properties
- **Missing Key Check:** If a caller requires hybrid mode, both public keys must be provided; otherwise `MissingKeyError` is raised before transmission.
- **Mode Enforcement:** If a container is encrypted with classical mode but the receiver requires hybrid, decryption is refused with `ModeMismatchError`.
- **Field Stripping Rejection:** Removing `x25519_eph` or `mlkem_ct` causes header validation failure with `IntegrityError`.
- **Label Tampering Rejection:** Changing the `mode` field in the header breaks the HKDF `info` parameter and the AEAD Associated Data tag.

---

## 4. Structured Message Envelope Specification

In multi-party communication workflows (Section 4.5), messages are encapsulated inside a canonical `MessageEnvelope`:

```json
{
  "message_id": "c1f7b029-...",
  "version": 1,
  "cryptographic_mode": "hybrid",
  "key_establishment_algorithm": "X25519 || ML-KEM-768 + HKDF-SHA256 + AES-256-GCM",
  "sender_identity": "Alice (Sender)",
  "recipient_identity": "Bob (Recipient)",
  "encapsulation_ciphertext": "Base64(1088 bytes)",
  "ephemeral_public_key": "Base64(32 bytes)",
  "encryption_algorithm": "AES-256-GCM (NIST SP 800-38D)",
  "nonce": "Base64(12 bytes)",
  "ciphertext": "Base64(N bytes)",
  "signature_algorithm": "ML-DSA-65",
  "signature": "Base64(3309 bytes)",
  "timestamp": "2026-11-01T12:00:00Z"
}
```

### 4.1 Canonical Signing
Before transmitting, the sender computes the deterministic canonical JSON of all header fields and payload ciphertext (excluding the signature itself) and signs it using ML-DSA-65 or Ed25519. The recipient verifies this signature prior to decapsulation.

---

## 5. Keystore Persistence Format (`.qsk`)

To allow decrypting persistent files across restarts without leaving plaintext keys on disk, the identity is exported to a password-protected keystore:

$$\text{Salt} = \text{random}(16), \quad \text{Nonce} = \text{random}(12)$$
$$K_{\text{backup}} = \text{Scrypt}(\text{passphrase}, \text{salt}, N=2^{15}, r=8, p=1, \text{len}=32)$$
$$\text{Container} = \text{b"QSK1"} \parallel \text{Salt} \parallel \text{Nonce} \parallel \text{AES-256-GCM}_{K_{\text{backup}}}(\text{Nonce}, \text{JSON(keys)}, \text{b"QSK1"})$$

---

## 6. Security Limitations and Disclaimers

1. **Local Demonstration:** The multi-party messaging workflow executes in a single local process. It demonstrates cryptographic key exchange and verification mechanics, but does not provide distributed network transport or public key infrastructure (PKI).
2. **Ephemeral vs. Long-Term KEM:** In this demonstration, ML-KEM public keys are treated as long-term identity keys, meaning post-compromise forward secrecy for the ML-KEM component requires session key ratcheting. Only the ephemeral X25519 component provides forward secrecy.
3. **No Side-Channel Guarantees:** Python does not provide constant-time execution guarantees. In production environments, cryptographic primitives must be deployed via vetted HSMs or constant-time C/Rust libraries.

