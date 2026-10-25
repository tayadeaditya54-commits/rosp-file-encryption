#!/usr/bin/env python3
"""
================================================================================
AUTOMATED TEST SUITE: ROSP Open Source File Encryption System
Experiment 10: Technical Verification & Validation
Candidate: Aditya Tayade | B.E. Information Technology | ACPCE Kharghar
Academic Year: 2026-2027
================================================================================
"""

import os
import secrets
import tempfile
import unittest

from file_encryptor import (
    FileEncryptor,
    IntegrityError,
    InvalidFileFormatError,
    MAGIC_HEADER,
    SALT_SIZE,
    IV_SIZE,
    HMAC_SIZE,
    AES256Engine
)

class TestFileEncryptorSuite(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.password = "StrongPass#2026_Aditya"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_nist_aes256_known_answer(self):
        """Test 1: Verify NIST FIPS-197 AES-256 block encryption against standard test vector."""
        key = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
        plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")
        expected = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")
        cipher = AES256Engine(key)
        self.assertEqual(cipher.encrypt_block(plaintext), expected)

    def test_02_key_derivation_and_salt_uniqueness(self):
        """Test 2: Verify PBKDF2 key derivation produces distinct keys for identical passwords with different salts."""
        salt1 = secrets.token_bytes(SALT_SIZE)
        salt2 = secrets.token_bytes(SALT_SIZE)
        enc1, mac1 = FileEncryptor.derive_keys(self.password, salt1)
        enc2, mac2 = FileEncryptor.derive_keys(self.password, salt2)

        self.assertEqual(len(enc1), 32)
        self.assertEqual(len(mac1), 32)
        self.assertNotEqual(enc1, enc2)
        self.assertNotEqual(mac1, mac2)

    def test_03_roundtrip_file_encryption_decryption(self):
        """Test 3: Verify end-to-end encryption and decryption of a text file restores exact byte content."""
        sample_path = os.path.join(self.temp_dir.name, "doc.txt")
        enc_path = os.path.join(self.temp_dir.name, "doc.txt.enc")
        dec_path = os.path.join(self.temp_dir.name, "doc_decrypted.txt")

        original_content = (
            b"ROSP Project: File Encryption System by Aditya Tayade.\n"
            b"Department of Information Technology, ACPCE Kharghar.\n"
            b"Confidential cryptographic research data."
        )
        with open(sample_path, "wb") as f:
            f.write(original_content)

        FileEncryptor.encrypt_file(sample_path, enc_path, self.password)
        self.assertTrue(os.path.exists(enc_path))
        self.assertNotEqual(os.path.getsize(enc_path), 0)

        FileEncryptor.decrypt_file(enc_path, dec_path, self.password)
        with open(dec_path, "rb") as f:
            recovered_content = f.read()

        self.assertEqual(original_content, recovered_content)

    def test_04_tamper_detection_triggers_integrity_error(self):
        """Test 4: Verify ciphertext bit flipping immediately fails HMAC verification and triggers IntegrityError."""
        sample_path = os.path.join(self.temp_dir.name, "tamper.txt")
        enc_path = os.path.join(self.temp_dir.name, "tamper.txt.enc")
        dec_path = os.path.join(self.temp_dir.name, "tamper_recovered.txt")

        with open(sample_path, "wb") as f:
            f.write(b"Highly sensitive banking transaction or medical record.")

        FileEncryptor.encrypt_file(sample_path, enc_path, self.password)

        # Corrupt one single byte in the ciphertext portion
        with open(enc_path, "r+b") as f:
            f.seek(len(MAGIC_HEADER) + SALT_SIZE + IV_SIZE + 5)
            byte = f.read(1)
            f.seek(-1, os.SEEK_CUR)
            f.write(bytes([byte[0] ^ 0xFF]))

        with self.assertRaises(IntegrityError):
            FileEncryptor.decrypt_file(enc_path, dec_path, self.password)

        self.assertFalse(os.path.exists(dec_path))

    def test_05_wrong_password_rejection(self):
        """Test 5: Verify decryption attempt with an incorrect password is fundamentally rejected."""
        sample_path = os.path.join(self.temp_dir.name, "auth.txt")
        enc_path = os.path.join(self.temp_dir.name, "auth.txt.enc")
        dec_path = os.path.join(self.temp_dir.name, "auth_dec.txt")

        with open(sample_path, "wb") as f:
            f.write(b"Confidential payload")

        FileEncryptor.encrypt_file(sample_path, enc_path, self.password)

        with self.assertRaises(IntegrityError):
            FileEncryptor.decrypt_file(enc_path, dec_path, "WrongPassword#9999")

    def test_06_chunked_streaming_handles_multichunk_files(self):
        """Test 6: Verify streaming encryption handles large multi-chunk files (>128 KB) with constant memory."""
        sample_path = os.path.join(self.temp_dir.name, "large.bin")
        enc_path = os.path.join(self.temp_dir.name, "large.bin.enc")
        dec_path = os.path.join(self.temp_dir.name, "large_dec.bin")

        # Generate 150 KB random binary data (crosses 64 KB chunk boundary twice)
        large_data = secrets.token_bytes(150 * 1024)
        with open(sample_path, "wb") as f:
            f.write(large_data)

        FileEncryptor.encrypt_file(sample_path, enc_path, self.password)
        FileEncryptor.decrypt_file(enc_path, dec_path, self.password)

        with open(dec_path, "rb") as f:
            recovered_data = f.read()

        self.assertEqual(large_data, recovered_data)

    def test_07_empty_file_handling(self):
        """Test 7: Verify zero-byte empty files encrypt and decrypt without crash."""
        sample_path = os.path.join(self.temp_dir.name, "empty.txt")
        enc_path = os.path.join(self.temp_dir.name, "empty.txt.enc")
        dec_path = os.path.join(self.temp_dir.name, "empty_dec.txt")

        with open(sample_path, "wb") as f:
            pass  # 0 bytes

        FileEncryptor.encrypt_file(sample_path, enc_path, self.password)
        expected_size = len(MAGIC_HEADER) + SALT_SIZE + IV_SIZE + HMAC_SIZE
        self.assertEqual(os.path.getsize(enc_path), expected_size)

        FileEncryptor.decrypt_file(enc_path, dec_path, self.password)
        self.assertEqual(os.path.getsize(dec_path), 0)

    def test_08_verify_file_api_and_header_validation(self):
        """Test 8: Verify FileEncryptor.verify_file returns correct boolean without disk writes."""
        sample_path = os.path.join(self.temp_dir.name, "verify.txt")
        enc_path = os.path.join(self.temp_dir.name, "verify.txt.enc")

        with open(sample_path, "wb") as f:
            f.write(b"Verification test data")

        FileEncryptor.encrypt_file(sample_path, enc_path, self.password)

        self.assertTrue(FileEncryptor.verify_file(enc_path, self.password))
        self.assertFalse(FileEncryptor.verify_file(enc_path, "WrongPassword"))


def run_and_print_summary():
    print("=" * 70)
    print("RUNNING AUTOMATED TEST SUITE: Open Source File Encryption System")
    print("Experiment 10: Technical Verification & Validation")
    print("Candidate: Aditya Tayade | B.E. IT | ACPCE Kharghar | A.Y. 2026-27")
    print("=" * 70 + "\n")

    suite = unittest.TestLoader().loadTestsFromTestCase(TestFileEncryptorSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"TEST SUMMARY: {result.testsRun - len(result.failures) - len(result.errors)} / {result.testsRun} tests passed successfully.")
    print(f"STATUS: {'ALL PASS' if result.wasSuccessful() else 'FAILURES DETECTED'}")
    print("=" * 70)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_and_print_summary())
