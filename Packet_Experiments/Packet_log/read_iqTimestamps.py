import numpy as np
import matplotlib.pyplot as plt

# Read I-Q samples
iq_samples = np.fromfile('iq_samplesTx.dat', dtype=np.complex64)

# Read timestamps
timestamps = np.loadtxt('timestampsTx.txt', delimiter=',')

print(f"Total samples: {len(iq_samples)}")
print(f"First timestamp: {timestamps[0]}")

# Plot
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(iq_samples.real[:1000])
plt.plot(iq_samples.imag[:1000])
plt.title('I-Q Samples')
plt.legend(['I', 'Q'])

plt.subplot(1, 2, 2)
plt.scatter(iq_samples.real[:1000], iq_samples.imag[:1000], alpha=0.5)
plt.title('Constellation')
plt.xlabel('In-phase')
plt.ylabel('Quadrature')
plt.grid(True)
plt.show()