#------------------------------------------------------------------maya-
# file: ark_arnoldShd.py
# version: 0.20
# date: 2023.12.29
# author: Arkadiy Demchenko
#-----------------------------------------------------------------------
# 2023.12.29 (v0.20) - initial version
#-----------------------------------------------------------------------
# Converts shading networks to arnold nodes for export to USD.
#
# TODO:
# - check normal map through aiUvTransform
# - nested file nodes
# - uvSets
# - non-aiStandardSurface scenarios (rayswitch, etc.)
#-----------------------------------------------------------------------
from maya.cmds import *
import os

def ark_arnoldShd():
	sgList = ls( sl=True )
	toDelete = []

	for sg in sgList:
		# GET THE LIST OF ALL SHADING NODES
		shd = listConnections( sg + '.aiSurfaceShader' )
		if shd == None:
			shd = listConnections( sg + '.surfaceShader' )
		disp = listConnections( sg + '.displacementShader' )

		shdList = listHistory( shd, pdo = True )
		if disp != None:
			shdList += listHistory( disp, pdo = True )
			
		shdList = list(set(shdList))
		
		# MOVE DISP PADDING TO MESH
		if disp != None:
			for dispShp in listHistory( sg ):
				if nodeType( dispShp ) == 'mesh':
					if getAttr( dispShp + '.aiDispPadding' ) == 0:
						setAttr( dispShp + '.aiDispPadding', getAttr( disp[0] + '.aiDisplacementPadding' ) )
		
		# REPLACEMENTS
		for each in shdList:
			inConns = listConnections( each, s = True, d = False, c = True, p = True )
			if inConns == None:
				inConns = []
			inConns = [inConns[i:i+2] for i in range( 0, len(inConns), 2 )]

			outConns = listConnections( each, s = False, d = True, c = True, p = True )
			outConns = [outConns[i:i+2] for i in range( 0, len(outConns), 2 )]
			
			rgbaToFloatList = []	   
			
			# FILE > AIIMAGE
			if nodeType( each ) == 'file':
				eachName = each + '__aiImage'
				if each[-4:] == 'file':
					eachName = each[:-4] + 'aiImage'
					
				aiImg = shadingNode( 'aiImage', asTexture = True, name = eachName )

				rootEnv = os.getenv('root').replace( '\\', '/' )
				if rootEnv[-1] == '/':
					rootEnv = rootEnv[:-1]

				filePath = getAttr( each + '.fileTextureName' ).replace(rootEnv, '[root]').replace('%root%', '[root]')
				if getAttr( each + '.uvTilingMode' ):
					filePath = filePath.replace( '.1001.', '.<udim>.' )
	 
				setAttr( aiImg + '.filename', filePath, type = 'string' )
				setAttr( aiImg + '.ignoreColorSpaceFileRules', True )
				setAttr( aiImg + '.colorSpace', getAttr( each + '.colorSpace' ), type = 'string' )
				if '__disp.' in filePath and filePath[-4:] == '.exr':
					setAttr( aiImg + '.singleChannel', True )

				if listConnections( each + '.colorGain', s = True, d = False ) == None:
					clrGn = getAttr( each + '.colorGain' )[0]
					setAttr( aiImg + '.multiply', clrGn[0], clrGn[1], clrGn[2], type = 'double3' )
				else:
					confirmDialog( title='Warning!', message='Unsupported nested file node:\n' + each, button=['OK'], defaultButton='OK' )					
				
				p2d = listConnections( each + '.uvCoord' )[0]

				cvr = getAttr( p2d + '.coverage' )[0]
				trsFr = getAttr( p2d + '.translateFrame' )[0]
				rotFr = getAttr( p2d + '.rotateFrame' )
				mirUV = (getAttr( p2d + '.mirrorU' ), getAttr( p2d + '.mirrorV' ))
				wrapUV = (getAttr( p2d + '.wrapU' ), getAttr( p2d + '.wrapV' ))
				stag = getAttr( p2d + '.stagger' )
				repUV = getAttr( p2d + '.repeatUV' )[0]
				off = getAttr( p2d + '.offset' )[0]
				rotUV = getAttr( p2d + '.rotateUV' )
				noiseUV = getAttr( p2d + '.noiseUV' )[0]
				
				out = aiImg + '.outColor'
				if cvr != (1.0, 1.0) or trsFr != (0.0, 0.0) or rotFr != 0.0 or mirUV != (False, False) or wrapUV != (True, True) or stag != False or repUV != (1.0, 1.0) or off != (0.0, 0.0) or rotUV != 0.0 or noiseUV != (0.0, 0.0):
					uv = shadingNode( 'aiUvTransform', asUtility = True, name = eachName[:-7] + 'aiUvTransform' )
					connectAttr( out, uv + '.passthrough' )

					setAttr( uv + '.coverage', cvr[0], cvr[1] )
					setAttr( uv + '.translateFrame', trsFr[0], trsFr[1] )
					setAttr( uv + '.rotateFrame', rotFr )
					setAttr( uv + '.mirrorU', mirUV[0] )
					setAttr( uv + '.mirrorV', mirUV[1] )
					setAttr( uv + '.wrapFrameU', (1-wrapUV[0]) )
					setAttr( uv + '.wrapFrameV', (1-wrapUV[1]) )
					setAttr( uv + '.stagger', stag )
					setAttr( uv + '.repeat', repUV[0], repUV[1] )
					setAttr( uv + '.offset', off[0], off[1] )
					setAttr( uv + '.rotate', rotUV )
					setAttr( uv + '.noise', noiseUV[0], noiseUV[1] )
					
					out = uv + '.outColor'
				
				for conn in outConns:
					if conn[0][-9:] == '.outAlpha' and '__normal.' in filePath:
						connectAttr( aiImg + '.outAlpha', conn[1], force = True )
					elif conn[0][-9:] == '.outColor':
						connectAttr( out, conn[1], force = True )
					elif conn[0][-10:-1] == '.outColor' or conn[0][-9:] == '.outAlpha':
						ch = conn[0][-1]
						if conn[0][-9:] == '.outAlpha':
							ch = 'A'
						rgbaToFloat = eachName + '__aiRgbaToFloat_' + ch
						if rgbaToFloat not in rgbaToFloatList:
							rgbaToFloat = shadingNode( 'aiRgbaToFloat', asUtility = True, name = rgbaToFloat )
							setAttr( rgbaToFloat + '.mode', 5 + ['R', 'G', 'B', 'A'].index(ch) )
							connectAttr( out, rgbaToFloat + '.input' )
							rgbaToFloatList.append( rgbaToFloat )
						connectAttr( rgbaToFloat + '.outValue', conn[1], force = True )

				toDelete.append( each )
				toDelete.append( p2d )
				
			# OTHER REPLACEMENTS AND RGB/XYZ CONNECTIONS > FLOAT
			elif nodeType( each ) not in [ 'place2dTexture' ]:
				if nodeType( each ) == "gammaCorrect":
					aiGamma = shadingNode( 'aiColorCorrect', asUtility = True, name = each + '__aiColorCorrect' )
					for conn in inConns:
						connectAttr( conn[1], aiGamma + '.input' )
					for conn in outConns:
						gammaDict = { 'e':'', 'X':'R', 'Y':'G', 'Z':'B' }
						connectAttr( aiGamma + '.outColor' + gammaDict[conn[0][-1]], conn[1], force=True )
					gVal = [getAttr(each + '.gammaX'), getAttr(each + '.gammaY'), getAttr(each + '.gammaZ')]
					if gVal[0] != gVal[1] or gVal[0] != gVal[2]:
						confirmDialog( title='Warning!', message='Gamma has different values! Using first one:\n' + each, button=['OK'], defaultButton='OK' )
					setAttr( aiGamma + '.gamma', gVal[0] )
					delete( each )
					each = aiGamma
					outConns = listConnections( each, s = False, d = True, c = True, p = True )
					outConns = [outConns[i:i+2] for i in range( 0, len(outConns), 2 )]

				for conn in outConns:
					node = conn[0].split('.')[0]
					attr = conn[0].split('.')[-1]
					parentAttr = attributeQuery( attr, node = node, listParent = True )
					if parentAttr != None:
						rgbaToFloat = node + '__aiRgbaToFloat_' + attr[-1]
						if rgbaToFloat not in rgbaToFloatList:
							rgbaToFloat = shadingNode( 'aiRgbaToFloat', asUtility = True, name = rgbaToFloat )
							if attr[-1] in ['R', 'G', 'B']:
								setAttr( rgbaToFloat + '.mode', 5 + ['R', 'G', 'B'].index(attr[-1]) )
							elif attr[-1] in ['X', 'Y', 'Z']:
								setAttr( rgbaToFloat + '.mode', 5 + ['X', 'Y', 'Z'].index(attr[-1]) )
							else:
								confirmDialog( title='Warning!', message='Unsupported channel:\n' + conn[0], button=['OK'], defaultButton='OK' )
							connectAttr( node + '.' + parentAttr[0], rgbaToFloat + '.input' )
							rgbaToFloatList.append( rgbaToFloat )
						connectAttr( rgbaToFloat + '.outValue', conn[1], force = True )

	# DELETE ORPHANED NODES
	for each in toDelete:
		legitConns = 0
		for conn in listConnections( each, s = False, d = True ):
			if nodeType( conn ) not in [ 'nodeGraphEditorInfo', 'defaultTextureList', 'defaultRenderUtilityList' ]:
				legitConns = 1
		if not legitConns:
			delete( each )
