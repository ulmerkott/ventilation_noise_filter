import bpy
import bmesh

from mathutils import Vector
from bmesh.types import BMVert
import numpy as np
from math import *
import mathutils

bpy.ops.object.select_all(action='DESELECT')

# This plugin adds a mesh object which is created based on research paper
# "Ultra-broadband acoustic ventilation barriers via hybrid-functional metasurfaces".
# The purpose is to cancel out audible noise in ventilation channels for a broad frequency range.
# https://www.researchgate.net/publication/349414533_Ultrabroadband_Acoustic_Ventilation_Barriers_via_Hybrid-Functional_Metasurfaces

# Constants
STEPS = 256 # Correlates to the number of verices (ie detail level)
SCALE = 0.001 # mm
THICKNESS = 1 # mm
LAYERS = 8
PARTITION_BLADES = 3

D = 100 - THICKNESS*2 # mm, remove thickness from diameter since we use offset=1 for solidify modifier
d = 44 # mm
b = THICKNESS # mm
h = 5.5 + b # mm, add b since thickness is included in the height
H = 53 # mm
v = 120 # degrees
t = 8 # degrees
Sn = 42.3 # mm2

mesh = bpy.data.meshes.new("NoiseFilter")  # add a new mesh
bm = bmesh.new()

for layer in range(LAYERS):
    z = -layer*h*SCALE

    # Create outer and inner circles and bridge them
    circle_outer = bmesh.ops.create_circle(bm,
        cap_ends=False,
        radius=D/2*SCALE,
        segments=STEPS)['verts']
    circle_outer_edges = [e for e in bm.edges if e.verts[0] in circle_outer]
    circle_inner = bmesh.ops.create_circle(bm,
        cap_ends=False,
        radius=d/2*SCALE,
        segments=STEPS)['verts']
    circle_inner_edges = [e for e in bm.edges if e.verts[0] in circle_inner]

    circle_faces = bmesh.ops.bridge_loops(bm, edges=circle_inner_edges+circle_outer_edges)
    bmesh.ops.translate(bm, verts=circle_inner+circle_outer, vec=(0,0,z))

    # Extrude outer circle
    extruded_geom = bmesh.ops.extrude_edge_only(bm, edges=circle_outer_edges)['geom']
    extruded_verts = [v for v in extruded_geom if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(
        bm,
        verts=extruded_verts,
        vec=(0.0, 0.0, h*SCALE))

    # Create blade for the opening
    blade_op = [
        bm.verts.new((d/2*SCALE, 0, z)),
        bm.verts.new((D/2*SCALE, 0, z)),
        bm.verts.new((D/2*SCALE, 0, z + h*SCALE)),
        bm.verts.new((d/2*SCALE, 0, z + h*SCALE))]
    bm.faces.new(blade_op)

    # Create blade and rotate on z axis by offset
    blade = [
        bm.verts.new((d/2*SCALE, 0, z)),
        bm.verts.new((D/2*SCALE, 0, z)),
        bm.verts.new((D/2*SCALE, 0, z + h*SCALE)),
        bm.verts.new((d/2*SCALE, 0, z + h*SCALE))]
    bm.faces.new(blade)
    bmesh.ops.rotate(bm,
        verts=blade,
        cent=(0,0,0),
        matrix=mathutils.Matrix.Rotation(radians(v+t*layer), 3, 'Z'))

# Opening and inner cylinder
opening_area_radians = Sn / ((d/2)*(h-b))
inner_cylinder_e = bm.edges.new(
    [bm.verts.new((d/2*SCALE, 0, h*SCALE)),
     bm.verts.new((d/2*SCALE, 0, (-H+h)*SCALE))])
bmesh.ops.rotate(bm,
    verts=inner_cylinder_e.verts,
    cent=(0,0,0),
    matrix=mathutils.Matrix.Rotation(opening_area_radians, 3, 'Z'))

# Spin edge to create a cylinder with an opening
ret = bmesh.ops.spin(bm,
    geom=list(inner_cylinder_e.verts) + [inner_cylinder_e],
    angle=radians(360)-opening_area_radians*2,
    steps=STEPS,
    axis=(0,0,1),
    cent=(0,0,0))


# Additional cirumferential partition blades
partition_offset = ((D/2-d/2)*SCALE) / (PARTITION_BLADES+1)
for partition in range(1, PARTITION_BLADES+1):
    x_offset = partition_offset * partition
    radie = d/2*SCALE + x_offset
    opening_area_radians = Sn / (radie*1000*(h-b))
    partition_cylinder_e = bm.edges.new(
        [bm.verts.new((radie, 0, h*SCALE)),
         bm.verts.new((radie, 0, (-H+h)*SCALE))])
    bmesh.ops.rotate(bm,
        verts=partition_cylinder_e.verts,
        cent=(0,0,0),
        matrix=mathutils.Matrix.Rotation(opening_area_radians, 3, 'Z'))

    # Spin edge to create a cylinder with an opening
    ret = bmesh.ops.spin(bm,
        geom=list(partition_cylinder_e.verts) + [partition_cylinder_e],
        angle=radians(360)-opening_area_radians*2,
        steps=STEPS,
        axis=(0,0,1),
        cent=(0,0,0))


bm.to_mesh(mesh)

bpy.ops.object.select_all(action='DESELECT')


# Add the mesh to the scene
obj = bpy.data.objects.new(mesh.name, mesh)  # add a new object using the mesh

bpy.context.collection.objects.link(obj)

bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# Set thickness
bpy.ops.object.modifier_add(type='SOLIDIFY')
bpy.context.object.modifiers["Solidify"].thickness = THICKNESS / 1000
bpy.context.object.modifiers["Solidify"].offset = 1
bpy.context.object.modifiers["Solidify"].use_even_offset = True


#bpy.context.object.name = "NoiseFilter"
