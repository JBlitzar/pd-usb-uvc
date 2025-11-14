import usb_video
import framebufferio
import displayio
import time
import gc
from array import array


WIDTH = 160
HEIGHT = 120
FPS = 5
BYTES_PER_ROW = (WIDTH + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * HEIGHT
KEYFRAME_MARKER = 0xFFFF


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

# Precompute bit masks for per-pixel toggles
MASKS = array("B", [0x80 >> i for i in range(8)])


def render_full_from_bits(frame_bits: bytes) -> None:
    for y in range(HEIGHT):
        row_offset = y * BYTES_PER_ROW
        base_fb = y * WIDTH
        for byte_index in range(BYTES_PER_ROW):
            b = frame_bits[row_offset + byte_index]
            lookup_base = b * 8

            remaining_pixels = WIDTH - (byte_index * 8)

            if remaining_pixels >= 8:
                dst_pos = base_fb + (byte_index * 8)
                src_pos = lookup_base
                buf16[dst_pos] = mv_lookup[src_pos]
                buf16[dst_pos + 1] = mv_lookup[src_pos + 1]
                buf16[dst_pos + 2] = mv_lookup[src_pos + 2]
                buf16[dst_pos + 3] = mv_lookup[src_pos + 3]
                buf16[dst_pos + 4] = mv_lookup[src_pos + 4]
                buf16[dst_pos + 5] = mv_lookup[src_pos + 5]
                buf16[dst_pos + 6] = mv_lookup[src_pos + 6]
                buf16[dst_pos + 7] = mv_lookup[src_pos + 7]
            else:
                for k in range(remaining_pixels):
                    dst_pos = base_fb + (byte_index * 8 + k)
                    src_pos = lookup_base + k
                    buf16[dst_pos] = mv_lookup[src_pos]


def flip_bit_inplace(bitbuf: bytearray, idx: int) -> None:
    # Kept for reference; not used in hot path
    byte_i = idx >> 3
    mask = MASKS[idx & 7]
    bitbuf[byte_i] ^= mask


f = open("crushed_frames.bin", "rb")

# initial keyframe
first = f.read(BYTES_PER_FRAME)
if not first or len(first) < BYTES_PER_FRAME:
    raise RuntimeError("Invalid stream: missing keyframe")

cur_bits = bytearray(first)
render_full_from_bits(cur_bits)
display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
fb.refresh()
gc.collect()

next_time = time.monotonic()
frame_count = 0

while True:
    # Every N frames, nuke the file handle
    if frame_count % 50 == 0 and frame_count > 0:
        current_position = f.tell()
        f.close()
        f = open("crushed_frames.bin", "rb")
        f.seek(current_position)

    frame_count += 1

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
        fb.refresh()
        if (frame_count % 20) == 0:
            gc.collect()
        continue

    payload_len = len_bytes[0] | (len_bytes[1] << 8)
    if payload_len == 0:
        # identical frame; refresh to present
        display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
        fb.refresh()
        if (frame_count % 20) == 0:
            gc.collect()
        continue

    if payload_len == KEYFRAME_MARKER:
        # next BYTES_PER_FRAME bytes are a full keyframe
        key = f.read(BYTES_PER_FRAME)
        if not key or len(key) < BYTES_PER_FRAME:
            # restart from beginning on truncation
            f.seek(0)
            first = f.read(BYTES_PER_FRAME)
            if not first or len(first) < BYTES_PER_FRAME:
                raise RuntimeError("Invalid stream after keyframe: missing data")
            cur_bits = bytearray(first)
        else:
            cur_bits = bytearray(key)
        render_full_from_bits(cur_bits)
        display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
        fb.refresh()
        if (frame_count % 20) == 0:
            gc.collect()
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
        fb.refresh()
        if (frame_count % 20) == 0:
            gc.collect()
        continue

    # apply flips with minimized Python overhead
    max_idx = WIDTH * HEIGHT
    masks = MASKS
    b16 = buf16
    bits = cur_bits
    for i in range(0, payload_len, 2):
        idx = payload[i] | (payload[i + 1] << 8)
        if idx >= max_idx:
            continue
        byte_i = idx >> 3
        mask = masks[idx & 7]
        val = bits[byte_i] ^ mask
        bits[byte_i] = val
        on = 1 if (val & mask) else 0
        b16[idx] = 0xFFFF if on else 0x0000

    # present frame after applying deltas
    display.refresh(target_frames_per_second=10, minimum_frames_per_second=0)
    fb.refresh()
    if (frame_count % 20) == 0:
        gc.collect()
