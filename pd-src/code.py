import usb_video
import framebufferio
import displayio
import time
import gc


WIDTH = 160
HEIGHT = 120
FPS = 10
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT


# https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html#module-usb_video
displayio.release_displays()
fb = usb_video.USBFramebuffer()
display = framebufferio.FramebufferDisplay(fb)

buf = memoryview(fb)
gc.collect()

# Precompute RGB565-swapped (LSB first) lookup for 8 pixels per input byte
BIT8_TO_RGB565_SWAPPED = bytearray(256 * 16)
for b in range(256):
    base = b * 16
    for bit in range(8):
        pixel_on = (b >> (7 - bit)) & 1
        color = 0xFFFF if pixel_on else 0x0000
        # swapped: low byte first, then high byte
        BIT8_TO_RGB565_SWAPPED[base + bit * 2] = color & 0xFF
        BIT8_TO_RGB565_SWAPPED[base + bit * 2 + 1] = (color >> 8) & 0xFF

mv_lookup = memoryview(BIT8_TO_RGB565_SWAPPED)


def render_full_from_bits(frame_bits: bytes) -> None:
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        base_fb = y * WIDTH * 2
        for byte_index in range(BYTES_PER_ROW):
            b = frame_bits[row_offset + byte_index]
            lookup_base = b * 16

            remaining_pixels = WIDTH - (byte_index * 8)
            num_pixels = 8 if remaining_pixels >= 8 else remaining_pixels

            for k in range(num_pixels):
                dst_pos = base_fb + (byte_index * 8 + k) * 2
                src_pos = lookup_base + k * 2
                buf[dst_pos] = mv_lookup[src_pos]
                buf[dst_pos + 1] = mv_lookup[src_pos + 1]


def flip_bit_inplace(bitbuf: bytearray, idx: int) -> None:
    byte_i = idx // 8
    bit_in_byte = 7 - (idx % 8)
    bitbuf[byte_i] ^= (1 << bit_in_byte)


with open("crushed_frames.bin", "rb") as f:
    first = f.read(BYTES_PER_FRAME)
    if not first or len(first) < BYTES_PER_FRAME:
        raise RuntimeError("Invalid stream: missing keyframe")

    cur_bits = bytearray(first)
    next_time = time.monotonic()

    while True:
        render_full_from_bits(cur_bits)
        fb.refresh()

        now = time.monotonic()
        sleep_for = next_time - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        next_time += 1 / FPS

        len_bytes = f.read(2)
        if not len_bytes or len(len_bytes) < 2:
            f.seek(0)
            first = f.read(BYTES_PER_FRAME)
            if not first or len(first) < BYTES_PER_FRAME:
                raise RuntimeError("Invalid stream after loop: missing keyframe")
            cur_bits[:] = first
            continue

        payload_len = len_bytes[0] | (len_bytes[1] << 8)
        if payload_len == 0:
            continue

        payload = f.read(payload_len)
        if not payload or len(payload) < payload_len:
            # restart from beginning on truncation
            f.seek(0)
            first = f.read(BYTES_PER_FRAME)
            if not first or len(first) < BYTES_PER_FRAME:
                raise RuntimeError("Invalid stream after truncation: missing keyframe")
            cur_bits[:] = first
            continue

        # flip indices (2 bytes little-endian each) and directly update framebuffer
        i = 0
        while i + 1 < payload_len:
            idx = payload[i] | (payload[i + 1] << 8)
            flip_bit_inplace(cur_bits, idx)

            # compute new pixel value from cur_bits
            byte_i = idx // 8
            bit_in_byte = 7 - (idx % 8)
            on = (cur_bits[byte_i] >> bit_in_byte) & 1
            dst = idx * 2
            if on:
                # white (RGB565-swapped): 0xFF, 0xFF
                buf[dst] = 0xFF
                buf[dst + 1] = 0xFF
            else:
                # black (RGB565-swapped): 0x00, 0x00
                buf[dst] = 0x00
                buf[dst + 1] = 0x00
            i += 2
