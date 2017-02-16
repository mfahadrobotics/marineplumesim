#!/bin/bash 

cd $PLUMESIM &&
python viz_update.py
cd $PLUMESIM &&
gnome-terminal -x bash -c "roslaunch marineplumesim.launch; exec $SHELL"

