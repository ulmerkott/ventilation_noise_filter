import bpy
import bmesh

from mathutils import Vector
from bmesh.types import BMVert
import numpy as np
from math import *

# This plugin adds a mesh object which is created based on research article
# "Broadband Acoustic Ventilation Barriers". The purpose is to cancel out
# audible noise in ventilation channels.
# https://www.researchgate.net/publication/340573606_Broadband_Acoustic_Ventilation_Barriers

# Constants
SCALE = 0.001 # mm
D = 100.0
d = 45.0
h = 25.0
L = 17.3
w = 2.1
a = 8.7
s0 = 1.0
s1 = 2.2
s2 = 3.2
p = -2.4

steps = 64
r_step = abs(d/2 - D/2) / steps

# Start values
r = d/2
r2 = D/2
verts = []
faces = []

# Horn-like helix layer1
s_step = abs(s1 - s2) / steps
s = s2
cur_vert = 0
for i in range(steps):
    verts.append((
        (r * sin(-w * s - p)),
        (r * cos(-w * s - p)),
        -(e ** s)))
    verts.append((
        (r2 * sin(-w * s - p)),
        (r2 * cos(-w * s - p)),
        -(e ** s)))
    cur_vert = len(verts)-1
    if cur_vert >= 3:
        faces.append((cur_vert-3, cur_vert-2, cur_vert, cur_vert-1))

    # print(f"Vert added: {verts[i]}, s={s}")
    s -= s_step


# Middle fix-pitch helix layer
s = -s0
s_step = abs(-s0 - s0) / steps
for i in range(steps, steps*2):
    verts.append((
        (r * sin(w * s)),
        (r * cos(w * s)),
        (a * s)))
    verts.append((
        (r2 * sin(w * s)),
        (r2 * cos(w * s)),
        (a * s)))
    cur_vert = len(verts)-1
    if cur_vert >= 3:
        faces.append((cur_vert-3, cur_vert-2, cur_vert, cur_vert-1))

    s += s_step

# Horn-like helix layer2
s_step = abs(s1 - s2) / steps
s = s1
for i in range(steps*2, steps*3):
    verts.append((
        (r * sin(w * s + p)),
        (r * cos(w * s + p)),
        (e ** s)))
    verts.append((
        (r2 * sin(w * s + p)),
        (r2 * cos(w * s + p)),
        (e ** s)))
    cur_vert = len(verts)-1
    if cur_vert >= 3:
        faces.append((cur_vert-3, cur_vert-2, cur_vert, cur_vert-1))
    # print(f"Vert added: {verts[i]}, s={s}")
    s += s_step

mesh = bpy.data.meshes.new("NoiseFilterSpiral")  # add a new mesh
obj = bpy.data.objects.new(mesh.name, mesh)  # add a new object using the mesh

scene = bpy.context.scene
scene.collection.objects.link(obj)

bpy.context.view_layer.objects.active = obj

mesh.from_pydata(verts, [], faces)

obj.select_set(True)
bpy.ops.transform.resize(value=(SCALE, SCALE, SCALE))
