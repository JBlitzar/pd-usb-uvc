from usb_video import USBFramebuffer
from framebufferio import FramebufferDisplay
from displayio import release_displays

# vibe-coded code that should work

print("Initializing...")
release_displays()
display = FramebufferDisplay(USBFramebuffer(), auto_refresh=True)
fb = display.framebuffer

print(f"Framebuffer size: {fb.width}x{fb.height}")

# Direct fill - simpler approach
magenta_bytes = b"\x1f\xf8" * (fb.width * fb.height)  # RGB565 magenta
memoryview(fb)[:] = magenta_bytes

print("Should be showing magenta now")
display.refresh()
