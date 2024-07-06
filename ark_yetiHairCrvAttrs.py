from maya.cmds import *

def ark_yetiHairCrvAttrs():
	aiList = [ 'aiRenderCurve',
				'aiCurveWidth',
				'aiSampleRate',
				'aiCurveShaderR',
				'aiCurveShaderG',
				'aiCurveShaderB' ]

	attrList = [ 'weight',
				'lengthWeight',
				'innerRadius',
				'outerRadius',
				'density',
				'baseAttraction',
				'tipAttraction',
				'attractionBias',
				'randomAttraction',
				'twist',
				'surfaceDirectionLimit',
				'surfaceDirectionLimitFalloff',
				'randomTwist' ]

	selList = ls( sl = True, long = True )

	crvList = []
	for each in selList:
		selType = objectType( each )
		if selType == 'nurbsCurve':
			crvList.append( each )
		if selType == 'transform':
			shps = listRelatives( each, shapes = True, fullPath = True )
			for shp in shps:
				if objectType( shp ) == 'nurbsCurve':
					crvList.append( shp )

	for crv in crvList:
		if not isConnected( crv + '.baseAttraction', crv + '.attractionProfile[0].attractionProfile_FloatValue' ):
			setAttr( crv + '.baseAttraction', 1 )
			connectAttr( crv + '.baseAttraction', crv + '.attractionProfile[0].attractionProfile_FloatValue', force = True )
		if not isConnected( crv + '.tipAttraction', crv + '.attractionProfile[1].attractionProfile_FloatValue' ):
			setAttr( crv + '.tipAttraction', 1 )
			connectAttr( crv + '.tipAttraction', crv + '.attractionProfile[1].attractionProfile_FloatValue', force = True )
		for attr in attrList:
			if attributeQuery( attr, node = crv, exists = True ):
				setAttr( crv + '.' + attr, channelBox = True )
		for ai in aiList:
			if attributeQuery( ai, node = crv, exists = True ):
				setAttr( crv + '.' + ai, keyable = False, channelBox = False )
