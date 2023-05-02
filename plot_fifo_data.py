import pickle
import matplotlib.pyplot as plt
import numpy as np

with open('fifo_data.pkl', 'rb') as file:
    samples = pickle.load(file)
I = []
Q = []
for samp in samples:
    I.append(samp & 0x0000FFFF)
    Q.append((samp & 0xFFFF0000) >> 16)

n = np.arange(0, len(samples))
plt.plot(n[1000:1300], I[1000:1300], n[1000:1300], Q[1000:1300])
plt.savefig('fifo_data.png')
