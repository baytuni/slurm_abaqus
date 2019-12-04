#!/bin/bash
scontrol suspend $1
sacctmgr -i modify resource name=abaqus set count=36
batch -p Express dummy.sh
sleep(4)
sacctmgr -i modify resource name=abaqus set count=18
