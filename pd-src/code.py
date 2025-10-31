import usb_video
import framebufferio
import displayio
import time
import gc
from array import array


WIDTH = 160
HEIGHT = 120
FPS = 10
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT


# https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html#module-usb_video
displayio.release_displays()
fb = usb_video.USBFramebuffer()
display = framebufferio.FramebufferDisplay(fb, auto_refresh=True)

# Framebuffer is 16-bit RGB565 elements
buf16 = memoryview(fb)
gc.collect()

# Precompute 16-bit RGB565 lookup for 8 pixels per input byte
BIT8_TO_RGB565 = array("H", [0] * (256 * 8))
for b in range(256):
    base = b * 8
    for bit in range(8):
        pixel_on = (b >> (7 - bit)) & 1
        BIT8_TO_RGB565[base + bit] = 0xFFFF if pixel_on else 0x0000

mv_lookup = BIT8_TO_RGB565


def render_full_from_bits(frame_bits: bytes) -> None:
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        base_fb = y * WIDTH
        for byte_index in range(BYTES_PER_ROW):
            b = frame_bits[row_offset + byte_index]
            lookup_base = b * 8

            remaining_pixels = WIDTH - (byte_index * 8)
            num_pixels = 8 if remaining_pixels >= 8 else remaining_pixels

            for k in range(num_pixels):
                dst_pos = base_fb + (byte_index * 8 + k)
                src_pos = lookup_base + k
                buf16[dst_pos] = mv_lookup[src_pos]


def flip_bit_inplace(bitbuf: bytearray, idx: int) -> None:
    byte_i = idx // 8
    bit_in_byte = 7 - (idx % 8)
    bitbuf[byte_i] ^= 1 << bit_in_byte


with open("crushed_frames.bin", "rb") as f:
    # initial keyframe
    first = f.read(BYTES_PER_FRAME)
    if not first or len(first) < BYTES_PER_FRAME:
        raise RuntimeError("Invalid stream: missing keyframe")

    cur_bits = bytearray(first)
    render_full_from_bits(cur_bits)
    display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)

    next_time = time.monotonic()

    while True:
        # timing gate for next frame
        now = time.monotonic()
        sleep_for = next_time - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        next_time += 1 / FPS

        # read delta
        len_bytes = f.read(2)
        if not len_bytes or len(len_bytes) < 2:
            # loop: new keyframe
            f.seek(0)
            first = f.read(BYTES_PER_FRAME)
            if not first or len(first) < BYTES_PER_FRAME:
                raise RuntimeError("Invalid stream after loop: missing keyframe")
            cur_bits = bytearray(first)
            render_full_from_bits(cur_bits)
            display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
            continue

        payload_len = len_bytes[0] | (len_bytes[1] << 8)
        if payload_len == 0:
            # identical frame; refresh to present
            display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
            continue

        payload = f.read(payload_len)
        if not payload or len(payload) < payload_len:
            # restart from beginning on truncation
            f.seek(0)
            first = f.read(BYTES_PER_FRAME)
            if not first or len(first) < BYTES_PER_FRAME:
                raise RuntimeError("Invalid stream after truncation: missing keyframe")
            cur_bits = bytearray(first)
            render_full_from_bits(cur_bits)
            display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
            continue

        # apply flips directly to buffer and cur_bits
        i = 0
        while i + 1 < payload_len:
            idx = payload[i] | (payload[i + 1] << 8)
            # Guard against malformed indices
            if idx >= WIDTH * HEIGHT:
                i += 2
                continue

            flip_bit_inplace(cur_bits, idx)

            byte_i = idx // 8
            bit_in_byte = 7 - (idx % 8)
            on = (cur_bits[byte_i] >> bit_in_byte) & 1
            buf16[idx] = 0xFFFF if on else 0x0000
            i += 2

        # present frame after applying deltas
        display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
