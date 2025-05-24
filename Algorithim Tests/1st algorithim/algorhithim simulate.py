import numpy as np
import matplotlib.pyplot as plt

# Generate a random array of amplitude values (input signal)
input_signal = np.random.randn(1000)

# Define FIR filter parameters
N = 21  # Number of taps (filter order + 1)
f_c = 0.1  # Normalized cutoff frequency (e.g., 0.1 for low-pass)

# Generate the filter coefficients using the window method (e.g., Hamming window)
n = np.arange(N)
h = np.sinc(2 * f_c * (n - (N - 1) / 2)) * np.hamming(N)
h = h / np.sum(h)  # Normalize to ensure unity gain at DC

# Apply the FIR filter to the input signal using convolution
filtered_signal = np.convolve(input_signal, h, mode='same')

# Plot the original signal
plt.figure(figsize=(15, 10))

plt.subplot(3, 1, 1)
plt.plot(input_signal, label='Original Signal', color='blue')
plt.title('Original Signal')
plt.legend()

# Plot the filtered signal
plt.subplot(3, 1, 2)
plt.plot(filtered_signal, label='Filtered Signal', color='red')
plt.title('Filtered Signal')
plt.legend()

# Plot both original and filtered signals overlapping
plt.subplot(3, 1, 3)
plt.plot(input_signal, label='Original Signal', color='blue', alpha=0.5)
plt.plot(filtered_signal, label='Filtered Signal', color='red', alpha=0.5)
plt.title('Original vs. Filtered Signal')
plt.legend()

plt.tight_layout()
plt.show()
