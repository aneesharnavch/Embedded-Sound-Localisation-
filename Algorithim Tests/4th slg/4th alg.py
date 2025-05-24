import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter

input_signal = np.random.randn(1000)
N = 21 
std_dev = 3 

n = np.arange(0, N) - (N - 1) / 2
gaussian_window = np.exp(-0.5 * (n / std_dev) ** 2)

gaussian_window /= np.sum(gaussian_window)
filtered_signal = lfilter(gaussian_window, 1.0, input_signal)
plt.figure(figsize=(15, 10))
plt.subplot(3, 1, 1)

plt.plot(input_signal, label='Original Signal', color='blue')
plt.title('Original Signal')
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(filtered_signal, label='Filtered Signal', color='red')
plt.title('Filtered Signal (Gaussian Window)')
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(input_signal, label='Original Signal', color='blue', alpha=0.5)
plt.plot(filtered_signal, label='Filtered Signal', color='red', alpha=0.5)
plt.title('Original vs. Filtered Signal (Gaussian Window)')
plt.legend()

plt.tight_layout()
plt.show()
