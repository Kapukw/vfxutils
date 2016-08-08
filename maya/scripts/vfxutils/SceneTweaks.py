﻿import os
import sys
import glob
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

g_nmLightsGroupName = "ffx_nm_lights"

def create_ffx_nm_rig():
    if cmds.objExists(g_nmLightsGroupName):
        cmds.delete(g_nmLightsGroupName)
    light_x = cmds.directionalLight(rgb=[1, 0, 0], rotation=(0, 90, 0),  name="directionalLightX")
    light_y = cmds.directionalLight(rgb=[0, 1, 0], rotation=(-90, 0, 0), name="directionalLightY")
    light_z = cmds.directionalLight(rgb=[0, 0, 1], rotation=(0, 0, 0),   name="directionalLightZ")
    cmds.group(light_x, light_y, light_z, name=g_nmLightsGroupName)

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
    cmds.setAttr("vraySettings.animType", 0)
    if cmds.objExists(g_nmLightsGroupName):
        cmds.setAttr(g_nmLightsGroupName + ".rotateX", cmds.getAttr("persp.rotateX"))
        cmds.setAttr(g_nmLightsGroupName + ".rotateY", cmds.getAttr("persp.rotateY"))
        cmds.setAttr(g_nmLightsGroupName + ".rotateZ", cmds.getAttr("persp.rotateZ"))
    mel.eval("renderIntoNewWindow render;")

def render_nm_animation():
    if not cmds.objExists("vraySettings"):
        Utils.maya_print("Object 'vraySettings' is not exists. Skip rendering.")
        return
    text = "ffx_nm_forward"
    if cmds.checkBox(g_invertLightsDirection, q=True, v=True):
        text = "ffx_nm_inverted"
    cmds.setAttr("vraySettings.fileNamePrefix", text, type="string")
    cmds.setAttr("vraySettings.animType", 1)
    mel.eval("renderIntoNewWindow render;")

def get_input_values():
    value = cmds.getAttr("fumeFXShape1.sh_shadow_falloff")
    cmds.floatSliderGrp(g_ffxShadowFalloff, e=True, v=value)

    valueX = cmds.getAttr("directionalLightXShape.intensity")
    valueY = cmds.getAttr("directionalLightYShape.intensity")
    valueZ = cmds.getAttr("directionalLightZShape.intensity")
    if   valueY == valueZ: value = valueX
    elif valueX == valueZ: value = valueY
    elif valueX == valueY: value = valueZ
    else: value = valueX
    cmds.setAttr("directionalLightXShape.intensity", value)
    cmds.setAttr("directionalLightYShape.intensity", value)
    cmds.setAttr("directionalLightZShape.intensity", value)
    cmds.floatSliderGrp(g_lightsIntencity, e=True, v=value)

def set_input_values():
    value = cmds.floatSliderGrp(g_ffxShadowFalloff, q=True, v=True)
    cmds.setAttr("fumeFXShape1.sh_shadow_falloff", value)

    value = cmds.floatSliderGrp(g_lightsIntencity, q=True, v=True)
    cmds.setAttr("directionalLightXShape.intensity", value)
    cmds.setAttr("directionalLightYShape.intensity", value)
    cmds.setAttr("directionalLightZShape.intensity", value)

def set_nm_lights_direction():
    mult = -1 if cmds.checkBox(g_invertLightsDirection, q=True, v=True) else 1
    cmds.setAttr("directionalLightX.rotateY", 90 * mult)
    cmds.setAttr("directionalLightY.rotateX", -90 * mult)
    cmds.setAttr("directionalLightZ.rotateX", 90 - 90 * mult)

def register_window_jobs():
    create_ffx_nm_rig()
    required_objs = ["fumeFXShape1", "directionalLightX", "directionalLightY", "directionalLightZ"]
    for obj in required_objs:
        if not cmds.objExists(obj):
            cmds.warning("Object '{}' is not exists.".format(obj))
            return

    cmds.scriptJob(attributeChange=['fumeFXShape1.sh_shadow_falloff',   "SceneTweaks.get_input_values()"], parent=g_window)
    cmds.scriptJob(attributeChange=['directionalLightXShape.intensity', "SceneTweaks.get_input_values()"], parent=g_window)
    cmds.scriptJob(attributeChange=['directionalLightYShape.intensity', "SceneTweaks.get_input_values()"], parent=g_window)
    cmds.scriptJob(attributeChange=['directionalLightZShape.intensity', "SceneTweaks.get_input_values()"], parent=g_window)
    get_input_values()

g_window                = "SceneTweaks_Window"

g_ffxShadowFalloff      = "g_ffxShadowFalloff"
g_lightsIntencity       = "g_lightsIntencity"
g_invertLightsDirection = "g_invertLightDirection"
g_animCurrentFrame      = "g_animCurrentFrame"
g_animStartFrame        = "g_animStartFrame"
g_animEndFrame          = "g_animEndFrame"

def scene_tweaks_window():
    if cmds.window(g_window, exists=True): cmds.deleteUI(g_window, window=True)
    window = cmds.window(g_window, sizeable=True, resizeToFitChildren=True, title="Scene Tweaks")
    cmds.columnLayout(adjustableColumn=True)

    cmds.frameLayout(label="Fume FX Tweaks", mw=5, mh=5)

    cmds.columnLayout(adjustableColumn=True)
    cmds.floatSliderGrp(g_ffxShadowFalloff, l="FFX Smoke Shadow Falloff", f=True, min=0.0, max=50.0, fmn=0.0, fmx=50.0, v=1.0, cc="SceneTweaks.set_input_values()")
    cmds.floatSliderGrp(g_lightsIntencity,  l="Lights Intencity",          f=True, min=0.0, max=20.0, fmn=0.0, fmx=20.0, v=1.0, cc="SceneTweaks.set_input_values()")
    cmds.checkBox(g_invertLightsDirection,  l="Invert Lights Direction", v=False, cc="SceneTweaks.set_nm_lights_direction()")
    cmds.setParent("..")

    register_window_jobs()

    cmds.rowLayout(numberOfColumns=2)
    cmds.columnLayout(adjustableColumn=True)
    cmds.rowLayout(numberOfColumns=2)
    cmds.text(l="Current frame"); cmds.floatField(g_animCurrentFrame, editable=False, precision=1)
    cmds.setParent("..")
    cmds.button(label="Render frame (diffuse)",         command="SceneTweaks.render_frame()")
    cmds.button(label="Render frame (normal map)",      command="SceneTweaks.render_nm_frame()")
    cmds.setParent("..")
    cmds.columnLayout(adjustableColumn=True)
    cmds.rowLayout(numberOfColumns=4)
    cmds.text(l="Start");         cmds.floatField(g_animStartFrame,   editable=True,  precision=1, v=cmds.getAttr("defaultRenderGlobals.startFrame"))
    cmds.text(l="End");           cmds.floatField(g_animEndFrame,     editable=True,  precision=1, v=cmds.getAttr("defaultRenderGlobals.endFrame"))
    cmds.setParent("..")
    cmds.button(label="Render animation (diffuse)",     command="SceneTweaks.render_animation()")
    cmds.button(label="Render animation (normal map)",  command="SceneTweaks.render_nm_animation()")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.setParent("..")

    cmds.frameLayout(label="Vray Tweaks", mw=5, mh=5)
    cmds.rowLayout(numberOfColumns=2)
    cmds.button(label="Default Setup")
    cmds.button(label="Fume FX Setup")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(label="Image Processing", mw=5, mh=5)
    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label="Make sprite sheet (diffuse)")
    cmds.button(label="Make sprite sheet (normal map)")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.setParent("..")
    cmds.showWindow(window)