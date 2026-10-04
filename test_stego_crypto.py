"""
test_stego_crypto.py - Automated Unit & Integration Tests
=========================================================
Tests cryptographic integrity, LSB embedding/extraction, capacity limits,
format enforcement, and edge case resilience.
"""

import os
import unittest
from PIL import Image

import crypto_utils as crypto
import steganography as stego


class TestCryptoUtils(unittest.TestCase):
    """Test cryptographic functions in crypto_utils.py."""

    def test_encrypt_decrypt_success(self):
        message = "Operation Overlord: 06-06-1944. Top Secret Clearance Required!"
        password = "SuperSecretPassword123!@#"

        encrypted = crypto.encrypt_message(message, password)
        self.assertTrue(crypto.is_encrypted(encrypted))
        self.assertNotEqual(message, encrypted)

        decrypted = crypto.decrypt_message(encrypted, password)
        self.assertEqual(message, decrypted)

    def test_wrong_password_raises_error(self):
        message = "Classified intelligence brief."
        password = "CorrectPassword"
        wrong_password = "WrongPassword"

        encrypted = crypto.encrypt_message(message, password)
        with self.assertRaises(crypto.InvalidPasswordError):
            crypto.decrypt_message(encrypted, wrong_password)

    def test_unicode_and_special_characters(self):
        message = "Steganography 🕵️‍♂️ • 像素秘密 • Секретные данные • 🚀🔒"
        password = "Key_🔑_123"

        encrypted = crypto.encrypt_message(message, password)
        decrypted = crypto.decrypt_message(encrypted, password)
        self.assertEqual(message, decrypted)

    def test_empty_message_or_password_raises(self):
        with self.assertRaises(ValueError):
            crypto.encrypt_message("", "pwd")
        with self.assertRaises(ValueError):
            crypto.encrypt_message("msg", "")


class TestSteganography(unittest.TestCase):
    """Test LSB encoding, decoding, and capacity checks."""

    def setUp(self):
        self.test_img_path = "test_cover.png"
        self.test_stego_path = "test_stego.png"
        self.test_jpg_path = "test_invalid.jpg"

        # Create a 100x100 RGB test image (10,000 pixels = 30,000 bits = 3,750 bytes capacity)
        self.img = Image.new("RGB", (100, 100), color=(128, 64, 200))
        self.img.save(self.test_img_path, format="PNG")

    def tearDown(self):
        for f in (self.test_img_path, self.test_stego_path, self.test_jpg_path):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def test_capacity_calculation(self):
        cap = stego.get_image_capacity(self.img)
        self.assertEqual(cap["width"], 100)
        self.assertEqual(cap["height"], 100)
        self.assertEqual(cap["total_pixels"], 10000)
        self.assertEqual(cap["total_bits"], 30000)
        self.assertEqual(cap["total_bytes"], 3750)
        self.assertEqual(cap["usable_bytes"], 3750 - len(stego.DEFAULT_DELIMITER.encode("utf-8")))

    def test_encode_and_decode_plaintext(self):
        secret = "The eagle flies at midnight. Latitude: 48.8584, Longitude: 2.2945."
        stego_img = stego.encode_lsb(self.img, secret)
        stego.save_stego_image(stego_img, self.test_stego_path)

        loaded_stego = Image.open(self.test_stego_path)
        extracted = stego.decode_lsb(loaded_stego)
        self.assertEqual(secret, extracted)

    def test_encode_and_decode_with_crypto(self):
        secret = "Highly sensitive cryptographic key payload: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        password = "StrongMasterPassword!99"

        encrypted_payload = crypto.encrypt_message(secret, password)
        stego_img = stego.encode_lsb(self.img, encrypted_payload)
        stego.save_stego_image(stego_img, self.test_stego_path)

        loaded_stego = Image.open(self.test_stego_path)
        extracted_raw = stego.decode_lsb(loaded_stego)
        self.assertTrue(crypto.is_encrypted(extracted_raw))

        decrypted = crypto.decrypt_message(extracted_raw, password)
        self.assertEqual(secret, decrypted)

    def test_capacity_exceeded_raises_error(self):
        # 100x100 has 3,750 bytes capacity. Let's create an oversized 5,000 byte message.
        huge_message = "A" * 4000
        with self.assertRaises(stego.CapacityExceededError):
            stego.encode_lsb(self.img, huge_message)

    def test_lossless_png_enforcement(self):
        stego_img = stego.encode_lsb(self.img, "Test")
        # Attempting to save as JPG must raise InvalidImageFormatError
        with self.assertRaises(stego.InvalidImageFormatError):
            stego.save_stego_image(stego_img, self.test_jpg_path)

    def test_no_hidden_message_in_clean_image(self):
        clean_img = Image.new("RGB", (50, 50), color=(0, 0, 0))
        with self.assertRaises(stego.NoHiddenMessageError):
            stego.decode_lsb(clean_img)


if __name__ == "__main__":
    unittest.main()
