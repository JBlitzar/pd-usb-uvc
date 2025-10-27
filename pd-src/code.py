import usb_video
import framebufferio
import displayio
import struct
import time


WIDTH = 150
HEIGHT = 112
FRAMES = 2190
FPS = 10
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT


# https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html#module-usb_video
displayio.release_displays()
fb = usb_video.USBFramebuffer()
display = framebufferio.FramebufferDisplay(fb)

buf = memoryview(fb)


def draw_frame(frame_bits):
    i = 0
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        for x in range(WIDTH):
            byte_index = row_offset + (x // 8)
            bit_index = 7 - (x % 8)  # MSB-first to match numpy.packbits
            b = frame_bits[byte_index]
            pixel_on = (b >> bit_index) & 1

            color = 0xFFFF if pixel_on else 0x0000
            struct.pack_into("<H", buf, i * 2, ((color >> 8) | ((color & 0xFF) << 8)))
            i += 1


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
