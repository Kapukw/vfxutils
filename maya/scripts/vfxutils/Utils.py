import os
import sys
import shutil
import glob
import maya.cmds as cmds

def get_colladafx_materials():
    return cmds.ls(type="colladafxShader")

def get_dx11_materials():
    return cmds.ls(type="dx11Shader")

def get_meshes():
    transforms = cmds.ls(long=True, tr=True)
    if transforms == []: return []

    # selectionMask=12, where 12 means 'Polygon'
    # cmds.filterExpand() -> None, list
    meshes = cmds.filterExpand(transforms, fullPath=True, selectionMask=12)
    if meshes == None: return []
    return meshes

def get_selected_meshes():
    sel = cmds.ls(sl=True, long=True, tr=True)
    if sel == []: return []

    # selectionMask=12, where 12 means 'Polygon'
    # cmds.filterExpand() -> None, list
    meshes = cmds.filterExpand(sel, fullPath=True, selectionMask=12)
    if meshes == None: return []
    return meshes

def get_selected_mesh_transforms():
    sel = cmds.ls(sl=True, long=True, tr=True)
    if sel == []: return []

    # selectionMask=12, where 12 means 'Polygon'
    # cmds.filterExpand() -> None, list
    meshes = cmds.filterExpand(sel, fullPath=True, selectionMask=12)
    if meshes == None: return []

    # cmds.listRelatives() -> None, list
    transforms = cmds.listRelatives(meshes, p=True, path=True)
    if transforms == None: return []
    return transforms

def get_selected_joints():
    return cmds.ls(sl=True, long=True, type="joint")

def get_meshes_polygons(meshes):
    cmds.select(cl=True)
    for mesh in meshes:
        cmds.select(mesh + ".f[:]", add=True)
    return set(cmds.ls(sl=True, long=True))

def get_meshes_materials(meshes):
    mats = set()
    for mesh in meshes:
        shading_groups = cmds.listConnections(mesh, type="shadingEngine")
        for shading_group in shading_groups:
            shader = cmds.listConnections(shading_group + ".surfaceShader")[0]
            mats.add(shader)
    return mats

def get_material_polygons(shader):
    cmds.hyperShade(objects=shader)
    shapes = cmds.ls(sl=True, long=True, type="geometryShape")
    if shapes != []:
        cmds.select(shapes, deselect=True)
        for shape in shapes:
            cmds.select(shape + ".f[:]", add=True)
    return set(cmds.ls(sl=True, long=True))

def get_objects_linked_to_attr(node, attr):
    if not cmds.attributeQuery(attr, node=node, exists=True):
        return []

    objects = []
    plugs = cmds.connectionInfo(node + "." + attr, destinationFromSource=True)

    for plug in plugs:
        obj = plug[:-len("." + attr)]
        objects.append(obj)

    return objects

def replace_materials_with_lambert():
    meshes = get_selected_meshes()
    polygons = get_meshes_polygons(meshes)
    materials = get_meshes_materials(meshes)

    for mat in materials:
        mat_polys = get_material_polygons(mat)
        dst_polys = list(mat_polys.intersection(polygons))

        color_tex = cmds.connectionInfo(mat + ".DiffuseSampler", sourceFromDestination=True)
        lambert = cmds.shadingNode("lambert", asShader=True)
        lambertSG = cmds.sets(name=lambert + "SG", renderable=True, noSurfaceShader=True, empty=True)
        cmds.connectAttr(lambert + ".outColor", lambertSG + ".surfaceShader")
        cmds.connectAttr(color_tex, lambert + ".color")

        if dst_polys != []:
            cmds.select(dst_polys)
            cmds.hyperShade(assign=lambert)

def set_string_array_attr(node, attr, value):
    cmds.setAttr(node + "." + attr, type="stringArray", *([len(value)] + value))

def compare_colladafx(obj1, obj2):
    if not obj1 or not obj2: return False

    vertProgram1 = cmds.getAttr(obj1 + ".vertexProgram")
    vertProgram2 = cmds.getAttr(obj2 + ".vertexProgram")
    fragProgram1 = cmds.getAttr(obj1 + ".fragmentProgram")
    fragProgram2 = cmds.getAttr(obj2 + ".fragmentProgram")
    if vertProgram1 != vertProgram2 or fragProgram1 != fragProgram2: return False

    textureList = cmds.listAttr(obj1, st="*Sampler")
    for each in textureList:
        texture1 = cmds.listConnections(obj1 + "." + each, t="file")
        texture2 = cmds.listConnections(obj2 + "." + each, t="file")
        if texture1 is None or texture2 is None:
            if texture1 != texture2: return False
        elif texture1[0] != texture2[0]: return False

    if cmds.getAttr(obj1 + ".COLOR0"   ) != cmds.getAttr(obj2 + ".COLOR0"   ): return False
    if cmds.getAttr(obj1 + ".TEXCOORD0") != cmds.getAttr(obj2 + ".TEXCOORD0"): return False
    if cmds.getAttr(obj1 + ".TEXCOORD1") != cmds.getAttr(obj2 + ".TEXCOORD1"): return False
    if cmds.getAttr(obj1 + ".TEXCOORD2") != cmds.getAttr(obj2 + ".TEXCOORD2"): return False
    if cmds.getAttr(obj1 + ".TEXCOORD3") != cmds.getAttr(obj2 + ".TEXCOORD3"): return False
    if cmds.getAttr(obj1 + ".TEXCOORD4") != cmds.getAttr(obj2 + ".TEXCOORD4"): return False
    if cmds.getAttr(obj1 + ".TEXCOORD5") != cmds.getAttr(obj2 + ".TEXCOORD5"): return False
    if cmds.getAttr(obj1 + ".TEXCOORD6") != cmds.getAttr(obj2 + ".TEXCOORD6"): return False
    if cmds.getAttr(obj1 + ".TEXCOORD7") != cmds.getAttr(obj2 + ".TEXCOORD7"): return False

    return True

def compare_dx11(obj1, obj2):
    if not obj1 or not obj2: return False

    if cmds.getAttr(obj1 + ".shader") != cmds.getAttr(obj2 + ".shader"): return False

    if cmds.attributeQuery("use_skins", node=obj1, exists=True): return False
    if cmds.attributeQuery("use_skins", node=obj2, exists=True): return False

    textureList = cmds.listAttr(obj1, st="*Sampler")
    for each in textureList:
        texture1 = cmds.listConnections(obj1 + "." + each, t="file")
        texture2 = cmds.listConnections(obj2 + "." + each, t="file")
        if texture1 == None or texture2 == None:
            if texture1 != texture2: return False
        elif texture1[0] != texture2[0]: return False

    attrs = cmds.listAttr(obj1, userDefined=True, settable=True, scalarAndArray=True)
    for attr in attrs:
        if cmds.getAttr(obj1 + "." + attr) != cmds.getAttr(obj2 + "." + attr): return False

    return True

def remove_texture_duplicates():
    textures = cmds.ls(tex=True)
    file2Node = dict()
    node2Node = list()
    needDelete = list()

    for texture in textures:
        tex_file = cmds.getAttr(texture + ".fileTextureName")
        if tex_file == "":
            continue

        plc2dTex = cmds.listConnections(texture, d=False)
        if plc2dTex != None and cmds.listConnections(plc2dTex[0], d=False) != None:
            continue

        otherTexture = file2Node.get(tex_file, None)
        if otherTexture == None:
            file2Node[tex_file] = texture
        else:
            node2Node.append(texture)
            node2Node.append(otherTexture)
            needDelete.append(texture)

            dsts = cmds.connectionInfo(texture + ".outColor", destinationFromSource=True)
            for dst in dsts:
                cmds.connectAttr(otherTexture + ".outColor", dst, force=True)

    for each in needDelete:
        parents = cmds.listConnections(each, t="place2dTexture")
        cmds.delete(each)
        if parents != None:
            cmds.delete(parents)

    sys.stdout.write(str(len(needDelete)) + " textures removed.\n")

def remove_material_duplicates(mats, compare_func):
    node2Node = list()
    needDelete = list()

    for i in xrange(0, len(mats)):
        for j in xrange(0, i):
            if compare_func(mats[i], mats[j]):
                node2Node.append(mats[i])
                node2Node.append(mats[j])
                needDelete.append(mats[i])

                cmds.hyperShade(objects=mats[i])
                sel = cmds.ls(sl=True)
                if sel != None and sel != []:
                    cmds.hyperShade(assign=mats[j])
                break

    for each in needDelete:
        listSG = cmds.listConnections(each, type="shadingEngine")
        cmds.delete(each)
        if listSG != None:
            for sg in listSG:
                if cmds.listConnections(sg, d=False) != None:
                    cmds.delete(sg)

    return len(needDelete)

def remove_colladafx_material_duplicates():
    mats = get_colladafx_materials()
    n = remove_material_duplicates(mats, compare_colladafx)
    sys.stdout.write(str(n) + " colladafx materials removed.\n")

def remove_dx11_material_duplicates():
    mats = get_dx11_materials()
    n = remove_material_duplicates(mats, compare_dx11)
    sys.stdout.write(str(n) + " dx11 materials removed.\n")

def name_textures_by_filenames():
    file_nodes = cmds.ls(type="file")
    for file_node in file_nodes:
        filepath = os.path.normcase(cmds.getAttr(file_node + ".fileTextureName"))
        filename, ext = os.path.splitext(os.path.basename(filepath))
        cmds.rename(file_node, filename)

def create_tex_by_filepath(filepath):

    filepath = os.path.normcase(filepath)

    file_nodes = cmds.ls(type="file")
    for file_node in file_nodes:
        if filepath == os.path.normcase(cmds.getAttr(file_node + ".fileTextureName")):
            return file_node

    if not os.path.exists(filepath):
        cmds.warning("File '" + filepath + "' is not exists.")
        return None

    filename, ext = os.path.splitext(os.path.basename(filepath))
    file_node = cmds.shadingNode("file", asTexture=True, name=filename)
    cmds.setAttr(file_node + ".fileTextureName", filepath, type="string")

    return file_node

def safe_connect_tex(mat, attr, tex):
    if mat is None or tex is None: return
    if cmds.objExists(mat) and cmds.objExists(tex):
        if cmds.attributeQuery(attr, node=mat, exists=True):
            if tex + ".outColor" != cmds.connectionInfo(mat + "." + attr, sourceFromDestination=True):
                cmds.connectAttr(tex + ".outColor", mat + "." + attr, force=True)

g_texBindMap = {"_a"  : "DiffuseSampler",
                "_n"  : "NormalSampler",
                "_g"  : "SpecularColorSampler",
                "_m"  : "MetalnessSampler",
                "_ao" : "OcclusionSampler"}

def get_tex_base_and_suffix(filepath):
    filename, ext = os.path.splitext(os.path.basename(filepath))
    for k in g_texBindMap.iterkeys():
        if filename.endswith(k):
            return (filename[:-len(k)], k)
    return None

def create_mats_from_folder(folder_path):
    fx_file = "y:\\evil-shaders\\object_norm.fx"

    folder_path = os.path.join(folder_path, "")
    files = glob.glob(folder_path + "*.*")

    mat_maps = dict()
    for f in files:
        pair = get_tex_base_and_suffix(f)
        if pair is None:
            continue

        maps = mat_maps.get(pair[0], [])
        maps.append((pair[1], f))
        mat_maps[pair[0]] = maps

    for mat_name, masks in mat_maps.iteritems():
        mat = cmds.shadingNode('dx11Shader', asShader=True, name=mat_name)
        mat_sg = cmds.sets(name=mat + "SG", renderable=True, noSurfaceShader=True, empty=True)
        cmds.setAttr(mat + ".shader", fx_file, type="string")
        cmds.connectAttr(mat + ".outColor", mat_sg + ".surfaceShader", force=True)

        for suffix, f in masks:
            safe_connect_tex(mat, g_texBindMap[suffix], create_tex_by_filepath(f))


def maya_print(s):
    if not s.endswith("\n"):
        s += "\n"
    sys.stdout.write(s)

def set_attr_if_new(attr, value):
    if value != cmds.getAttr(attr):
        cmds.setAttr(attr, value)