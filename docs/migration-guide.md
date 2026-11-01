# Enterprise Post-Quantum Cryptography Migration Framework

**Platform:** Q-SHIELD Migration Intelligence (`services/migration_service.py`, `pages/7_Migration_Analyzer.py`)  
**Target Audiences:** Chief Information Security Officers (CISOs), Cryptographic Architects, Security Engineers  
**Regulatory Frameworks:** NIST SP 800-227, NSA CNSA 2.0, CISA PQC Initiative, White House National Security Memorandum 10 (NSM-10)  

---

## 1. The Imperative for Immediate Action

Many organizations mistakenly assume that post-quantum migration can wait until a Cryptographically Relevant Quantum Computer (CRQC) is physically operational. This assumption overlooks the active, existential threat of **Harvest Now, Decrypt Later (HNDL)** attacks.

### 1.1 Harvest Now, Decrypt Later (HNDL)
Adversaries and nation-state intelligence agencies are actively recording encrypted TLS, VPN, and confidential communication streams from public fiber taps and internet exchanges today. While they cannot decrypt these packets with current classical supercomputers, the encrypted data will be retroactively decrypted once a quantum computer with sufficient logical qubits is brought online.

Any information with a confidentiality shelf-life exceeding 5 to 10 years (such as health records, proprietary intellectual property, diplomatic communications, and national defense intelligence) is **already compromised** if transmitted over classical public-key channels today.

---

## 2. Mathematical Urgency: Mosca's Theorem

Dr. Michele Mosca (University of Waterloo / Institute for Quantum Computing) formalized the mathematical condition determining whether an organization is already too late to protect its data:

$$\text{Define:}$$
$$X = \text{The required confidentiality lifetime of the protected data (years)}$$
$$Y = \text{The time required to migrate the enterprise cryptographic infrastructure (years)}$$
$$Z = \text{The estimated time until a Cryptographically Relevant Quantum Computer arrives (years)}$$

$$\text{The Mosca Invariant:}$$
$$\text{If } X + Y > Z \implies \text{Confidentiality will be breached retroactively.}$$

```
Years Today: 0 ----------------- Y (Migration Complete)
Data Shelf Life: 0 ------------------------------------------ X (Data Becomes Public)
CRQC Arrival:    0 ----------------------- Z (Quantum Computer Online)
                     ▲
                     └── If Z occurs before X + Y, recorded data is vulnerable!
```

If an enterprise requires 3 years to migrate its legacy systems ($Y=3$), and holds patient records that must remain confidential for 30 years ($X=30$), then $X + Y = 33$ years. Even under conservative estimates that quantum computers are 8 to 10 years away ($Z=8$), $33 > 8$. **The organization is already 25 years inside the risk window.**

---

## 3. Recommended Algorithm Replacements

NIST finalized its first set of Post-Quantum Cryptography standards in August 2024:

| Legacy Algorithm | Category | Primary Vulnerability | Recommended PQC Replacement | Standard |
|---|---|---|---|---|
| **RSA-2048 / 4096** | Key Exchange | Shor's algorithm ($O((\log N)^3)$) | **ML-KEM-768** or **Hybrid X25519 + ML-KEM-768** | NIST FIPS 203 |
| **ECDH (P-256 / X25519)** | Key Exchange | Shor's discrete log | **ML-KEM-768** or **Hybrid X25519 + ML-KEM-768** | NIST FIPS 203 |
| **RSA-PSS / PKCS#1** | Digital Signature | Shor's factoring | **ML-DSA-65** or **SLH-DSA** | NIST FIPS 204 / 205 |
| **ECDSA / Ed25519** | Digital Signature | Shor's discrete log | **ML-DSA-65** | NIST FIPS 204 |
| **AES-256-GCM** | Symmetric Cipher | Grover's quadratic speedup | **RETAIN AES-256-GCM** | NIST FIPS 197 / SP 800-38D |
| **AES-128 / 3DES** | Symmetric Cipher | Grover's halves to 64-bit | **Upgrade to AES-256-GCM** | NIST SP 800-38D |

> [!IMPORTANT]
> **Do NOT replace AES-256.** Grover's algorithm provides only an $O(\sqrt{N})$ search speedup. A 256-bit symmetric key is reduced to 128 bits of quantum security margin, which requires $2^{128}$ operations to brute-force—a computational barrier that remains physically impossible to breach under the known laws of physics.

---

## 4. The 4-Phase Enterprise Migration Roadmap

### Phase 1: Cryptographic Discovery & Inventory (Months 1–6)
- Scan source code, network endpoints, TLS termination proxies, CI/CD pipelines, HSMs, and firmware for cryptographic algorithms.
- Classify assets by data confidentiality lifetime ($X$), network exposure, and algorithm type.
- Populate machine-readable cryptographic inventories (such as Q-SHIELD's `crypto-inventory.json`).

### Phase 2: Risk Scoring & Prioritization (Months 7–12)
- Apply Mosca's theorem and HNDL criteria to identify critical priority assets.
- Target internet-facing TLS 1.3 termination points and long-lived VPN tunnels as **Urgency: IMMEDIATE**.
- Target code signing and long-term legal digital signature authorities as **Urgency: NEAR-TERM**.

### Phase 3: Hybrid Pilot Deployments (Years 1–2)
- Deploy dual-algorithm hybrid key exchange (`X25519 || ML-KEM-768`) in non-critical tunnels and API gateways.
- Validate network MTU boundaries to ensure the 1,088-byte ML-KEM ciphertext does not cause packet fragmentation issues.
- Benchmark system performance and handshake latency under real-world traffic loads using tools like Q-SHIELD's Benchmark Lab.

### Phase 4: Full PQC Migration & Legacy Deprecation (Years 2–4)
- Transition all production web servers and clients to pure ML-KEM-768 or standardized hybrid profiles.
- Roll out ML-DSA-65 for code signing and document notarization.
- Completely deprecate RSA key exchange and classical elliptic curve suites in accordance with NSA CNSA 2.0 deadlines.

