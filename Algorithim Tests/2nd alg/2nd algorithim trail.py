import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter

# Generate a random array of amplitude values (input signal)
input_signal = np.random.randn(1000)

# Define FIR filter parameters
N = 51  # Number of taps (filter order + 1)
f_c = 0.1  # Normalized cutoff frequency (e.g., 0.1 for low-pass)
beta = 8.6  # Beta parameter for the Kaiser window (controls shape)

# Design the FIR filter using the Kaiser window and desired cutoff frequency
h = firwin(N, cutoff=f_c, window=('kaiser', beta), pass_zero=True)

# Apply the FIR filter to the input signal using convolution
filtered_signal = lfilter(h, 1.0, input_signal)

# Plot the original signal
plt.figure(figsize=(15, 10))

plt.subplot(3, 1, 1)
plt.plot(input_signal, label='Original Signal', color='blue')
plt.title('Original Signal')
plt.legend()

# Plot the filtered signal
plt.subplot(3, 1, 2)
plt.plot(filtered_signal, label='Filtered Signal', color='red')
plt.title('Filtered Signal (Kaiser Window)')
plt.legend()

# Plot both original and filtered signals overlapping
plt.subplot(3, 1, 3)
plt.plot(input_signal, label='Original Signal', color='blue', alpha=0.5)
plt.plot(filtered_signal, label='Filtered Signal', color='red', alpha=0.5)
plt.title('Original vs. Filtered Signal (Kaiser Window)')
plt.legend()

plt.tight_layout()
plt.show()
