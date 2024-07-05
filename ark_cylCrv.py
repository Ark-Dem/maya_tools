from maya.cmds import *

def ark_cylCrv():
	obj = ls( sl = True )[0]

	uvCount = polyEvaluate( obj, uv = True )

	uvDict = {}
	for i in xrange( 0, uvCount ):
		vCoord = polyEditUV( obj + '.map[' + str(i) + ']', query = True )[1]
		
		if vCoord in uvDict.keys():
			uvDict[vCoord] = uvDict[vCoord] + [i]
		else:
			uvDict[vCoord] = [i]    

	sections = uvDict.keys()
	sections.sort()

	crv = ''
	for each in sections:
		uvs = []
		for uv in uvDict[each]:
			uvs.append( obj + '.map[' + str(uv) + ']' )
		vtx = polyListComponentConversion( uvs, fuv = True, tv = True )
		vtx = ls( vtx, fl = True )

		cent = [0, 0, 0]
		for vt in vtx:
			ppos = pointPosition( vt )
			cent = [cent[0]+ppos[0], cent[1]+ppos[1], cent[2]+ppos[2]]
		cent = [cent[0]/len(vtx), cent[1]/len(vtx), cent[2]/len(vtx)]

		if crv == '':
			crv = curve( p = cent, worldSpace = True )
		else:
			curve( crv, append = True, p = cent, worldSpace = True )
