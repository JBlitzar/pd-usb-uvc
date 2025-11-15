# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
# ]
# ///
import struct
import time
from PIL import Image
import os


WIDTH = 160
HEIGHT = 120
FPS = 5
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT
KEYFRAME_MARKER = 0xFFFF

fb = bytearray(WIDTH * HEIGHT)
buf = memoryview(fb)


# Lookup table: maps a byte of 8 pixels (MSB first) to 8 grayscale bytes (255/0)
BIT8_TO_L = [bytearray(8) for _ in range(256)]
for b in range(256):
    arr = BIT8_TO_L[b]
    for bit in range(8):
        pixel_on = (b >> (7 - bit)) & 1
        arr[bit] = 255 if pixel_on else 0
    BIT8_TO_L[b] = bytes(arr)


def draw_frame(frame_bits: bytes) -> None:
    i = 0
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        for byte_index in range(BYTES_PER_ROW):
            b = frame_bits[row_offset + byte_index]
            lookup = BIT8_TO_L[b]
            remaining_pixels = WIDTH - (byte_index * 8)
            num_pixels = 8 if remaining_pixels >= 8 else remaining_pixels
            buf[i : i + num_pixels] = lookup[:num_pixels]
            i += num_pixels


def flip_bit_inplace(bitbuf: bytearray, idx: int) -> None:
    byte_i = idx // 8
    bit_in_byte = 7 - (idx % 8)
    bitbuf[byte_i] ^= 1 << bit_in_byte


with open("pd-src/crushed_frames.bin", "rb") as f:
    key = f.read(BYTES_PER_FRAME)
    if not key or len(key) < BYTES_PER_FRAME:
        raise SystemExit("Invalid stream: missing keyframe")

    cur_bits = bytearray(key)
    next_time = time.monotonic()

    while True:
        draw_frame(cur_bits)

        os.makedirs("output", exist_ok=True)
        img = Image.frombytes("L", (WIDTH, HEIGHT), bytes(buf))
        img.save("output/cur.bmp")

        now = time.monotonic()
        sleep_for = next_time - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        next_time += 1 / FPS

        len_bytes = f.read(2)
        if not len_bytes or len(len_bytes) < 2:
            f.seek(0)
            key = f.read(BYTES_PER_FRAME)
            if not key or len(key) < BYTES_PER_FRAME:
                raise SystemExit("Invalid stream after loop: missing keyframe")
            cur_bits[:] = key
            continue

        payload_len = len_bytes[0] | (len_bytes[1] << 8)
        if payload_len == 0:
            continue

        if payload_len == KEYFRAME_MARKER:
            key = f.read(BYTES_PER_FRAME)
            if not key or len(key) < BYTES_PER_FRAME:
                f.seek(0)
                key = f.read(BYTES_PER_FRAME)
                if not key or len(key) < BYTES_PER_FRAME:
                    raise SystemExit("Invalid stream after keyframe: missing data")
            cur_bits[:] = key
            continue

        payload = f.read(payload_len)
        if not payload or len(payload) < payload_len:
            f.seek(0)
            key = f.read(BYTES_PER_FRAME)
            if not key or len(key) < BYTES_PER_FRAME:
                raise SystemExit("Invalid stream after truncation: missing keyframe")
            cur_bits[:] = key
            continue

        i = 0
        while i + 1 < payload_len:
            idx = payload[i] | (payload[i + 1] << 8)
            flip_bit_inplace(cur_bits, idx)
            i += 2
