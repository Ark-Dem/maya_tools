#------------------------------------------------------------------maya-
# file: ark_geoCache.py
# version: 0.80
# date: 2020.10.22
# author: Arkadiy Demchenko
#-----------------------------------------------------------------------
# 2020.10.22 (v0.80) - added substeps checkbox (caches with 10 steps)
# 2020.07.11 (v0.70) - switches evaluation mode to DG for caching
# 2017.09.25 (v0.60) - exports custom attributes that start with 'user_'
# 2017.09.10 (v0.50) - initial version
#-----------------------------------------------------------------------
# Alembic Geometry Cache utility based on Exocortex Crate.
#-----------------------------------------------------------------------
# TO DO:
# - proper work with references (make sure no vtx edits in refEdits)
# - check transforms
# - apply updates path for existing setup
# - add new objects
# - multiFile
# - name created caches based on asset names
# - proper network for curves and nurbs
# - add elapsed/approx export time
#-----------------------------------------------------------------------

from maya.cmds import *
import maya.mel
import os, os.path, time
from string import zfill


# CONFIRM DIALOG
def ark_geoCache_confirm( ttl, btn, *msg ):
	message = msg[0] + '     '
	for each in msg[1:]:
		message += '\r\n' + each + '     '
	confirmDialog( title = ttl, message = message, button = btn )


# CHECK THE SELECTION AND PREPARE GEOLIST
def ark_geoCache_select():
	assNode = 'cache_data'
	assAttr = 'geoList'

	selList = ls( sl = True, long = True )

	# SEPARATE OBJECTS THAT HAS CACHEDATA WITH NAMESPACES FROM OTHERS
	selListTmp = []
	nmList = []
	for each in selList:
		if ':' in each:
			nm = each.split( '|' )[-1][:each.split( '|' )[-1].find( ':' )]
			if objExists( nm + ':' + assNode ):
				selListTmp.append( each )
				if not nm in nmList:
					nmList.append( nm )
	for each in selListTmp:
		selList.remove( each )
	
	# USE CACHEDATA TO FORM ASSET LIST
	assList = {}
	for nm in nmList:
		# CHECK IF GEOMETRY EXISTS
		geoList = getAttr( nm + ':' + assNode + '.' + assAttr ).split()
		geoListTmp = []
		for geo in geoList:
			if not objExists( nm + ':' + geo ):
				ark_geoCache_confirm( 'ERROR!', 'CANCEL', 'This object in geoList doesn\'t exist:', nm + ':' + geo )
				return
			if len( ls( nm + ':' + geo ) ) > 1:
				ark_geoCache_confirm( 'ERROR!', 'CANCEL', 'Multiple objects with the same name exist:', *ls( nm + ':' + geo ) )
				return
		# CONVERT TO LONG NAME AND FORM ASSET LIST
		assList[ nm.split( ':' )[-1] ] = [ ls( nm + ':' + geo, long = True )[0] for geo in geoList ]
	
	# ADD OBJECTS WITHOUT NAMESPACE TO A SPECIAL KEY KEEPING ONLY CACHEABLE SHAPES
	miscList = []
	for each in selList:
		modList = [ each ]
		if objectType( each ) == 'transform':
			shps = listRelatives( each, shapes = True, noIntermediate = True, fullPath = True )
			if shps == None:
				modList = []
			else:
				modList = shps
		for eachMod in modList:
			if objectType( eachMod ) in [ 'mesh', 'nurbsSurface', 'nurbsCurve' ]:
				if ':' in eachMod:
					nm = eachMod.split( '|' )[-1][:eachMod.split( '|' )[-1].rfind( ':' )]
					if nm.split( ':' )[-1] in assList.keys():
						assList[ nm.split( ':' )[-1] ] += [ eachMod ]
					else:
						assList[ nm.split( ':' )[-1] ] = [ eachMod ]
				else:
					miscList.append( eachMod )

	if miscList != []:
		assList[ '__tmp__' ] = miscList

	return assList


# EXPORT GEOMETRY CACHE
def ark_geoCache_cache( assList, filePath, fileName, frameRange ):
	abcJobs = []
	for asset in assList:
		# CONVERT SHAPES LIST TO TRANSFORMS LIST
		objList = []
		objListTmp = []
		for shp in assList[asset]:
			trs = listRelatives( shp, parent = True, fullPath = True )[0]
			if not trs in objList:
				if trs.split( '|' )[-1] in objListTmp:
					ark_geoCache_confirm( 'ERROR!', 'CANCEL', 'Multiple objects with the same name selected:', trs.split( '|' )[-1] )
					return
				else:
					objList.append( trs )
					objListTmp.append( trs.split( '|' )[-1] )
		list( set( objList ) )

		# CREATE DIRS
		if not os.path.exists( filePath ):
			os.makedirs( filePath )

		# EXOCORTEX CRATE ALEMBIC JOB
		cmd = 'in=' + str(frameRange[0]) + ';'
		cmd += 'out=' + str(frameRange[1]) + ';'
		cmd += 'step=' + str(frameRange[2]) + ';'
		cmd += 'substep=' + str(frameRange[3]) + ';'
		cmd += 'filename=' + filePath + fileName + '.abc;'
		cmd += 'objects=' + ','.join(objList) + ';'
		cmd += 'ogawa=1;'
		cmd += 'purepointcache=1;'
		cmd += 'dynamictopology=0;'
		cmd += 'normals=0;'
		cmd += 'uvs=0;'
		cmd += 'facesets=0;'
		cmd += 'globalspace=1;'
		cmd += 'withouthierarchy=1;'
		cmd += 'transformcache=0;'
		cmd += 'userattrprefixes=user_;'
		cmd += 'search=.+:;replace=()'

		abcJobs.append( cmd )

	# SWITCH EVALUATION MODE TO DG
	origEval = evaluationManager( query = True, mode = True )[0]
	if origEval != 'off':
		evaluationManager( mode = 'off' )

	# EXPORT CACHE
	ExocortexAlembic_export( j = abcJobs )

	# SWITCH EVALUATION MODE TO ORIGINAL
	if origEval != 'off':
		evaluationManager( mode = origEval )


# CREATE/UPDATE CACHE NETWORK
def ark_geoCache_apply( assList, filePath, fileName ):
	for asset in assList:
		if not objExists( asset + ':cache_file' ):
			# CREATE NEW CACHE NETWORK
			ark_geoCache_cleanup( assList[asset] )

			nm = asset
			if asset == '__tmp__':
				nm = ''
			else:
				nm += '__'

			aTime = createNode( 'ExocortexAlembicTimeControl', name = nm + 'cache_timeControl' )
			aFile = createNode( 'ExocortexAlembicFile', name = nm + 'cache_file' )

			setAttr( aFile + '.fileName', filePath + fileName + '.abc', type = 'string' )
			
			for each in [aTime, aFile]:
				setAttr( each + '.ihi', 0 )	

			connectAttr( 'time1.outTime', aTime + '.inTime' )
			connectAttr( aTime + '.outTime', aFile + '.inTime' )

			for geoShape in assList[asset]:
				geo = listRelatives( geoShape, parent = True )[0]
				geoName = geo
				if geo[-4:] == '_geo':
					geoName = geo[:-4]

				orig = ark_geoCache_outIn( geoShape, geoShape, 0 )
				
				aDef = createNode( 'ExocortexAlembicPolyMeshDeform', name = nm + geoName + '__cache_deform' )
				aTrs = createNode( 'ExocortexAlembicXform', name = nm + geoName + '__cache_xform' )
				aGpt = createNode( 'groupParts', name = nm + geoName + '__cache_groupParts' )
				aGid = createNode( 'groupId', name = nm + geoName + '__cache_groupId' )
			
				setAttr( aGpt + '.ic', 1, 'vtx[*]', type = 'componentList' )
				setAttr( aTrs + '.identifier', '/' + geo, type = 'string' )
				setAttr( aDef + '.identifier', '/' + geo + '/' + geoShape.replace('|',':').split(':')[-1], type = 'string' )
				for each in [aTrs, aGpt, aGid]:
					setAttr( each + '.ihi', 0 )
			
				connectAttr( aTime + '.outTime', aDef + '.inTime' )
				connectAttr( aFile + '.outFileName', aTrs + '.fileName' )
				connectAttr( aFile + '.outFileName', aDef + '.fileName' )
				connectAttr( orig + '.worldMesh[0]', aGpt + '.inputGeometry' )
				connectAttr( aGid + '.groupId', aGpt + '.groupId' )
				connectAttr( aGid + '.groupId', aDef + '.input[0].groupId' )
				connectAttr( aGpt + '.outputGeometry', aDef + '.input[0].inputGeometry' )
			
				connectAttr( aDef + '.outputGeometry[0]', geoShape + '.inMesh', force = True )
				connectAttr( aTrs + '.translate', geo + '.translate', force = True )
				connectAttr( aTrs + '.rotate', geo + '.rotate', force = True )
				connectAttr( aTrs + '.scale', geo + '.scale', force = True )
		else:
			setAttr( asset + ':cache_file.fileName', filePath + fileName + '.abc', type = 'string' )


# OUT-IN GEOMETRY DATA TRANSFER (PUT THE SAME SHAPE TWICE TO MAKE ORIG)
def ark_geoCache_outIn( outGeoShape, inGeoShape, keep ):
	geoType = objectType( outGeoShape )

	origMode = 0
	if outGeoShape == inGeoShape:
		origMode = 1
		inGeoShape = createNode( geoType )

	if geoType == 'mesh':
		connectAttr( outGeoShape + '.outMesh', inGeoShape + '.inMesh' )
		polyEvaluate( inGeoShape )
		if not keep:
			disconnectAttr( outGeoShape + '.outMesh', inGeoShape + '.inMesh' )
	elif geoType == 'nurbsSurface' or geoType == 'nurbsCurve':
		connectAttr( outGeoShape + '.local', inGeoShape + '.create' )
		if geoType == 'nurbsSurface':
			getAttr( inGeoShape + '.spansU' )
		else:
			getAttr( inGeoShape + '.spans' )
		if not keep:
			disconnectAttr( outGeoShape + '.local', inGeoShape + '.create' )

	if origMode:
		inGeo = listRelatives( inGeoShape, parent = True, fullPath = True )[0]
		outGeo = listRelatives( outGeoShape, parent = True, fullPath = True )[0]

		orig = rename( inGeoShape, outGeoShape.replace('|',':').split(':')[-1] + 'Orig' )
		parent( orig, outGeo, add = True, shape = True )
		delete( inGeo )
		setAttr( orig + '.intermediateObject', True )

		return orig


# CLEANUP GEOMETRY
def ark_geoCache_cleanup( geoList, **mode ):
	if mode == {}:
		mode['all'] = True
	if 'all' in mode.keys():
		if mode['all']:
			if not 'hierarchy' in mode.keys():
				mode['hierarchy'] = True
			if not 'history' in mode.keys():
				mode['history'] = True
			if not 'transforms' in mode.keys():
				mode['transforms'] = True
			if not 'controlPoints' in mode.keys():
				mode['controlPoints'] = True

	for geoShp in geoList:
		geo = listRelatives( geoShp, parent = True, fullPath = True )[0]

		# CLEANUP HIERARACHY
		if 'hierarchy' in mode.keys():
			if mode['hierarchy']:
				#ark_geoCache_feedback( 'Cleaning hierarchy...' + geoShp )
				chds = listRelatives( geo, children = True, fullPath = True )
				origs = ls( chds, intermediateObjects = True )
				if origs != []:
					delete( origs )

				chds = listRelatives( geo, children = True, fullPath = True )
				for chd in chds:
					if not objectType( chd ) in [ 'mesh', 'nurbsCurve', 'nurbsSurface' ]:
						delete( chd )

		# CLEANUP HISTORY
		if 'history' in mode.keys():
			if mode['history']:
				#ark_geoCache_feedback( 'Cleaning history...' + geoShp )
				delete( geo, constructionHistory = True )

		# CLEANUP TRANSFORMS, PIVOT AND SET WORLDSPACE MATRIX TO DEFAULT
		if 'transforms' in mode.keys():
			if mode['transforms']:
				#ark_geoCache_feedback( 'Cleaning transforms...' + geoShp )
				makeIdentity( geo, apply = True )
				xform( geo, worldSpace = True, piv = ( 0, 0, 0 ) )
				maya.mel.eval( 'xform -ws -m 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 ' + geo + ';' )

		# CLEANUP CONTROL POINTS TRANSFORMATIONS
		if 'controlPoints' in mode.keys():
			if mode['controlPoints']:
				#ark_geoCache_feedback( 'Cleaning controlPoints...' + geoShp )
				tmpShp = createNode( objectType( geoShp ) )
				ark_geoCache_outIn( geoShp, tmpShp, 0 )

				cpCount = len( ls( geoShp + '.controlPoints[*]', flatten = True ) )
				cmd = 'setAttr ' + geoShp + '.controlPoints[0:' + str( cpCount - 1 ) + ']'
				for i in xrange( 0, cpCount ):
					cmd += ' 0 0 0'
				maya.mel.eval( cmd )

				ark_geoCache_outIn( tmpShp, geoShp, 0 )
				delete( listRelatives( tmpShp, parent = True ) )


# WORK WITH CACHE LIST
def ark_geoCache_data( assList ):
	for asset in assList:
		geoList = assList[asset]

		# MAKE A STRING OUT OF SHAPES LIST, STORE ROOT GROUPS
		roots = []
		geoStr = geoList[0].split( '|' )[-1]
		for geoShp in geoList[1:]:
			geoStr += ' ' + geoShp.split( '|' )[-1]

			root = geoShp.split( '|' )[1]
			roots.append( root )

		# CREATE NEW CACHE_DATA NODE, UNLOCK IF IT ALREADY EXISTS
		data = 'cache_data'
		if not objExists( data ):
			group( empty = True, world = True, name = data )
			addAttr( data, ln = 'geoList', dt = 'string' )

			# FIND THE ROOT GROUP THAT HAS THE MOST OF SELECTED OBJECTS
			mainRoot = ''
			maxCount = 0
			rootsUnique = list( set( roots ) )
			for root in rootsUnique:
				if roots.count( root ) > maxCount:
					mainRoot = root
					maxCount = roots.count( root )

			parent( data, mainRoot )
			for attr in listAttr( data, k = True ):
				setAttr( data + '.' + attr, k = False, l = True )
		else:
			lockNode( data, lock = False )
			setAttr( data + '.geoList', lock = False )
		
		setAttr( data + '.geoList', geoStr, type = 'string' )

		setAttr( data + '.geoList', lock = True )
		lockNode( data, lock = True )
		
		return [ len( geoList ), ls( data, long = True )[0] ]
	

# TIMER
def ark_geoCache_timer( startTime ):
	endTime = time.clock()	
	secs = int( (endTime - startTime) % 60 )
	hours = int( (endTime - startTime - secs ) / 3600 )
	mins = int( (endTime - startTime - secs - hours * 3600) / 60 )
	duration = zfill( str( hours ), 2 ) + ':' + zfill( str( mins ), 2 ) + ':' + zfill( str( secs ), 2 )

	return duration


# COLLECT DATA FROM GUI AND RUN FUNCTIONS
def ark_geoCache_do( mode ):
	# START TIMER
	startTime = time.clock()

	# REMEMBER SELECTION
	selList = ls( sl = True )

	# GET THE FILEPATH AND FILENAME
	path = textFieldButtonGrp( 'ark_geoCache_path_ctrl', query = True, text = True )
	if path == '':
		path = workspace( query = True, rd = True ) + 'cache/geoCache'
	path = path.replace( '\\', '/' )

	fileName = path.split( '/' )[-1]
	if fileName == '':
		fileName = 'geoCache'
	else:
		fileName = fileName[:fileName.rfind( '.' )]
	
	filePath = path[:path.rfind( '/' )+1]

	# GET FRAMERANGE FROM TIMELINE, IF CTRL WAS PRESSED - CACHE FRAME 1 ONLY
	startFrame = int( playbackOptions( query = True, minTime = True ) )
	endFrame = int( playbackOptions( query = True, maxTime = True ) )

	# SINGLE FRAME FOR STATIC MODE
	if mode == 'static':
		mode = 'cache'
		startFrame = int( currentTime( query = True ) )
		endFrame = startFrame
	
	# CHECK IF FILES ARE WRITABLE
	cacheWritable = 0
	if os.path.exists( filePath + fileName + '.abc' ):
		if os.access( filePath + fileName + '.abc', os.W_OK ):
			cacheWritable += 1
	else:
		cacheWritable += 1

	# RUN PROCEDURE DEPENDING ON THE MODE CHOSEN
	if mode == 'cache':
		# STOP THE SCRIPT IF FILES CAN'T BE OVERWRITTEN
		if cacheWritable < 1:
			ark_geoCache_confirm( 'Error!', 'CANCEL', 'Can\'t overwrite read-only cache files!' )
			return

		# SUBSTEPS
		substeps = 1
		if checkBox( 'ark_geoCache_substeps_ctrl', query = True, value = True ):
			substeps = 10

		# MAIN CACHING FUNCTION
		ark_geoCache_cache( ark_geoCache_select(), filePath, fileName, [startFrame, endFrame, 1, substeps] )

		# CALCULATE DURATION AND SHOW FINAL CONFIRMATION
		duration = ark_geoCache_timer( startTime )
		ark_geoCache_confirm( 'Caching Complete', 'OK', 'Caching completed successfully in ' + duration )

	elif mode == 'apply':
		# MAIN APPLICATON FUNCTION
		ark_geoCache_apply( ark_geoCache_select(), filePath, fileName )

		# CALCULATE DURATION AND SHOW FINAL CONFIRMATION
		duration = ark_geoCache_timer( startTime )
		ark_geoCache_confirm( 'Cache Applied', 'OK', 'Cache applied successfully in ' + duration )
	
	elif mode == 'data':
		data = ark_geoCache_data( ark_geoCache_select() )

		# SHOW FINAL CONFIRMATION WITH CACHEDATA LOCATION
		ark_geoCache_confirm( 'Data Stored', 'OK', 'Stored ' + str( data[0] ) + ' shape(s) into:', data[1] )
	
	# RESTORE SELECTION
	select( selList, replace = True )


# BROWSE FOR A PATH
def ark_geoCache_browse():
	origPath = textFieldButtonGrp( 'ark_geoCache_path_ctrl', query = True, text = True )
	startDir = workspace( query = True, rd = True ) + 'cache'

	flt = 'Alembic Files .abc (*.abc)'
	path = fileDialog2( fileFilter = flt, 
						dialogStyle = 2, 
						fileMode = 0,
						caption = 'Select File',
						okCaption = 'Select',
						startingDirectory = startDir )

	if path == None:
		textFieldButtonGrp( 'ark_geoCache_path_ctrl', edit = True, text = origPath )
	else:
		textFieldButtonGrp( 'ark_geoCache_path_ctrl', edit = True, text = path[0] )


# GUI
def ark_geoCache():
	tool = 'ark_geoCache'
	win = tool + '_win'

	if window( win, exists = True ):
		deleteUI( win )
	
	win = window( win, title = 'Cache Geometry', sizeable = False )

	columnLayout( adj = True, columnAttach = ['both', 2] )

	rowLayout( numberOfColumns = 2, height = 25 )
	
	textFieldButtonGrp( tool + '_path_ctrl',
						label = 'Path: ',
						columnWidth3 = [30, 315, 0],
						text = workspace( query = True, rd = True ) + 'cache/geoCache.abc',
						buttonLabel = '...',
						buttonCommand = tool + '_browse()' )

	checkBox( tool + '_substeps_ctrl', label = 'Substeps' )

	setParent( '..' )

	rowLayout( numberOfColumns = 5, height = 25 )

	button( label = 'Create',
			width = 165,
			command = tool + '_do( "cache" )' )
	button( label = 'Static', 
			width = 50,
			command = tool + '_do( "static" )' )

	separator( horizontal = False, width = 4 )

	button( label = 'Apply', 
			width = 165,
			command = tool + '_do( "apply" )' )
	button( label = 'Data', 
			width = 50,
			command = tool + '_do( "data" )' )

	setParent( '..' )

	showWindow( win )
	window( win, edit = True, width = 450, height = 53 )
