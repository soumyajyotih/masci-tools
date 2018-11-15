#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 17:00:10 2018

SiScLab 2018 Project 8
Task 1: Plot band structure from Fleur HDF5 files.

- TODO for Week01:
 - Model (ie, what the code is doing):
   - Fermi energy for offset: y scale 
   - y-axis scaling: convert to Hartree
   - OPTIONAL: weights: look into Stefan's code
   - don't do TOO much in Week001
 - Code Cleanup:
   - refactoring (classes, naming, minimal doc)
 - Modularize:
   - perhaps: make installable as python package / module
 - Ideas for later:
   - plot 3D path for kspace

@author: christianpartmann
"""

import numpy as np
from matplotlib import pyplot as plt
import h5py

filename = 'banddos_Co.hdf'
f = h5py.File(filename, 'r')

Eigenvalues = f["/eigenvalues/eigenvalues"]
kpts = f["/kpts/coordinates"]
special_points = f["/kpts/specialPointIndices"]
fermi_energy = f["/general"]
weights = f["/kpts/weights"]
atoms_coords = f["/atoms/positions"]
atom_group = f["/atoms/equivAtomsGroup"]


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
# Plot the values
for i in range(len(atoms_coords[:].T[0])):
    ax.scatter(atoms_coords[:].T[0][i], atoms_coords[:].T[1][i], atoms_coords[:].T[2][i], c="blue")

def E_i(i):
    return Eigenvalues[0].T[i]

#E0 = Eigenvalues[0].T[0]
kx = kpts[:].T[0]
ky = kpts[:].T[1]
kz = kpts[:].T[2]
k_dist = np.zeros(len(kx))

k_dist[0] = 0 #np.sqrt((kx[1]-kx[0])**2 +(kx[1]-kx[0])**2 + (kx[1]-kx[0])**2

for i in range(1, len(kx)):
    k_dist[i] = k_dist[i-1] + np.sqrt((kx[i]-kx[i-1])**2 +(ky[i]-ky[i-1])**2 +(kz[i]-kz[i-1])**2)

plt.figure()
Number_Bands = Eigenvalues.shape[2]

for i in range(Number_Bands):
    plt.plot(k_dist, E_i(i), ".", ms = 1)

for i in range(len(special_points)):
    index = special_points[i]
    plt.vlines(k_dist[index-1], -0.25, 0.4)
#plt.ylim(-1.85, -1.82)

plt.savefig("bandstruckture.png", dpi=2000)

