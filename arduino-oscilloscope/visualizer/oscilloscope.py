"""
Arduino Oscilloscope - Python Visualizer (Upgraded)
-----------------------------------------------------
این اسکریپت داده‌های دو کاناله را از پورت سریال آردوینو می‌خواند
(هر خط ارسالی باید به فرم "A0,A1" باشد، یعنی دو عدد جدا شده با کاما)
و آن‌ها را به‌صورت زنده مانند یک اسیلوسکوپ رسم می‌کند.

قابلیت‌های اضافه شده نسبت به نسخه اولیه:
  1) محور زمان واقعی بر حسب ثانیه (به‌جای فقط شماره نمونه)
  2) دکمه Pause/Resume برای متوقف کردن نمودار و بررسی دقیق سیگنال
  3) دکمه Clear Buffer برای پاک کردن داده‌های بافر
  4) دکمه Save CSV برای ذخیره داده‌های نمایش‌داده‌شده در فایل
  5) دکمه Save PNG برای گرفتن اسنپ‌شات از نمودار فعلی
  6) نمایش زنده اندازه‌گیری‌ها برای هر کانال: Vpp, Vmax, Vmin, Vavg, Vrms
  7) گزینه Auto Scale برای تنظیم خودکار محور Y (به‌جای بازه ثابت)
  8) نمایشگر وضعیت اتصال: Connected / No data / Paused / Serial error
  9) پنل تحلیل فرکانسی FFT قابل روشن/خاموش کردن (مثل اسیلوسکوپ‌های واقعی)
 10) تنظیم پورت سریال، نرخ ارتباط و اندازه بافر از طریق آرگومان‌های خط فرمان
 11) مدیریت خطای قطع اتصال سریال بدون کرش کردن برنامه

نصب پیش‌نیازها (در صورت نیاز):
    pip install pyserial numpy matplotlib

نحوه اجرا:
    python arduino_oscilloscope.py
    python arduino_oscilloscope.py --port COM5 --baud 115200 --buffer 200
"""

import argparse
import csv
import time
from collections import deque

import numpy as np
import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MultipleLocator
from matplotlib.widgets import CheckButtons, Button

# ---------------------------------------------------------------------------
# آرگومان‌های خط فرمان (با مقادیر پیش‌فرض همان تنظیمات کد اصلی شما)
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Arduino Oscilloscope Visualizer")
parser.add_argument('--port', default='COM4', help='Serial port, e.g. COM4 or /dev/ttyUSB0')
parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
parser.add_argument('--buffer', type=int, default=100, help='Number of samples kept in the view')
args = parser.parse_args()

# ثابت‌های کالیبراسیون مدار (دقیقاً مقادیر کد اصلی شما - در صورت نیاز تغییرشان دهید)
ADC_MIN_V = 0.36       # ولتاژ متناظر با کمترین مقدار خوانده‌شده از ADC
ADC_MAX_V = 4.52       # ولتاژ متناظر با بیشترین مقدار خوانده‌شده از ADC
DC_OFFSET_V = 2.444    # افست DC (ولتاژ مرکز نوسان روی مدار شما)
GAIN = 0.104           # ضریب مدار تقسیم/تقویت ولتاژ ورودی

Y_LIMIT = 22           # بازه پیش‌فرض محور Y وقتی Auto Scale خاموش است

# ---------------------------------------------------------------------------
# اتصال به پورت سریال
# ---------------------------------------------------------------------------
try:
    ser = serial.Serial(args.port, args.baud, timeout=0.1)
except serial.SerialException as e:
    print(f"[خطا] اتصال به پورت {args.port} برقرار نشد: {e}")
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# بافرهای داده
# ---------------------------------------------------------------------------
list_ch0 = deque(maxlen=args.buffer)
list_ch1 = deque(maxlen=args.buffer)
list_time = deque(maxlen=args.buffer)

start_time = time.time()
last_data_time = start_time
paused = False
serial_error = False

# ---------------------------------------------------------------------------
# ساخت Figure و کنترل‌ها (دو نمودار: دامنه زمان + دامنه فرکانس)
# ---------------------------------------------------------------------------
fig, (ax, ax_fft) = plt.subplots(2, 1, figsize=(11, 7), gridspec_kw={'height_ratios': [3, 1.2]})
plt.subplots_adjust(left=0.09, right=0.98, top=0.90, bottom=0.08, hspace=0.4)
try:
    fig.canvas.manager.set_window_title("Arduino Oscilloscope")
except Exception:
    pass

# چک‌باکس‌ها: انتخاب کانال + گزینه‌های نمایش
rax = fig.add_axes([0.015, 0.75, 0.14, 0.18])
check = CheckButtons(rax, ('Channel 1', 'Channel 2', 'Auto Scale', 'Show FFT'),
                      (True, True, False, False))


def make_button(y, label):
    bax = fig.add_axes([0.015, y, 0.14, 0.05])
    return Button(bax, label)


pause_button = make_button(0.68, 'Pause / Resume')
clear_button = make_button(0.61, 'Clear Buffer')
save_csv_button = make_button(0.54, 'Save CSV')
save_png_button = make_button(0.47, 'Save PNG')

status_text = fig.text(0.015, 0.42, 'Status: connecting...', fontsize=9)
info_text = fig.text(0.985, 0.965, '', fontsize=8, ha='right', va='top')


def toggle_pause(event):
    global paused
    paused = not paused


def clear_buffers(event):
    list_ch0.clear()
    list_ch1.clear()
    list_time.clear()


def save_csv(event):
    filename = f"scope_data_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 'ch1_V', 'ch2_V'])
        for t, v0, v1 in zip(list_time, list_ch0, list_ch1):
            writer.writerow([f"{t:.4f}", f"{v0:.4f}", f"{v1:.4f}"])
    print(f"داده‌ها ذخیره شدند: {filename}")


def save_png(event):
    filename = f"scope_snapshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
    fig.savefig(filename, dpi=150)
    print(f"عکس نمودار ذخیره شد: {filename}")


pause_button.on_clicked(toggle_pause)
clear_button.on_clicked(clear_buffers)
save_csv_button.on_clicked(save_csv)
save_png_button.on_clicked(save_png)


# ---------------------------------------------------------------------------
# خواندن داده از سریال (مقاوم در برابر قطع اتصال)
# ---------------------------------------------------------------------------
def read_serial():
    global last_data_time, serial_error
    got_data = False
    try:
        while ser.in_waiting > 0:
            raw = ser.readline().decode('utf-8', errors='ignore').strip()
            parts = raw.split(',')
            if len(parts) == 2:
                try:
                    a0 = float(parts[0])
                    a1 = float(parts[1])
                except ValueError:
                    continue
                va0 = ADC_MIN_V + (a0 / 1023) * (ADC_MAX_V - ADC_MIN_V)
                va1 = ADC_MIN_V + (a1 / 1023) * (ADC_MAX_V - ADC_MIN_V)
                vp0 = (va0 - DC_OFFSET_V) / GAIN
                vp1 = (va1 - DC_OFFSET_V) / GAIN
                list_ch0.append(vp0)
                list_ch1.append(vp1)
                list_time.append(time.time() - start_time)
                got_data = True
        serial_error = False
    except (OSError, serial.SerialException):
        serial_error = True
    if got_data:
        last_data_time = time.time()
    return got_data


def compute_stats(data):
    arr = np.array(data)
    return {
        'vpp': float(arr.max() - arr.min()),
        'vmax': float(arr.max()),
        'vmin': float(arr.min()),
        'vavg': float(arr.mean()),
        'vrms': float(np.sqrt(np.mean(arr ** 2))),
    }


def plot_fft(data, dt, color, label):
    if len(data) < 8 or dt is None or dt <= 0:
        return
    arr = np.array(data, dtype=float)
    arr = arr - arr.mean()          # حذف مؤلفه DC برای دیدن بهتر هارمونیک‌ها
    n = len(arr)
    freqs = np.fft.rfftfreq(n, d=dt)
    mags = np.abs(np.fft.rfft(arr)) / n * 2
    ax_fft.plot(freqs, mags, color=color, label=label)


# ---------------------------------------------------------------------------
# تابع بروزرسانی انیمیشن
# ---------------------------------------------------------------------------
def update(frame):
    if not paused:
        read_serial()

    status = check.get_status()
    show_ch1, show_ch2, auto_scale, show_fft = status

    ax.cla()
    ax_fft.cla()

    now_ref = list_time[-1] if list_time else 0.0
    x_vals = [t - now_ref for t in list_time]

    dt = None
    if len(list_time) > 1:
        dt = float(np.mean(np.diff(list(list_time))))

    info_lines = []

    if show_ch1 and list_ch0:
        ax.plot(x_vals, list_ch0, label="Channel 1", color='tab:blue')
        s = compute_stats(list_ch0)
        info_lines.append(
            f"CH1  Vpp={s['vpp']:.2f}V  Vmax={s['vmax']:.2f}V  "
            f"Vmin={s['vmin']:.2f}V  Vavg={s['vavg']:.2f}V  Vrms={s['vrms']:.2f}V")
        if show_fft:
            plot_fft(list_ch0, dt, 'tab:blue', 'CH1 FFT')

    if show_ch2 and list_ch1:
        ax.plot(x_vals, list_ch1, label="Channel 2", color='tab:orange')
        s = compute_stats(list_ch1)
        info_lines.append(
            f"CH2  Vpp={s['vpp']:.2f}V  Vmax={s['vmax']:.2f}V  "
            f"Vmin={s['vmin']:.2f}V  Vavg={s['vavg']:.2f}V  Vrms={s['vrms']:.2f}V")
        if show_fft:
            plot_fft(list_ch1, dt, 'tab:orange', 'CH2 FFT')

    info_text.set_text("\n".join(info_lines))

    if auto_scale:
        ax.relim()
        ax.autoscale(axis='y')
    else:
        ax.set_ylim(-Y_LIMIT, Y_LIMIT)
        ax.yaxis.set_major_locator(MultipleLocator(5))
        ax.yaxis.set_minor_locator(MultipleLocator(1))

    ax.grid(True, which='major', color='gray', linestyle='-', linewidth=0.8)
    ax.grid(True, which='minor', color='lightgray', linestyle=':', linewidth=0.5)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (V)")
    ax.set_title("Time Domain")
    if show_ch1 or show_ch2:
        ax.legend(loc="lower right", fontsize=8)

    if show_fft:
        ax_fft.set_xlabel("Frequency (Hz)")
        ax_fft.set_ylabel("Magnitude")
        ax_fft.set_title("Frequency Domain (FFT)")
        ax_fft.grid(True, linestyle=':', linewidth=0.5)
        if show_ch1 or show_ch2:
            ax_fft.legend(loc="upper right", fontsize=8)
    else:
        ax_fft.axis('off')
        ax_fft.text(0.5, 0.5, "Enable 'Show FFT' to view frequency spectrum",
                    ha='center', va='center', fontsize=9, color='gray')

    # نمایشگر وضعیت اتصال
    since_last = time.time() - last_data_time
    if serial_error:
        status_text.set_text("Status: Serial error")
        status_text.set_color('red')
    elif paused:
        status_text.set_text("Status: Paused")
        status_text.set_color('orange')
    elif since_last < 1.0:
        status_text.set_text("Status: Connected")
        status_text.set_color('green')
    else:
        status_text.set_text("Status: No data")
        status_text.set_color('red')


animation = FuncAnimation(fig, update, interval=20, cache_frame_data=False)

try:
    plt.show()
finally:
    ser.close()
