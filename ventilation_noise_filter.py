import bpy
import bmesh

from mathutils import Vector
from bmesh.types import BMVert
import numpy as np
from math import *

bpy.ops.object.select_all(action='DESELECT')

# This plugin adds a mesh object which is created based on research paper
# "Broadband Acoustic Ventilation Barriers". The purpose is to cancel out
# audible noise in ventilation channels for a specific frequency range.
# https://www.researchgate.net/publication/340573606_Broadband_Acoustic_Ventilation_Barriers

# Constants
STEPS = 128 # Correlates to the number of verices (ie detail level)
SCALE = 0.001 # mm
THICKNESS = 1 # mm
D = 100
d = 45.0
h = 25.0
w = 2.1
a = 8.7
s0 = 1.0
s1 = 2.2
s2 = 3.2
p = -2.4
r = d/2
r2 = D/2

# Helix consists of two horn-like helices and one fixed-pitch helix
HONE_HELIX_LEN = abs(s1 - s2)
FIXED_HELIX_LEN = abs(-s0 - s0)
TOT_HELIX_LEN = HONE_HELIX_LEN * 2 + FIXED_HELIX_LEN

# Z-values for helix part endpoints
HORN_HELIX_TOP = -(e ** s1)
FIXED_HELIX_TOP = a*(s0)
HORN_HELIX2_TOP = (e ** s2)

verts = []
faces = []

z = 0
s_bottom = s2   # Buttom helix start value
s_middle = -s0  # Middle helix start value
s_top = s1      # Top helix start value
s_step = TOT_HELIX_LEN / STEPS
for step in range(STEPS+3):
    # Create bottom horn-like helix
    if (z := -(e ** s_bottom)) <= HORN_HELIX_TOP:
        print(f"First helix with z = {z} step={step}")
        x = (r * sin(-w * s_bottom - p))
        y = (r * cos(-w * s_bottom - p))
        x2 = (r2 * sin(-w * s_bottom - p))
        y2 = (r2 * cos(-w * s_bottom - p))
        s_bottom -= s_step
    # Create middle fixed-pitch helix
    elif (z := (a * s_middle)) <= FIXED_HELIX_TOP:
        print(f"Second helix with z = {z} step={step}")
        x = (r * sin(w * s_middle))
        y = (r * cos(w * s_middle))
        x2 = (r2 * sin(w * s_middle))
        y2 = (r2 * cos(w * s_middle))
        s_middle += s_step
    # Create top horn-like helix
    elif z <= HORN_HELIX2_TOP:
        print(f"Last helix with z = {z} step={step}")
        x = (r * sin(w * s_top + p))
        y = (r * cos(w * s_top + p))
        x2 = (r2 * sin(w * s_top + p))
        y2 = (r2 * cos(w * s_top + p))
        z = (e ** s_top)
        s_top += s_step

    # Add vertices for inner and outer part of helix
    verts.append((x,y,z))
    verts.append((x2,y2,z))
    cur_vert = len(verts)-1
    if cur_vert >= 3:
        faces.append((cur_vert-3, cur_vert-2, cur_vert, cur_vert-1)) 

mesh = bpy.data.meshes.new("NoiseFilterSpiral")  # add a new mesh
obj = bpy.data.objects.new(mesh.name, mesh)  # add a new object using the mesh

scene = bpy.context.scene
scene.collection.objects.link(obj)

bpy.context.view_layer.objects.active = obj

mesh.from_pydata(verts, [], faces)

# Apply scale
obj.select_set(True)
bpy.ops.transform.resize(value=(SCALE, SCALE, SCALE))
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Add duplicated spiral rotated 180degrees
bpy.ops.object.duplicate_move()
bpy.ops.transform.rotate(value=3.14159, orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True))

# Join the two spirals
bpy.data.objects[obj.name].select_set(True)
bpy.ops.object.join()
obj_name = bpy.context.selected_objects[0].name

# Add outer cylinder
bpy.ops.mesh.primitive_cylinder_add(vertices=STEPS, end_fill_type='NOTHING', radius=D/2*SCALE, depth=2*h*SCALE, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

bpy.data.objects[obj_name].select_set(True)
bpy.ops.object.join()
obj_name = bpy.context.selected_objects[0].name

# Add inner cylinder
bpy.ops.mesh.primitive_cylinder_add(vertices=STEPS, end_fill_type='NOTHING', radius=d/2*SCALE, depth=2*h*SCALE, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
bpy.data.objects[obj_name].select_set(True)
bpy.ops.object.join()

# Set thickness for spiral
bpy.ops.object.modifier_add(type='SOLIDIFY')
bpy.context.object.modifiers["Solidify"].thickness = THICKNESS / 1000
bpy.context.object.modifiers["Solidify"].offset = 0

bpy.context.object.name = "Noise_filter"
