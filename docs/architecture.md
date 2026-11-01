# Q-SHIELD Platform Architecture & System Design

**Project Name:** Q-SHIELD — Quantum-Safe Hybrid Cryptography & Security Intelligence Platform  
**Architecture Classification:** Enterprise Cybersecurity Platform / Post-Quantum Cryptographic Suite  
**Programming Language:** Python 3.13  
**UI Framework:** Streamlit  
**Quantum Framework:** Qiskit SDK 2.x & Qiskit Aer Simulator  

---

## 1. System Architecture Overview

Q-SHIELD is an end-to-end post-quantum cryptographic security platform designed to address the catastrophic risk quantum computing poses to modern public-key cryptography. It combines standardized post-quantum algorithms (NIST FIPS 203 ML-KEM-768 and FIPS 204 ML-DSA-65), defense-in-depth hybrid key establishment, an authentic Qiskit-powered Shor's factoring quantum simulator, a wall-clock performance benchmarking laboratory, and an automated migration readiness analyzer.

```mermaid
flowchart TD
    subgraph UI ["User Interface Layer (Streamlit)"]
        APP["app.py (Command Center)"]
        P1["1_Dashboard.py"]
        P2["2_Secure_Messaging.py"]
        P3["3_File_Protection.py"]
        P4["4_Algorithm_Explorer.py"]
        P5["5_Benchmark_Lab.py"]
        P6["6_Quantum_Threat_Lab.py"]
        P7["7_Migration_Analyzer.py"]
        P8["8_Documentation.py"]
    end

    subgraph ServiceLayer ["Service Layer (services/)"]
        CS["crypto_service.py"]
        MS["messaging_service.py"]
        FS["file_service.py"]
        SS["signature_service.py"]
        BS["benchmark_service.py"]
        QS["quantum_service.py"]
        MIGS["migration_service.py"]
    end

    subgraph EngineLayer ["Core Engines & Primitives"]
        QC["qs_crypto.py<br/>(ML-KEM-768, ML-DSA-65, X25519, Ed25519, AES-256-GCM)"]
        BENCH["bench.py<br/>(Real Wall-Clock Timing & Size Engine)"]
        subgraph QuantumModule ["quantum/ (Qiskit 2.x)"]
            SHOR["shor.py"]
            CIRC["circuits.py (QPE & CSWAP)"]
            OF["order_finding.py (AerSimulator)"]
            POST["postprocessing.py (Continued Fractions)"]
        end
    end

    subgraph ModelsLayer ["Domain Models & Utils"]
        MODELS["models/<br/>(messages, identities, migration, benchmarks)"]
        UTILS["utils/<br/>(serialization, validation, metadata, logging)"]
    end

    UI --> ServiceLayer
    ServiceLayer --> EngineLayer
    ServiceLayer --> ModelsLayer
    EngineLayer --> ModelsLayer
```

---

## 2. Component Breakdown

### 2.1 Streamlit Interface Layer (`pages/` and `app.py`)
- **`app.py`**: Central gateway providing persistent session state, identity backup/restore, and direct module dispatching.
- **`pages/1_Dashboard.py`**: Executive command dashboard showing live system status, FIPS compliance status, and live self-tests.
- **`pages/2_Secure_Messaging.py`**: Multi-party messaging simulation with Alice and Bob, structured envelopes, and real-time tampering rejection.
- **`pages/3_File_Protection.py`**: Authenticated container (`.qsh`) encryption, tamper rejection, and scrypt keystore management.
- **`pages/4_Algorithm_Explorer.py`**: Mathematical deep dive into lattice cryptography, hardness assumptions, and parameter sizes.
- **`pages/5_Benchmark_Lab.py`**: Wall-clock performance benchmarking laboratory with statistical metrics (median, mean, min, max, p95) and CSV export.
- **`pages/6_Quantum_Threat_Lab.py`**: Interactive quantum simulation executing Shor's factoring algorithm using Qiskit Aer.
- **`pages/7_Migration_Analyzer.py`**: Automated organizational inventory risk analyzer based on Mosca's theorem and HNDL threat modeling.
- **`pages/8_Documentation.py`**: Interactive engineering reference portal.

### 2.2 Core Cryptographic Engine (`qs_crypto.py`)
- **NIST FIPS 203 (ML-KEM-768):** Lattice-based key encapsulation mechanism based on Module Learning with Errors (M-LWE).
- **NIST FIPS 204 (ML-DSA-65):** Lattice-based digital signature algorithm based on Module Short Integer Solution (M-SIS).
- **RFC 7748 (X25519):** Classical Montgomery curve Diffie-Hellman key exchange for baseline comparison.
- **RFC 8032 (Ed25519):** Classical Edwards curve digital signature algorithm for baseline comparison.
- **NIST FIPS 197 / SP 800-38D (AES-256-GCM):** Authenticated encryption with associated data providing AEAD security.
- **RFC 5869 (HKDF-SHA256):** Domain-separated key derivation function with length-prefixed public context binding.
- **Passphrase-Protected Keystore:** Password-based key derivation using Scrypt ($N=2^{15}, r=8, p=1$) and AES-256-GCM.

### 2.3 Quantum Threat Engine (`quantum/`)
- **`circuits.py`**: Constructs genuine Quantum Phase Estimation (QPE) circuits containing counting registers, work registers, Hadamards, controlled modular exponentiation gates (CSWAP / unitary permutations), and inverse QFT.
- **`order_finding.py`**: Manages circuit transpilation with `qiskit.transpile()` and executes runs on `qiskit_aer.AerSimulator`.
- **`postprocessing.py`**: Performs continued fraction expansion on measured bitstring phase angles, estimates order $r$, computes $\gcd(a^{r/2} \pm 1, N)$, and verifies non-trivial factorization.
- **`shor.py`**: Orchestrates the entire quantum workflow and returns a typed `ShorResult`.

### 2.4 Migration Intelligence Engine (`services/migration_service.py`)
- Evaluates assets against quantum vulnerabilities.
- Models **Mosca's Theorem**: $X + Y > Z$, where $X$ is confidentiality lifetime, $Y$ is migration execution time, and $Z$ is time until a Cryptographically Relevant Quantum Computer (CRQC).
- Identifies **Harvest Now, Decrypt Later (HNDL)** exposures for internet-facing public-key key exchange channels.
- Calculates organizational security posture score (0–100) and exports structured JSON and Markdown audit reports.

---

## 3. Data Flow Architecture

### 3.1 Multi-Party Secure Messaging Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant Alice as Alice (Sender)
    participant Channel as Communication Channel
    participant Bob as Bob (Recipient)

    Note over Bob: Generates long-term identity (X25519, ML-KEM-768, ML-DSA-65)
    Bob->>Alice: Exchanges Public Bundle (x_pub, kem_pk, dsa_pk, ed_pub)
    
    Note over Alice: 1. Encapsulates ML-KEM secret (kem_ct, ss_k)<br/>2. Generates ephemeral X25519 (eph, ss_x)<br/>3. Derives AES key via HKDF(ss_k || ss_x)<br/>4. Encrypts plaintext with AES-256-GCM<br/>5. Signs canonical envelope with ML-DSA-65
    Alice->>Channel: Transmits MessageEnvelope (JSON)
    
    Channel->>Bob: Delivers MessageEnvelope
    Note over Bob: 1. Verifies Alice's ML-DSA-65 signature on envelope<br/>2. Decapsulates ML-KEM secret using kem_sk<br/>3. Computes X25519 exchange with eph<br/>4. Re-derives identical AES key via HKDF<br/>5. Authenticates & decrypts AES-256-GCM ciphertext
    Bob-->>Bob: Displays authentic decrypted plaintext
```

### 3.2 Shor's Algorithm Execution Flow

```mermaid
flowchart LR
    IN["Input: N=15, a=2"] --> PREP["Hadamard Superposition on 4 Counting Qubits"]
    PREP --> INIT["Initialize 4 Work Qubits to |0001>"]
    INIT --> MODEXP["Controlled Modular Exponentiation: a^(2^j) mod 15 (CSWAP gates)"]
    MODEXP --> IQFT["Inverse Quantum Fourier Transform (IQFT)"]
    IQFT --> MEAS["Measure Counting Register (1024 shots)"]
    MEAS --> AER["Qiskit AerSimulator Execution"]
    AER --> CONTFRAC["Continued Fractions Expansion (s/r)"]
    CONTFRAC --> ORDER["Recover Multiplicative Order r=4"]
    ORDER --> GCD["Compute gcd(a^(r/2) ± 1, N)"]
    GCD --> OUT["Verified Factors: 15 = 3 × 5"]
```

