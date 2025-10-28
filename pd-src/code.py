import usb_video
import framebufferio
import displayio
import struct
import time


WIDTH = 150
HEIGHT = 112
FRAMES = 300
FPS = 10
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT


# https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html#module-usb_video
displayio.release_displays()
fb = usb_video.USBFramebuffer()
display = framebufferio.FramebufferDisplay(fb)

buf = memoryview(fb)


BIT8_TO_RGB565 = [bytearray(16) for _ in range(256)]
for b in range(256):
    arr = BIT8_TO_RGB565[b]
    for bit in range(8):
        pixel_on = (b >> (7 - bit)) & 1
        color = 0xFFFF if pixel_on else 0x0000
        arr[bit * 2] = color >> 8
        arr[bit * 2 + 1] = color & 0xFF
    BIT8_TO_RGB565[b] = bytes(arr)


def draw_frame(frame_bits):
    i = 0
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        for byte_index in range(BYTES_PER_ROW):
            b = frame_bits[row_offset + byte_index]
            lookup = BIT8_TO_RGB565[b]

            remaining_pixels = WIDTH - (byte_index * 8)
            num_pixels = min(8, remaining_pixels)
            num_bytes = num_pixels * 2

            buf[i : i + num_bytes] = lookup[:num_bytes]
            i += num_bytes


with open("crushed_frames.bin", "rb") as f:
    frame_num = 0
    next_time = time.monotonic()
    while True:
        frame_bits = f.read(BYTES_PER_FRAME)
        if not frame_bits or len(frame_bits) < BYTES_PER_FRAME:
            f.seek(0)
            frame_bits = f.read(BYTES_PER_FRAME)
            frame_num = 0

        draw_frame(frame_bits)
        fb.refresh()

        now = time.monotonic()
        sleep_for = next_time - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        next_time += 1 / FPS

        frame_num += 1
