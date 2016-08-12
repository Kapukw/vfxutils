import os
import sys
import glob
import subprocess
import maya.cmds as cmds
import maya.mel as mel

import Utils

g_jobsPool = list()

def register_jobs():
    global g_jobsPool
    #g_jobsPool.append(cmds.scriptJob(event=["SceneOpened", "import maya.cmds as cmds\ncmds.evalDeferred(\"SceneTweaks.remove_unknown_nodes()\")"],  protected=True))
    sys.stdout.write("SceneTweaks: {} jobs registered\n".format(len(g_jobsPool)))

def unregister_jobs():
    global g_jobsPool
    for jobNum in g_jobsPool:
        cmds.scriptJob(kill=jobNum, force=True)
    sys.stdout.write("SceneTweaks: {} jobs unregistered\n".format(len(g_jobsPool)))
    g_jobsPool = list()

def remove_unknown_nodes():
    removed_count = 0

    unknown_nodes = cmds.ls(type="unknown")
    for node in unknown_nodes:
        if cmds.objExists(node):
            sys.stdout.write("Remove unknown node '{}'.\n".format(node))
            cmds.lockNode(node, lock=False)
            cmds.delete(node)
            removed_count += 1

    if cmds.pluginInfo("Turtle.mll", q=True, loaded=True):
        cmds.pluginInfo("Turtle.mll", e=True, autoload=False)
        cmds.unloadPlugin("Turtle.mll", force=True)
    turtle_nodes = ["TurtleDefaultBakeLayer",
                    "TurtleBakeLayerManager",
                    "TurtleRenderOptions",
                    "TurtleUIOptions"]
    for node in turtle_nodes:
        if cmds.objExists(node):
            sys.stdout.write("Remove Turtle node '{}'.\n".format(node))
            cmds.lockNode(node, lock=False)
            cmds.delete(node)
            removed_count += 1

    sys.stdout.write(str(removed_count) + " unknown nodes removed.\n")

def set_nm_rig_direction():
    mult = 1
    if cmds.checkBox(g_invertLightsDirection_checkBox, q=True, v=True):
        mult = -1
    cmds.setAttr("directionalLightX.rotateY", 90 * mult)
    cmds.setAttr("directionalLightY.rotateX", -90 * mult)
    cmds.setAttr("directionalLightZ.rotateX", 90 - 90 * mult)

def set_nm_rig_rotation():
    cmds.setAttr(g_ffxNormalMapLightingRig + ".rotateX", cmds.getAttr("persp.rotateX"))
    cmds.setAttr(g_ffxNormalMapLightingRig + ".rotateY", cmds.getAttr("persp.rotateY"))
    cmds.setAttr(g_ffxNormalMapLightingRig + ".rotateZ", cmds.getAttr("persp.rotateZ"))

def sync_nm_rig_intensity(light_dir):
    value = cmds.getAttr("directionalLight{}Shape.intensity".format(light_dir))
    Utils.set_attr_if_new("directionalLightXShape.intensity", value)
    Utils.set_attr_if_new("directionalLightYShape.intensity", value)
    Utils.set_attr_if_new("directionalLightZShape.intensity", value)

def render_frame():
    if not cmds.objExists("vraySettings"):
        Utils.maya_print("Object 'vraySettings' is not exists. Skip rendering.")
        return
    cmds.setAttr("vraySettings.animType", 0)
    mel.eval("renderIntoNewWindow render;")

def render_animation():
    if not cmds.objExists("vraySettings"):
        Utils.maya_print("Object 'vraySettings' is not exists. Skip rendering.")
        return
    cmds.setAttr("vraySettings.fileNamePrefix", "ffx_d", type="string")
    cmds.setAttr("vraySettings.animType", 1)
    mel.eval("renderIntoNewWindow render;")

def render_nm_frame():
    if not cmds.objExists("vraySettings"):
        Utils.maya_print("Object 'vraySettings' is not exists. Skip rendering.")
        return
    set_nm_rig_rotation()
    cmds.setAttr("vraySettings.animType", 0)
    mel.eval("renderIntoNewWindow render;")

def render_nm_animation():
    if not cmds.objExists("vraySettings"):
        Utils.maya_print("Object 'vraySettings' is not exists. Skip rendering.")
        return
    set_nm_rig_rotation()
    text = "ffx_nm_forward"
    if cmds.checkBox(g_invertLightsDirection_checkBox, q=True, v=True):
        text = "ffx_nm_inverted"
    cmds.setAttr("vraySettings.fileNamePrefix", text, type="string")
    cmds.setAttr("vraySettings.animType", 1)
    mel.eval("renderIntoNewWindow render;")

def update_ui():
    if g_skipUiUpdate:
        return
    value = cmds.getAttr("fumeFXShape1.sh_shadow_falloff");     cmds.floatSliderGrp(g_ffxShadowFalloff_floatSliderGrp,  e=True, v=value)
    value = cmds.getAttr("directionalLightXShape.intensity");   cmds.floatSliderGrp(g_lightsIntencity_floatSliderGrp,   e=True, v=value)
    value = cmds.currentTime(query=True);                       cmds.floatField(g_animCurrentFrame_floatField,          e=True, v=value)
    value = cmds.getAttr("defaultRenderGlobals.startFrame");    cmds.floatField(g_animStartFrame_floatField,            e=True, v=value)
    value = cmds.getAttr("defaultRenderGlobals.endFrame");      cmds.floatField(g_animEndFrame_floatField,              e=True, v=value)

def set_attrs():
    global g_skipUiUpdate
    g_skipUiUpdate = True
    
    value = cmds.floatSliderGrp(g_ffxShadowFalloff_floatSliderGrp, q=True, v=True)
    Utils.set_attr_if_new("fumeFXShape1.sh_shadow_falloff", value)
    
    value = cmds.floatSliderGrp(g_lightsIntencity_floatSliderGrp, q=True, v=True)
    Utils.set_attr_if_new("directionalLightXShape.intensity", value)
    Utils.set_attr_if_new("directionalLightYShape.intensity", value)
    Utils.set_attr_if_new("directionalLightZShape.intensity", value)

    value = cmds.floatField(g_animStartFrame_floatField, q=True, v=True)
    Utils.set_attr_if_new("defaultRenderGlobals.startFrame", value)
    value = cmds.floatField(g_animEndFrame_floatField, q=True, v=True)
    Utils.set_attr_if_new("defaultRenderGlobals.endFrame", value)

    g_skipUiUpdate = False

def setup_objects():
    if cmds.objExists(g_ffxNormalMapLightingRig):
        cmds.delete(g_ffxNormalMapLightingRig)
    light_x = cmds.directionalLight(rgb=[1, 0, 0], rotation=(0, 90, 0),  name="directionalLightX")
    light_y = cmds.directionalLight(rgb=[0, 1, 0], rotation=(-90, 0, 0), name="directionalLightY")
    light_z = cmds.directionalLight(rgb=[0, 0, 1], rotation=(0, 0, 0),   name="directionalLightZ")
    cmds.group(light_x, light_y, light_z, name=g_ffxNormalMapLightingRig)
    set_nm_rig_direction()

    required_objs = ["defaultRenderGlobals", "fumeFXShape1", "directionalLightX", "directionalLightY", "directionalLightZ"]
    for obj in required_objs:
        if not cmds.objExists(obj):
            cmds.warning("Object '{}' is not exists.".format(obj))
            return

    cmds.scriptJob(attributeChange=['directionalLightXShape.intensity', "SceneTweaks.sync_nm_rig_intensity('X')\nSceneTweaks.update_ui()"], parent=g_window)
    cmds.scriptJob(attributeChange=['directionalLightYShape.intensity', "SceneTweaks.sync_nm_rig_intensity('Y')\nSceneTweaks.update_ui()"], parent=g_window)
    cmds.scriptJob(attributeChange=['directionalLightZShape.intensity', "SceneTweaks.sync_nm_rig_intensity('Z')\nSceneTweaks.update_ui()"], parent=g_window)
    cmds.scriptJob(attributeChange=['fumeFXShape1.sh_shadow_falloff',   "SceneTweaks.update_ui()"], parent=g_window)
    cmds.scriptJob(          event=["timeChanged",                      "SceneTweaks.update_ui()"], parent=g_window)
    cmds.scriptJob(attributeChange=['defaultRenderGlobals.startFrame',  "SceneTweaks.update_ui()"], parent=g_window)
    cmds.scriptJob(attributeChange=['defaultRenderGlobals.endFrame',    "SceneTweaks.update_ui()"], parent=g_window)

    update_ui()

g_ffxNormalMapLightingRig           = "ffxNormalMapLightingRig"
g_skipUiUpdate                      = False

g_window                            = "SceneTweaks_Window"
g_ffxShadowFalloff_floatSliderGrp   = "g_ffxShadowFalloff_floatSliderGrp"
g_lightsIntencity_floatSliderGrp    = "g_lightsIntencity_floatSliderGrp"
g_invertLightsDirection_checkBox    = "g_invertLightsDirection_checkBox"
g_animCurrentFrame_floatField       = "g_animCurrentFrame_floatField"
g_animStartFrame_floatField         = "g_animStartFrame_floatField"
g_animEndFrame_floatField           = "g_animEndFrame_floatField"

def scene_tweaks_window():
    if cmds.window(g_window, exists=True): cmds.deleteUI(g_window, window=True)
    window = cmds.window(g_window, sizeable=True, resizeToFitChildren=True, title="Scene Tweaks")
    cmds.columnLayout(adjustableColumn=True)

    cmds.frameLayout(label="Fume FX Tweaks", mw=5, mh=5)

    cmds.columnLayout(adjustableColumn=True)
    cmds.floatSliderGrp(g_ffxShadowFalloff_floatSliderGrp, l="FFX Smoke Shadow Falloff", f=True, min=0.0, max=50.0, fmn=0.0, fmx=50.0, pre=3, v=1.0, cc="SceneTweaks.set_attrs()")
    cmds.floatSliderGrp(g_lightsIntencity_floatSliderGrp,  l="Lights Intencity",         f=True, min=0.0, max=20.0, fmn=0.0, fmx=20.0, pre=3, v=1.0, cc="SceneTweaks.set_attrs()")
    cmds.checkBox(g_invertLightsDirection_checkBox,  l="Invert Lights Direction", v=False, cc="SceneTweaks.set_nm_rig_direction()")
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=2)
    cmds.columnLayout(adjustableColumn=True)
    cmds.rowLayout(numberOfColumns=2)
    cmds.text(l="Current frame"); cmds.floatField(g_animCurrentFrame_floatField, editable=False, pre=1)
    cmds.setParent("..")
    cmds.button(label="Render frame (diffuse)",         command="SceneTweaks.render_frame()")
    cmds.button(label="Render frame (normal map)",      command="SceneTweaks.render_nm_frame()")
    cmds.setParent("..")
    cmds.columnLayout(adjustableColumn=True)
    cmds.rowLayout(numberOfColumns=4)
    cmds.text(l="Start");         cmds.floatField(g_animStartFrame_floatField,   editable=True,  pre=1, v=0.0, cc="SceneTweaks.set_attrs()")
    cmds.text(l="End");           cmds.floatField(g_animEndFrame_floatField,     editable=True,  pre=1, v=1.0, cc="SceneTweaks.set_attrs()")
    cmds.setParent("..")
    cmds.button(label="Render animation (diffuse)",     command="SceneTweaks.render_animation()")
    cmds.button(label="Render animation (normal map)",  command="SceneTweaks.render_nm_animation()")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.setParent("..")

    cmds.frameLayout(label="Vray Tweaks", mw=5, mh=5)
    cmds.rowLayout(numberOfColumns=2)
    cmds.button(label="Default Setup", command="SceneTweaks.vray_default_setup()")
    cmds.button(label="Fume FX Setup", command="SceneTweaks.vray_fumefx_setup()")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(label="Image Processing", mw=5, mh=5)
    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label="Make sprite sheet (diffuse)",    command="SceneTweaks.make_sprite_sheet()")
    cmds.button(label="Make sprite sheet (normal map)", command="SceneTweaks.make_nm_sprite_sheet()")
    cmds.setParent("..")
    cmds.setParent("..")

    setup_objects()

    cmds.setParent("..")
    cmds.showWindow(window)

def vray_default_setup():
    mel.eval("setCurrentRenderer \"vray\";")
    if not cmds.objExists("vraySettings"):
        Utils.maya_print("Node 'vraySettings' must be initialized. Open render settings.")
        mel.eval("unifiedRenderGlobalsWindow;")

    presets = cmds.nodePreset(list="vraySettings")
    if "Vray_Default" in presets:
        cmds.nodePreset(load=("vraySettings", "Vray_Default"))
        Utils.maya_print("Vray now using default setup.")

def vray_fumefx_setup():
    mel.eval("setCurrentRenderer \"vray\";")
    if not cmds.objExists("vraySettings"):
        Utils.maya_print("Node 'vraySettings' must be initialized. Open render settings.")
        mel.eval("unifiedRenderGlobalsWindow;")

    # VRay Common
    cmds.setAttr("vraySettings.imageFormatStr", "tga", type="string")
    cmds.setAttr("vraySettings.fileNamePadding", 4)
    cmds.setAttr("defaultRenderGlobals.modifyExtension", 1)
    cmds.setAttr("defaultRenderGlobals.startExtension", 0)
    cmds.setAttr("defaultRenderGlobals.byExtension", 1)
    cmds.setAttr("vraySettings.width",  256)
    cmds.setAttr("vraySettings.height", 256)
    cmds.setAttr("vraySettings.aspectRatio", 1.0)
    # VRay
    cmds.setAttr("vraySettings.globopt_geom_displacement", 0)
    #cmds.setAttr("vraySettings.globopt_cache_bitmaps", 1)               # (maybe make it True)
    #cmds.setAttr("vraySettings.globopt_gi_dontRenderImage", 1)          # (maybe make it True)
    #cmds.setAttr("vraySettings.globopt_mtl_reflectionRefraction", 0)    # (maybe make it False)
    #cmds.setAttr("vraySettings.globopt_mtl_glossy", 0)                  # (maybe make it False)
    cmds.setAttr("vraySettings.samplerType", 0) # Fixed rate
    cmds.setAttr("vraySettings.aaFilterOn", 0)
    # RT Engine
    cmds.setAttr("vraySettings.rt_engineType", 1) # 0: CPU, 1: OpenCL, 2: CUDA

    Utils.maya_print("Vray now using FumeFX setup.")

def make_sprite_sheet():
    cmd = "process_ffx('C:/Projects/ffx/images/ffx_d.{}.tga', (8, 4))\n"
    subprocess.call(["C:\\Python27\\python.exe", "C:\\Projects\\vfxutils\\utils\\GridMaker.py", cmd], stdout=sys.__stdout__)

def make_nm_sprite_sheet():
    cmd  = "process_ffx('C:/Projects/ffx/images/ffx_nm_forward.{}.tga', (8, 4))\n"
    cmd += "process_ffx('C:/Projects/ffx/images/ffx_nm_inverted.{}.tga', (8, 4))\n"
    cmd += "combine_ffx_normals('C:/Projects/ffx/images/ffx_nm_forward.{}.tga', 'C:/Projects/ffx/images/ffx_nm_inverted.{}.tga')\n"
    subprocess.call(["C:\\Python27\\python.exe", "C:\\Projects\\vfxutils\\utils\\GridMaker.py", cmd], stdout=sys.__stdout__)
