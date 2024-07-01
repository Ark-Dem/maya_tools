from maya.cmds import *

# ATTRIBUTES TO RECORD
attrList = [ 'translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ' ]

# SET ANGULAR UNITS TO RADIANS
currentUnit( a = 'rad' )

# SELECT OBJECT TO RECORD AND TYPE ATTRIBUTES TO RECORD
recordAttr( at = attrList )

# START RECORDING (ESC TO STOP)
play( record = True )

# SET ANGULAR UNITS TO DEGREES
currentUnit( a = 'deg' )

# REMOVE RECORDING NODES
recordAttr( at = attrList, d = True )
