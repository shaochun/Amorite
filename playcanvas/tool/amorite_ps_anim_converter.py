# -*- coding: utf-8 -*-
#author @shaochun <·> http://github.com/shaochun

import json

#=====================================================================
# JSON OUTPUT DATA STRUCTURE
#=====================================================================
class Joint:
    def __init__(self):
        self.mNode        = None
        self.mBoneIndex   = -3
        self.mParentIndex = -3
        self.mName        = ""

#-------------------------------------------
class Root():
    def __init__(self):
        self.animation = None

class Animation():
    def __init__(self):
        self.version  = 4
        self.name     = ""
        self.duration = -3.0
        self.nodes = [] #Node


class Node():
    def __init__(self):
        self.name = ""
        self.defaults = { "s": [1, 1, 1] }
        self.keys = [] #Key

class Key():
    def __init__(self):
        self.t = [0,0,0]
        self.p = [0,0,0]
        self.r = [0,0,0]

#=====================================================================
# MAIN CLASS
#=====================================================================
class Amorite_PlayCanvas_Animation_Converter:

    def __init__(self):

        self.options = None
        self.args    = None

        self.rootNodeName = ""
        self.rootScale = 0
        self.rootRotation = [-90,-90,0]

        self.sceneStatic = None

        self.scene   = None
        self.joints  = [] #for json export
        self.bones   = [] #for animation iteration

        self.stackName = ""
        self.duration = -3.0

    # ######################################################################################
    # json output
    # ######################################################################################

    def writeJsonData(self, data):
        if self.options.pretty:
            jsonData = json.dumps(data, sort_keys=False, indent=4, separators=(',', ': '), default=lambda o: o.__dict__)
        else:
            jsonData = json.dumps(data, sort_keys=False, default=lambda o: o.__dict__)

        #print(jsonData)

        writefile = open(self.args[2], 'w')
        writefile.write(jsonData)
        writefile.close()


    def writeIt(self):
        _nodes = self.loadAnimation() #this goes first to setup name and duration

        r = Root()

        a          = Animation()
        a.name     = self.stackName
        a.duration = self.duration
        a.nodes    = _nodes

        r.animation = a
        self.writeJsonData(r)

        print("\nWriting file: %s written sucessfully." % self.args[2])



    # ######################################################################################
    # handle skeleton hierarchy
    # ######################################################################################
    def processSkeletonHierarchy(self):

        print("self.rootNodeName= " + self.rootNodeName)

        rootNode = self.scene.FindNodeByName(self.rootNodeName)
        rootName = rootNode.GetName()
        childCount = rootNode.GetChildCount()

        #put in the root node
        rootJoint = Joint()
        rootJoint.mBoneIndex   = 0
        rootJoint.mParentIndex = -1
        rootJoint.mNode        = rootNode #not necessary
        rootJoint.mName        = rootName

        self.joints.append(rootJoint)
        self.bones.append(rootNode)

        #put in the children
        for childIndex in xrange(rootNode.GetChildCount()):
            iteratedNode = rootNode.GetChild(childIndex)
            childName = iteratedNode.GetName()
            self.processSkeletonHierarchyRecursively(iteratedNode, len(self.joints), 0)


    def processSkeletonHierarchyRecursively(self, node, boneIndex, boneParentIndex):
        if(node.GetNodeAttribute() and node.GetNodeAttribute().GetAttributeType() \
            and node.GetNodeAttribute().GetAttributeType() == FbxNodeAttribute.eSkeleton):

            #this is for json
            currJoint = Joint()

            currJoint.mBoneIndex   = len(self.joints)
            currJoint.mParentIndex = boneParentIndex
            currJoint.mNode        = node               #not necessary
            currJoint.mName        = node.GetName()
            self.joints.append(currJoint)

            #this is for skeleton and animation
            self.bones.append(node)

            for i in xrange(node.GetChildCount()):
                self.processSkeletonHierarchyRecursively(node.GetChild(i), len(self.joints), boneIndex)

    # ######################################################################################
    # initialize fbx scene
    # ######################################################################################
    def loadFbxScene(self):

        sdk_manager, self.scene = InitializeSdkObjects()
        fbxConverter = FbxGeometryConverter(sdk_manager)

        #print(self.scene)

        #----------------------------------------------------------
        """
        args[0] : source_anim_fbx
        args[1] : rootNode
        args[2] : export_anim_json
        """
        if len(self.args) >= 3:   #at least 3, input_fbxfile, rootNodeName, output_json_file
            self.rootNodeName = self.args[1]
            if self.rootNodeName == "": print("RootNodeName is null.")

            self.rootScale =    float(self.options.rootScale)
            self.rootRotation = eval(self.options.rootRotation)

            print("\nLoading file: %s" % self.args[0])
            result = LoadScene(sdk_manager, self.scene, self.args[0])

            #axis_system = FbxAxisSystem(FbxAxisSystem.eYAxis, FbxAxisSystem.eParityOdd , FbxAxisSystem.eLeftHanded)
            axis_system = None
            if self.options.dcc.lower() == "mayay":
                axis_system = FbxAxisSystem.MayaYUp
            elif self.options.dcc.lower() == "mayaz":
                axis_system = FbxAxisSystem.MayaZUp
            elif self.options.dcc.lower() == "max":
                axis_system = FbxAxisSystem.Max
            else:
                axis_system = FbxAxisSystem.MayaYUp


            axis_system.ConvertScene(self.scene)

        else:
            result = False
            print("\nUsage: amorite_ps_anim_converter [source_anim.fbx] [rootNode] [output_anim.js] [options]\n")
            quit()

        #----------------------------------------------------------
        if not result:
            print("\nAn error occurred while loading the file...")
            quit()
        else:

            print("FbxScene loaded.")

    # ######################################################################################
    # handle animation
    # ######################################################################################
    def loadAnimation(self):

        cas = self.scene.GetCurrentAnimationStack()
        animStackName = cas.GetName()
        self.stackName = cas.GetName()

        localTimeSpan = cas.GetLocalTimeSpan()

        #duration = localTimeSpan.GetDuration()
        self.duration = localTimeSpan.GetDuration().GetSecondDouble()

        self.processSkeletonHierarchy()
        #-------------------

        layerCount = cas.GetMemberCount()
        layer      = cas.GetMember(0)
        curveNode  = layer.GetMember(0)

        nodes = [] #WANTED

        for boneNode in self.bones:

            node = Node()

            boneName = boneNode.GetName()
            node.name = boneName
            if (node.name == self.rootNodeName):
                node.defaults = {
                    "s": [self.rootScale, self.rootScale, self.rootScale],
                    "r": self.rootRotation }
            node.keys = []

            Tcurve = boneNode.LclTranslation.GetCurve(layer)
            Rcurve = boneNode.LclRotation.GetCurve(layer)
            Scurve = boneNode.LclScaling.GetCurve(layer)

            #S/R/T curves' keycount has to be same
            numKeys = Rcurve.KeyGetCount()
            for keyIndex in xrange(0, numKeys, 3):

                frameSeconds = 0
                tx=0; ty=0; tz=0
                rx=0; ry=0; rz=0
                sx=0; sy=0; sz=0

                if Rcurve != None:
                    frameTime = Scurve.KeyGetTime(keyIndex)
                    rotation = boneNode.EvaluateLocalRotation(frameTime)
                    rx = rotation[0]; ry = rotation[1]; rz = rotation[2]

                if Tcurve != None:
                    frameTime = Scurve.KeyGetTime(keyIndex)
                    position = boneNode.EvaluateLocalTranslation(frameTime)
                    if boneName == self.rootNodeName:
                        tx = position[0] * self.rootScale; ty = position[1] * self.rootScale; tz = position[2] * self.rootScale
                    else:
                        tx = position[0]; ty = position[1]; tz = position[2]

                    frameSeconds = frameTime.GetSecondDouble()

                key = Key()
                key.t = frameSeconds
                key.p = [tx,ty,tz]
                key.r = [rx,ry,rz]

                node.keys.append(key)


            #get the last key----------------------------------
            if numKeys%3 != 0:

                frameSeconds = 0
                tx=0; ty=0; tz=0
                rx=0; ry=0; rz=0
                sx=0; sy=0; sz=0

                #get the last key
                if Rcurve != None:
                    frameTime = Scurve.KeyGetTime(numKeys-1)
                    rotation = boneNode.EvaluateLocalRotation(frameTime)
                    rx = rotation[0]; ry = rotation[1]; rz = rotation[2]

                if Tcurve != None:
                    frameTime = Scurve.KeyGetTime(numKeys-1)
                    position = boneNode.EvaluateLocalTranslation(frameTime)
                    if boneName == self.rootNodeName:
                        tx = position[0] * self.rootScale; ty = position[1] * self.rootScale; tz = position[2] * self.rootScale
                    else:
                        tx = position[0]; ty = position[1]; tz = position[2]

                    frameSeconds = frameTime.GetSecondDouble()

                #append the last key
                key = Key()
                key.t = frameSeconds
                key.p = [tx,ty,tz]
                key.r = [rx,ry,rz]

                node.keys.append(key)

            nodes.append(node)

        return nodes

    # ######################################################################################
    # handle user inputs
    # ######################################################################################
    def userInputInit(self):

        #usage = "Usage: %prog [source_anim.fbx] [rootNode] [rootScale] [rootRotation] [output_anim.js] [options]"
        usage = "Usage: %prog [source_anim.fbx] [rootNode] [output_anim.js] [options]"
        parser = OptionParser(usage=usage)

        parser.add_option('-s', '--scale',      action='store', dest='rootScale',       help="setup the root joint scale",              default=1)
        parser.add_option('-r', '--rotation',   action='store', dest='rootRotation',    help="setup the root joint rotation",           default="[-90,-90,0]")
        parser.add_option('-d', '--dcc',        action='store', dest='dcc',             help="setup dcc coordinate system",             default="mayaY")
        #parser.add_option('-a', '--upaxis',     action='store', dest='upAxis',          help="setup Y or Z-axis up-vector",             default="Y")
        #parser.add_option('-c', '--coord',      action='store', dest='coord',           help="left or right-handed coordinate system",  default="right")
        parser.add_option('-p', '--pretty',     action='store_false', dest='pretty',    help="pretty format json output",               default=True)

        (self.options, self.args) = parser.parse_args()



# ######################################################################################
# main
# ######################################################################################
if __name__ == "__main__":
    from optparse import OptionParser

    try:
        from FbxCommon import *
    except ImportError:
        import platform
        msg = 'Could not locate the python FBX SDK 2015!\n'
        msg += 'You need to copy the FBX SDK 2015 into your python install folder such as '
        if platform.system() == 'Windows' or platform.system() == 'Microsoft':
            msg += '"Python27/Lib/site-packages"'
        elif platform.system() == 'Linux':
            msg += '"/usr/local/lib/python2.7/site-packages"'
        elif platform.system() == 'Darwin':
            msg += '"/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages"'
        msg += ' folder.'
        print(msg)
        sys.exit(1)

    #----------------------------------------------------------
    converter = Amorite_PlayCanvas_Animation_Converter()
    converter.userInputInit()

    #----------------------------------------------------------
    converter.loadFbxScene()
    converter.writeIt()






