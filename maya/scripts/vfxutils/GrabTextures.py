import os
import shutil
import maya.cmds as cmds

def grab_textures():

    projectDir = os.path.normpath(cmds.workspace(q=True, rootDirectory=True).lower())
    workDir = os.path.normpath(os.path.dirname(cmds.file(q=True, sceneName=True).lower()))
    saveDir = cmds.fileDialog2(fileMode=3)
    if not saveDir: return
    saveDir = os.path.normpath(saveDir[0].lower())
    saveDirRel = os.path.relpath(saveDir, workDir)

    fileNodes = cmds.ls(type="file")
    for fileNode in fileNodes:
        oldPath = os.path.normpath(cmds.getAttr(fileNode + '.fileTextureName').lower())
        tempPath = os.path.relpath(oldPath, projectDir) if oldPath.startswith(projectDir) else os.path.basename(oldPath)
        newPath = os.path.join(saveDir, tempPath)
        newPathRel = os.path.join(saveDirRel, tempPath)
        directory = os.path.dirname(newPath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        shutil.copyfile(oldPath, newPath)
        cmds.setAttr(fileNode + '.fileTextureName', newPathRel, type='string')
