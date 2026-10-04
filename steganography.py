"""
steganography.py - Core Least Significant Bit (LSB) Steganography Engine
========================================================================
Implements spatial domain LSB encoding and decoding across RGB color channels
with capacity validation, lossless format enforcement, and boundary termination.

Mathematical Foundations of LSB Substitution:
----------------------------------------------
In an 8-bit digital image, each color channel (Red, Green, Blue) is represented 
by an integer value ranging from 0 to 255 (binary 00000000 to 11111111):
    Bit position:  7   6   5   4   3   2   1   0
    Bit weight:  128  64  32  16   8   4   2   1  (LSB)

The Least Significant Bit (Bit 0) carries the smallest numerical weight (2^0 = 1).
Altering Bit 0 shifts the pixel's color channel intensity by at most ±1 unit,
an amplitude change of ~0.39% (1/256), which is undetectable to the human eye.

Bitwise Operations:
-------------------
1. Clear LSB:
   pixel_channel & ~1  (or pixel_channel & 0xFE / 254)
   Example: 11010111 & 11111110 = 11010110

2. Embed Message Bit (b in {0, 1}):
   new_channel = (pixel_channel & ~1) | b
   Example with b=1: 11010110 | 00000001 = 11010111
   Example with b=0: 11010110 | 00000000 = 11010110

3. Extract LSB:
   extracted_bit = pixel_channel & 1
"""

import os
from typing import Dict, Any, Generator, Tuple
from PIL import Image

# Sentinel delimiter indicating end of embedded payload
DEFAULT_DELIMITER = "###END###"


class SteganographyError(Exception):
    """Base exception for all steganography errors."""
    pass


class CapacityExceededError(SteganographyError):
    """Raised when the secret message exceeds the storage capacity of the cover image."""
    pass


class NoHiddenMessageError(SteganographyError):
    """Raised when no valid hidden message or delimiter is discovered in the image."""
    pass


class InvalidImageFormatError(SteganographyError):
    """Raised when an unsupported or lossy image format is encountered."""
    pass


class ImageProcessingError(SteganographyError):
    """Raised when an image cannot be read, converted, or written."""
    pass


def get_image_capacity(img: Image.Image, delimiter: str = DEFAULT_DELIMITER) -> Dict[str, Any]:
    """
    Calculate the theoretical and usable data capacity of an image for LSB embedding.

    Capacity Calculation Formula:
        Total Bits = Width * Height * 3 channels (R, G, B)
        Total Bytes = Total Bits // 8
        Usable Payload Bytes = Total Bytes - len(delimiter.encode('utf-8'))

    Args:
        img: A PIL Image object.
        delimiter: The termination sentinel string.

    Returns:
        A dictionary containing detailed capacity statistics.
    """
    width, height = img.size
    total_pixels = width * height
    total_bits = total_pixels * 3  # Using 3 channels (RGB) per pixel
    total_bytes = total_bits // 8

    delimiter_bytes = delimiter.encode("utf-8")
    delimiter_len = len(delimiter_bytes)
    usable_bytes = max(0, total_bytes - delimiter_len)

    return {
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "total_bits": total_bits,
        "total_bytes": total_bytes,
        "delimiter_len": delimiter_len,
        "usable_bytes": usable_bytes,
        # In UTF-8, English ASCII characters take 1 byte; complex unicode takes 2-4 bytes
        "usable_ascii_chars": usable_bytes,
    }


def _bytes_to_bits(data: bytes) -> Generator[int, None, None]:
    """
    Generate bits (0 or 1) sequentially from a byte sequence, Most Significant Bit (MSB) first.

    Args:
        data: Raw byte string to iterate over.

    Yields:
        Individual integer bits (0 or 1).
    """
    for byte in data:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1


def encode_lsb(image: Image.Image, secret_text: str, delimiter: str = DEFAULT_DELIMITER) -> Image.Image:
    """
    Embed a secret text string into the RGB channels of an image using LSB steganography.

    Args:
        image: Original cover PIL Image.
        secret_text: Secret message to hide.
        delimiter: Sentinel delimiter marking payload boundary.

    Returns:
        New PIL Image object containing the encoded secret payload.

    Raises:
        ValueError: If the secret text is empty.
        CapacityExceededError: If the message plus delimiter exceeds image capacity.
        ImageProcessingError: If the image cannot be converted to RGB/RGBA.
    """
    if not secret_text:
        raise ValueError("Secret message cannot be empty.")

    # Convert image to RGB or RGBA mode to ensure standard color channels
    if image.mode not in ("RGB", "RGBA"):
        try:
            image = image.convert("RGB")
        except Exception as e:
            raise ImageProcessingError(f"Failed to convert image mode '{image.mode}' to RGB: {e}")

    # Prepare payload bytes (secret message + delimiter)
    full_payload = (secret_text + delimiter).encode("utf-8")
    required_bytes = len(full_payload)
    required_bits = required_bytes * 8

    # Validate image capacity
    capacity = get_image_capacity(image, delimiter)
    if required_bytes > capacity["total_bytes"]:
        raise CapacityExceededError(
            f"Message payload exceeds image capacity!\n"
            f"Required: {required_bytes:,} bytes ({required_bytes * 8:,} bits)\n"
            f"Available: {capacity['total_bytes']:,} bytes ({capacity['total_bits']:,} bits)\n"
            f"Deficit: {required_bytes - capacity['total_bytes']:,} bytes"
        )

    # Create a mutable copy of the image
    stego_image = image.copy()
    width, height = stego_image.size
    pixels = stego_image.load()

    has_alpha = (stego_image.mode == "RGBA")
    bit_gen = _bytes_to_bits(full_payload)
    bit_exhausted = False

    # Sequentially iterate through pixels and modify RGB channels
    for y in range(height):
        for x in range(width):
            current_pixel = pixels[x, y]
            r, g, b = current_pixel[0], current_pixel[1], current_pixel[2]
            alpha = current_pixel[3] if has_alpha else None

            channels = [r, g, b]
            modified_channels = []

            for c in channels:
                try:
                    bit = next(bit_gen)
                    # Bitwise logic: clear LSB (c & ~1) and set with secret bit
                    new_val = (c & ~1) | bit
                    modified_channels.append(new_val)
                except StopIteration:
                    bit_exhausted = True
                    modified_channels.append(c)

            if has_alpha:
                pixels[x, y] = (modified_channels[0], modified_channels[1], modified_channels[2], alpha)
            else:
                pixels[x, y] = (modified_channels[0], modified_channels[1], modified_channels[2])

            if bit_exhausted:
                return stego_image

    return stego_image


def decode_lsb(image: Image.Image, delimiter: str = DEFAULT_DELIMITER) -> str:
    """
    Extract a hidden secret message from the RGB channels of an image using LSB steganography.

    Args:
        image: Stego PIL Image containing embedded data.
        delimiter: Sentinel delimiter marking payload boundary.

    Returns:
        The extracted secret message string.

    Raises:
        NoHiddenMessageError: If the termination delimiter is not found.
        ImageProcessingError: If the image mode cannot be read.
    """
    if image.mode not in ("RGB", "RGBA"):
        try:
            image = image.convert("RGB")
        except Exception as e:
            raise ImageProcessingError(f"Failed to read image in RGB mode: {e}")

    delimiter_bytes = delimiter.encode("utf-8")
    delimiter_len = len(delimiter_bytes)

    width, height = image.size
    pixels = image.load()

    current_byte = 0
    bits_collected = 0
    extracted_bytes = bytearray()

    # Read LSB from RGB channels sequentially
    for y in range(height):
        for x in range(width):
            current_pixel = pixels[x, y]
            r, g, b = current_pixel[0], current_pixel[1], current_pixel[2]

            for channel in (r, g, b):
                # Extract the Least Significant Bit
                bit = channel & 1
                current_byte = (current_byte << 1) | bit
                bits_collected += 1

                if bits_collected == 8:
                    extracted_bytes.append(current_byte)
                    current_byte = 0
                    bits_collected = 0

                    # Check for delimiter match at the tail of the buffer
                    if len(extracted_bytes) >= delimiter_len and extracted_bytes.endswith(delimiter_bytes):
                        # Found boundary delimiter!
                        message_bytes = extracted_bytes[:-delimiter_len]
                        try:
                            return message_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            # Attempt decoding with fallback for binary streams or corrupted encodings
                            return message_bytes.decode("utf-8", errors="replace")

    raise NoHiddenMessageError(
        "No hidden message found! The termination delimiter was not encountered.\n"
        "Ensure the image contains an embedded secret and was not compressed using a lossy format."
    )


def save_stego_image(stego_image: Image.Image, output_path: str) -> None:
    """
    Save the stego-image strictly in PNG lossless format.

    Why PNG is mandatory:
        JPEG and WebP use lossy compression (Discrete Cosine Transform, chroma subsampling,
        and quantization) which alters high-frequency pixel values, instantly corrupting LSB data.
        PNG uses lossless Deflate compression, guaranteeing exact pixel reconstruction.

    Args:
        stego_image: The encoded PIL Image.
        output_path: Destination file path. Must end with .png.

    Raises:
        InvalidImageFormatError: If the destination does not end with '.png'.
        ImageProcessingError: If saving the file fails.
    """
    ext = os.path.splitext(output_path)[1].lower()
    if ext != ".png":
        raise InvalidImageFormatError(
            f"Invalid file extension '{ext}'!\n"
            f"LSB steganography strictly requires lossless PNG format (.png).\n"
            f"Lossy formats like JPEG discard LSB data during compression."
        )

    try:
        stego_image.save(output_path, format="PNG", optimize=False)
    except Exception as e:
        raise ImageProcessingError(f"Failed to save stego-image to '{output_path}': {e}")
