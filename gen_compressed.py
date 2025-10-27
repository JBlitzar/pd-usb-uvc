import PIL
from PIL import Image
import os
import glob
import numpy as np
from tqdm import tqdm
import random

WIDTH = 150
HEIGHT = 150 * 3 // 4
FPS = 10

orig_fps = 30
big_array = []
for filepath in tqdm(sorted(glob.glob("frames/*.jpg"))):
    if (
        int(os.path.basename(filepath).split("_")[1].split(".")[0]) % (orig_fps // FPS)
    ) != 0:
        continue
    with Image.open(filepath) as img:
        img = img.resize((WIDTH, HEIGHT))

        img = img.convert("L")
        img_array = np.array(img)
        binary_array = (img_array > 128).astype(np.uint8)
        big_array.append(binary_array)
big_array = np.array(big_array)
big_array = big_array

print(big_array.shape)

# xor_array = np.zeros_like(big_array)
# xor_array[0] = big_array[0]
# for i in range(1, big_array.shape[0]):
#     xor_array[i] = big_array[i] ^ big_array[i - 1]

# avg_ones = np.mean(np.sum(xor_array, axis=(1, 2)))
# print("Average number of ones per xor frame:", avg_ones)


# random.seed(42)
# sample_indices = random.sample(range(len(xor_array)), min(10, len(xor_array)))

# for idx in sample_indices:
#     frame = xor_array[idx] * 255
#     img = Image.fromarray(frame.astype(np.uint8), mode="L")
#     img.save(f"output/xor_frame_{idx:04d}.png")

# print(f"Saved {len(sample_indices)} random xor frames as PNG images")


# xor_array = np.packbits(xor_array, axis=-1)
big_array = np.packbits(big_array, axis=-1)
with open("pd-src/crushed_frames.bin", "wb") as f:
    f.write(big_array.tobytes())
