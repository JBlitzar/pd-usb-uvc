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


WIDTH = 150
HEIGHT = 112
FRAMES = 100
FPS = 10
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT

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


def draw_frame(frame_bits):
    i = 0
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        for byte_index in range(BYTES_PER_ROW):
            b = frame_bits[row_offset + byte_index]
            lookup = BIT8_TO_L[b]

            remaining_pixels = WIDTH - (byte_index * 8)
            num_pixels = min(8, remaining_pixels)

            buf[i : i + num_pixels] = lookup[:num_pixels]
            i += num_pixels


with open("pd-src/crushed_frames.bin", "rb") as f:
    frame_num = 0
    next_time = time.monotonic()
    while True:
        frame_bits = f.read(BYTES_PER_FRAME)

        if not frame_bits:
            f.seek(0)
            frame_bits = f.read(BYTES_PER_FRAME)
            frame_num = 0

        draw_frame(frame_bits)

        os.makedirs("output", exist_ok=True)

        img = Image.frombytes("L", (WIDTH, HEIGHT), bytes(buf))
        img.save("output/cur.bmp")

        now = time.monotonic()
        sleep_for = next_time - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        next_time += 1 / FPS

        frame_num += 1
        # print("Displayed frame", frame_num)
