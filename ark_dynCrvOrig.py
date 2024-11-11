from maya.cmds import *
import maya.mel

def ark_dynCrvOrig():
	selList = ls( sl = True )

	crvList = []
	geoList = []
	for each in selList:
		if nodeType( each ) == 'transform':
			obj = listRelatives( each, shapes = True )
			if obj != None:
				objType = nodeType( obj )
			else:
				objType = 'misc'
				
		if objType == 'nurbsCurve':
			crvList.append( each )
		elif objType == 'mesh' or objType == 'nurbsSurface':
			geoList.append( each )

	origList = []
	origSel = []
	for crv in crvList:
		dup = createNode( 'nurbsCurve', name = crv + '_Orig' )
		connectAttr( crv + '.local', dup + '.create' )
		refresh()
		disconnectAttr( crv + '.local', dup + '.create' )
		origList.append( [dup, crv] )
		origSel.append( dup )

	select( origSel + geoList, replace = True )
	maya.mel.eval( 'makeCurvesDynamic 2 { "1", "0", "1", "1", "0"};' )

	for crv in origList:
		hist = listHistory( crv[0], future = True )
		for each in hist:
			if objExists( each ):
				if nodeType( each ) == 'follicle':
					conn = listConnections( each + '.outCurve', s = False, d = True, c = False, p = False )[0]
					connectAttr( each + '.outCurve', crv[1] + '.create', force = True )
					delete( conn )
