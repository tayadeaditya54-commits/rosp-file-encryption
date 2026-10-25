# Experiment No.10

**Aim : Identify an Open Source Problem, Contribute to an Existing Project or Develop an Enhancement, Submit a Pull Request, Prepare a Technical Report, and Present the Work**

**[Technical Report]**

**Open Source Secure File Encryption & Decryption System using Authenticated AES-256 and HMAC-SHA256**

Submitted by: **Aditya Tayade**  
Class: **B.E. Information Technology**  
College: **A. C. Patil College of Engineering, Kharghar, Navi Mumbai**  
Academic Year: **2026–2027**  
Subject / Course: **Recent Open Source Project Lab (ROSP)**  

---

### Certificate

This is to certify that the mini-project report titled **“Open Source Secure File Encryption & Decryption System using Authenticated AES-256 and HMAC-SHA256”** is prepared and submitted by **Aditya Tayade** as part of Experiment No. 10 of the Recent Open Source Project Lab (ROSP) curriculum. The report describes an open-source security enhancement, architectural design, cryptographic implementation, automated test plan, and GitHub contribution workflow.

Faculty Signature: ___________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date: ___________________________

---

### Acknowledgement

I express my sincere gratitude to my subject teacher, laboratory faculty, and the Department of Information Technology at A. C. Patil College of Engineering, Kharghar, for providing the guidance and opportunity to work on real-world open-source software and security systems. I also acknowledge the Python Cryptographic Authority (`pyca/cryptography`), the NIST standards community, and open-source contributors worldwide for providing transparent documentation and reference architectures.

---

### Abstract

Data security in open-source environments requires robust confidentiality and integrity verification for files stored on local disks or transmitted over public networks. Standard ad-hoc encryption scripts often suffer from critical vulnerabilities: loading entire files into memory causing out-of-memory errors on large datasets, omitting authenticated encryption (AEAD) which allows ciphertext bit-flipping and padding oracle attacks, and using weak password hashing without random salts.

This project delivers a production-grade Open Source File Encryption & Decryption tool implementing Authenticated Encryption (Encrypt-then-MAC) using NIST FIPS-197 compliant AES-256 in Counter (CTR) mode coupled with HMAC-SHA256. Key derivation is handled via PBKDF2-HMAC-SHA256 with 600,000 iterations and a cryptographically secure 128-bit salt. A chunked streaming pipeline processes arbitrarily large files with $O(1)$ constant memory overhead. Any tampering with encrypted bytes immediately triggers an `IntegrityError` before plaintext recovery. The system is validated through an 8-test automated unit test suite with 100% pass rate.

---

### 1. Introduction to Open Source Cryptography

Open Source Software (OSS) provides the cornerstone for modern cybersecurity. Because cryptographic primitives must be publicly scrutinized to ensure no hidden backdoors or mathematical weaknesses exist (Kerckhoffs's Principle), industry standard encryption tools are almost exclusively open-source.

In the ROSP curriculum, this project fulfills the requirement of contributing to and developing secure open-source utilities that adhere to clean architecture, standard algorithms, and peer-reviewed protocols.

---

### 2. Problem Statement

Many open-source utilities and user scripts implement file encryption insecurely:
1. **Memory Exhaustion (DoS):** Encrypting multi-gigabyte video or database files by reading the whole file into RAM causes memory exhaustion crashes.
2. **Lack of Authenticity (Bit-Flipping Attacks):** Unauthenticated ciphers allow an adversary to alter ciphertext bytes; upon decryption, predictable bit errors appear without alerting the user.
3. **Weak Key Derivation:** Storing raw passwords or single-round MD5/SHA-256 hashes makes encryption keys vulnerable to precomputed Rainbow Table and dictionary attacks.
4. **Platform & Dependency Failures:** Heavy native C/Rust dependencies can fail to compile across diverse operating systems due to DLL policy restrictions.

---

### 3. Objectives

* Implement NIST FIPS-197 AES-256 in CTR mode without external native compilation issues.
* Apply Encrypt-then-MAC using HMAC-SHA256 for authenticated encryption (AEAD).
* Derive dual 256-bit keys (Encryption + Authentication) using PBKDF2 with 600,000 rounds and 16-byte random salts.
* Ensure streaming I/O with a 64 KB buffer for $O(1)$ memory consumption.
* Prevent unauthorized file decryption with strict tamper rejection.
* Build an automated test suite verifying all cryptographic properties.

---

### 4. Proposed Architecture & Header Format

The encrypted file uses a binary format:

```text
+------------------+------------------+------------------+-----------------------+-------------------+
| Magic (8 Bytes)  | Salt (16 Bytes)  | IV (16 Bytes)    | Ciphertext (Variable) | HMAC Tag (32 Bytes)|
| b"ROSPENC1"      | secrets.token    | secrets.token    | AES-256-CTR Stream    | SHA-256 HMAC      |
+------------------+------------------+------------------+-----------------------+-------------------+
|<------------------------- Authenticated by HMAC-SHA256 Tag ------------------------->|
```

1. **Magic Signature:** `b"ROSPENC1"` confirms file validity.
2. **Salt:** 16-byte random salt unique per file encryption.
3. **IV:** 16-byte initial counter block for CTR mode.
4. **Ciphertext:** Stream-encrypted data in 64 KB chunks.
5. **HMAC Tag:** 32-byte authentication digest over Header + Ciphertext.

---

### 5. Implementation Details

#### 5.1 Dual-Key Derivation
```python
def derive_keys(password: str, salt: bytes) -> Tuple[bytes, bytes]:
    derived = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt,
        iterations=600000,
        dklen=64
    )
    return derived[:32], derived[32:64]  # enc_key, mac_key
```

#### 5.2 Streaming Encryption with Authenticated MAC
```python
salt = secrets.token_bytes(16)
iv = secrets.token_bytes(16)
enc_key, mac_key = derive_keys(password, salt)
ctr = AES256CTRStream(enc_key, iv)
mac = hmac.new(mac_key, digestmod=hashlib.sha256)

# Header update
header = MAGIC_HEADER + salt + iv
mac.update(header)
fout.write(header)

# Streaming chunk loop
while chunk := fin.read(65536):
    ciphertext = ctr.process(chunk)
    mac.update(ciphertext)
    fout.write(ciphertext)

# Final tag
fout.write(mac.digest())
```

---

### 6. GitHub Contribution Workflow

```bash
# Initialize local Git repository
git init
git branch -M main

# Add files
git add file_encryptor.py test_file_encryptor.py test_results.txt README.md

# Commit
git commit -m "feat(crypto): implement chunked AES-256 authenticated file encryption"

# Link to GitHub remote and push
git remote add origin https://github.com/adityatayade/rosp-file-encryption.git
git push -u origin main
```

---

### 7. Testing & Verification

Automated suite `test_file_encryptor.py` executes 8 comprehensive checks:

| Test ID | Test Description | Expected Result | Status |
| :--- | :--- | :--- | :--- |
| Test 1 | NIST FIPS-197 AES-256 Known-Answer Test | Matches official NIST test vector | **PASS** |
| Test 2 | PBKDF2 Key Derivation & Salt Uniqueness | Different salts yield orthogonal keys | **PASS** |
| Test 3 | Roundtrip Encryption / Decryption | Bit-for-bit identical content restored | **PASS** |
| Test 4 | Tamper Detection (1-bit flipped) | Raises `IntegrityError`, zero output written | **PASS** |
| Test 5 | Incorrect Password Rejection | Authentication failed error raised | **PASS** |
| Test 6 | Chunked Streaming (>128 KB) | Constant $O(1)$ memory, exact match | **PASS** |
| Test 7 | Empty File Handling (0 bytes) | Header + MAC generated, clean restore | **PASS** |
| Test 8 | Verify File API (dry-run) | Returns boolean without disk operations | **PASS** |

**Summary: 8 / 8 Tests Passed (Exit Code 0)**

---

### 8. Assessment Rubrics (25 Marks)

* Understanding / Project Selection — **5 Marks**
* Git, Repository & OSS Practices — **5 Marks**
* Implementation / Contribution — **5 Marks**
* Testing, Result & Documentation — **5 Marks**
* Presentation / Viva / Mini Project — **5 Marks**
* **Total: 25 Marks**

---

### 9. Conclusion

The open-source file encryption system created for ROSP provides a verified, tamper-proof, and memory-efficient tool. By adhering to open-source cryptographic principles and standard authenticated encryption, the project demonstrates proficiency in software security, test automation, and collaborative development.
