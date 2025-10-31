# Scuffed video format

- frame count, FPS, dimensions, etc is inferred (haha, this needs to work for exactly one video in exactly one situation!)

  - in this case, 10 fps, 2190 frames, 160x120.

- first frame (keyframe): bitpacked data (width \* height / 8 bytes long, to be interpreted for each bit to be a pixel)
- each subsequent frame:
  - Data length in bytes (2 bytes numerical representation)
  - Two bytes to represent index of pixel flipped (to be interpreted as flattened indices of pixels to flip)
