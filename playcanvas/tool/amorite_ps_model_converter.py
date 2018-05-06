# -*- coding: utf-8 -*-
#author @shaochun <·> http://github.com/shaochun

"""
▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉
▉     STILL WORKING IN PROCESS, DON'T USE ME                     ▉
▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉
"""

""" TODO
defaults
embeds
geometries
materials
metadata
objects
textures
transform
"""

import json

#=====================================================================
# JSON FLOAT DIGITS SWALLOWER
#=====================================================================
#http://stackoverflow.com/questions/1447287/format-floats-with-standard-json-module
class PrettyFloat(float):
    def __repr__(self):
        return '%.8g' % self

def pretty_floats(obj):
    if isinstance(obj, float):
        return PrettyFloat(obj)
    elif isinstance(obj, dict):
        return dict((k, pretty_floats(v)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        return map(pretty_floats, obj)             
    return obj

#print simplejson.dumps(pretty_floats([23.67, 23.97, 23.87]))

#=====================================================================
# JSON OUTPUT DATA STRUCTURE
#=====================================================================
class Skin:
    def __init__(self):
        self.mesh_node_name = "" #should be 'name of the geometry node'
                                 #not using in output json file, just for annotation
        self.inverseBindMatrices = [] #item is a list of 16 floats (matrix of bone)
        self.boneNames = [] #item is a string (bonename)

class Joint:
    def __init__(self):
        self.mNode        = None
        self.mBoneIndex   = -3
        self.mParentIndex = -3
        self.mName        = ""

#-------------------------------------------
class Root():
    def __init__(self):
        self.model = None

class Model():
    def __init__(self):
        self.version  = 2
        self.name     = ""
        self.nodes = [] #list of Node
        #self.skins_and_deformers = [] #list of Skin_and_deformers if deformers>1
        self.skins = [] #list of Skin


class Node():
    def __init__(self):
        self.name = ""
        #self.defaults = { "s": [1, 1, 1] }
        self.position = []
        self.rotation = []
        self.scale    = []


#=====================================================================
# MAIN CLASS
#=====================================================================
class Amorite_PlayCanvas_Model_Converter:

    def __init__(self):

        self.options = None
        self.args    = None

        self.rootNodeName = ""
        self.rootScale = 0
        self.rootRotation = [0,0,0]

        self.sceneStatic = None

        self.scene   = None
        self.joints  = [] #for json export
        self.bones   = [] #for animation iteration

        self.stackName = ""
        self.duration = -3.0

    # ######################################################################################
    # utilities
    # ######################################################################################
    def GetGeometryTransformation(self, node):
        if not node:
            print("Geometry is null.")
            quit()

        t = node.GetGeometricTranslation(0) #FbxNode.eSourcePivot)
        r = node.GetGeometricRotation(0)
        s = node.GetGeometricScaling(0)

        return FbxAMatrix(t,r,s)


    def FindBoneIndexByName(self, name):
        for i in xrange(len(self.bones)):
            if self.bones[i].GetName() == name:
                return i

        #if not found
        print("bone not found.")
        quit()

    #this method is NOT using for now
    def ToggleYZMatrix(self, input):

        #output = input

        translation = input.GetT();
        rotation = input.GetR();

        translation.Set(translation[0], translation[1], translation[2]); #This negate Z of Translation Component of the matrix
        rotation.Set(rotation[0], rotation[1], rotation[2]);             #This negate X,Y of Rotation Component of the matrix

        #These 2 lines finally set "input" to the eventual converted result
        input.SetT(translation);
        input.SetR(rotation);

        return input

    # ######################################################################################
    # json output
    # ######################################################################################
    def writeJsonData(self, data):
        if self.options.pretty:
            jsonData = json.dumps(data, sort_keys=False, indent=4, separators=(',', ': '), default=lambda o: o.__dict__)
        else:
            #jsonData = json.dumps(data, sort_keys=False, default=lambda o: o.__dict__)
            jsonData = json.dumps(pretty_floats(data), sort_keys=False, default=lambda o: o.__dict__)

        #print(jsonData)

        writefile = open(self.args[2], 'w')
        writefile.write(jsonData)
        writefile.close()


    def writeIt(self):
        m       = Model()
        m.name  = self.args[0][:-4] # PlayBot(.fbx) remove suffix

        _nodes  = self.processSkeletonTransforms()
        m.nodes = _nodes

        #m.skins
        self.processGeometry(self.scene.GetRootNode(), m)


        r       = Root()
        r.model = m

        self.writeJsonData(r)

        print("\nWriting file: %s written sucessfully." % self.args[2])


    # ######################################################################################
    # handle skeleton hierarchy
    # ######################################################################################
    def processSkeletonHierarchy(self):

        print("self.rootNodeName= " + self.rootNodeName)

        rootNode   = self.scene.FindNodeByName(self.rootNodeName)
        rootName   = rootNode.GetName()
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
        args[0] : source_model_fbx
        args[1] : rootNode
        args[2] : wirte_model_json
        """
        #----------------------------------------------------------
        if len(self.args) >= 2:   #at least 3, input_fbxfile, rootNodeName, output_json_file
            self.rootNodeName = self.args[1]
            if self.rootNodeName == "": print("RootNodeName is null.")

            self.rootScale =    float(self.options.rootScale)
            self.rootRotation = eval(self.options.rootRotation)

            print("\nLoading file: %s" % self.args[0])
            result = LoadScene(sdk_manager, self.scene, self.args[0])

            #upVector = self.scene.GetGlobalSettings().GetAxisSystem().GetUpVector()
            #cs = self.scene.GetGlobalSettings().GetAxisSystem().GetCoorSystem()
            #print(upVector, cs)

            ### GOOD
            # axis_system = None
            # if self.options.dcc.lower() == "mayay":
            #     axis_system = FbxAxisSystem.MayaYUp
            # elif self.options.dcc.lower() == "mayaz":
            #     axis_system = FbxAxisSystem.MayaZUp
            # elif self.options.dcc.lower() == "max":
            #     axis_system = FbxAxisSystem.Max
            # else:
            #     axis_system = FbxAxisSystem.MayaYUp

            #http://stackoverflow.com/questions/21221029/fbx-sdk-up-axis-conversion/21647895#21647895
            axis_system = FbxAxisSystem(FbxAxisSystem.eYAxis, FbxAxisSystem.eParityOdd , FbxAxisSystem.eRightHanded)
            axis_system.ConvertScene(self.scene)

        else:
            result = False
            print("\nUsage: amorite_ps_model_converter [source_model.fbx] [rootNode] [output_model.js] [options]\n")
            quit()

        #----------------------------------------------------------
        if not result:
            print("\nAn error occurred while loading the file...")
            quit()
        else:

            print("FbxScene loaded.")

        #----------------------------------------------------------
        # Destroy all objects created by the FBX SDK.
        #sdk_manager.Destroy()


    # ######################################################################################
    # handle geometry (this is a generator)
    # ######################################################################################
    def processGeometry(self, node, model):
        if node.GetNodeAttribute():
            if node.GetNodeAttribute().GetAttributeType() == FbxNodeAttribute.eMesh:
                self.processSkins(node, model)

        for i in xrange(0, node.GetChildCount()):
            self.processGeometry(node.GetChild(i), model)


    # ######################################################################################
    # handle skin
    # ######################################################################################
    def processSkins(self, node, model):

        self.processSkeletonHierarchy()

        #---- LOAD SKIN ---- (this is called from processGeometry)

        #PB Head index = 6
        mesh = node.GetMesh()

        numOfDeformers = mesh.GetDeformerCount()
        print("numOfDeformers= " , numOfDeformers) #1

        geometryTransform = self.GetGeometryTransformation(node)

        _skins     = [] #WANTED
        _bonenames = [] #WANTED

        for deformerIndex in xrange(numOfDeformers):
            skin = mesh.GetDeformer(deformerIndex, FbxDeformer.eSkin) #as FbxSkin
            if not skin: continue

            _skin = Skin()
            _skin.mesh_node_name = node.GetName() #not using in output json file, just for annotation

            numOfClusters = skin.GetClusterCount()
            print("numOfClusters= " , numOfClusters) #44

            for clusterIndex in xrange(numOfClusters):
                cluster = skin.GetCluster(clusterIndex)
                boneName = cluster.GetLink().GetName()
                boneIndex = self.FindBoneIndexByName(boneName)

                transformMatrix             = FbxAMatrix()
                transformLinkMatrix         = FbxAMatrix()
                globalBindposeInverseMatrix = FbxAMatrix()

                #- toggleYZMatrix              = FbxAMatrix(FbxVector4(1.0, 0.0, 0.0, 0.0),  FbxVector4(0.0, 0.0, 1.0, 0.0),  FbxVector4(0.0, 1.0, 0.0, 0.0))
                toggleYZMatrix              = FbxMatrix();
                toggleYZMatrix.Set(0,0,1.0);
                toggleYZMatrix.Set(1,2,1.0); toggleYZMatrix.Set(1,1,0);
                toggleYZMatrix.Set(2,1,-1.0); toggleYZMatrix.Set(2,2,0);
                toggleYZMatrix.Set(3,3,1.0);

                cluster.GetTransformMatrix(transformMatrix);            #The transformation of the mesh at binding time
                cluster.GetTransformLinkMatrix(transformLinkMatrix);    #The transformation of the cluster(bone) at binding time from bone space to world space
                wbi = transformLinkMatrix.Inverse() * transformMatrix * geometryTransform

                #(row, column)
                m00 = wbi.Get(0,0); m01 = wbi.Get(0,1); m02 = wbi.Get(0,2); m03 = wbi.Get(0,3)
                m10 = wbi.Get(1,0); m11 = wbi.Get(1,1); m12 = wbi.Get(1,2); m13 = wbi.Get(1,3)
                m20 = wbi.Get(2,0); m21 = wbi.Get(2,1); m22 = wbi.Get(2,2); m23 = wbi.Get(2,3)
                m30 = wbi.Get(3,0); m31 = wbi.Get(3,1); m32 = wbi.Get(3,2); m33 = wbi.Get(3,3)
                del wbi
                
                wbi = FbxMatrix()
                wbi.Set(0,0, m00);  wbi.Set(0,1, m01);  wbi.Set(0,2, m02);  wbi.Set(0,3, m03)
                wbi.Set(1,0, m10);  wbi.Set(1,1, m11);  wbi.Set(1,2, m12);  wbi.Set(1,3, m13)
                wbi.Set(2,0, m20);  wbi.Set(2,1, m21);  wbi.Set(2,2, m22);  wbi.Set(2,3, m23)
                wbi.Set(3,0, m30);  wbi.Set(3,1, m31);  wbi.Set(3,2, m32);  wbi.Set(3,3, m33)

                wbi = wbi * toggleYZMatrix

                m00 = wbi.Get(0,0)  #
                m10 = wbi.Get(1,0)  #
                m20 = wbi.Get(2,0)  #
                m30 = wbi.Get(3,0)  #

                m01 = wbi.Get(0,1)  #  #
                m11 = wbi.Get(1,1)  #  #
                m21 = wbi.Get(2,1)  #  #
                m31 = wbi.Get(3,1)  #  #

                m02 = wbi.Get(0,2)  #  #  #
                m12 = wbi.Get(1,2)  #  #  #
                m22 = wbi.Get(2,2)  #  #  #
                m32 = wbi.Get(3,2)  #  #  #

                m03 = wbi.Get(0,3)  #  #  #  #
                m13 = wbi.Get(1,3)  #  #  #  #
                m23 = wbi.Get(2,3)  #  #  #  #
                m33 = wbi.Get(3,3)  #  #  #  #


                # !! check items order
                #_skin.inverseBindMatrices.append( [ m00,m10,m20,m30,
                #                                    m01,m11,m21,m31,
                #                                    m02,m12,m22,m32,
                #                                    m03,m13,m23,m33] )
                _skin.inverseBindMatrices.append( [ m00,m01,m02,m03,
                                                    m10,m11,m12,m13,
                                                    m20,m21,m22,m23,
                                                    m30,m31,m32,m33] )
                
                _skin.boneNames.append(boneName)

            _skins.append(_skin)
            print("bp")

            #----------------------------------------------------
            if numOfDeformers > 1:
                print("numOfDeformers > 1.")
                #model.skins_and_deformers.append(_skins)
                quit()
            else:
                model.skins = _skins

        print("bp")


    def processSkeletonTransforms(self):

        self.processSkeletonHierarchy()

        _nodes = [] #WANTED

        for boneNode in self.bones:

            node = Node()

            boneName = boneNode.GetName()
            node.name = boneName

            #if (node.name == self.rootNodeName):
            #    node.defaults = {
            #        "s": [self.rootScale, self.rootScale, self.rootScale],
            #        "r": self.rootRotation }

            position = boneNode.LclTranslation.Get();
            rotation = boneNode.LclRotation.Get();
            scale    = boneNode.LclScaling.Get();

            tx = position[0]; ty = position[1]; tz = position[2]
            rx = rotation[0]; ry = rotation[1]; rz = rotation[2]
            sx = scale[0];    sy = scale[1];    sz = scale[2]

            node.position = [tx,ty,tz]
            node.rotation = [rx,ry,rz]
            node.scale    = [sx,sy,sz]

            _nodes.append(node)

        return _nodes

    # ######################################################################################
    # handle user inputs
    # ######################################################################################
    def userInputInit(self):

        usage = "Usage: %prog [source_model.fbx] [rootNode] [output_model.js] [options]"
        parser = OptionParser(usage=usage)

        parser.add_option('-s', '--scale',      action='store', dest='rootScale',       help="setup the root joint scale",              default=1)
        parser.add_option('-r', '--rotation',   action='store', dest='rootRotation',    help="setup the root joint rotation",           default="[0,0,0]")
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
    converter = Amorite_PlayCanvas_Model_Converter()
    converter.userInputInit()

    #----------------------------------------------------------
    converter.loadFbxScene()
    converter.writeIt()




