#!/usr/bin/env python

from tempfile import mkstemp
from shutil import move
from os import remove, close, environ
from xml.dom import minidom

sim_path = environ.get('PLUMESIM')

xmldoc = minidom.parse(sim_path+'/sim_properties.xml')
itemlist = xmldoc.getElementsByTagName('grid_x')
grid_x=float(itemlist[0].attributes['val'].value)
itemlist = xmldoc.getElementsByTagName('grid_y')
grid_y=float(itemlist[0].attributes['val'].value)
value = min([grid_x,grid_y])
file_path = sim_path+"/rviz/marineplumesim.rviz"
pattern = '      Size (m):'
subst = '      Size (m): '+str(value)+'\n'

fh, abs_path = mkstemp()
new_file = open(abs_path,'w')
old_file = open(file_path)
for line in old_file:
    new_file.write(subst if pattern in line else line)
#close temp file
new_file.close()
close(fh)
old_file.close()
#Remove original file
remove(file_path)
#Move new file
move(abs_path, file_path)


