from maya.cmds import *
import maya.mel
import os, os.path
import unicodedata as ud

#####################################################################################################
# SELECT ALL MESHES IN HIERARCHY

def ark_utils_hiGeo():
	select( hierarchy = True )
	selList = ls( selection = True )

	geoList = []
	for each in selList:
		if objectType( each ) == 'mesh':
			geoList.append( each )

	if geoList != []:
		select( geoList, replace = True )
	else:
		select( clear = True )

#####################################################################################################
# SELECT MEGA/GLUK SHADERS ON SELECTED GEOMETRY

def ark_utils_selShd():
	select( hierarchy = True )
	selList = ls( selection = True )

	geoList = []
	for each in selList:
		if objectType( each ) == 'mesh' or objectType( each ) == 'nurbsSurface':
			par = listRelatives( each, allParents = True, fullPath = True )
			if par > 1:
				each = par[0] + '|' + each.split( '|' )[-1]
			if each not in geoList:
				geoList.append( each )

	newList = []
	for each in geoList:
		conns = listConnections( each, s = False, d = True, type = 'shadingEngine' )
		conns = list( set( conns ) )
		for eachConn in conns:
			hist = listHistory( eachConn )
			for eachHist in hist:
				if objectType( eachHist ) == 'p_MegaTK' or objectType( eachHist ) == 'p_HairTK' or objectType( eachHist ) == 'gluk_hair':
					if eachHist not in newList:
						newList.append( eachHist )

	if newList != []:
		select( newList, noExpand = True, replace = True )
	else:
		select( clear = True )

#####################################################################################################
# SELECT SHADING GROUPS ON SELECTED GEOMETRY

def ark_utils_selSG():
	select( hierarchy = True )
	selList = ls( selection = True )

	geoList = []
	for each in selList:
		if objectType( each ) == 'mesh' or objectType( each ) == 'nurbsSurface':
			par = listRelatives( each, allParents = True, fullPath = True )
			if par > 1:
				each = par[0] + '|' + each.split( '|' )[-1]
			if each not in geoList:
				geoList.append( each )

	newList = []
	for each in geoList:
		conns = listConnections( each, s = False, d = True, type = 'shadingEngine' )
		conns = list( set( conns ) )
		for eachConn in conns:
			hist = listHistory( eachConn )
			for eachHist in hist:
				if objectType( eachHist ) == 'shadingEngine':
					if eachHist not in newList:
						newList.append( eachHist )

	if 'forestGeoShader' in listNodeTypes( 'rendernode/mentalray/geometry' ):
		allPar = []
		for each in geoList:
			allPar += listRelatives( each, allParents = True, fullPath = True )
		allPar = list( set( allPar ) )

		for par in allPar:
			allFst = listConnections( par + '.miGeoShader', s = True, d = False, type = 'forestGeoShader' )
			if allFst != None:
				for fst in allFst:
					allSg = listConnections( fst + '.material', s = True, d = False, type = 'shadingEngine' )
					if allSg != None:
						for sg in allSg:
							if sg not in newList:
								newList.append( sg )

	if newList != []:
		select( newList, noExpand = True, replace = True )
	else:
		select( clear = True )

#####################################################################################################
# ASSIGN A SHADER TO SELECTED SHADINGGROUPS VIA OVERRIDES

def ark_utils_shdToSG():
	selList = ls( selection = True )
	
	prompt = promptDialog(
		title = 'Assign Shader to SGs',
		message = 'Input shader name:',
		button = [ 'OK', 'Cancel' ],
		defaultButton = 'OK',
		cancelButton = 'Cancel',
		dismissString = 'Cancel' )
	
	shd = ''
	if prompt == 'OK':
		shd = promptDialog( query = True, text = True )
	
		if objExists( shd ):
			for each in selList:
				editRenderLayerAdjustment( each + '.aiSurfaceShader' )
				if not isConnected( shd + '.outColor', each + '.aiSurfaceShader' ):
					connectAttr( shd + '.outColor', each + '.aiSurfaceShader', force = True )
				
#####################################################################################################
# SET IRRADIANCE FOR ALL SHADERS TO 1/PI

def ark_utils_set318():
	selList = ls( type = 'p_MegaTK' )
	selList += ls( type = 'p_HairTK' )
	selList += ls( type = 'eyeIrisMaterial' )

	for each in selList:
		setAttr( each + '.cInd', 0.318, 0.318, 0.318, type = 'double3' )

#####################################################################################################
# SELECT ALL NODES BY TYPE

def ark_utils_selectByType( nodeType ):
	if nodeType == 'orig':
		selList = ls( type = 'mesh', io = True )
		if selList != []:
			select( selList, replace = True )
	else:
		selList = ls( type = nodeType )
		if selList != []:
			select( selList, replace = True )

#####################################################################################################
# SELECT ALL ORIGS WITHOUT INPUT CONNECTIONS, TOGGLE MAKE NON-INTERMEDIATE

def ark_utils_origs():
	selList = ls( sl = True )

	if selList == []:
		selList = ls( type = 'mesh', io = True )

		outList = []
		for each in selList:
			if listConnections( each, s = True, d = False ) == None:
				setAttr( each + '.intermediateObject', 0 )
				outList.append( each )

		select( outList, replace = True )

	else:
		for each in selList:
			setAttr( each + '.intermediateObject', 1 )

		select( cl = True )

#####################################################################################################
# CHANGE NODES CATEGORY (MATERIAL, TEXTURE, UTILITY, etc.)

def ark_utils_list():
	util = 'ark_utils_list'
	if window( util + '_win', exists = True ):
		deleteUI( util + '_win' )

	window( util + '_win', title = 'Change Category', sizeable = False )

	columnLayout( adj = True, columnAttach = ['both', 3] )

	rowLayout( numberOfColumns = 3 )

	chbWd = 90
	chbHt = 20
	checkBox( util + '_material_CHB', label = 'Material', value = False, width = chbWd, height = chbHt )
	checkBox( util + '_texture_CHB', label = 'Texture', value = False, width = chbWd, height = chbHt )
	checkBox( util + '_utility_CHB', label = 'Utility', value = False, width = chbWd, height = chbHt )

	setParent( '..' )

	button( util + '_add_BTN', label = 'Set', command = util + '_do( "' + util + '" )' )

	showWindow( util + '_win' )

	window( util + '_win', edit = True, width = 270, height = 50 )

def ark_utils_list_do( util ):
	lstDict = {'material':['defaultShaderList', 'shaders'], 'texture':['defaultTextureList', 'textures'], 'utility':['defaultRenderUtilityList', 'utilities'] }

	selList = ls( sl = True )

	for lst in lstDict.keys():
		val = checkBox( util + '_' + lst + '_CHB', query = True, value = True )

		for	each in selList:
			conns = listConnections( each + '.message', s = False, d = True, type = lstDict[lst][0], c = False, p = True )

			if val:
				if conns == None:
					connectAttr( each + '.message', lstDict[lst][0] + '1.' + lstDict[lst][1], na = True )
			else:
				if conns != None:
					disconnectAttr( each + '.message', conns[0] )

#####################################################################################################
# ADD MISSS EXPRESSION

def ark_utils_misssExpr():
	selList = ls( type = 'misss_fast_lmap_maya' )

	lmapsRes = ''
	for each in selList:
		tex = listConnections( each + '.lightmap', s = True, d = False )
		if tex != None:
			lmapsRes += '\n' + tex[0] + '.miWidth = defaultResolution.width * 2 * 0.5;'
			lmapsRes += '\n' + tex[0] + '.miHeight = defaultResolution.height * 0.5;'

	expression( s = lmapsRes, name = '_misss_expr' )

#####################################################################################################
# MOVE OBJECTS FROM NAMESPACE TO ROOT AND DELETE THIS NAMESPACE

def ark_utils_nmRemove():

	prompt = promptDialog(
		title = 'Remove Namespace',
		message = 'Namespace to remove (* for all):',
		button = [ 'OK', 'Cancel' ],
		defaultButton = 'OK',
		cancelButton = 'Cancel',
		dismissString = 'Cancel' )
	
	line = ''
	if prompt == 'OK':
		line = promptDialog( query = True, text = True )

	if line != '':
		if line == '*':
			namespace( set = ':' )
			allNm = namespaceInfo( lon = True )
			allNm.remove( 'UI' )
			allNm.remove( 'shared' )
			while allNm != []:
				for nm in allNm:
					namespace( mv = ( nm, ':' ), f = True )
					namespace( rm = nm )
				allNm = namespaceInfo( lon = True )
				allNm.remove( 'UI' )
				allNm.remove( 'shared' )
		else:
			nms = line.split( ':' )
			for nm in nms:
				namespace( mv = ( nm, ':' ), f = True )
				namespace( rm = nm )

#####################################################################################################
# OVERRIDE CAST/RECEIVE ATTRIBUTES (VISIBLE IN TRANSPARENCY, SHADOW) ON SELECTED

def ark_utils_castReceiveOverride( mode, attr ):
	selList = ls( sl = True )

	rLayer = editRenderLayerGlobals( query = True, crl = True )
	if rLayer != 'defaultRenderLayer':
		for each in selList:
			eachTr = each
			if nodeType( each ) == 'mesh':
				eachTr = listRelatives( each, parent = True, f = True )[0]

			geoConn = listConnections( eachTr + '.miGeoShader', s = True, d = False )

			if mode == 'set':
				editRenderLayerAdjustment( each + '.' + attr[0] )
				setAttr( each + '.' + attr[0], 0 )

				if geoConn != None:
					if nodeType( geoConn[0] ) == 'forestGeoShader':
						editRenderLayerAdjustment( geoConn[0] + '.' + attr[1] )
						setAttr( geoConn[0] + '.' + attr[1], 2 )
						if attr[1] == 'shadow':
							editRenderLayerAdjustment( geoConn[0] + '.use_various_colors' )
							setAttr( geoConn[0] + '.use_various_colors', 0 )

			elif mode == 'remove':
				editRenderLayerAdjustment( each + '.' + attr[0], remove = True )

				if geoConn != None:
					if nodeType( geoConn[0] ) == 'forestGeoShader':
						editRenderLayerAdjustment( geoConn[0] + '.' + attr[1], remove = True )
						if attr[1] == 'shadow':
							editRenderLayerAdjustment( geoConn[0] + '.use_various_colors', remove = True )
	else:
		confirmDialog( title = 'Error...', message = 'Switch to any render layer!', button = [ 'OK' ] )
	
	select( cl = True )

#####################################################################################################
# CREATES A SET OF SHADERS FOR RGB-MASKS, SHADOW AND OCCLUSION CATCHING

def ark_utils_auxShaders( shdType ):
	selList = ls( sl = True )
	
	# RGBK SHADERS
	if not objExists( 'red_SHD' ):
		shd = shadingNode( shdType, asShader = True, name = 'red_SHD' )
		setAttr( shd + '.color', 1, 0, 0, type = 'double3' )
	if not objExists( 'green_SHD' ):
		shd = shadingNode( shdType, asShader = True, name = 'green_SHD' )
		setAttr( shd + '.color', 0, 1, 0, type = 'double3' )
	if not objExists( 'blue_SHD' ):
		shd = shadingNode( shdType, asShader = True, name = 'blue_SHD' )
		setAttr( shd + '.color', 0, 0, 1, type = 'double3' )
	if not objExists( 'black_SHD' ):
		shd = shadingNode( shdType, asShader = True, name = 'black_SHD' )
		setAttr( shd + '.color', 0, 0, 0, type = 'double3' )
	
	# OCCL SHADER
	if not objExists( 'occl_SHD' ):
		shd = shadingNode( shdType, asShader = True, name = 'occl_SHD' )
	if not objExists( 'occl_tex' ):
		tex = shadingNode( 'mib_amb_occlusion', asTexture = True, name = 'occl_tex' )
		setAttr( tex + '.samples', 64 )
		setAttr( tex + '.max_distance', 50 )
		setAttr( tex + '.id_inclexcl', -13 )
		setAttr( tex + '.id_nonself', 13 )
	if not isConnected( 'occl_tex.outValue', 'occl_SHD.color' ):
		connectAttr( 'occl_tex.outValue', 'occl_SHD.color', force = True )
	
	# SHADOW SHADER
	if not objExists( 'shadow_SHD' ):
		shd = shadingNode( 'mip_matteshadow', asShader = True, name = 'shadow_SHD' )
		setAttr( shd + '.background', 1, 1, 1, type = 'double3' )
		setAttr( shd + '.ao_on', 0 )

	if selList != []:
		select( selList, replace = True )
	else:
		select( cl = True )

#####################################################################################################
# MOVE PIVOT FOR SELECTED OBJECTS

def ark_utils_placePivot( mode ):
	selList = ls( sl = True, fl = True )

	if mode == 'vtxCenter':
		obj = selList[0].split('.')[0]

		i = 0
		pos = [0,0,0]
		for each in selList:
			tr = pointPosition( each, world = True )
			pos = [pos[0]+tr[0], pos[1]+tr[1], pos[2]+tr[2]]
			i += 1
		pos = [pos[0]/i, pos[1]/i, pos[2]/i]
		xform( obj, piv = pos, ws = True )
		#move( -pos[0], -pos[1], -pos[2], obj, r = True )

	else:
		for each in selList:
			piv = pointPosition( each + '.rotatePivot', w = True )
			if mode == 'origin':
				xform( each, piv = (0, 0, 0), ws = True )
			elif mode == 'base':
				xform( each, piv = (piv[0], xform( each, query = True, ws = True, bb = True )[1], piv[2]), ws = True )
			elif mode == 'top':
				xform( each, piv = (piv[0], xform( each, query = True, ws = True, bb = True )[4], piv[2]), ws = True )
			elif mode == 'y0':
				xform( each, piv = (piv[0], 0, piv[2]), ws = True )

#####################################################################################################
# CREATE MISSS NETWORK

def ark_utils_misssNetwork( mode ):
	prompt = promptDialog(
		title = 'Network Name',
		message = 'Enter Network Prefix:',
		button = [ 'OK', 'Cancel' ],
		defaultButton = 'OK',
		cancelButton = 'Cancel',
		dismissString = 'Cancel' )
	
	name = ''
	if prompt == 'OK':
		name = promptDialog( query = True, text = True )

	if name != '':
		tex = shadingNode( 'mentalrayTexture', asTexture = True, name = name + '_lightmap' )
		setAttr( tex + '.miWritable', 1 )
		setAttr( tex + '.miDepth', 4 )
		setAttr( tex + '.miWidth', 2048 )
		setAttr( tex + '.miHeight', 1024 )

		norm = shadingNode( 'misss_set_normal', asUtility = True, name = name + '_set_normal' )

		diff = shadingNode( 'mia_material_x', asShader = True, name = name + '_diffuse_SHD' )
		setAttr( diff + '.diffuse', 0.95, 0.95, 1.0, type = 'double3' )
		setAttr( diff + '.reflectivity', 0 )
		setAttr( diff + '.ao_on', 1 )
		setAttr( diff + '.ao_samples', 32 )
		setAttr( diff + '.ao_distance', 5.0 )

		mia = shadingNode( 'mia_material_x', asShader = True, name = name + '_spec_SHD' )
		setAttr( mia + '.diffuse', 0, 0, 0, type = 'double3' )
		setAttr( mia + '.diffuse_weight', 0 )

		lmap = shadingNode( 'misss_fast_lmap_maya', asUtility = True, name = name + '_lmap' )
		connectAttr( tex + '.message', lmap + '.lightmap' )

		if mode == 'skin' or mode == 'skin2':
			shdType = 'shader'
			if mode == 'skin2':
				shdType = 'shader2'

			shal = shadingNode( 'misss_fast_' + shdType + '_x', asUtility = True, name = name + '_shallow_SSS' )
			connectAttr( tex + '.message', shal + '.lightmap' )
			connectAttr( diff + '.message', shal + '.diffuse_illum' )
			setAttr( shal + '.screen_composit', 0 )
			setAttr( shal + '.samples', 128 )
			setAttr( shal + '.diffuse_weight', 0.3 )
			setAttr( shal + '.front_sss_color', 1.0, 0.85, 0.6, type = 'double3' )
			setAttr( shal + '.front_sss_weight', 0.5 )
			setAttr( shal + '.front_sss_radius', 8 )
			setAttr( shal + '.back_sss_color', 0, 0, 0, type = 'double3' )
			setAttr( shal + '.back_sss_weight', 0 )
			setAttr( shal + '.back_sss_radius', 0 )

			deep = shadingNode( 'misss_fast_' + shdType + '_x', asShader = True, name = name + '_SHD' )
			connectAttr( tex + '.message', deep + '.lightmap' )
			connectAttr( norm + '.outValue', deep + '.bump' )
			connectAttr( deep + '.result', mia + '.additional_color' )
			connectAttr( shal + '.result', deep + '.diffuse_illum' )
			setAttr( deep + '.screen_composit', 0 )
			setAttr( deep + '.samples', 128 )
			setAttr( deep + '.diffuse_weight', 1.0 )
			setAttr( deep + '.front_sss_color', 0.95, 0.5, 0.2, type = 'double3' )
			setAttr( deep + '.front_sss_weight', 0.4 )
			setAttr( deep + '.front_sss_radius', 25 )
			setAttr( deep + '.back_sss_color', 0.7, 0.1, 0.1, type = 'double3' )
			setAttr( deep + '.back_sss_weight', 0.5 )
			setAttr( deep + '.back_sss_radius', 25 )
			setAttr( deep + '.back_sss_depth', 25 )

		elif mode == 'simple' or mode == 'simple2':
			shdType = 'shader'
			if mode == 'simple2':
				shdType = 'shader2'

			shd = shadingNode( 'misss_fast_' + shdType + '_x', asShader = True, name = name + '_SHD' )
			connectAttr( tex + '.message', shd + '.lightmap' )
			connectAttr( diff + '.message', shd + '.diffuse_illum' )
			connectAttr( norm + '.outValue', shd + '.bump' )
			connectAttr( shd + '.result', mia + '.additional_color' )
			setAttr( shd + '.screen_composit', 0 )
			setAttr( shd + '.samples', 128 )
			setAttr( shd + '.diffuse_weight', 0.5 )
			setAttr( shd + '.front_sss_color', 0.8, 0.4, 0.1, type = 'double3' )
			setAttr( shd + '.front_sss_weight', 0.5 )
			setAttr( shd + '.front_sss_radius', 10 )
			setAttr( shd + '.back_sss_color', 0.8, 0.4, 0.1, type = 'double3' )
			setAttr( shd + '.back_sss_weight', 0.5 )
			setAttr( shd + '.back_sss_radius', 10 )
			setAttr( shd + '.back_sss_depth', 10 )

#####################################################################################################
# TRANSFER ALL CONNECTIONS FROM ONE NODE TO ANOTHER

def ark_utils_transferConnections( mode ):
	selList = ls( selection = True )

	#INCOMING CONNECTIONS
	if mode == 'both' or mode == 'in':
		conns = listConnections( selList[0], source = True, destination = False, plugs = True, connections = True )
		if conns != None:
			for i in xrange(0, len(conns), 2 ):
				try:
					connectAttr( conns[i+1], selList[1] + conns[i][conns[i].find('.'):], force = True )
				except:
					print( 'Not connected: ' + conns[i+1] + ' to ' + selList[1] + conns[i][conns[i].find('.'):] )

	#OUTGOING CONNECTIONS
	if mode == 'both' or mode == 'out':
		conns = listConnections( selList[0], source = False, destination = True, plugs = True, connections = True )
		if conns != None:
			for i in xrange(0, len(conns), 2 ):
				if not conns[i+1].split('.')[0] in [ 'defaultTextureList1', 'defaultRenderUtilityList1', 'defaultShaderList1' ]: 
					try:
						connectAttr( selList[1] + conns[i][conns[i].find('.'):], conns[i+1], force = True  )
					except:
						print( 'Not connected: ' + selList[1] + conns[i][conns[i].find('.'):] + ' to ' +  conns[i+1] )

#####################################################################################################
# SET EPISODE LENGTH OF ALL ANIMATED FORESTGEOSHADERS TO THE LENGTH OF THE SCENE BY TIMELINE

def ark_utils_forestLength():
	for each in ls( type = 'forestGeoShader' ):
		if getAttr( each + '.object_filename' ).find( '#' ) > -1:
			setAttr( each + '.episode_length', int( playbackOptions( query = True, max = True ) ) )


#####################################################################################################
# RETURN STARTUP CAMERAS TO DEFAULT

def ark_utils_startupCamerasFix():
	setAttr( 'persp.t', 2400, 1800, 2400, type = 'double3' )
	setAttr( 'persp.r', -28, 45, 0, type = 'double3' )
	setAttr( 'persp.s', 1, 1, 1, type = 'double3' )
	setAttr( 'persp.v', 0 )
	setAttr( 'persp.nearClipPlane', 1.0 )
	setAttr( 'persp.farClipPlane', 10000.0 )
	setAttr( 'persp.backgroundColor', 0, 0, 0, type = 'double3' )
	setAttr( 'persp.filmFit', 1 )
	setAttr( 'persp.displayGateMask', 1 )
	setAttr( 'persp.displayGateMaskColor', 0.5, 0.5, 0.5, type = 'double3' )
	setAttr( 'persp.overscan', 1.95 )

	setAttr( 'top.t', 0, 5000, 0, type = 'double3' )
	setAttr( 'top.r', -90, 0, 0, type = 'double3' )
	setAttr( 'top.s', 1, 1, 1, type = 'double3' )
	setAttr( 'top.v', 0 )
	setAttr( 'top.orthographic', 1 )
	setAttr( 'top.orthographicWidth', 1000 )
		
	setAttr( 'front.t', 0, 0, 5000, type = 'double3' )
	setAttr( 'front.r', 0, 0, 0, type = 'double3' )
	setAttr( 'front.s', 1, 1, 1, type = 'double3' )
	setAttr( 'front.v', 0 )
	setAttr( 'front.orthographic', 1 )
	setAttr( 'front.orthographicWidth', 1000 )

	setAttr( 'side.t', 5000, 0, 0, type = 'double3' )
	setAttr( 'side.r', 0, 90, 0, type = 'double3' )
	setAttr( 'side.s', 1, 1, 1, type = 'double3' )
	setAttr( 'side.v', 0 )
	setAttr( 'side.orthographic', 1 )
	setAttr( 'side.orthographicWidth', 1000 )

#####################################################################################################
# SET ALL TEXTURE PATHS TO LOCAL DIRECTORY AND ENABLE IGNORE COLORSPACE FILE RULES

def ark_utils_localizeFileNodes( dirPath ):
	for each in ls( type = 'file' ):
		setAttr( each + '.ignoreColorSpaceFileRules', 1 )
		filePath = getAttr( each + '.fileTextureName' )
		if '<UDIM>' not in filePath:
			if '%root%' not in filePath:
				setAttr( each + '.fileTextureName', dirPath + '/' + filePath.replace( '\\', '/' ).split( '/' )[-1], type = 'string' )

#####################################################################################################
# SET ALL FUR MAPS TO LOCAL DIRECTORY

def ark_utils_localizeFurMaps( dirPath ):
	attrs = [   'BaseColorMap', 
				'TipColorMap', 
				'BaseAmbientColorMap', 
				'TipAmbientColorMap', 
				'SpecularColorMap',
				'SpecularSharpnessMap',
				'LengthMap',
				'BaldnessMap',
				'InclinationMap',
				'RollMap',
				'PolarMap',
				'BaseOpacityMap',
				'TipOpacityMap',
				'BaseWidthMap',
				'TipWidthMap',
				'BaseCurlMap',
				'TipCurlMap',
				'ScraggleMap',
				'ScraggleFrequencyMap',
				'ScraggleCorrelationMap',
				'ClumpingMap',
				'ClumpingFrequencyMap',
				'ClumpShapeMap',
				'SegmentsMap',
				'AttractionMap',
				'OffsetMap'
				]

	for each in ls( type = 'FurDescription' ):
		for attr in attrs:
			for i in getAttr( each + '.' + attr, mi = True ):
				filePath = getAttr( each + '.' + attr + '[' + str(i) + ']' )
				if filePath != None and filePath != '':
					setAttr( each + '.' + attr + '[' + str(i) + ']', dirPath + '/' + filePath.replace( '\\', '/' ).split( '/' )[-1], type = 'string' )

#####################################################################################################
# ADD ATTRIBUTES FOR HAIR/FUR TO EXPORT CUSTOM MR MATERIAL

def ark_utils_hairMtlAttrs( mode ):
	trList = []

	if mode == 'selection':
		for each in ls( sl = True ):
			if nodeType( each ) == 'transform':
				trList.append( each )
	elif mode == 'all':
		for each in ls( type = 'pfxHair' ) + ls( type = 'FurFeedback' ):
			trList.append( listRelatives( each, parent = True )[0] )

	for each in trList:
		if not attributeQuery( 'miExportMaterial', exists = True, node = each ):
			addAttr( each, ln = 'miExportMaterial', at = 'bool', dv = 1 )
		if not attributeQuery( 'miMaterial', exists = True, node = each ):
			addAttr( each, ln = 'miMaterial', at = 'message' )

#####################################################################################################
# ADD LOCAL/FILTER ATTRIBUTES FOR FILE NODES

def ark_utils_locFiltTexAttrs( mode ):
	trList = []

	if mode == 'selection':
		for each in ls( sl = True ):
			if nodeType( each ) == 'file':
				trList.append( each )
	elif mode == 'all':
		trList = ls( type = 'file' )

	for each in trList:
		if not attributeQuery( 'miLocal', exists = True, node = each ):
			addAttr( each, ln = 'miLocal', at = 'bool', dv = 1 )
		if not attributeQuery( 'miFilter', exists = True, node = each ):
			addAttr( each, ln = 'miFilter', at = 'bool', dv = 1 )
		if not attributeQuery( 'miFilterSize', exists = True, node = each ):
			addAttr( each, ln = 'miFilterSize', at = 'float', dv = 1.0 )

		setAttr( each + '.filterType', 1 )
		setAttr( each + '.preFilter', 0 )
		setAttr( each + '.miOverrideConvertToOptim', 1 )
		setAttr( each + '.miConvertToOptim', 0 )
		setAttr( each + '.miUseEllipticalFilter', 0 )

#####################################################################################################
# ADD SUFFIX TO SELECTED NODES

def ark_utils_addSuffix( suff='' ):
	if suff == '':
		prompt = promptDialog(
			title = 'Add Suffix',
			message = 'Type suffix to add:',
			text = '_geo',
			button = [ 'OK', 'Cancel' ],
			defaultButton = 'OK',
			cancelButton = 'Cancel',
			dismissString = 'Cancel' )
		
		suff = ''
		if prompt == 'OK':
			suff = promptDialog( query = True, text = True )

	if suff != '':
		for each in ls( sl = True ):
			rename( each, each + suff )

#####################################################################################################
# EXPORT SELECTED OBJECTS TO SEPARATE OBJ FILES

def ark_utils_objExport( named=False ):
	selList = ls( sl=True )

	dir = workspace( query = True, rd = True )

	print( 'MESHES EXPORTED TO OBJS:' )
	for each in selList:
		obj = each.replace('|','_').replace(':','_')

		if named:
			prompt = promptDialog(
				title = 'OBJ name',
				message = 'Type OBJ name:',
				text = obj,
				button = [ 'OK', 'Cancel' ],
				defaultButton = 'OK',
				cancelButton = 'Cancel',
				dismissString = 'Cancel' )
			
			obj = ''
			if prompt == 'OK':
				obj = promptDialog( query = True, text = True )

		if obj != '':
			select( each, replace = True )
			par = listRelatives( each, parent = True, fullPath = True )
			if par != None:
				parent( each, world = True )
			file( dir + 'data/' + obj, force = True, options = 'groups=1;ptgroups=1;materials=0;smoothing=1;normals=1', typ = 'OBJexport', pr = True, es = True )
			if par != None:
				parent( each, par[0] )
			print( each + ' -> ' + dir + 'data/' + obj + '.obj' )

	select( selList, replace = True )

#####################################################################################################
# FIX SHAPE NAMES (MESH ONLY)

def ark_utils_fixShapeName():
	selList = ls( sl = True )

	for each in selList:
		shps = listRelatives( each, shapes = True )
		if shps != None:
			for shp in shps:
				if shp[-4:] == 'Orig':
					rename( shp, each + 'ShapeOrig' )
				else:
					rename( shp, each + 'Shape' )

#####################################################################################################
# CONVERT TO INSTANCES

def ark_utils_convertToInstances():
	selList = ls( sl = True )

	for each in selList[1:]:
		par = listRelatives( each, parent = True )[0]
		inst = instance( selList[0], name = 'tmp_geo' )[0]
		parent( inst, each )
		makeIdentity( inst, apply = False, t = True, r = True, s = True )
		parent( inst, par )
		delete( each )
		rename( inst, each )
	select( selList, replace = True )

#####################################################################################################
# REMOVE UNKNOWN PLUGINS

def ark_utils_removeUnknownPlugins():
	plugs = unknownPlugin( query = True, list = True )

	if plugs == None:
		plugs = 'No unknown plugins found!'
	else:
		for each in plugs:
			unknownPlugin( each, remove = True )
		plugs = 'Removed unknown plugins:\n\n' + '\n'.join(plugs)

	confirmDialog( title = 'Done!', message = plugs, button = 'OK' )

#####################################################################################################
# UNLOCK AND DELETE UNKNOWN NODES

def ark_utils_deleteUnknownNodes():
	unkNodes = ls( type = 'unknown' )

	if unkNodes != []:
		lockNode( unkNodes, lock = False )
		delete( unkNodes )
		unkNodes = 'Removed unknown nodes:\n\n' + '\n'.join(unkNodes)
	else:
		unkNodes = 'No unknown nodes found!'

	confirmDialog( title = 'Done!', message = unkNodes, button = 'OK' )

#####################################################################################################
# CONVERT COLOR VALUES IN 1.0/255 FORMAT INTO LINEAR/SRGB AND ROUND THE RESULT

def ark_utils_linConvert( clr, to='lin', mode='1.0', rnd=3 ):
	if mode == '255':
		clr = [clr[0]/256.0, clr[1]/256.0, clr[2]/256.0]

	pw = 2.2
	if to == 'sRGB':
		pw = 0.4545

	outClr = [round(pow(clr[0],pw),rnd), round(pow(clr[1],pw),rnd), round(pow(clr[2],pw),rnd)]

	return outClr

#####################################################################################################
# CHECK FOR SAME NAMES

def ark_utils_findSameNames():
	feedback = []
	for each in ls( dag = True ):
		if each.find( '|' ) > -1:
			try:
				tmp = listRelatives( each.split('|')[-1], allParents = True )
			except:
				feedback.append( each )

	feedback.sort( key = lambda x: x.split('|')[-1] )

	if feedback != []:
		msg = 'Selecting objects with the same name:\n'
		print( msg )
		print( '' )
		for each in feedback:
			msg += '\n' + each
			print( each )
		confirmDialog( title = 'Result', message = msg, button = [ 'OK' ] )
		select( feedback, replace = True )
	else:
		confirmDialog( title = 'Result', message = 'No objects with the same name found!', button = [ 'OK' ] )

#####################################################################################################
# CHECK NON-UNICODE NAMES AND FILE NODE PATHS (CODE SOMEWHERE FROM WEB)

def ark_utils_findNonUnicode():
	latin_letters = {}

	def ark_utils_is_latin( uchr ):
		try: return latin_letters[uchr]
		except KeyError:
			 return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))

	def ark_utils_only_roman_chars( unistr ):
		return all(ark_utils_is_latin(uchr)
			for uchr in unistr
			if uchr.isalpha())

	feedback1 = []
	for each in ls( type = 'file' ):
		filePath = getAttr( each + '.fileTextureName' )
		if not ark_utils_only_roman_chars( filePath ):
			feedback1.append( each )

	feedback2 = []
	for each in ls():
		if not ark_utils_only_roman_chars( each ):
			feedback2.append( each )

	if feedback1 != [] or feedback2 != []:
		msg1 = 'Paths with non-unicode characters:\n'
		print( msg1 )
		print( '' )
		if feedback1 != []:
			for each in feedback1:
				msg1 += '\n' + each
				print( each )
		else:
			msg1 += '\n----'
			print( '----' )

		msg2 = '\n\nNode names with non-unicode characters:\n'
		print( msg2 )
		print( '' )
		if feedback2 != []:
			for each in feedback2:
				msg2 += '\n' + each
				print( each )
		else:
			msg2 += '\n----'
			print( '----' )

		confirmDialog( title = 'Result', message = (msg1 + msg2), button = [ 'OK' ] )
	else:
		confirmDialog( title = 'Result', message = 'No non-unicode characters found!', button = [ 'OK' ] )

#####################################################################################################
# CREATE NODES NETWORK TEMPLATE

def ark_utils_networkTemplate( mode='arnold5_surface' ):
	prompt = promptDialog(
		title = 'Nodes Network Template',
		message = 'Input network name:',
		button = [ 'OK', 'Cancel' ],
		defaultButton = 'OK',
		cancelButton = 'Cancel',
		dismissString = 'Cancel' )

	netName = ''
	if prompt == 'OK':
		netName = promptDialog( query = True, text = True )

	if netName != '':
		place2d_to_file_conns = (('outUV', 'uvCoord'),
								('outUvFilterSize', 'uvFilterSize'),
								('coverage', 'coverage'),
								('translateFrame', 'translateFrame'),
								('rotateFrame', 'rotateFrame'),
								('mirrorU', 'mirrorU'),
								('mirrorV', 'mirrorV'),
								('stagger', 'stagger'),
								('wrapU', 'wrapU'),
								('wrapV', 'wrapV'),
								('repeatUV', 'repeatUV'),
								('vertexUvOne', 'vertexUvOne'),
								('vertexUvTwo', 'vertexUvTwo'),
								('vertexUvThree', 'vertexUvThree'),
								('vertexCameraOne', 'vertexCameraOne'),
								('noiseUV', 'noiseUV'),
								('offset', 'offset'),
								('rotateUV', 'rotateUV'))

		if mode == 'arnold5_surface':
			sg = sets( renderable = True, noSurfaceShader = True, empty = True, name = netName + '_SG' )
			shd = shadingNode( 'aiStandardSurface', asShader = True, name = netName + '_SHD' )
			disp = shadingNode( 'displacementShader', asUtility = True, name = netName + '_DISP' )
			bump = shadingNode( 'bump2d', asUtility = True, name = netName + '__color__bump' )
			specW = shadingNode( 'remapValue', asUtility = True, name = netName + '__specWeight__remap' )
			specR = shadingNode( 'remapValue', asUtility = True, name = netName + '__specRough__remap' )
			clr = shadingNode( 'file', asTexture = True, isColorManaged = True, name = netName + '__color__file' )
			dsp = shadingNode( 'file', asTexture = True, isColorManaged = True, name = netName + '__disp__file' )
			plc = shadingNode( 'place2dTexture', asUtility = True, name = netName + '__place2d' )

			for conn in place2d_to_file_conns:
				connectAttr( plc + '.' + conn[0], clr + '.' + conn[1] )
				connectAttr( plc + '.' + conn[0], dsp + '.' + conn[1] )

			connectAttr( dsp + '.outColorR', disp + '.displacement' )
			connectAttr( clr + '.outColorR', bump + '.bumpValue' )
			connectAttr( clr + '.outColorR', specW + '.inputValue' )
			connectAttr( clr + '.outColorR', specR + '.inputValue' )
			connectAttr( clr + '.outColor', shd + '.baseColor' )
			connectAttr( bump + '.outNormal', shd + '.normalCamera' )
			connectAttr( specW + '.outValue', shd + '.specular' )
			connectAttr( specR + '.outValue', shd + '.specularRoughness' )            
			connectAttr( shd + '.outColor', sg + '.surfaceShader' )
			connectAttr( disp + '.displacement', sg + '.displacementShader' )

			setAttr( clr + '.defaultColor', 0, 0, 0, type = 'double3' )
			setAttr( dsp + '.defaultColor', 0, 0, 0, type = 'double3' )
			setAttr( specW + '.value[0].value_Position', 0.1 )
			setAttr( specW + '.value[1].value_FloatValue', 0.5 )
			setAttr( specR + '.value[0].value_FloatValue', 0.7 )
			setAttr( specR + '.value[1].value_FloatValue', 0.3 )            
			setAttr( bump + '.bumpDepth', 0.3 )
			setAttr( disp + '.aiDisplacementPadding', 0.2 )
			setAttr( shd + '.base', 1.0 )
			setAttr( clr + '.fileTextureName', 'p:/relicts/3d/_textures/misc/gray50.tif', type = 'string' )


#####################################################################################################
# RENAME FILE NODES BASED ON TEXTURE NAMES

def ark_utils_nameFileNodes():
	for each in ls( type = 'file' ):
		fileName = getAttr( each + '.fileTextureName' )

		outName = fileName.split( '/' )[-1]
		outName = outName[:outName.find('.')] + '__file'
		outName = outName[outName.find( '__' )+2:]

		rename( each, outName )

#####################################################################################################
# MAKE A COMBINED MESH FROM SELECTED OBJECTS VIA BRANCH IN NODES NETWORK

def ark_utils_branchCombine():
	selList = ls( sl = True )

	comb = createNode( 'polyUnite' )

	i = 0
	for each in selList:
		connectAttr( each + '.outMesh', comb + '.inputPoly[' + str(i) + ']' )
		connectAttr( each + '.worldMatrix[0]', comb + '.inputMat[' + str(i) + ']' )
		i += 1

	mesh = createNode( 'mesh' )

	connectAttr( comb + '.output', mesh + '.inMesh' )

#####################################################################################################
# BREAKS ALL CONNECTION TO AND FROM SELECTED NODES

def ark_utils_disconnectAll():
	for each in ls( sl = True ):
		inConns = listConnections( each, s = True, d = False, c = True, p = True )
		outConns = listConnections( each, s = False, d = True, c = True, p = True )
		if inConns != None:
			for i in xrange( 0, len(inConns), 2 ):
				try:
					disconnectAttr( inConns[i+1], inConns[i] )
				except:
					pass
		if outConns != None:
			for i in xrange( 0, len(outConns), 2 ):
				try:
					disconnectAttr( outConns[i], outConns[i+1] )
				except:
					pass

#####################################################################################################
# STORE/APPLY ALL ATTRIBUTES

def ark_utils_attrList( path='', read=True ):
	if path == '':
		tmp = os.getenv( 'TEMP' )
		if tmp != None:
			path = tmp + '/attrList.dat'
		else:
			confirmDialog( title = 'Error!', message = 'Path is not defined!', button = [ 'CANCEL' ] )
	elif not os.path.exists( path ):
		if read:
			confirmDialog( title = 'Error!', message = 'File doesn\'t exist!', button = [ 'CANCEL' ] )
	try:
		if read:
			f = open( path, 'r' )
		else:
			f = open( path, 'w' )
	except:
		confirmDialog( title = 'Error!', message = 'Path is invalid!', button = [ 'CANCEL' ] )

	if read:
		for line in f:
			each = line.split()[0]
			data = line[line.find('[')+1:-2].replace('u\'','').replace(', ',' ').replace('\'', '').split()
			for attr in data:
				if attributeQuery( attr.split(':')[0], node = each, exists = True ):
					attrPath = each + '.' + attr.split(':')[0]
					attrVal = attr.split(':')[1]
					if not getAttr( attrPath, lock = True ):
						attrType = getAttr( attrPath, typ = True )
						if attrVal == 'True':
							attrVal = 1
						elif attrVal == 'False':
							attrVal = 0
						try:
							setAttr( attrPath, float(attrVal) )
						except:
							print( 'Cannot set ' + attrPath + ' to ' + str(attrVal) )
	else:
		for each in ls( sl = True ):
			attrList = listAttr( each )

			data = []
			for attr in attrList:
				try:
					attrType = getAttr( each + '.' + attr, type = True )
				except:
					attrType = ''

				if not attrType in [ '', 'attributeAlias' ]:
					try:
						data.append( attr + ':' + str( getAttr( each + '.' + attr ) ) )
						#print( 'Saving ' + each + '.' + str(attr) )
					except:
						print( 'Skipping ' + each + '.' + str(attr) )
				else:
					print( 'Skipping ' + each + '.' + str(attr) )
			f.write( each + ' ' + str(data) + '\n' )

	f.close()

#####################################################################################################
# CHECK IF SAME TEXTURE MAP USES DIFFERENT COLOR SPACES

def ark_utils_imgCSpaceCheck():
	files = {}
	shared = []
	for each in ls( type = 'file' ):
		path = getAttr( each + '.fileTextureName' )
		img = path.split('/')[-1]
		cs = getAttr( each + '.colorSpace' )
		if not img in files.keys():
			files[img] = cs
		else:
			if not cs == files[img]:
				shared.append( img )
				print( 'Map uses different colorSpaces: ' + img )

	if shared != []:
		msg = 'Maps that use different colorSpaces:\n'
		for each in shared:
			msg += '\n' + each
		confirmDialog( title = 'Result', message = msg, button = [ 'OK' ] )
	else:
		confirmDialog( title = 'Result', message = 'No maps share the same colorSpace!', button = [ 'OK' ] )

#####################################################################################################
# GIVEN START TIMECODE, END TIMECODE AND FPS, RETURNS NUMBER OF FRAMES

def ark_utils_clipDuration( start, end, fps ):
    startFrame = sum(f * int(t) for f,t in zip((3600*fps, 60*fps, fps, 1), start.split(':')))
    endFrame = sum(f * int(t) for f,t in zip((3600*fps, 60*fps, fps, 1), end.split(':')))
    return (endFrame - startFrame)

#####################################################################################################
# KEEP SELECTION ONLY FOR NODES THAT DON'T HAVE ANY INPUT OR OUTPUT CONNECTIONS

def ark_utils_unconnected():
	exclList = [ 'characterPartition',
				'defaultColorMgtGlobals',
				'defaultHardwareRenderGlobals',
				'defaultLightList1',
				'defaultRenderUtilityList1',
				'defaultTextureList1',
				'defaultViewColorManager',
				'dynController1',
				'globalCacheControl',
				'hardwareRenderGlobals',
				'hardwareRenderingGlobals',
				'hyperGraphInfo',
				'hyperGraphLayout',
				'ikSystem',
				'lightList1',
				'poseInterpolatorManager',
				'sceneInitializerNode',
				'sequenceManager1',
				'strokeGlobals',
				'time1' ]

	selList = ls( sl = True )
	outList = []
	for each in selList:
		conns = listConnections( each, s = True, d = True )
		if conns == None and each not in exclList:
			outList.append( each )
	select( outList, replace = True )

#####################################################################################################
# REPLACE ALL TEXTURE PATHS TO TX

def ark_utils_texPathToTx():
	for each in ls( type = 'file' ):
		origPath = getAttr( each + '.fileTextureName' )

		if origPath.split('.')[-1] != 'jpg':
			ign = getAttr( each + '.ignoreColorSpaceFileRules' )
			setAttr( each + '.ignoreColorSpaceFileRules', 1 )
			setAttr( each + '.fileTextureName', origPath[:origPath.rfind('.')] + '.tx', type = 'string' )
			setAttr( each + '.ignoreColorSpaceFileRules', ign )

#####################################################################################################
# GROUNDED PRIMITIVES

def ark_utils_groundPrims( prim ):
	if prim == 'cube':
		obj = polyCube()[0]
	elif prim == 'sphere':
		obj = polySphere( r = 0.5 )[0]
	elif prim == 'cyl':
		obj = polyCylinder( h = 1.0, r = 0.5, sx = 8 )[0]

	setAttr( obj + '.translateY', 0.5 )
	select( obj, replace = True )
	makeIdentity( apply = True )
	xform( obj, piv = (0, 0, 0) )

#####################################################################################################
# HIDE NODES FROM GUI

def ark_utils_ihi0():
	for each in ls( sl = True ):
		setAttr( each + '.ihi', 0 )

#####################################################################################################
# SELECT ALL OBJECTS BY TYPE

def ark_utils_selByType( typ ):
	selList = ls( type = typ )
	select( selList, replace = True )

#####################################################################################################
# CACHE DYNAMICS

def ark_utils_cacheDyn():
	cmd = 'doCreateNclothCache 5 { "2", "1", "10", "OneFilePerFrame", "1", "", "1", "", "0", "add", "0", "1", "1", "0", "1", "mcx" } ;'
	maya.mel.eval( cmd )

#####################################################################################################
# CREATE AND CONNECT FOLLICLE TO SELECTED MESHES

def ark_utils_follicle():
	selList = ls( sl = True )
	for each in selList:
		foll = createNode( 'follicle' )
		setAttr( foll + '.collide', 0 )
		connectAttr( each + '.outMesh', foll + '.inputMesh' )
		connectAttr( each + '.worldMatrix[0]', foll + '.inputWorldMatrix' )
		follTr = listRelatives( foll, parent = True )[0]
		connectAttr( foll + '.outTranslate', follTr + '.translate' )
		connectAttr( foll + '.outRotate', follTr + '.rotate' )
		select( follTr, replace = True )

#####################################################################################################
# DISABLE ARNOLD AOVs AS A CURRENT RENDERLAYER ADJUSTMENT

def ark_utils_rlayAiAovOff():
	for each in ls( type='aiAOV' ):
		editRenderLayerAdjustment( each + '.enabled' )
		setAttr( each + '.enabled', 0 )
	for each in ['denoiseBeauty', 'outputVarianceAOVs']:
		editRenderLayerAdjustment( 'defaultArnoldRenderOptions.' + each )
		setAttr( 'defaultArnoldRenderOptions.' + each, 0 ) 

#####################################################################################################
# LIST ALL ATTRIBUTES AND THEIR VALUES FROM CHANNELBOX AS TWO COLUMNS FOR COPY-PASTING

def ark_utils_attrValues():
	for each in ls( sl=True ):
		for attr in listAttr( each, keyable = True ):
			print( attr + '\t' + str(getAttr( each + '.' + attr )) )

#####################################################################################################
# BIFROST GEO TO MAYA MESH
def ark_utils_biGeo():
	selList = ls( sl = True )

	biList = []
	for each in selList:
		eachType = nodeType( each )

		if eachType == 'bifrostGeoToMaya':
			biList.append( each )
		elif eachType == 'transform':
			eachShapes = listRelatives( each )
			for eachShape in eachShapes:
				if nodeType( eachShape ) == 'bifrostGraphShape':
					biList.append( eachShape )

	for each in biList:
		biGeo = createNode( 'bifrostGeoToMaya', name = each + '__bifrostGeoToMaya' )
		connectAttr( each + '.out_geometry', biGeo + '.bifrostGeo' )

		mayaGeo = createNode( 'mesh' )
		connectAttr( biGeo + '.mayaMesh[0]', mayaGeo + '.inMesh' )
		rename( listRelatives( mayaGeo, parent = True )[0], each + '__geo' )
	
		hyperShade( assign = 'initialShadingGroup' )

#####################################################################################################
