# Qiskit Quantum Threat Component: Shor's Factoring Algorithm

**Framework:** Qiskit SDK 2.x & Qiskit Aer Simulator (`qiskit==2.6.1`, `qiskit-aer==0.18.2`)  
**Experiment:** Factoring $N = 15$ with coprime base $a = 2$  
**Outcome:** Mathematically verified non-trivial factors $15 = 3 \times 5$  
**Quantum Technique:** Quantum Phase Estimation (QPE) and Order Finding  

---

## 1. Real-World Relevance & Theoretical Threat

RSA public-key cryptography and Diffie-Hellman key exchanges underpin the security of the global internet (HTTPS, TLS 1.3, SSH, VPNs, and electronic signatures). The security of RSA relies on the computational intractability of factoring large composite integers $N = p \cdot q$ using classical computers:

$$\text{Classical Best (General Number Field Sieve): } \mathcal{O}\left( \exp\left( \left( \sqrt[3]{\frac{64}{9}} + o(1) \right) (\ln N)^{\frac{1}{3}} (\ln \ln N)^{\frac{2}{3}} \right) \right)$$

In 1994, Peter Shor demonstrated that a quantum computer can factor composite integers in polynomial time:

$$\text{Quantum (Shor's Algorithm): } \mathcal{O}((\log N)^2 (\log \log N) (\log \log \log N))$$

This fundamental breakthrough proves that once a Cryptographically Relevant Quantum Computer (CRQC) is constructed, all conventional RSA, Diffie-Hellman, and elliptic curve cryptography will be instantly broken.

---

## 2. Order Finding as the Core Engine

Factoring an odd composite integer $N$ can be reduced to the problem of finding the multiplicative order $r$ of a randomly chosen integer $a$ coprime to $N$ ($\gcd(a, N) = 1$):

$$a^r \equiv 1 \pmod N$$

If $r$ is even, we can rewrite this congruence as a difference of squares:

$$a^r - 1 = (a^{r/2} - 1)(a^{r/2} + 1) \equiv 0 \pmod N$$

This implies that $N$ divides $(a^{r/2} - 1)(a^{r/2} + 1)$. Unless $a^{r/2} \equiv -1 \pmod N$, computing the greatest common divisor using Euclid's classical algorithm:

$$p = \gcd(a^{r/2} - 1, N), \quad q = \gcd(a^{r/2} + 1, N)$$

yields non-trivial factors of $N$ with high probability ($> 50\%$).

---

## 3. The $N=15, a=2$ Demonstration

To demonstrate this principle within the constraints of high-fidelity local quantum circuit simulation, we choose:

$$N = 15, \quad a = 2$$

Let us trace the classical modular exponentiation sequence:
- $2^0 \equiv 1 \pmod{15}$
- $2^1 \equiv 2 \pmod{15}$
- $2^2 \equiv 4 \pmod{15}$
- $2^3 \equiv 8 \pmod{15}$
- $2^4 \equiv 16 \equiv 1 \pmod{15}$

The order is $r = 4$.
Because $r=4$ is even:
$$a^{r/2} = 2^2 = 4$$
$$a^{r/2} - 1 = 4 - 1 = 3 \implies \gcd(3, 15) = 3$$
$$a^{r/2} + 1 = 4 + 1 = 5 \implies \gcd(5, 15) = 5$$
$$3 \times 5 = 15$$

---

## 4. Quantum Circuit Architecture

The quantum circuit constructed by `quantum/circuits.py` uses 8 qubits in total:
- **Counting Register ($t = 4$ qubits):** Stores the phase estimation and superposition of exponents.
- **Work Register ($n = 4$ qubits):** Holds the modular multiplication states ($2^4 = 16 > 15$).
- **Classical Register ($4$ bits):** Collects the measurement of the counting register.

```
count_0: ───[H]──────■─────────────────────────────────[IQFT]──[M]
                     │
count_1: ───[H]──────┼──────────■──────────────────────[IQFT]──[M]
                     │          │
count_2: ───[H]──────┼──────────┼──────────■───────────[IQFT]──[M]
                     │          │          │
count_3: ───[H]──────┼──────────┼──────────┼───────────[IQFT]──[M]
                   ┌─┴─┐      ┌─┴─┐      ┌─┴─┐
 work_0: ───[X]────┤   ├──────┤   ├──────┤   ├────────────────────
                   │   │      │   │      │   │
 work_1: ──────────┤ U ├──────┤ U²├──────┤ U⁴├────────────────────
                   │   │      │   │      │   │
 work_2: ──────────┤   ├──────┤   ├──────┤   ├────────────────────
                   │   │      │   │      │   │
 work_3: ──────────┤   ├──────┤   ├──────┤   ├────────────────────
                   └───┘      └───┘      └───┘
```

### 4.1 Step 1: Superposition Preparation
Applying Hadamard gates ($H$) to all 4 counting qubits prepares an equal superposition of all $2^4 = 16$ possible computational states:
$$|\psi_0\rangle = \frac{1}{\sqrt{16}} \sum_{x=0}^{15} |x\rangle |0000\rangle$$

Applying a Pauli-$X$ gate to work qubit 0 initializes the work register to $|1\rangle = |0001\rangle$:
$$|\psi_1\rangle = \frac{1}{4} \sum_{x=0}^{15} |x\rangle |1\rangle$$

### 4.2 Step 2: Controlled Modular Multiplication
Each counting qubit $j \in \{0, 1, 2, 3\}$ controls the application of the unitary operator $U^{2^j}$, mapping:
$$|x\rangle |y\rangle \to |x\rangle |(a^{2^j} \cdot y) \pmod{15}\rangle$$

For $a = 2 \pmod{15}$, the modular multiplication on the 4 work qubits $|q_3 q_2 q_1 q_0\rangle$ corresponds to a cyclic permutation of the 4 basis states:
$$|1\rangle \to |2\rangle \to |4\rangle \to |8\rangle \to |1\rangle$$

This is implemented using three controlled-swap (Fredkin) gates:
1. `cswap(count_j, work_2, work_3)`
2. `cswap(count_j, work_1, work_2)`
3. `cswap(count_j, work_0, work_1)`

For $a^2 = 4 \pmod{15}$, the permutation is:
$$|1\rangle \to |4\rangle, \quad |2\rangle \to |8\rangle, \quad |4\rangle \to |1\rangle, \quad |8\rangle \to |2\rangle$$
which is implemented with two controlled-swaps: `cswap(work_0, work_2)` and `cswap(work_1, work_3)`.

For $a^4 = 16 \equiv 1 \pmod{15}$, the operation is identity (no gates required).

### 4.3 Step 3: Phase Kickback and Inverse QFT
Through phase kickback, the eigenvalues $\lambda_s = e^{2\pi i (s / r)}$ are transferred into the relative phases of the counting register:
$$\frac{1}{4} \sum_{s=0}^{3} \left( \frac{1}{4} \sum_{x=0}^{15} e^{2\pi i x (s/4)} |x\rangle \right) |u_s\rangle$$

The Inverse Quantum Fourier Transform (IQFT) converts these relative phase differences into constructive interference at the specific computational basis states representing the phase:
$$\theta = \frac{s}{r} = \frac{s}{4} \quad \text{for } s \in \{0, 1, 2, 3\}$$

---

## 5. Classical Post-Processing via Continued Fractions

When the counting register is measured across 1024 shots on `AerSimulator`, the probability concentrates on four discrete bitstrings:

| Measured Bitstring | Integer $m$ | Phase $\theta = m / 2^4$ | Continued Fraction $s / r$ | Candidate Order $r$ | Outcome |
|---|---|---|---|---|---|
| `0000` | 0 | 0.00 | $0 / 1$ | 1 | Trivial phase (no order info) |
| `0100` | 4 | 0.25 | $1 / 4$ | 4 | **Valid order ($2^4 \equiv 1$)** |
| `1000` | 8 | 0.50 | $1 / 2$ | 2 | Partial order ($2^2 \equiv 4$) |
| `1100` | 12 | 0.75 | $3 / 4$ | 4 | **Valid order ($2^4 \equiv 1$)** |

For $r = 4$:
$$2^{4/2} = 4 \implies \gcd(4 - 1, 15) = 3, \quad \gcd(4 + 1, 15) = 5$$
The factors are verified: $3 \times 5 = 15$.

---

## 6. Honest Technical Limitations

- **Simulation vs. Physical Hardware:** This experiment runs on the high-performance Qiskit Aer local simulator. It executes the mathematically genuine quantum circuit, but within a simulated statevector / Clifford / matrix product setting.
- **Physical Scaling Realities:** Breaking RSA-2048 requires approximately 4,096 logical qubits and millions of physical noisy qubits with surface-code fault-tolerant error correction. Today's physical QPUs (50–1,000 noisy physical qubits) cannot yet execute Shor's algorithm for cryptographically meaningful numbers.
- **Educational Intent:** This demonstration is an educational proof-of-concept illustrating why lattice cryptography (FIPS 203 and FIPS 204) is essential to replace number-theoretic public-key algorithms.

