import time
import random
import cv2
import numpy as np
import pyautogui
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

# ===== 模板图片路径（放在 ./assets 文件夹下）=====
DOTS_IMG = "assets/menu_dots.png"         # 二点按钮
LIKE_IMG = "assets/menu_like.png"         # “赞”
UNLIKE_IMG = "assets/menu_unlike.png"     # “取消”
DIVIDER_IMG = "assets/moments_divider.png" # 朋友圈分界线

# 匹配阈值
THRESH = 0.85

# 滚动与间隔设置
SCROLL_SKIP = -300   # 没找到按钮时快速下滑
CLICK_DELAY = (0.5, 1.0)

# 朋友圈窗口范围 (left, top, right, bottom) —— 需手动调整
MOMENTS_WINDOW = (1730, 705, 2546, 1520)

# 全局状态
paused = False
running = True

# ===== GUI 界面 =====
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("朋友圈自动点赞机器人")
        self.root.geometry("450x350")

        self.text = ScrolledText(root, state="disabled", wrap="word")
        self.text.pack(expand=True, fill="both")

        self.status = tk.Label(root, text="状态: 等待启动", fg="blue")
        self.status.pack()

        # 按钮
        self.btn_pause = tk.Button(root, text="暂停", command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=10, pady=5)

        self.btn_stop = tk.Button(root, text="停止", command=self.stop)
        self.btn_stop.pack(side=tk.LEFT, padx=10, pady=5)

    def log(self, msg):
        self.text.config(state="normal")
        self.text.insert(tk.END, msg + "\n")
        self.text.see(tk.END)
        self.text.config(state="disabled")

    def set_status(self, msg, color="black"):
        self.status.config(text="状态: " + msg, fg=color)

    def toggle_pause(self):
        global paused
        paused = not paused
        if paused:
            self.set_status("已暂停", "red")
            self.btn_pause.config(text="继续")
        else:
            self.set_status("运行中", "green")
            self.btn_pause.config(text="暂停")

    def stop(self):
        global running
        running = False
        self.set_status("已停止", "black")


app = None  # GUI 实例


# ===== 工具函数 =====
def screenshot_gray():
    """截图朋友圈窗口并转为灰度图"""
    img = pyautogui.screenshot(region=MOMENTS_WINDOW)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)


def find_image(screen, template_path, threshold=0.85):
    """在截图中查找模板图像"""
    template = cv2.imread(template_path, 0)
    if template is None:
        return None
    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    points = list(zip(*loc[::-1]))
    if not points:
        return None
    return points[0]


def click(x, y):
    """模拟点击（限定在朋友圈窗口范围内）"""
    abs_x = MOMENTS_WINDOW[0] + x
    abs_y = MOMENTS_WINDOW[1] + y
    pyautogui.moveTo(abs_x, abs_y, duration=0.2)
    pyautogui.click()
    time.sleep(random.uniform(*CLICK_DELAY))


def scroll_random():
    """随机下滑 -120 ~ -180"""
    step = random.randint(-210, -150)
    pyautogui.scroll(step)
    return step


# ===== 主逻辑 =====
def like_moments():
    global paused, running
    time.sleep(3)  # 给用户时间切换到微信窗口
    rounds_no_target = 0

    while running:
        if paused:
            time.sleep(1)
            continue
        else:
            app.set_status("运行中", "green")

        screen = screenshot_gray()

        # 找分界线，帮助避免遗漏
        divider_pos = find_image(screen, DIVIDER_IMG, THRESH)
        if divider_pos:
            app.log("检测到分界线，确保逐条处理")

        # 找二点按钮
        dots_pos = find_image(screen, DOTS_IMG, THRESH)

        if dots_pos:
            x, y = dots_pos
            app.log(f"[发现二点按钮] 相对坐标: {x}, {y}")
            click(x, y)

            time.sleep(0.5)
            menu_screen = screenshot_gray()

            if find_image(menu_screen, UNLIKE_IMG, THRESH):
                app.log(" → 已点赞，跳过")
                step = scroll_random()
                app.log(f" → 下滑 {step}px")

            elif find_image(menu_screen, LIKE_IMG, THRESH):
                app.log(" → 未点赞，执行点赞操作")
                like_pos = find_image(menu_screen, LIKE_IMG, THRESH)
                if like_pos:
                    lx, ly = like_pos
                    click(lx, ly)
                    app.log(" → 点赞完成")
                    step = scroll_random()
                    app.log(f" → 下滑 {step}px")
            else:
                app.log(" → 菜单未识别，跳过")
                step = scroll_random()
                app.log(f" → 下滑 {step}px")
        else:
            app.log("未找到二点按钮 → 快速下滑寻找新内容")
            pyautogui.scroll(SCROLL_SKIP)
            rounds_no_target += 1
            time.sleep(1.5)

        if rounds_no_target >= 5:
            app.log("没有更多动态，任务结束。")
            app.set_status("已完成", "blue")
            break

    app.set_status("已停止", "black")


# ===== 启动程序 =====
def start_program():
    threading.Thread(target=like_moments, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    app.log("程序启动，切换到微信朋友圈界面。")
    app.log("自动检测朋友圈 → 点赞 → 下滑")
    start_program()
    root.mainloop()
