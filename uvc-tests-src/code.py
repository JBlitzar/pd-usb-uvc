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

for i in range(total_pixels):
    buf[i] = 0x1FF8

print("Refreshing display...")
display.refresh()
fb.refresh()
print("Done! Should be magenta now!")
