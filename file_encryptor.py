#!/usr/bin/env python3
"""
================================================================================
ROSP Lab - Experiment 10 / Mini Project: Open Source File Encryption System
Author: Aditya Tayade | B.E. Information Technology | ACPCE Kharghar
Academic Year: 2026-2027
Target: Cryptographic File Security & Open Source Contribution

Features:
- Authenticated Encryption: AES-256 CTR Mode with HMAC-SHA256 (Encrypt-Then-MAC)
- NIST FIPS-197 Compliant Standard Implementation
- PBKDF2-HMAC-SHA256 Key Derivation (600,000 iterations + 128-bit random salt)
- Streaming I/O with constant O(1) memory usage for arbitrary file sizes
- Cryptographic Tamper Detection & Integrity Verification
================================================================================
"""

import argparse
import hashlib
import hmac
import os
import secrets
import struct
import sys
from typing import Tuple

# Magic signature identifying files encrypted by ROSP File Encryptor v1
MAGIC_HEADER = b"ROSPENC1"
SALT_SIZE = 16          # 128-bit salt
IV_SIZE = 16            # 128-bit initialization vector
HMAC_SIZE = 32          # 256-bit SHA-256 HMAC tag
PBKDF2_ITERATIONS = 600000
CHUNK_SIZE = 64 * 1024  # 64 KB streaming buffer

# Standard Rijndael S-Box
SBOX = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
]

RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]

def _xtime(a: int) -> int:
    return ((a << 1) ^ 0x1B) & 0xFF if (a & 0x80) else (a << 1)

class AES256Engine:
    """NIST FIPS-197 compliant AES-256 block cipher engine."""
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("AES-256 requires exactly a 32-byte (256-bit) key")
        self._round_keys = self._key_expansion(key)

    def _sub_word(self, word):
        return [SBOX[b] for b in word]

    def _rot_word(self, word):
        return word[1:] + word[:1]

    def _key_expansion(self, key: bytes):
        w = [list(key[i:i+4]) for i in range(0, 32, 4)]
        for i in range(8, 60):
            temp = list(w[i - 1])
            if i % 8 == 0:
                temp = self._sub_word(self._rot_word(temp))
                temp[0] ^= RCON[i // 8]
            elif i % 8 == 4:
                temp = self._sub_word(temp)
            w.append([w[i - 8][j] ^ temp[j] for j in range(4)])
        return [bytes([b for word in w[i:i+4] for b in word]) for i in range(0, 60, 4)]

    def encrypt_block(self, block: bytes) -> bytes:
        state = list(block)
        rk = self._round_keys

        # Initial Round
        state = [state[i] ^ rk[0][i] for i in range(16)]

        # Rounds 1 through 13
        for r in range(1, 14):
            # SubBytes
            state = [SBOX[b] for b in state]
            # ShiftRows
            state = [
                state[0], state[5], state[10], state[15],
                state[4], state[9], state[14], state[3],
                state[8], state[13], state[2], state[7],
                state[12], state[1], state[6], state[11]
            ]
            # MixColumns
            new_state = [0] * 16
            for c in range(4):
                c4 = c * 4
                s0, s1, s2, s3 = state[c4], state[c4+1], state[c4+2], state[c4+3]
                t = s0 ^ s1 ^ s2 ^ s3
                new_state[c4+0] = s0 ^ t ^ _xtime(s0 ^ s1)
                new_state[c4+1] = s1 ^ t ^ _xtime(s1 ^ s2)
                new_state[c4+2] = s2 ^ t ^ _xtime(s2 ^ s3)
                new_state[c4+3] = s3 ^ t ^ _xtime(s3 ^ s0)
            state = [new_state[i] ^ rk[r][i] for i in range(16)]

        # Final Round (Round 14) without MixColumns
        state = [SBOX[b] for b in state]
        state = [
            state[0], state[5], state[10], state[15],
            state[4], state[9], state[14], state[3],
            state[8], state[13], state[2], state[7],
            state[12], state[1], state[6], state[11]
        ]
        return bytes(state[i] ^ rk[14][i] for i in range(16))


class AES256CTRStream:
    """CTR Mode Stream Cipher Generator using AES-256."""
    def __init__(self, key: bytes, iv: bytes):
        if len(iv) != 16:
            raise ValueError("IV must be exactly 16 bytes for AES-CTR")
        self.cipher = AES256Engine(key)
        self.counter = int.from_bytes(iv, byteorder="big")
        self.keystream_buffer = b""
        self.buffer_idx = 0

    def process(self, data: bytes) -> bytes:
        out = bytearray(len(data))
        for i in range(len(data)):
            if self.buffer_idx >= len(self.keystream_buffer):
                counter_bytes = self.counter.to_bytes(16, byteorder="big")
                self.keystream_buffer = self.cipher.encrypt_block(counter_bytes)
                self.counter = (self.counter + 1) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                self.buffer_idx = 0
            out[i] = data[i] ^ self.keystream_buffer[self.buffer_idx]
            self.buffer_idx += 1
        return bytes(out)


class EncryptionError(Exception):
    """Base exception for file encryption errors."""
    pass


class IntegrityError(EncryptionError):
    """Raised when ciphertext tampering or wrong password is detected."""
    pass


class InvalidFileFormatError(EncryptionError):
    """Raised when the input file is not a valid ROSP encrypted file."""
    pass


class FileEncryptor:
    """
    High-level File Encryption manager implementing Authenticated Encryption (AEAD).
    Encrypt-then-MAC: AES-256-CTR + HMAC-SHA256
    """

    @staticmethod
    def derive_keys(password: str, salt: bytes) -> Tuple[bytes, bytes]:
        """
        Derives two independent 256-bit keys using PBKDF2-HMAC-SHA256:
        - enc_key (32 bytes): for AES-256 encryption
        - mac_key (32 bytes): for HMAC-SHA256 authentication
        """
        derived = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
            dklen=64
        )
        return derived[:32], derived[32:64]

    @classmethod
    def encrypt_file(cls, input_path: str, output_path: str, password: str) -> None:
        """
        Encrypts an arbitrary file with authenticated streaming encryption.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        salt = secrets.token_bytes(SALT_SIZE)
        iv = secrets.token_bytes(IV_SIZE)
        enc_key, mac_key = cls.derive_keys(password, salt)

        ctr = AES256CTRStream(enc_key, iv)
        mac = hmac.new(mac_key, digestmod=hashlib.sha256)

        # Header payload: MAGIC (8B) + SALT (16B) + IV (16B)
        header = MAGIC_HEADER + salt + iv
        mac.update(header)

        temp_output_path = output_path + ".tmp"
        try:
            with open(input_path, "rb") as fin, open(temp_output_path, "wb") as fout:
                # Write placeholder for header (header + placeholder for HMAC)
                fout.write(header)

                while True:
                    chunk = fin.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    ciphertext = ctr.process(chunk)
                    mac.update(ciphertext)
                    fout.write(ciphertext)

                # Write final 32-byte HMAC at the end
                tag = mac.digest()
                fout.write(tag)

            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_output_path, output_path)
        except Exception:
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
            raise

    @classmethod
    def decrypt_file(cls, input_path: str, output_path: str, password: str) -> None:
        """
        Decrypts an encrypted file, verifying HMAC authentication prior to writing plain output.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Encrypted file not found: {input_path}")

        file_size = os.path.getsize(input_path)
        min_size = len(MAGIC_HEADER) + SALT_SIZE + IV_SIZE + HMAC_SIZE
        if file_size < min_size:
            raise InvalidFileFormatError("File is smaller than the minimum ROSP encrypted header size.")

        with open(input_path, "rb") as fin:
            header_magic = fin.read(len(MAGIC_HEADER))
            if header_magic != MAGIC_HEADER:
                raise InvalidFileFormatError("Invalid magic header. File is not a valid ROSP encrypted file.")

            salt = fin.read(SALT_SIZE)
            iv = fin.read(IV_SIZE)

            enc_key, mac_key = cls.derive_keys(password, salt)

            # Verification pass: check HMAC over (Header + Ciphertext)
            mac = hmac.new(mac_key, digestmod=hashlib.sha256)
            mac.update(MAGIC_HEADER + salt + iv)

            ciphertext_len = file_size - len(MAGIC_HEADER) - SALT_SIZE - IV_SIZE - HMAC_SIZE
            bytes_left = ciphertext_len
            while bytes_left > 0:
                to_read = min(CHUNK_SIZE, bytes_left)
                chunk = fin.read(to_read)
                mac.update(chunk)
                bytes_left -= len(chunk)

            expected_tag = fin.read(HMAC_SIZE)
            calculated_tag = mac.digest()

            if not hmac.compare_digest(expected_tag, calculated_tag):
                raise IntegrityError("Authentication failed: Wrong password or file has been tampered with!")

            # Decryption pass (authenticated guaranteed)
            fin.seek(len(MAGIC_HEADER) + SALT_SIZE + IV_SIZE)
            ctr = AES256CTRStream(enc_key, iv)

            temp_output = output_path + ".tmp"
            try:
                with open(temp_output, "wb") as fout:
                    bytes_left = ciphertext_len
                    while bytes_left > 0:
                        to_read = min(CHUNK_SIZE, bytes_left)
                        chunk = fin.read(to_read)
                        plaintext = ctr.process(chunk)
                        fout.write(plaintext)
                        bytes_left -= len(chunk)

                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(temp_output, output_path)
            except Exception:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                raise

    @classmethod
    def verify_file(cls, input_path: str, password: str) -> bool:
        """Verifies the cryptographic integrity of an encrypted file without writing output."""
        file_size = os.path.getsize(input_path)
        min_size = len(MAGIC_HEADER) + SALT_SIZE + IV_SIZE + HMAC_SIZE
        if file_size < min_size:
            return False

        with open(input_path, "rb") as fin:
            header_magic = fin.read(len(MAGIC_HEADER))
            if header_magic != MAGIC_HEADER:
                return False

            salt = fin.read(SALT_SIZE)
            iv = fin.read(IV_SIZE)
            _, mac_key = cls.derive_keys(password, salt)

            mac = hmac.new(mac_key, digestmod=hashlib.sha256)
            mac.update(MAGIC_HEADER + salt + iv)

            ciphertext_len = file_size - len(MAGIC_HEADER) - SALT_SIZE - IV_SIZE - HMAC_SIZE
            bytes_left = ciphertext_len
            while bytes_left > 0:
                to_read = min(CHUNK_SIZE, bytes_left)
                chunk = fin.read(to_read)
                mac.update(chunk)
                bytes_left -= len(chunk)

            expected_tag = fin.read(HMAC_SIZE)
            return hmac.compare_digest(expected_tag, mac.digest())


def main():
    parser = argparse.ArgumentParser(
        description="ROSP Open Source File Encryption & Decryption System (Aditya Tayade)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Encrypt command
    enc_parser = subparsers.add_parser("encrypt", help="Encrypt a file")
    enc_parser.add_argument("input", help="Path to input file")
    enc_parser.add_argument("-o", "--output", help="Path to output file (default: <input>.enc)")
    enc_parser.add_argument("-p", "--password", required=True, help="Password for encryption")

    # Decrypt command
    dec_parser = subparsers.add_parser("decrypt", help="Decrypt an encrypted file")
    dec_parser.add_argument("input", help="Path to encrypted file (.enc)")
    dec_parser.add_argument("-o", "--output", help="Path to decrypted output file")
    dec_parser.add_argument("-p", "--password", required=True, help="Password for decryption")

    # Verify command
    ver_parser = subparsers.add_parser("verify", help="Verify integrity of an encrypted file")
    ver_parser.add_argument("input", help="Path to encrypted file")
    ver_parser.add_argument("-p", "--password", required=True, help="Password to verify")

    args = parser.parse_args()

    if args.command == "encrypt":
        output = args.output or (args.input + ".enc")
        print(f"[+] Encrypting: '{args.input}' -> '{output}'...")
        FileEncryptor.encrypt_file(args.input, output, args.password)
        print("[SUCCESS] File encrypted with AES-256 + HMAC-SHA256 authenticated encryption.")

    elif args.command == "decrypt":
        if args.output:
            output = args.output
        elif args.input.endswith(".enc"):
            output = args.input[:-4]
        else:
            output = args.input + ".dec"

        print(f"[+] Decrypting: '{args.input}' -> '{output}'...")
        try:
            FileEncryptor.decrypt_file(args.input, output, args.password)
            print("[SUCCESS] File verified and decrypted successfully.")
        except IntegrityError as e:
            print(f"[ERROR] Integrity verification failed: {e}", file=sys.stderr)
            sys.exit(1)
        except InvalidFileFormatError as e:
            print(f"[ERROR] Invalid format: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "verify":
        print(f"[*] Verifying integrity of: '{args.input}'...")
        valid = FileEncryptor.verify_file(args.input, args.password)
        if valid:
            print("[PASS] File is authentic, untampered, and password is valid.")
        else:
            print("[FAIL] Integrity check failed. Password incorrect or file corrupted/tampered.")
            sys.exit(1)


if __name__ == "__main__":
    main()
