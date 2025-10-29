import usb_video
import framebufferio
import displayio
import time
import gc


WIDTH = 150
HEIGHT = 112
FRAMES = 100
FPS = 10
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT


# https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html#module-usb_video
displayio.release_displays()
fb = usb_video.USBFramebuffer()
display = framebufferio.FramebufferDisplay(fb)

buf = memoryview(fb)
gc.collect()

BIT8_TO_RGB565 = bytearray(256 * 16)
for b in range(256):
    base = b * 16
    for bit in range(8):
        pixel_on = (b >> (7 - bit)) & 1
        color = 0xFFFF if pixel_on else 0x0000
        BIT8_TO_RGB565[base + bit * 2] = color >> 8
        BIT8_TO_RGB565[base + bit * 2 + 1] = color & 0xFF

mv_lookup = memoryview(BIT8_TO_RGB565)


def draw_frame(frame_bits):
    i = 0
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        fb_offset = y * 160 * 2  # full framebuffer row (160 pixels, RGB565 = 2 bytes)
        for byte_index in range(BYTES_PER_ROW):
            b = frame_bits[row_offset + byte_index]
            # scuffed lookup
            # should be LITERALLY memcpy at this point
            # plus, what, 3 ops per bit?
            # I guess I'll unroll the loop if it's still too slow
            # "developing on the edge!!" means terrible perf constraints
            # and yet I'm determined to not use C if at all possible
            lookup_start = b * 16

            remaining_pixels = WIDTH - (byte_index * 8)
            num_pixels = min(8, remaining_pixels)
            num_bytes = num_pixels * 2

            src = mv_lookup[lookup_start : lookup_start + num_bytes]
            buf[
                fb_offset + byte_index * 16 : fb_offset + byte_index * 16 + num_bytes
            ] = src


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
