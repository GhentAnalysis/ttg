#!/usr/bin/env python

import numpy as np

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.ticker import MaxNLocator

dp = np.random.poisson(12.5, 1000)
print dp

fig = plt.figure(figsize=(6, 6))
plt.hist(dp, bins=20)
fig.savefig('stat.pdf')
