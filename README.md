# pd-usb-uvc

https://github.com/user-attachments/assets/e737253a-b9ba-4cf4-a35d-660bea247a19

<img src=readme/demo-linux.png style="width: 50%">

Streams the _Bad Apple_ video to webcam stream using the pico at 160x120 resolution! First working standalone utilization of usb_video module published on [Github](https://github.com/search?q=%22import+usb_video%22+language%3APython+path%3A*.py+NOT+%22thonny%22&type=code) as far as I can tell

_has been tested on RP2350 and Xiao RP2040!_

## Why This Exists

CircuitPython's `usb_video` module is barely documented and has exactly one other working example on GitHub (which throws type errors). This project serves as:

1. A complete, working reference implementation
2. Documentation of platform quirks and workarounds
3. Proof that USB webcam emulation is possible on the Pico
4. A collection of performance optimizations for constrained environments

If you're trying to use `usb_video` in your own project, this codebase may be the most complete resource available.

A minimal working example can be found in [`uvc-tests-src/`](uvc-tests-src)

## Technical details

### File format

The foremost constraints are those of storage space and compute power. I downscaled the video significantly. When storing the file, I store one initial keyframe and the rest as XOR diffs (since this is a binary video). Since this is a binary video, I can also store eight pixel values in one byte. Read more about the format of `crushed_frames.bin` at [format-spec.md](format-spec.md). I originally didn't store xor diffs and instead just had a series of bitpacked frames, but I ended up storing the diffs after realizing that _FrameBuffer doesn't allow slice assignment and makes you assign pixels one at a time_. Especially since I'm in circuitpython, the goal is to do as little as possible on the pico itself.

The pico reads the file in a streaming manner so as to not hold all of it in memory. (Although I ended up getting OOM anyways: the solution was to occasionally close and reopen the file and then `.seek()` to the last location to pick back up where it left off)

FrameBuffer expects pixel values to be in the "RGB 565 Swapped" pixel format. Who knows what that means? Luckily, pretty much universally black is all `0x0000`s and white is all `0xffff`s. At one point I tried to fill the screen with magenta and it turned out green so ¯\\\_(ツ)\_/¯ (Although maybe `ffplay` was just incorrectly interpreting it as YUYV? Honestly who knows atp).

See the code in action! Parsing and preparation is done in [gen_compressed.py](gen_compressed.py) while decoding and streaming is in [pd-src/code.py](pd-src/code.py)

### On documentation and bugs.

The second (and more daunting) problem that only revealed itself later was the severe lack of documentation or even [usage](https://github.com/search?q=%22import+usb_video%22+language%3APython+path%3A*.py+NOT+%22thonny%22&type=code) of this module. I guess it's a pretty esoteric use case, but still, I'm surprised that literally only one other person thought to use `usb_video` on the pico and publish it on Github. (the implementation of which throws type errors, by the way. So this is the only working implementation, as far as I can tell). [The documentation](https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html) is a stub. Lots of random issues like how it just doesn't work on Windows, or that the api exposes a `bytebuffer` that is 4\*width\*height bytes but only has `len()` of width \* height because each item is a 16-bit word. Or that `display.refresh()` and `fb.refresh()` are distinct and both need to be called. So hopefully this can be a resource to others.

### Deploying on the edge.

> _The hard part of coding isn't the code; it's everything else_

This project shows why.

The statement couldn't be more true in the case of this project. Quite literally a 20% implementation, 80% troubleshooting time breakdown. Especially because half of the time there was no error, so I had to troubleshoot and guess blindly a bit. _(Screen enumerates but is all black? weird. Video streams but only when you reload the serial monitor is closed and reopened? cursed.)_ Even more so, this was built entirely via proxy testing with volunteers. So thank you to all the volunteers who helped test this out. I truly appreciate your help.

## Installation

> [!NOTE]
> USB UVC on the Pico does not work on Windows! This is an issue with the underlying library / how Windows deals with composite devices and is not something I am able to fix.

(requires a Pico of course, or any [compatible circuitpython-enabled board](readme/compatible_boards.txt))

- Install [Circuitpy firmware](https://circuitpython.org/board/raspberry_pi_pico2/)
- Copy everything in `pd-src` into the CIRCUITPY drive.
- Physically re-plug in the Pico and check your video devices!

## Hacking

Swap out badapple.mp4 for a video file of your choosing, update `prepare.sh`, and run `prepare.sh` to use a different video

## Licensing

See LICENSE
