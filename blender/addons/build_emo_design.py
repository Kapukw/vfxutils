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
    "name": "Build EMO Design",
    "author": "Igor Frolov",
    "version": (0, 1),
    "blender": (2, 78, 0),
    "location": "Properties > Scene > Convert to Parts PBS",
    "description": "Build EMO Design",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts",
    "tracker_url": "",
    "category": "Targem"}

import bpy

import os
import xml.etree.ElementTree as ET

def toBlenderRot(quat):
    pass

class EmoPart(object):
    def __init__(self, xmlNode):
        filepath = os.path.normcase('Y:\\art\\source\\' + xmlNode.get('model') + '.dae')
        filename, ext = os.path.splitext(os.path.basename(filepath))

        self.exists = True
        if not os.path.exists(filepath):
            #cmds.warning("File '" + filepath + "' not exists.")
            self.exists = False

        self.filepath = filepath
        self.name = filename

        pos = (xmlNode.get('pos') if xmlNode.get('pos') else xmlNode.get('weld_pos')).split()
        self.pos = (float(pos[0]), float(pos[1]), -float(pos[2]))

        quat = (xmlNode.get('weld_rot')).split() if xmlNode.get("weld_rot") else (0, 0, 0, 1)
        self.rot = toBlenderRot(quat)

    def loadFromFile(self):
        bpy.ops.wm.collada_import(filepath=self.filepath)

def buildFromXmlFunc():

    # set render to cycles
    bpy.context.scene.render.engine = 'CYCLES'

    # get filepath
    filepath = "Y:\\art\\source\\_car_designs\\cbt2\\cbt2.xml"

    tree = ET.parse(filepath)
    root = tree.getroot()
    
    parts = []

    xmlChassis = root.find('Chassis')
    parts.append(EmoPart(xmlChassis))

    xmlParts = chassis.findall('Part')
    for xmlPart in xmlParts:
        parts.append(EmoPart(xmlPart))

    counter = 0

    for part in parts:
        if not part.exists:
            continue

        counter += 1
        #maya_part.group_name = "part_" + maya_part.name + "_" + str(counter)
        #cmds.file(maya_part.filepath, r=True, type="mayaAscii", gr=True, gn=maya_part.group_name, mergeNamespacesOnClash=False, namespace=maya_part.name, options="v=0;")

    for part in parts:
        if not part.exists:
            continue
        #cmds.xform(maya_part.group_name, pivots=(0.0, 0.0, 0.0), a=True, ws=True)
        #cmds.setAttr(maya_part.group_name + ".translate", maya_part.pos[0], maya_part.pos[1], maya_part.pos[2], type="double3")
        #cmds.setAttr(maya_part.group_name + ".rotate", maya_part.rot[0], maya_part.rot[1], maya_part.rot[2], type="double3")

class build_from_xml(bpy.types.Operator):
    bl_idname = "emo_design.build_from_xml"
    bl_label = "Build EMO Design from XML"
    bl_description = "Build EMO Design from XML"
    bl_register = True
    bl_undo = True

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        buildFromXmlFunc()
        return {'FINISHED'}

from bpy.props import *

class OBJECT_PT_scenemassive(bpy.types.Panel):
    bl_label = "Build EMO Design"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        sc = context.scene
        layout = self.layout
        row = layout.row()
        box = row.box()
        box.operator("emo_design.build_from_xml", text="Build EMO Design")

def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()
