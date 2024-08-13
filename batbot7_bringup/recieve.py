#!/usr/bin/env python

from serial import Serial
import time
import os
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.colors as colors
import numpy as np
from scipy import signal

from batbot7_bringup.sonar.bb_listener import EchoRecorder

Fs = 1E6
Ts = 1/Fs
T_chirp = 5E-3
NFFT = 512
noverlap = 400
window = signal.windows.hann(NFFT)
spec_settings = (Fs, NFFT, noverlap, window)

N_chirp = int(Fs * T_chirp)

def process2(raw, N_chirp, spec_settings, time_offs=0):
    # unraw = [((y << 8) | x) for x, y in zip(raw[::2], raw[1::2])]
    # unraw_balanced = unraw - np.mean(unraw)
    unraw_balanced = raw - np.mean(raw)

    pt_cut = unraw_balanced[time_offs:]
    remainder = unraw_balanced[:time_offs]

    Fs, NFFT, noverlap, window = spec_settings
    spec_tup = mlab.specgram(pt_cut, Fs=Fs, NFFT=NFFT, noverlap=noverlap)

    return spec_tup, pt_cut, remainder


def plot_spec(
    ax, fig, spec_tup, fbounds=(20e3, 100e3), dB_range=150, plot_title="spec"
):
    fmin, fmax = fbounds
    s, f, t = spec_tup

    lfc = (f >= fmin).argmax()
    s = 20 * np.log10(s)
    f_cut = f[lfc:]
    s_cut = s[:][lfc:]

    max_s = np.amax(s_cut)
    s_cut = s_cut - max_s

    [rows_s, cols_s] = np.shape(s_cut)

    dB = -dB_range
    # for vc in cols_s:
    #    vc = [dB if n < dB else n for n in vc]

    for col in range(cols_s):
        for row in range(rows_s):
            if s_cut[row][col] < dB:
                s_cut[row][col] = dB

    cf = ax.pcolormesh(t, f_cut, s_cut, cmap="jet", shading="auto")
    cbar = fig.colorbar(cf, ax=ax)

    ax.set_ylim(fmin, fmax)
    ax.set_ylabel("Frequency (Hz)")
    ax.set_xlabel("Time (sec)")
    ax.title.set_text(plot_title)

    cbar.ax.set_ylabel("dB")


def autocorr(unraw, chirp, min_dist=None):
    xcor = signal.correlate(unraw, chirp, mode="same", method="auto")
    xcor = np.abs(xcor) / np.max(xcor)

    primary_height = 0.4

    peaks, apeaks = signal.find_peaks(
        xcor, height=primary_height, prominence=[0.9, 2.0], distance=min_dist
    )

    return xcor, peaks


def plot_and_fft(new_data: np.uint16):
    plt.figure()
    plt.subplot(1, 2, 1)
    x_vals = np.linspace(0, len(new_data) / 1e6, num=len(new_data))
    plt.plot(x_vals, new_data, "ro-", linewidth=0.1, markersize=1.25)
    plt.xlabel("Time (s)")

    # do fft
    Fs = 1e6
    T = 1 / Fs
    N = len(new_data)
    X = np.fft.fft(new_data)
    freqs = np.fft.fftfreq(N, d=T)
    plt.subplot(1, 2, 2)
    plt.plot(freqs, np.abs(X), linewidth=1)
    plt.title("FFT")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude")
    plt.xlim(0, Fs / 2)  # Display only positive frequencies
    # plt.tight_layout()
    plt.show()


def read_bytes_to_uint16(file_name: str) -> np.uint16:
    new_data = np.zeros(int(os.path.getsize(file_name) / 2), dtype=np.uint16)
    count = 0
    with open(file_name, "rb") as f:
        dat = f.read(2)
        while dat:
            # new_data.append(dat[0] | dat[1] << 8)
            new_data[count] = dat[0] | dat[1] << 8
            count += 1
            dat = f.read(2)
    return new_data


def plot_split_ears(raw_data: np.uint16, left_ear: np.uint16, right_ear: np.uint16):
    # plt.figure()
    # plt.subplot(3, 1, 3)
    # x_vals = np.linspace(0, len(raw_data) / 1e6, num=len(raw_data))
    # plt.plot(x_vals, raw_data, "o-", linewidth=0.5, markersize=1)
    # plt.xlabel("Raw Input")

    # plt.subplot(4, 1, 1)
    # x_vals = np.linspace(0, len(left_ear) / 1e6, num=len(left_ear))
    # plt.plot(x_vals, left_ear, "o-", linewidth=0.5, markersize=1)
    # plt.xlabel("'Left Ear' @ 100kHz Sine")

    # plt.subplot(4, 1, 2)
    # x_vals = np.linspace(0, len(right_ear) / 1e6, num=len(right_ear))
    # plt.plot(x_vals, right_ear, "o-", linewidth=0.5, markersize=1)
    # plt.xlabel("'Right Ear' @ 500 Hz Sine")

    fig1, ax_spec = plt.subplots(nrows = 2)
    spec_tup1, pt_cut1, pt1 = process2(right_ear, N_chirp, spec_settings)
    plot_spec(ax_spec[0], fig1, spec_tup1, fbounds = (30E3, 100E3), dB_range=40, plot_title='Right Ear Spectrogram')

    spec_tup2, pt_cut2, pt2 = process2(left_ear, N_chirp, spec_settings)
    plot_spec(ax_spec[1], fig1, spec_tup2, fbounds = (30E3, 100E3), dB_range=40, plot_title='Left Ear Spectrogram')


    plt.tight_layout()
    plt.show()


def split_raw_to_LR(
    raw_data: np.uint16, channel_len: np.uint16, left_first=True
) -> tuple[np.uint16, np.uint16]:
    """Given a raw input of uint16, we assume the channel is split data, alternating
        between the left and right channel of data at bursts of channel_len. Could be
        right and then left, use left_first flag accordingly.

    Args:
        raw_data (npu.uint16): alternating left and right channel data
        channel_len (np.uint16): length of each channel's run
        left_first (bool, optional): If the left channel data is first. Defaults to True.

    Returns:
        tuple[np.uint16,np.uint16]: left channel, right channel
    """
    on_left_ear = left_first

    # want to leave no room for zeros in array so precisely calc
    #   the size depending on who starts first
    rem = len(raw_data) / 2 % channel_len
    mult = np.floor(len(raw_data) / 2 * 1 / channel_len)

    if np.floor(len(raw_data) / channel_len % 2) == 1.0:
        print("odd")
        is_odd = True
    else:
        is_odd = False

    if on_left_ear:
        if not is_odd:
            l_len = int(int(len(raw_data) / 2) - rem)
            r_len = len(raw_data) - l_len
        else:
            r_len = int(channel_len * (mult + 1))
            l_len = len(raw_data) - r_len

    else:
        if not is_odd:
            r_len = int(int(len(raw_data) / 2) - rem)
            l_len = len(raw_data) - r_len
        else:
            l_len = int(channel_len * (mult + 1))
            r_len = len(raw_data) - l_len

    # L R L R L R L R L R L R L R L R L  17

    print(f"Left: {l_len} right {r_len} mult {mult} rem {rem}")

    # allocate np buffers
    left_channel = np.zeros(l_len, dtype=np.uint16)
    right_channel = np.zeros(r_len, dtype=np.uint16)

    l_index = 0
    r_index = 0

    for i, data in enumerate(raw_data):
        if i % channel_len == 0:
            on_left_ear = not on_left_ear

        if on_left_ear:
            left_channel[l_index] = data
            l_index += 1
        else:
            right_channel[r_index] = data
            r_index += 1

    print(f"Left: {l_index} right {r_index}")
    return left_channel, right_channel


# teensy = Serial("/dev/tty.usbmodem136132801", baudrate=480e6,timeout=1)
# teensy = Serial("COM8", baudrate=480e6,timeout=1)

# read_time = 1e9
# count = 0
# file_path = 'data.bin'
# start_time = time.time_ns()
# with open(file_path, 'wb') as f:
#     teensy.write(b'1')
#     while time.time_ns() - start_time < read_time:
#         # data = teensy.read(8192)
#         data = teensy.read(1024)
#         f.write(data)
# teensy.write(b'0')
# teensy.close()

CHAN_BURST = 1000
bb_ears = EchoRecorder(
    Serial("/dev/ttyACM0"), channel_burst_len=CHAN_BURST
)

file_path = "data.bin"

if __name__ == "__main__":
    start = time.time_ns()
    raw_data, left_ear, right_ear = bb_ears.listen(30)

    dif = time.time_ns() - start

    print(f"Took {dif *1e-9*1e3 } ms")

    # new_data = read_bytes_to_uint16(file_path)
    print(f"Length {len(raw_data)}")

    dev = Serial()

    plot_split_ears(raw_data, left_ear, right_ear)

    exit()
