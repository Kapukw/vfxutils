import os
import sys
import glob
import maya.cmds as cmds
import maya.mel as mel

import Utils

g_jobsPool = list()

def register_jobs():
    global g_jobsPool
    #g_jobsPool.append(cmds.scriptJob(event=["SceneOpened", "SceneTweaks.clean_scene()"], protected=True))
    sys.stdout.write("SceneTweaks: {} jobs registered\n".format(len(g_jobsPool)))
    #clean_scene()

def unregister_jobs():
    global g_jobsPool
    for jobNum in g_jobsPool:
        cmds.scriptJob(kill=jobNum, force=True)
    sys.stdout.write("SceneTweaks: {} jobs unregistered\n".format(len(g_jobsPool)))
    g_jobsPool = list()

def clean_scene():
    unknown_nodes = cmds.ls(type="unknown")
    sys.stdout.write("Delete " + str(len(unknown_nodes)) + " nodes of type 'unknown'.\n")
    for node in unknown_nodes:
        if cmds.objExists(node):
            cmds.lockNode(node, lock=False)
            cmds.delete(node)

    if cmds.pluginInfo("Turtle.mll", q=True, loaded=True):
        cmds.unloadPlugin("Turtle.mll", force=True)
    locked_nodes = ["TurtleDefaultBakeLayer", "ilrOptionsNode", "ilrUIOptionsNode", "ilrBakeLayerManager"]
    for node in locked_nodes:
        if cmds.objExists(node):
            cmds.lockNode(node, lock=False)
            cmds.delete(node)

g_window = "SceneTweaks_Window"

def scene_tweaks_window():
    if cmds.window(g_window, exists=True): cmds.deleteUI(g_window, window=True)
    window = cmds.window(g_window, sizeable=False, title="Scene Tweaks")

    tabs = cmds.tabLayout(childResizable=False, scrollable=False, innerMarginWidth=5, innerMarginHeight=5)
    tab1 = scene_tweaks_tab()
    tab2 = utils_tab()
    cmds.tabLayout(tabs, edit=True, tabLabel=((tab1, "Material Tweaks"), (tab2, "Scene Cleanup")))
    cmds.setParent("..")

    cmds.showWindow(window)

g_nmLightsGroupName = "ffx_nm_lights"

def create_ffx_nm_rig():
    if cmds.objExists(g_nmLightsGroupName):
        cmds.delete(g_nmLightsGroupName)
    light_x = cmds.directionalLight(rgb=[1, 0, 0], rotation=(0, 90, 0),  name="directionalLightX")
    light_y = cmds.directionalLight(rgb=[0, 1, 0], rotation=(-90, 0, 0), name="directionalLightY")
    light_z = cmds.directionalLight(rgb=[0, 0, 1], rotation=(0, 0, 0),   name="directionalLightZ")
    cmds.group(light_x, light_y, light_z, name=g_nmLightsGroupName)

def render_frame():
    cmds.setAttr("vraySettings.animType", 0)
    mel.eval("renderIntoNewWindow render;")

def render_animation():
    cmds.setAttr("vraySettings.fileNamePrefix", "ffx_d", type="string")
    cmds.setAttr("vraySettings.animType", 1)
    mel.eval("renderIntoNewWindow render;")

def render_nm_frame():
    cmds.setAttr("vraySettings.animType", 0)
    if cmds.objExists(g_nmLightsGroupName):
        cmds.setAttr(g_nmLightsGroupName + ".rotateX", cmds.getAttr("persp.rotateX"))
        cmds.setAttr(g_nmLightsGroupName + ".rotateY", cmds.getAttr("persp.rotateY"))
        cmds.setAttr(g_nmLightsGroupName + ".rotateZ", cmds.getAttr("persp.rotateZ"))
    mel.eval("renderIntoNewWindow render;")

def render_nm_animation():
    text = "ffx_nm_forward"
    if cmds.checkBox(g_invertLightsDirection, q=True, v=True):
        text = "ffx_nm_inverted"
    cmds.setAttr("vraySettings.fileNamePrefix", text, type="string")
    cmds.setAttr("vraySettings.animType", 1)
    mel.eval("renderIntoNewWindow render;")

g_ffxShadowFalloff = "g_ffxShadowFalloff"
g_lightsIntencity = "g_lightsIntencity"
g_invertLightsDirection = "g_invertLightDirection"
g_animStartFrame = "g_animStartFrame"
g_animEndFrame = "g_animEndFrame"

def get_input_values():
    cmds.floatSliderGrp(g_ffxShadowFalloff, e=True, v=cmds.getAttr("fumeFXShape1.sh_shadow_falloff"))

def set_input_values():
    cmds.setAttr("fumeFXShape1.sh_shadow_falloff", cmds.floatSliderGrp(g_ffxShadowFalloff, q=True, v=True))

    value = cmds.floatSliderGrp(g_lightsIntencity, q=True, v=True)
    cmds.setAttr("directionalLightXShape.intensity", value)
    cmds.setAttr("directionalLightYShape.intensity", value)
    cmds.setAttr("directionalLightZShape.intensity", value)

def set_nm_lights_direction():
    mult = 1
    if cmds.checkBox(g_invertLightsDirection, q=True, v=True):
        mult = -1

    cmds.setAttr("directionalLightX.rotateY", 90 * mult)
    cmds.setAttr("directionalLightY.rotateX", -90 * mult)
    cmds.setAttr("directionalLightZ.rotateX", 90 - 90 * mult)

def scene_tweaks_tab():

    cmds.scriptJob(attributeChange=['fumeFXShape1.sh_shadow_falloff', "SceneTweaks.get_input_values()"], parent=g_window)

    tab = cmds.columnLayout(adjustableColumn=True, w=450, h=500)

    cmds.frameLayout(label="Scene Tweaks", mw=5, mh=5)

    value = cmds.getAttr("fumeFXShape1.sh_shadow_falloff")
    cmds.floatSliderGrp(g_ffxShadowFalloff, l="FFX: Smoke Shadow Falloff", f=True, min=0.0, max=50.0, fmn=0.0, fmx=50.0, v=value, cc="SceneTweaks.set_input_values()")
    cmds.floatSliderGrp(g_lightsIntencity, l="Lights Intencity", f=True, min=0.0, max=20.0, fmn=0.0, fmx=20.0, v=1.0, cc="SceneTweaks.set_input_values()")
    cmds.checkBox(g_invertLightsDirection, l="Invert Lights Direction", v=False, cc="SceneTweaks.set_nm_lights_direction()")

    cmds.rowLayout(numberOfColumns=2)
    value = cmds.getAttr("defaultRenderGlobals.startFrame")
    cmds.floatField(g_animStartFrame, v=value)
    value = cmds.getAttr("defaultRenderGlobals.endFrame")
    cmds.floatField(g_animEndFrame, v=value)
    cmds.setParent("..")

    # direct control <-> attr bind
    #cmds.attrFieldSliderGrp(min=0.0, max=50.0, at="fumeFXShape1.sh_shadow_falloff")

    cmds.button(label="Delete Unknown Nodes",           command="SceneTweaks.clean_scene()")
    cmds.button(label="Create FumeFX normal map rig",   command="SceneTweaks.create_ffx_nm_rig()")
    cmds.button(label="Render frame",                   command="SceneTweaks.render_frame()")
    cmds.button(label="Render animation",               command="SceneTweaks.render_animation()")
    cmds.button(label="Render normal map frame",        command="SceneTweaks.render_nm_frame()")
    cmds.button(label="Render normal map animation",    command="SceneTweaks.render_nm_animation()")

    cmds.setParent("..")

    cmds.setParent("..")

    return tab

def utils_tab():

    tab = cmds.columnLayout(adjustableColumn=True, w=450, h=500)

    cmds.setParent("..")

    return tab
