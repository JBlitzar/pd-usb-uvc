from usb_video import USBFramebuffer
from framebufferio import FramebufferDisplay
from displayio import release_displays

print("Initializing...")
release_displays()
display = FramebufferDisplay(USBFramebuffer(), auto_refresh=True)
fb = display.framebuffer
print(f"Filling {fb.width}x{fb.height} with magenta...")
buf = memoryview(fb)
total_pixels = fb.width * fb.height
# RGB565 magenta bytes
byte0 = 0x1F
byte1 = 0xF8
# Write pixel by pixel
# all that matters is that 0xFFFF is white and 0x0000 is black
# this magenta shows up as green, haha
for i in range(total_pixels):
    pos = i * 2
    buf[pos] = byte0
    buf[pos + 1] = byte1
print("Refreshing display...")
display.refresh()
fb.refresh()
print("Done! Should be magenta now!")
