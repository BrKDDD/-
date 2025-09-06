import pyautogui
import time

print("请在 3 秒后点击朋友圈窗口的 **左上角** ...")
time.sleep(3)
x1, y1 = pyautogui.position()
print(f"左上角坐标: ({x1}, {y1})")

time.sleep(1)
print("请在 3 秒后点击朋友圈窗口的 **右下角** ...")
time.sleep(3)
x2, y2 = pyautogui.position()
print(f"右下角坐标: ({x2}, {y2})")

print("\n==== 建议的 MOMENTS_WINDOW 设置 ====")
print(f"MOMENTS_WINDOW = ({x1}, {y1}, {x2}, {y2})")
