import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import time
import random
import pyautogui
import keyboard
import os

# --- Windows 消息 ---
import win32gui
import win32api
import win32con

# ===================== 基本配置 =====================
# 朋友圈窗口坐标： (left, top, right, bottom)
MOMENTS_WINDOW = (1732, 489, 2542, 1515)

ASSETS_DIR = "assets"
DOTS_IMG   = os.path.join(ASSETS_DIR, "menu_dots.png")
LIKE_IMG   = os.path.join(ASSETS_DIR, "menu_like.png")
UNLIKE_IMG = os.path.join(ASSETS_DIR, "menu_unlike.png")

CONFIDENCE = 0.85

running = False
paused  = False
checked_count = 0
liked_count   = 0

# ================ 工具 & 消息封装 ===================
def region_wh():
    L, T, R, B = MOMENTS_WINDOW
    return (L, T, R - L, B - T)

def center_point():
    L, T, R, B = MOMENTS_WINDOW
    return ((L + R) // 2, (T + B) // 2)

def locate_image(img, region=None, confidence=CONFIDENCE):
    try:
        return pyautogui.locateOnScreen(img, region=region, confidence=confidence)
    except Exception as e:
        log(f"[定位出错] {img}: {e}")
        return None

def send_click_screen(sx, sy):
    target = win32gui.WindowFromPoint((sx, sy))
    if not target:
        return
    cx, cy = win32gui.ScreenToClient(target, (sx, sy))
    lparam = win32api.MAKELONG(cx & 0xFFFF, cy & 0xFFFF)
    win32api.SendMessage(target, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    win32api.SendMessage(target, win32con.WM_LBUTTONUP,   0,                     lparam)

def send_wheel_screen(sx, sy, delta):
    target = win32gui.WindowFromPoint((sx, sy))
    if not target:
        return
    lparam = win32api.MAKELONG(sx & 0xFFFF, sy & 0xFFFF)

    # HIWORD: delta (带符号16位)，LOWORD: 按键状态
    d16 = delta & 0xFFFF
    wparam = (d16 << 16) | 0

    win32api.PostMessage(target, win32con.WM_MOUSEWHEEL, wparam, lparam)

def scroll_random_wheel():
    """
    随机下滑 (150-210 像素之间)，不移动鼠标
    """
    cx, cy = center_point()
    step = random.randint(150, 210)  # 随机像素
    # 每一档 = 120 像素，delta = -120 表示向下
    delta = -120
    times = max(1, round(step / 120))

    for _ in range(times):
        send_wheel_screen(cx, cy, delta)
        time.sleep(0.02)

    return -step

# ====================== 日志 ========================
def log(msg):
    log_box.config(state="normal")
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    log_box.config(state="disabled")

# ====================== 主逻辑 ======================
def like_moments():
    global running, paused, checked_count, liked_count

    region = region_wh()

    while running:
        if paused:
            time.sleep(0.3)
            continue

        dots = locate_image(DOTS_IMG, region=region)
        if not dots:
            scroll_random_wheel()
            time.sleep(0.6)
            dots = locate_image(DOTS_IMG, region=region)
            if not dots:
                scroll_random_wheel()
                log("未检测到更多可操作的动态，脚本结束。")
                running = False
                break

        dx, dy = pyautogui.center(dots)
        send_click_screen(dx, dy)
        time.sleep(0.25)

        unlike_btn = locate_image(UNLIKE_IMG, region=region)
        like_btn   = locate_image(LIKE_IMG,   region=region)

        checked_count += 1

        if unlike_btn:
            log(f"[已点赞] 第 {checked_count} 条 → 下滑")
            scroll_random_wheel()
            time.sleep(0.6)
            continue

        if like_btn:
            lx, ly = pyautogui.center(like_btn)
            send_click_screen(lx, ly)
            liked_count += 1
            log(f"[点赞成功] 总点赞: {liked_count} / 已检测: {checked_count}")
            time.sleep(0.35)
            scroll_random_wheel()
            time.sleep(0.6)
            continue

        log("[菜单未识别] 下滑继续")
        scroll_random_wheel()
        time.sleep(0.6)

    log(f"任务完成。总检测: {checked_count} 条，总点赞: {liked_count} 条")

# ====================== 控制区 ======================
def start_script():
    global running, paused, checked_count, liked_count
    if running:
        log("脚本已在运行中。")
        return
    checked_count = 0
    liked_count = 0
    running = True
    paused = False
    threading.Thread(target=like_moments, daemon=True).start()
    log("脚本已启动。")

def stop_script():
    global running
    running = False
    log("脚本已停止。")

def toggle_pause():
    global paused
    paused = not paused
    log("暂停中…" if paused else "继续运行")

# ======================= GUI =======================
root = tk.Tk()
root.title("微信朋友圈自动点赞（滚轮+消息版）")
root.geometry("520x420")

btn_start = tk.Button(root, text="开始", command=start_script, bg="lightgreen")
btn_start.pack(pady=6)

btn_pause = tk.Button(root, text="暂停/继续 (P)", command=toggle_pause, bg="lightblue")
btn_pause.pack(pady=6)

btn_stop = tk.Button(root, text="停止", command=stop_script, bg="lightcoral")
btn_stop.pack(pady=6)

log_box = ScrolledText(root, state="disabled", wrap="word", height=15)
log_box.pack(expand=True, fill="both", padx=10, pady=10)

keyboard.add_hotkey("p", toggle_pause)

log(f"程序启动，窗口区域：{MOMENTS_WINDOW}")
root.mainloop()
