# 🔒 Secrets within Pixels – The Art of Steganography

> **A professional, robust, and feature-rich desktop steganography application combining Spatial Domain LSB (Least Significant Bit) manipulation with authenticated AES-Fernet encryption.**

---

## 📌 Table of Contents
1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Architecture & Project Structure](#-architecture--project-structure)
4. [Mathematical & Cryptographic Foundations](#-mathematical--cryptographic-foundations)
   - [LSB Pixel Manipulation](#lsb-pixel-manipulation)
   - [Capacity Formula](#capacity-formula)
   - [Lossless PNG vs. Lossy JPEG](#lossless-png-vs-lossy-jpeg)
   - [Password-Based Encryption Architecture](#password-based-encryption-architecture)
5. [Installation & Setup](#-installation--setup)
6. [Usage Guide](#-usage-guide)
   - [Hiding Secrets (Encode)](#hiding-secrets-encode)
   - [Extracting Secrets (Decode)](#extracting-secrets-decode)
7. [Running Automated Tests](#-running-automated-tests)
8. [Error Handling & Security Resilience](#-error-handling--security-resilience)

---

## 👁️ Overview

**Secrets within Pixels** bridges the gap between **Steganography** (*hiding the existence of a message*) and **Cryptography** (*protecting the contents of a message*). 

While steganography alone provides *security through obscurity*, this application employs a defense-in-depth model: confidential data can be optionally encrypted with **AES-128 in CBC mode with HMAC-SHA256 (Fernet)** derived via **PBKDF2-HMAC-SHA256 (480,000 rounds)** before being sequentially embedded into the least significant bits of an image's Red, Green, and Blue channels.

---

## ✨ Key Features

- **Spatial Domain LSB Substitution Engine**: Modifies the LSB of 8-bit RGB channels, incurring less than $0.39\%$ alteration per channel—completely invisible to the human visual system (HVS).
- **Real-World Capacity Safeguards**: Automatically computes the exact byte/character capacity of any cover image ($W \times H \times 3 \div 8$). Dynamically checks payload size in real time and prevents capacity overrun.
- **Strict Format Enforcement (Lossless PNG)**: Strictly enforces `.png` for stego-images to guarantee pixel fidelity and prevent JPEG discrete cosine transform (DCT) from wiping hidden data.
- **Password-Authenticated Encryption (Optional Toggle)**: Optional military-grade encryption with a unique random salt generated per image. Tamper-evident HMAC prevents partial extraction under a wrong password.
- **Modern, Intuitive Tkinter Dashboard**:
  - Dark cybersecurity slate theme (`#0f172a`) with custom typography and clean margins.
  - Live character counter and dynamic capacity usage meter (Green $\to$ Amber $\to$ Red).
  - Thumbnail preview with aspect ratio preservation and image metadata inspector.
  - Show/Hide toggle for password entries.
  - Multi-threaded execution: encoding and decoding run asynchronously without freezing the UI.
  - One-click "Copy to Clipboard" and "Save to .txt" for extracted secrets.
- **Educational Guide & Specs Tab**: Built-in reference explaining the mathematics, bitwise logic, and security implications directly within the app.

---

## 🏗️ Architecture & Project Structure

The codebase is engineered with strict separation of concerns into modular components:

```
project1/
│
├── app.py                   # Modern Tkinter GUI, event handlers, and threading
├── steganography.py         # Pure LSB encoding, decoding, and capacity validation
├── crypto_utils.py          # PBKDF2 key derivation and Fernet encryption/decryption
├── requirements.txt         # Core dependencies (Pillow, cryptography)
├── test_stego_crypto.py     # Automated test suite (unit and integration tests)
├── generate_sample_image.py # Utility script to generate a high-res cover image
└── README.md                # Full documentation and technical specifications
```

---

## 🔬 Mathematical & Cryptographic Foundations

### LSB Pixel Manipulation
In standard 24-bit TrueColor images, every pixel is comprised of three 8-bit color channels:
$$\text{Pixel} = (R, G, B), \quad \text{where } R, G, B \in [0, 255]$$

In binary, an 8-bit channel value ranges from `00000000` to `11111111`:
$$\text{Channel Value} = \sum_{i=0}^{7} b_i \cdot 2^i = b_7 \cdot 128 + b_6 \cdot 64 + \dots + b_1 \cdot 2 + b_0 \cdot 1$$

Bit 0 ($b_0$) is the **Least Significant Bit (LSB)**. Flipping Bit 0 changes the color intensity by at most $\pm 1$ unit out of 256 ($\approx 0.391\%$).

#### Bitwise Embedding Operation:
To embed bit $b \in \{0, 1\}$ into channel value $v$:
1. **Clear Bit 0**: $v_{\text{cleared}} = v \ \& \ \sim 1$ (bitwise AND with `0xFE` / `254`)
2. **Inject Bit**: $v_{\text{new}} = v_{\text{cleared}} \ | \ b$ (bitwise OR with message bit)

#### Bitwise Extraction Operation:
To retrieve the embedded bit from channel value $v$:
$$b = v \ \& \ 1$$

---

### Capacity Formula
Each pixel holds 3 bits (1 bit in Red, 1 bit in Green, 1 bit in Blue).

$$\text{Total Available Bits} = \text{Width} \times \text{Height} \times 3$$
$$\text{Total Available Bytes} = \left\lfloor \frac{\text{Width} \times \text{Height} \times 3}{8} \right\rfloor$$
$$\text{Usable Payload Bytes} = \text{Total Available Bytes} - \text{len}(\text{Delimiter})$$

| Resolution | Total Pixels | Usable Bits | Usable Capacity (Bytes) | Equivalent Storage |
| :--- | :--- | :--- | :--- | :--- |
| **$640 \times 480$** | 307,200 | 921,600 | **115,200 bytes** | ~23,000 words (essay) |
| **$1280 \times 720$ (HD)** | 921,600 | 2,764,800 | **345,600 bytes** | ~70,000 words (short novel) |
| **$1920 \times 1080$ (FHD)** | 2,073,600 | 6,220,800 | **777,600 bytes** | ~155,000 words (full book) |

---

### Lossless PNG vs. Lossy JPEG
- **PNG (Portable Network Graphics)**: Uses **Deflate** compression (LZ77 + Huffman coding), which is mathematically **lossless**. Decompressed pixels are $100\%$ bit-identical to the original pixel values.
- **JPEG (Joint Photographic Experts Group)**: Uses **Discrete Cosine Transform (DCT)**, chroma subsampling (e.g. 4:2:0), and aggressive quantization. High-frequency variations (such as modified LSBs) are discarded as imperceptible noise during compression, which **destroys all hidden LSB data**.
- **Enforcement**: The application strictly mandates `.png` for saving stego-images.

---

### Password-Based Encryption Architecture
When encryption is enabled, the secret payload undergoes authenticated symmetric encryption:

```
[User Password] + [16-Byte Cryptographic Salt (os.urandom)]
                     │
                     ▼  PBKDF2-HMAC-SHA256 (480,000 iterations)
           [256-Bit Symmetric Key]
                     │
                     ▼  Fernet (AES-128-CBC + HMAC-SHA256)
  [Ciphertext + Initialization Vector + Integrity HMAC]
                     │
                     ▼  Bundled Package
        `ENC:v1:<Base64(Salt + FernetToken)>`
```

- **Salt**: 16 cryptographically random bytes generated anew for each encryption to defend against precomputed rainbow table attacks.
- **HMAC Verification**: If an incorrect password is entered or image pixels are tampered with, HMAC verification fails immediately with `InvalidPasswordError` before any corrupt plaintext can be displayed.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+ installed on your system.

### 1. Clone or Navigate to Directory
```powershell
cd "c:\Users\DELL INSPIRON 14\Desktop\project1"
```

### 2. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

---

## 💻 Usage Guide

### Launching the Desktop Application
```powershell
python app.py
```

### Hiding Secrets (Encode)
1. Navigate to the **"🛡️ Hide Secret (Encode)"** tab.
2. Click **"Browse Image..."** and choose any cover photo (PNG, BMP, JPG, etc.).
3. Notice the **Thumbnail Preview** and the calculated **Max Storage Capacity**.
4. Type or paste your secret message in the text box. Observe the live **Capacity Meter** update dynamically.
5. *(Optional)* Check **"Encrypt secret with password"** and enter a secret passphrase.
6. Click **"⚡ Encode Secret & Save PNG Image..."** and choose a location to save your output `.png` file.

### Extracting Secrets (Decode)
1. Navigate to the **"🔍 Extract Secret (Decode)"** tab.
2. Click **"Browse Stego-Image..."** and select the encoded `.png` image.
3. If the message was encrypted, enter the passphrase in the **Password** field.
4. Click **"🔓 Extract Hidden Secret"**.
5. The hidden message will appear in the output window. You can click **"📋 Copy to Clipboard"** or **"💾 Save to .txt..."**.

---

## 🧪 Running Automated Tests

Run the comprehensive unit and integration test suite:

```powershell
python -m unittest test_stego_crypto.py -v
```

The test suite validates:
- PBKDF2 + Fernet encryption & decryption roundtrip.
- Wrong password rejection (`InvalidPasswordError`).
- Unicode, emoji, and multilingual payload support.
- LSB spatial embedding and extraction fidelity.
- Delimiter termination.
- Capacity limit enforcement (`CapacityExceededError`).
- Lossless PNG format enforcement (`InvalidImageFormatError`).
- Clean images without payloads (`NoHiddenMessageError`).

---

## 🛡️ Error Handling & Security Resilience

- **Non-blocking GUI**: Heavy pixel encoding is dispatched to background threads so large images never cause the interface to hang.
- **Graceful Failure**: Incorrect passwords, malformed payloads, or corrupted files trigger explanatory dialogs rather than unhandled crashes.
- **Alpha Channel Preservation**: When encoding transparent images (RGBA), the Alpha channel is preserved intact to maintain transparency visuals.
