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
FRAMES = 100

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
frames = frames[:FRAMES]
if frames.shape[0] == 0:
    raise SystemExit("No frames selected; check frames directory and fps downsampling")

print("Original size:", orig_size)
print("Selected frames:", frames.shape)

H, W = HEIGHT, WIDTH
BYTES_PER_ROW = (W + 7) // 8
BYTES_PER_FRAME = BYTES_PER_ROW * H


def pack_bits(frame_bool: np.ndarray) -> bytes:
    return np.packbits(frame_bool, axis=-1).tobytes()


delta_sizes = []


def encode_delta(prev: np.ndarray, cur: np.ndarray) -> bytes:
    xor = prev ^ cur
    ys, xs = np.nonzero(xor)
    delta_sizes.append(ys.size)
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
print("stats:")
total_deltas = len(delta_sizes)
print(" total frames (incl keyframe):", total_deltas + 1)
total_changed = sum(delta_sizes)
print(" total changed pixels:", total_changed)
avg_changed = total_changed / total_deltas
print(" avg changed pixels per frame:", avg_changed)
std_changed = np.std(delta_sizes)
q1_changed = np.percentile(delta_sizes, 25)
q3_changed = np.percentile(delta_sizes, 75)
min_changed = np.min(delta_sizes)
max_changed = np.max(delta_sizes)

print(" std changed pixels per frame:", std_changed)
print(" q1 changed pixels per frame:", q1_changed)
print(" q3 changed pixels per frame:", q3_changed)
print(" min changed pixels per frame:", min_changed)
print(" max changed pixels per frame:", max_changed)
