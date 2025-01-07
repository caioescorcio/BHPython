import base64
import win32api
import win32con
import win32gui
import win32ui

def get_dimensions():
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    
    return (width, height, left, top)

def screenshot(name='screenshot'):
    hdesktop = win32gui.GetDesktopWindow()
    width, height, left, top = get_dimensions()
    
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)
    mem_dc = img_dc.CreateCompatibleDC()
    
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)
    mem_dc.BitBlt((0,0), (width, height),
                  img_dc, (left, top), win32con.SRCCOPY)
    screenshot.SaveBitmapFile(mem_dc, f'{name}.bmp')
    mem_dc.DeleteDC()
    win32gui.DeleteObject(screenshot.GetHandle())

def decode_and_save_image(base64_data, output_filename='decoded_image.bmp'):
    binary_data = base64.b64decode(base64_data)
    with open(output_filename, 'wb') as f:
        f.write(binary_data)

def run():
    screenshot()
    with open('screenshot.bmp', 'rb') as f:
        img = f.read()
        # img = bas64.b64encode(f.read())
    return img

if __name__ == '__main__':
    run()