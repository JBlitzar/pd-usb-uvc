# pd-usb-uvc

https://github.com/user-attachments/assets/b60fbd34-49d6-4a2f-8e0a-33bf9a720d01

Play Bad Apple from your pico! Project enumerates as a webcam and streams bad apple at 160x120 resolution. First working standalone utilization of usb_video module published on [Github](https://github.com/search?q=%22import+usb_video%22+language%3APython+path%3A*.py+NOT+%22thonny%22&type=code) as far as I can tell

_has been tested on Xiao RP2040!_

## Technical details

The foremost constraints are those of storage space and compute power. I downscaled the video significantly. When storing the file, I store one initial keyframe and the rest as XOR diffs (since this is a binary video). Since this is a binary video, I can also store eight pixel values in one byte. Read more about the format of `crushed_frames.bin` at [format-spec.md](format-spec.md). I originally didn't store xor diffs and instead just had a series of bitpacked frames, but I ended up storing the diffs after realizing that _FrameBuffer doesn't allow slice assignment and makes you assign pixels one at a time_. Especially since I'm in circuitpython, the goal is to do as little as possible on the pico itself.

The second (and more daunting) problem that only revealed itself later was the severe lack of documentation or even [usage](https://github.com/search?q=%22import+usb_video%22+language%3APython+path%3A*.py+NOT+%22thonny%22&type=code) of this module. I guess it's a pretty esoteric use case, but still, I'm surprised that literally only one other person thought to use `usb_video` on the pico and publish it on Github. (the implementation of which throws type errors, by the way. So this is the only working implementation, as far as I can tell). [The documentation](https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html) is a stub. Lots of random issues like how it just doesn't work on Windows, or that the api exposes a `bytebuffer` that is 4\*width\*height bytes but only has `len()` of width \* height because each item is a 16-bit word. Or that `display.refresh()` and `fb.refresh()` are distinct and both need to be called. So hopefully this can be a resource to others.

Deploying on the edge.

> _The hard part of coding isn't the code; it's everything else_

Couldn't be more true in the case of this project. This project was quite literally 20% implementation, 80% troubleshooting. Especially because half of the time there was no error, so I had to troubleshoot and guess blindly a bit. _(Screen enumerates but is all black? weird. Video streams but only when you reload the serial monitor is closed and reopened? cursed.)_ Thank you to all the volunteers who helped test this out (I don't actually own a pico as of the time of writing). I truly appreciate your help.

## Installation

- Install Circuitpy firmware
- Copy everything in `pd-src` into the CIRCUITPY folder.

## Hacking

Swap out badapple.mp4 for a video file of your choosing, update `prepare.sh`, and run `prepare.sh` to use a different video

## Licensing

See LICENSE
