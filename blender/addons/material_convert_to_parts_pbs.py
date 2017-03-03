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
    "version": (1, 0),
    "blender": (2, 78, 0),
    "location": "Properties > Material > Convert to Parts PBS",
    "description": "Convert scene materials to Cycles Parts PBS shader",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts",
    "tracker_url": "",
    "category": "Targem"}

import os
import bpy

def do_convert():

    if 'Parts PBS' not in bpy.data.node_groups:
        return

    mats = bpy.data.materials
    for mat in mats:

        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # remove old nodes
        for n in nodes:
            nodes.remove(n)

        pbs_shader = nodes.new('ShaderNodeGroup')
        pbs_shader.node_tree = bpy.data.node_groups['Parts PBS']
        pbs_shader.location = 0, 0
    
        pbs_output = nodes.new('ShaderNodeOutputMaterial')
        pbs_output.location = 200, 0

        links.new(pbs_shader.outputs[0], pbs_output.inputs[0])

        for tex in mat.texture_slots:
            if tex and tex.texture.type == 'IMAGE':
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.location = -200, 260
                tex_node.image = tex.texture.image
                tex_filepath = tex.texture.image.filepath
                base, ext = os.path.splitext(tex_filepath)

                if base.endswith('_a'):
                    tex_node.color_space = 'COLOR'
                    tex_node.location = -200, -50
                    links.new(tex_node.outputs[0], pbs_shader.inputs["AlbedoM Tex"])

                elif base.endswith('_n'):
                    tex_node.color_space = 'NONE'
                    tex_node.location = -360, -70
                    links.new(tex_node.outputs[0], pbs_shader.inputs["Normal Tex"])

                elif base.endswith('_g'):
                    tex_node.color_space = 'NONE'
                    tex_node.location = -520, -90
                    links.new(tex_node.outputs[0], pbs_shader.inputs["Gloss Tex"])

                elif base.endswith('_m'):
                    tex_node.color_space = 'NONE'
                    tex_node.location = -680, -110
                    links.new(tex_node.outputs[0], pbs_shader.inputs["Metalness Tex"])

                elif base.endswith('_ao'):
                    tex_node.color_space = 'COLOR'
                    tex_node.location = -840, -130
                    links.new(tex_node.outputs[0], pbs_shader.inputs["Baked AO Tex"])

                # try load blend mask, assuming that all masks stored in same folder
                if base.endswith('_a'):
                    blendtex_image = None
                    blendtex_filepath = base[:-2] + "_b.png"
                    if blendtex_image is None and os.path.exists(bpy.path.abspath(blendtex_filepath)):
                        blendtex_image = bpy.data.images.load(blendtex_filepath, check_existing=True)
                    blendtex_filepath = base[:-2] + "_b.tif"
                    if blendtex_image is None and os.path.exists(bpy.path.abspath(blendtex_filepath)):
                        blendtex_image = bpy.data.images.load(blendtex_filepath, check_existing=True)
                    if blendtex_image is not None:
                        blendtex_node = nodes.new('ShaderNodeTexImage')
                        blendtex_node.image = blendtex_image
                        blendtex_node.color_space = 'NONE'
                        blendtex_node.location = -1000, -150

    bpy.context.scene.render.engine = 'CYCLES'

class emo_convert_to_parts_pbs(bpy.types.Operator):
    bl_idname = "emo.convert_to_parts_pbs"
    bl_label = "Convert All Materials to Parts PBS"
    bl_description = "Convert all materials in the scene to Cycles Parts PBS"
    bl_register = True
    bl_undo = True

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        do_convert()
        return {'FINISHED'}

from bpy.props import *

class OBJECT_PT_scenemassive(bpy.types.Panel):
    bl_label = "Convert All Materials to Parts PBS"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        row = layout.row()
        box = row.box()
        box.operator("emo.convert_to_parts_pbs", text="Convert All Materials to Parts PBS")

def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()
