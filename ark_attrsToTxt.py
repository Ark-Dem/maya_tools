from maya.cmds import *

f = open( workspace( query=True, rd=True ) + 'data/attrs.txt', 'w' )

for each in ls( sl=True ):
    for attr in listAttr( each, keyable = True ):
        f.write( attr + '\t' + str(getAttr( each + '.' + attr )) + '\n' )

f.close()
