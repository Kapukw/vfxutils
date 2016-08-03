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

g_ffxShadowFalloff      = "g_ffxShadowFalloff"
g_lightsIntencity       = "g_lightsIntencity"
g_invertLightsDirection = "g_invertLightDirection"
g_animStartFrame        = "g_animStartFrame"
g_animEndFrame          = "g_animEndFrame"

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

def scene_tweaks_tab():

    tab = cmds.columnLayout(adjustableColumn=True, w=450, h=500)

    cmds.frameLayout(label="Scene Tweaks", mw=5, mh=5)

    cmds.floatSliderGrp(g_ffxShadowFalloff, l="FFX: Smoke Shadow Falloff", f=True, min=0.0, max=50.0, fmn=0.0, fmx=50.0, v=1.0, cc="SceneTweaks.set_input_values()")
    cmds.floatSliderGrp(g_lightsIntencity,  l="Lights Intencity",          f=True, min=0.0, max=20.0, fmn=0.0, fmx=20.0, v=1.0, cc="SceneTweaks.set_input_values()")
    
    cmds.checkBox(g_invertLightsDirection,  l="Invert Lights Direction", v=False, cc="SceneTweaks.set_nm_lights_direction()")

    cmds.rowLayout(numberOfColumns=2)
    cmds.floatField(g_animStartFrame, v=cmds.getAttr("defaultRenderGlobals.startFrame"))
    cmds.floatField(g_animEndFrame, v=cmds.getAttr("defaultRenderGlobals.endFrame"))
    cmds.setParent("..")

    register_window_jobs()

    #cmds.button(label="Delete Unknown Nodes",           command="SceneTweaks.clean_scene()")
    #cmds.button(label="Create FumeFX normal map rig",   command="SceneTweaks.create_ffx_nm_rig()")
    cmds.button(label="Render frame",                   command="SceneTweaks.render_frame()")
    cmds.button(label="Render animation",               command="SceneTweaks.render_animation()")
    cmds.button(label="Render normal map frame",        command="SceneTweaks.render_nm_frame()")
    cmds.button(label="Render normal map animation",    command="SceneTweaks.render_nm_animation()")

    cmds.setParent("..")

    cmds.setParent("..")

    return tab


g_window = "SceneTweaks_Window"

def scene_tweaks_window():
    if cmds.window(g_window, exists=True): cmds.deleteUI(g_window, window=True)
    window = cmds.window(g_window, sizeable=False, title="Scene Tweaks")

    tabs = cmds.tabLayout(childResizable=False, scrollable=False, innerMarginWidth=5, innerMarginHeight=5)
    cmds.tabLayout(tabs, edit=True, tabLabel=((scene_tweaks_tab(), "Material Tweaks")))
    cmds.setParent("..")

    cmds.showWindow(window)

def scene_tweaks_window_new():
    if cmds.window(g_window, exists=True): cmds.deleteUI(g_window, window=True)
    window = cmds.window(g_window, sizeable=True, resizeToFitChildren=True, title="Scene Tweaks")
    cmds.columnLayout(adjustableColumn=True)

    cmds.frameLayout(label="Env Settings", mw=5, mh=5)

    rl = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.columnLayout(adjustableColumn=True)
    cmds.textFieldGrp(g_brdfPath_textFieldGrp,          label="BRDF Texture",           text="", cc="SceneTweaks.set_env_tex('BrdfSampler')")
    cmds.textFieldGrp(g_diffuseEnvPath_textFieldGrp,    label="Diffuse Env Cubemap",    text="", cc="SceneTweaks.set_env_tex('DiffuseLightingSampler')")
    cmds.textFieldGrp(g_specularEnvPath_textFieldGrp,   label="Specular Env Cubemap",   text="", cc="SceneTweaks.set_env_tex('SpecularLightingSampler')")
    cmds.setParent("..")
    cmds.columnLayout(adjustableColumn=False)
    cmds.iconTextButton(style="iconOnly", image1="fileOpen.png", command="SceneTweaks.set_env_tex('BrdfSampler', file_dialog=True)")
    cmds.iconTextButton(style="iconOnly", image1="fileOpen.png", command="SceneTweaks.set_env_tex('DiffuseLightingSampler', file_dialog=True)")
    cmds.iconTextButton(style="iconOnly", image1="fileOpen.png", command="SceneTweaks.set_env_tex('SpecularLightingSampler', file_dialog=True)")
    cmds.setParent("..")
    cmds.rowLayout(rl, e=True, columnAttach=[(1, "right", 0), (2, "both", 0)])
    cmds.setParent("..")

    cmds.columnLayout(adjustableColumn=False)
    cmds.optionMenu(g_techniqueList_optionMenu, label="Technique", cc="SceneTweaks.set_technique();")
    for technique in g_techniques: cmds.menuItem(label=technique)
    cmds.checkBox(g_toggleLocalAo_checkBox, label="Use Local AO", cc="SceneTweaks.toggle_local_ao()")
    cmds.setParent("..")

    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label="Set Default Env Textures", command="SceneTweaks.set_default_env_textures()")
    cmds.button(label="Reload All Dx11 Shaders", command="SceneTweaks.reload_all_dx11_shaders()")
    cmds.setParent("..")

    cmds.setParent("..")

    cmds.frameLayout(label="Scene Tweaks", mw=5, mh=5)

    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label="Remove Unknown Nodes", command="SceneTweaks.remove_unknown_nodes()")
    cmds.button(label="Remove Texture/Material Duplicates", command="SceneTweaks.remove_duplicates()")
    cmds.button(label="Fix Semantic Values", command="SceneTweaks.fix_semantic_values()")
    cmds.button(label="Fix UV Set Names", command="SceneTweaks.fix_uvset_names()")
    cmds.setParent("..")

    cmds.setParent("..")

    cmds.setParent("..")
    cmds.showWindow(window)