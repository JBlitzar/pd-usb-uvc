import struct
import time
from PIL import Image
import os


WIDTH = 150
HEIGHT = 112
FRAMES = 2190
FPS = 10
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT

fb = bytearray(WIDTH * HEIGHT)
buf = memoryview(fb)


def draw_frame(frame_bits):
    i = 0
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        for x in range(WIDTH):
            byte_index = row_offset + (x // 8)
            bit_index = 7 - (x % 8)
            b = frame_bits[byte_index]
            pixel_on = (b >> bit_index) & 1
            buf[i] = 255 if pixel_on else 0
            i += 1


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

        time.sleep(1 / FPS)

        frame_num += 1
        # print("Displayed frame", frame_num)
