# Scuffed video format

- frame count, FPS, dimensions, etc is inferred (haha, this needs to work for exactly one video in exactly one situation!)

  - in this case, 10 fps, 2190 frames, 160x120.

- first frame (keyframe): bitpacked data (width * height / 8 bytes long, MSB-first per byte)
- each subsequent frame begins with a 2-byte little-endian header, followed by payload:
  - 0x0000: no changes (repeat previous frame)
  - 0xFFFF: keyframe — next (width * height / 8) bytes are a full bitpacked frame
  - any other even value N: delta — N bytes follow, interpreted as a list of 2-byte little-endian pixel indices (flattened y * width + x) to flip
