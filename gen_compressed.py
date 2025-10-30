# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "numpy",
#     "pillow",
#     "tqdm",
# ]
# ///
import PIL
from PIL import Image
import os
import glob
import numpy as np
from tqdm import tqdm

WIDTH = 160
HEIGHT = 120
FPS = 10

ORIG_FPS = 30
frames_bin = []
for filepath in tqdm(sorted(glob.glob("frames/*.png"))):
    frame_idx = int(os.path.basename(filepath).split("_")[1].split(".")[0])
    if (frame_idx % (ORIG_FPS // FPS)) != 0:
        continue
    with Image.open(filepath) as img:
        orig_size = img.size
        img = img.resize((WIDTH, HEIGHT))
        img = img.convert("L")
        img_array = np.array(img)
        binary_array = (img_array > 128).astype(np.uint8)
        frames_bin.append(binary_array)

frames = np.array(frames_bin, dtype=np.uint8)
if frames.shape[0] == 0:
    raise SystemExit("No frames selected; check frames directory and fps downsampling")

print("Original size:", orig_size)
print("Selected frames:", frames.shape)

H, W = HEIGHT, WIDTH
BYTES_PER_ROW = (W + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * H


def pack_bits(frame_bool: np.ndarray) -> bytes:
    return np.packbits(frame_bool, axis=-1).tobytes()


def encode_delta(prev: np.ndarray, cur: np.ndarray) -> bytes:
    xor = prev ^ cur
    ys, xs = np.nonzero(xor)
    if ys.size == 0:
        return (0).to_bytes(2, "little")
    idxs = (ys.astype(np.int32) * W + xs.astype(np.int32)).astype(np.uint16)
    payload = bytearray(2 * idxs.size)
    j = 0
    for v in idxs.tolist():
        payload[j] = v & 0xFF
        payload[j + 1] = (v >> 8) & 0xFF
        j += 2
    length_le = (len(payload)).to_bytes(2, "little")
    return length_le + payload


with open("pd-src/crushed_frames.bin", "wb") as f:
    # keyframe: bitpacked, MSB-first per np.packbits default
    f.write(pack_bits(frames[0]))
    # subsequent frames: 2-byte little-endian length followed by 2-byte LE indices
    for i in range(1, frames.shape[0]):
        f.write(encode_delta(frames[i - 1], frames[i]))

print("Wrote compressed stream to pd-src/crushed_frames.bin")
