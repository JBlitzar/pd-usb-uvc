import usb_video
import usb_hid
import usb_midi

# all of the negative documentation we possess
# https://github.com/search?q=%22import+usb_video%22+language%3APython+path%3A*.py+NOT+%22thonny%22&type=code
# ONE other github result.

# https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html


# https://github.com/adafruit/circuitpython/pull/8831 says maybe disabling HID and MIDI helps?

# https://github.com/PyDevices/pydisplay/blob/ef14624e6ff605a87784b5cd3ef641d7301e6ed4/board_configs/fbdisplay/cp_usb_video/board_config.py says it just doesn't work on windows
"""
usb_video - Allows streaming to a host computer via USB emulating a webcam

This is a CircuitPython only capability, and currently is only supported on RP2040 boards.
See:
    https://docs.circuitpython.org/en/latest/shared-bindings/usb_video/index.html
    https://github.com/adafruit/circuitpython/pull/8831

Currently, it shows up on Windows as an unsupported USB Composite Device, so it isn't working.
It is working on Unix, including ChromeOS.  To see how to enable external cameras on ChromeOS:
    https://support.google.com/chromebook/thread/187930465/how-do-i-use-my-usb-webcam?hl=en

The `auto_refresh` setting is not working, so `display_drv.show()` must be called after drawing
to the buffer.

NOTE:  You must put the following 2 lines in your boot.py.  Currently, the width and height
are set to 160 and 120 regardless of what you enter.

    from usb_video import enable_framebuffer
    enable_framebuffer(160, 120)
"""

usb_hid.disable()
usb_midi.disable()

usb_video.enable_framebuffer(160, 120)
