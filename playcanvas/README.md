# Amorite Playcanvas Model Animation Converter

## Intro

This is a python tool converting FBX files to Playcanvas Animation Json files, providing a simple way for the animation conversion offline.

Use any DCC tools to export your animated models as FBX, then use this Amorite tool to convert it to Playcanvas Animation Json format.

## Usage

python amorite_ps_anim_converter.py [input_fbx_anim] [rootNode] [rootScale] [rootRotation] [output_json_anim]

Example: python amorite_ps_anim_converter.py Playbot_run.fbx "PB" 0.01 "[-90,-90,0]" a1.json

##Options

- -s, -scale ---- this scales up or shrinks down the animation. Default is 1

- -r, -rotation ---- this provides an easy way to quick rotate the animation, for example "[0, 90, -90]" means rotate the animtion 90 and -90 degrees along the Y and Z axis respectively. Default is [-90,-90,0].

- -d, -dcc ---- supports three types of coordinate system: mayaY , mayaZ , and max. Default is mayaY.

- -p, -pretty ---- pretty formatted Json output.

## Installation

1. install **Python FBX SDK 2015**. Make sure you copy **fbx.pyd** & **FbxCommon.py** from the installed folder to **%python_path%/Lib/site-packages**.

2. Python 2.7.x

## Constraints

1. Animation fps is bound to 30fps.

2. The exported FBX has to be baked. This means the Position/Rotation/Scale track needs to have the exact same frames.

3. Currently only the first animation stack is converted.
