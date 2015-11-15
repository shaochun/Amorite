# Playcanvas Animation Converter

## Intro

This is a simple python tool converting FBX file --> Playcanvas Animation JSON format.

## Usage

python ps_anim_converter.py [input_fbx_anim] [rootNode] [rootScale] [rootRotation] [output_json_anim]

Example: python ps_anim_converter.py Playbot_run.fbx "PB" 0.01 "[-90,-90,0]" a1.json

## Install

1) install Python FBX SDK 2015. make sure you copy fbx.pyd & FbxCommon.py from the installed folder to %python_path%/Lib/site-packages
2) Python 2.7.x

## Constraints

1) Axis-Y-Up, Left Handed (Maya FBX)
2) Animation fps is bound to 30fps.