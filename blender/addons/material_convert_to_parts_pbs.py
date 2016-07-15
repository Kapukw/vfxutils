# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


bl_info = {
    "name": "Convert to Parts PBS",
    "author": "Igor Frolov",
    "version": (0, 1),
    "blender": (2, 76, 0),
    "location": "Properties > Material > Convert to Parts PBS",
    "description": "Convert non-nodes materials to Cycles Parts PBS shader",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts",
    "tracker_url": "",
    "category": "Kapukw"}

import bpy

def AutoNode():

    mats = bpy.data.materials
    for cmat in mats:
        cmat.use_nodes = True
        TreeNodes = cmat.node_tree
        links = TreeNodes.links

        # Convert this material from non-nodes to Cycles nodes
        sT = False
            
        for n in TreeNodes.nodes:
            TreeNodes.nodes.remove(n)

        # Starting point is diffuse BSDF and output material
        shader = TreeNodes.nodes.new('ShaderNodeBsdfDiffuse')
        shader.location = 0, 470
        shout = TreeNodes.nodes.new('ShaderNodeOutputMaterial')
        shout.location = 200, 400
        links.new(shader.outputs[0], shout.inputs[0])

        shader.inputs['Color'].default_value = cmat.diffuse_color.r, cmat.diffuse_color.g, cmat.diffuse_color.b, 1

        if shader.type == 'ShaderNodeBsdfDiffuse':
            shader.inputs['Roughness'].default_value = cmat.specular_intensity

        for tex in cmat.texture_slots:
            sT = False
            if tex:
                if tex.use:
                    if tex.texture.type == 'IMAGE':
                        img = tex.texture.image
                        shtext = TreeNodes.nodes.new('ShaderNodeTexImage')
                        shtext.location = -200, 400
                        shtext.image = img
                        sT = True

            if sT:
                if tex.use_map_color_diffuse :
                    links.new(shtext.outputs[0], shader.inputs[0])

                if tex.use_map_normal:
                    t = TreeNodes.nodes.new('ShaderNodeRGBToBW')
                    t.location = -0, 300
                    links.new(t.outputs[0], shout.inputs[2])
                    links.new(shtext.outputs[0], t.inputs[0])

    bpy.context.scene.render.engine = 'CYCLES'

class mlrefresh_parts_pbs(bpy.types.Operator):
    bl_idname = "ml.refresh_parts_pbs"
    bl_label = "Convert All Materials to Parts PBS"
    bl_description = "Convert all materials in the scene to Cycles Parts PBS"
    bl_register = True
    bl_undo = True

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        AutoNode()
        #bpy.ops.object.editmode_toggle()
        #bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
        #bpy.ops.object.editmode_toggle()

        return {'FINISHED'}

from bpy.props import *

class OBJECT_PT_scenemassive(bpy.types.Panel):
    bl_label = "Convert BI Materials to Parts PBS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        row = layout.row()
        box = row.box()
        box.operator("ml.refresh_parts_pbs", text="Convert All Materials to Parts PBS", icon="MATERIAL")

def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()
