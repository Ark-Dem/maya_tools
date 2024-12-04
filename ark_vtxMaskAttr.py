from maya.cmds import *
import maya.mel

def ark_vtxMaskAttr():
	attr = 'handleMask'
	aiAttr = 'mtoa_varying_' + attr

	shp = listRelatives( ls( sl = True )[0].split('.')[0], shapes = True )[0]

	vtxList = []
	for each in ls( sl = True, fl = True ):
		vtxList.append( int(each.split('[')[-1][:-1]) )

	if not attributeQuery( aiAttr, node = shp, exists = True ):
		addAttr( shp, dataType = 'doubleArray', longName = aiAttr )

	vtxCount = polyEvaluate( shp, v = True )
	cmd = 'setAttr ' + shp + '.' + aiAttr + ' -type doubleArray ' + str(vtxCount)
	for i in xrange( 0, vtxCount ):
		if i in vtxList:
			cmd += ' 1.0'
		else:        
			cmd += ' 0.0'
	cmd += ';'

	maya.mel.eval( cmd )
