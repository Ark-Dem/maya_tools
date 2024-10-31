from maya.cmds import *

def ark_a4to5():
	# ALSURFACE TO AISTANDARDSURFACE ATTRIBUTES LIST
	attrs = [ ['diffuseStrength','base'],
				['diffuseColor','baseColor'],
				['diffuseRoughness','diffuseRoughness'],
				#['backlightStrength',''],
				#['backlightColor',''],
				#['backlightIndirectStrength',''],
				['sssMix','subsurface'],
				['specular1Strength','specular'],
				['specular1Color','specularColor'],
				['specular1Roughness','specularRoughness'],
				#['specular1Anisotropy','specularAnisotropy'],
				#['specular1Rotation','specularRotation'],
				['specular1Ior','specularIOR'],
				['specular2Strength','coat'],
				['specular2Color','coatColor'],
				['specular2Roughness','coatRoughness'],
				#['specular2Anisotropy',''],
				#['specular2Rotation',''],
				['specular2Ior','coatIOR'],
				['transmissionStrength','transmission'],
				['transmissionColor','transmissionColor'],
				#['transmissionRoughness',''],
				#['transmissionIor',''],
				['opacity','opacity'],
				['normalCamera','normalCamera'] ]

	# REPLACE ALSURFACE WITH AISTANDARDSURFACE
	for each in ls( type = 'alSurface' ):
		nm = each
		if nm[-4:] == '_SHD':
			nm = nm[:-4]

		orig = rename( each, each + '__al2ai' )
		shadingNode( 'aiStandardSurface', asShader = True, name = each )
		sgs = listConnections( orig, s = False, d = True, c = False, p = True, type = 'shadingEngine' )
		for sg in sgs: 
			connectAttr( each + '.outColor', sg, force = True )
 
		for attr in attrs:
			conns = listConnections( orig + '.' + attr[0], s = True, d = False, c = True, p = True )
			if conns != None:
				connectAttr( conns[1], each + '.' + attr[1], force = True )
			else:
				val = getAttr( orig + '.' + attr[0] )
				if type(val) == list:
					setAttr( each + '.' + attr[1], val[0][0], val[0][1], val[0][2], type = 'double3' )
				else:
					setAttr( each + '.' + attr[1], val )
				'''
				if attr[1] == 'specularIOR':
					if getAttr( orig + '.specular1FresnelMode' ) == 1:
						refl = getAttr( orig + '.specular1Reflectivity' )[0]
						edge = getAttr( orig + '.specular1EdgeTint' )[0]
						clr = getAttr( orig + '.specular1Color' )[0]
						ior = shadingNode( 'aiComplexIor', asUtility = True, name = nm + '__spec__ior' )
						setAttr( ior + '.reflectivity', refl[0]*clr[0], refl[1]*clr[1], refl[2]*clr[2], type = 'double3' )
						setAttr( ior + '.edgetint', edge[0]*clr[0], edge[1]*clr[1], edge[2]*clr[2], type = 'double3' )
						connectAttr( ior + '.outColor', each + '.specularColor', force = True )
				elif attr[1] == 'coatIOR':
					if getAttr( orig + '.specular2FresnelMode' ) == 1:
						refl = getAttr( orig + '.specular2Reflectivity' )[0]
						edge = getAttr( orig + '.specular2EdgeTint' )[0]
						clr = getAttr( orig + '.specular2Color' )[0]
						ior = shadingNode( 'aiComplexIor', asUtility = True, name = nm + '__coat__ior' )
						setAttr( ior + '.reflectivity', refl[0]*clr[0], refl[1]*clr[1], refl[2]*clr[2], type = 'double3' )
						setAttr( ior + '.edgetint', edge[0]*clr[0], edge[1]*clr[1], edge[2]*clr[2], type = 'double3' )
						connectAttr( ior + '.outColor', each + '.coatColor', force = True )
				'''
		#delete( orig )
        
	# REMOVE GAMMACORRECT NODES
	forDel = []
	for each in ls( type = 'gammaCorrect' ):
		gm = getAttr( each + '.gamma' )[0]
		if gm[0] < 0.4546 and gm[1] < 0.4546 and gm[2] < 0.4546:
			inConn = listConnections( each, s = True, d = False, c = False, p = True )
			if inConn != None:
				if len(inConn) == 1:
					gmConns = listConnections( each, s = False, d = True, c = True, p = True )
					if gmConns != None:
						for k in xrange( 0, len(gmConns), 2 ):
							if not nodeType( gmConns[k+1].split('.')[0] ) in [ 'nodeGraphEditorInfo', 'defaultRenderUtilityList' ]:
								outType = getAttr( inConn[0], type = True )
								inType = getAttr( gmConns[k+1], type = True )
								if outType == 'float' and inType == 'float3':
									try:
										connectAttr( inConn[0], gmConns[k+1] + 'R', force = True )
										connectAttr( inConn[0], gmConns[k+1] + 'G', force = True )
										connectAttr( inConn[0], gmConns[k+1] + 'B', force = True )
									except:
										pass
									try:
										connectAttr( inConn[0], gmConns[k+1] + 'X', force = True )
										connectAttr( inConn[0], gmConns[k+1] + 'Y', force = True )
										connectAttr( inConn[0], gmConns[k+1] + 'Z', force = True )
									except:
										pass
								elif outType == 'float3' and inType == 'float':
									outs = { 'X':'R', 'Y':'G', 'Z':'B' }
									try:
										connectAttr( inConn[0] + outs[gmConns[k][-1]], gmConns[k+1], force = True )
									except:
										pass
								else:
									try:
										connectAttr( inConn[0], gmConns[k+1], force = True )
									except:
										pass
			if not each in forDel:
				forDel.append( each )
	if forDel != []:
		#delete( forDel )
		select( forDel, replace = True )

	# FIX REMAP NAMES
	for each in ls( '*spec1*' ):
		rename( each, each.replace( 'spec1', 'spec' ) )
	for each in ls( '*spec2*' ):
		rename( each, each.replace( 'spec2', 'coat' ) )
	for each in ls( '*Str*' ):
		rename( each, each.replace( 'Str', 'Weight' ) )
	for each in ls( '*Weight*' ) + ls( '*Rough*' ):
		if each.split('_')[-1] != 'remap':
			rename( each, each + '__remap' )
	
	# CLEAR SELECTION
	#select( clear = True )
