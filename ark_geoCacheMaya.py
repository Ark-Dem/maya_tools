#------------------------------------------------------------------maya-
# file: ark_geoCacheMaya.py
# version: 0.13
# date: 2021.01.01
# author: Arkadiy Demchenko (sagroth@sigillarium.com)
#-----------------------------------------------------------------------
# 2021.01.01 (v0.13) - mcx, per object files, substeps
# 2017.05.03 (v0.12) - reworked GUI, static frame export current frame
# 2014.02.10 (v0.11) - added cacheData creation and reading
# 2014.02.09 (v0.10) - main release
#-----------------------------------------------------------------------
# Utility for using Maya Geometry Cache in a more effective way.
#-----------------------------------------------------------------------
# TO DO:
# - cache file name after character
# - option to update viewport while caching
# - apply/append cache to existing setup
#-----------------------------------------------------------------------

from maya.cmds import *
import maya.mel
from string import zfill
import time, os, os.path


# CONFIRM DIALOG FORM
def ark_geoCacheMaya_confirm( ttl, btn, *msg ):
	message = msg[0] + '     '
	for each in msg[1:]:
		message += '\r\n' + each + '     '
	confirmDialog( title = ttl, message = message, button = btn )


# SCRIPT EDITOR FEEDBACK FORM
def ark_geoCacheMaya_feedback( *msg ):
	feedback = ' ' + msg[0]
	feedLen = len( feedback )
	for each in msg[1:]:
		feedback += '\r\n ' + each
		feedLen = max( feedLen, len( each ) )

	liner = '#'
	for i in xrange( 0, feedLen ):
		liner += '#'
	print ''
	print liner
	print feedback
	print liner


# CHECK THE SELECTION AND PREPARE GEOLIST
def ark_geoCacheMaya_select():
	selList = ls( sl = True, long = True )

	# GET LIST OF NAMESPACES FROM SELECTION
	nmList = []
	for each in selList:
		nm = ''
		if ':' in each:
			nm = each.split( '|' )[1][:each.split( '|' )[1].find( ':' )+1]
		if not nm in nmList:
			nmList.append( nm )
	
	# SEARCH FOR CACHEDATA NODES WITH SELECTED NAMESPACES AND LOAD SELLIST FROM THEM
	for nm in nmList:
		firstNm = True
		if objExists( nm + 'cacheData' ):
			if firstNm:
				selList = []
				firstNm = False				
			cacheDataListOrig = getAttr( nm + 'cacheData.geoList' ).split()

			# ADD NAMESPACE TO EACH OBJECT
			cacheDataList = []
			for cacheData in cacheDataListOrig:
				cacheDataList.append( nm + cacheData )

			# STOP THE SCRIPT IF THERE IS AN OBJECT THAT DOESN'T EXIST
			for cacheData in cacheDataList:
				if not objExists( cacheData ):
					ark_geoCacheMaya_confirm( 'Error!', 'CANCEL', 'This object doesn\'t exist:', cacheData )
					return
				if len( ls( cacheData ) ) > 1:
					ark_geoCacheMaya_confirm( 'Error!', 'CANCEL', 'Multiple objects exist:', *ls( cacheData ) )
					return

			# CONVERT TO LONG PATHS AND ADD TO SELLIST
			selList += ls( cacheDataList, long = True )

	# FILTER SELECTION
	geoList = []
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
				geoList.append( eachMod )

	return geoList


# OUT-IN GEOMETRY DATA TRANSFER
def ark_geoCacheMaya_outIn( outGeo, inGeo, keep ):
	geoType = objectType( outGeo )

	if geoType == 'mesh':
		connectAttr( outGeo + '.outMesh', inGeo + '.inMesh' )
		polyEvaluate( inGeo )
		if not keep:
			disconnectAttr( outGeo + '.outMesh', inGeo + '.inMesh' )
	elif geoType == 'nurbsSurface' or geoType == 'nurbsCurve':
		connectAttr( outGeo + '.local', inGeo + '.create' )
		if geoType == 'nurbsSurface':
			getAttr( inGeo + '.spansU' )
		else:
			getAttr( inGeo + '.spans' )
		if not keep:
			disconnectAttr( outGeo + '.local', inGeo + '.create' )


# CACHE GEOMETRY
def ark_geoCacheMaya_cache( geoList, filePath, fileName, frameRange, simRate ):
	# CREATE TEMPORARY GROUP
	tmpDir = '_ark_geoCacheMaya_DELETE'
	if objExists( tmpDir ):
		delete( tmpDir )
	dupGrp = group( em = True, name = tmpDir )

	# CREATE DUPLICATE FOR EACH OBJECT AND BLENDSHAPE IT TO ORIGINAL
	dupList = []
	renDict = {}
	for geo in geoList:
		geoType = objectType( geo )

		# TO AVOID DEALING WITH CHILDREN AND INTERMEDIATE SHAPES, CREATE DUPLICATE VIA NEW CLEAN GEOMETRY
		dupShp = createNode( geoType )
		dup = listRelatives( dupShp, parent = True )[0]
		parent( dup, dupGrp )

		# NAME PROPERLY, RENAME OTHER OBJECTS IF THEY HAVE THE SAME NAME
		shp = geo.replace( '|', ':' ).split( ':' )[-1]
		for eachShp in ls( shp, long = True ):
			newName = rename( eachShp, shp + '_ark_geoCacheMaya_tmpName#' )
			renDict[newName] = shp
			if eachShp == geo:
				geo = newName
		dupShp = rename( dupShp, shp )

		# TURN BLANK GEOMETRY INTO ORIGINAL VIA OUT-IN CONNECTION AND FORCE IT'S EVALUATION (IN CASE HIDDEN OR OUT OF VIEW)
		ark_geoCacheMaya_outIn( geo, dupShp, 0 )

		# BLENSHAPE DUPLICATE TO ORIGINAL
		bShp = blendShape( geo, dupShp, origin = 'world', weight = [0, 1] )

		# ADD DUPLICATE TO LIST
		dupList.append( dupShp )

	# CACHE DUPLICATES
	cacheFile(	refresh = False,
				directory = filePath, 
				cacheFormat = 'mcx', 
				doubleToFloat = True,
				format = 'OneFile', 
				singleCache = False, 
				simulationRate = simRate, 
				startTime = frameRange[0],
				endTime = frameRange[1], 
				points = dupList 
			)

	# DELETE DUPLICATES
	delete( dupGrp )

	# RENAME TEMPORARY RENAMED SHAPES BACK
	for each in renDict:
		rename( each, renDict[each] )


# CLEANUP GEOMETRY
def ark_geoCacheMaya_cleanup( geoList, **mode ):
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
				#ark_geoCacheMaya_feedback( 'Cleaning hierarchy...' + geoShp )
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
				#ark_geoCacheMaya_feedback( 'Cleaning history...' + geoShp )
				delete( geo, constructionHistory = True )

		# CLEANUP TRANSFORMS, PIVOT AND SET WORLDSPACE MATRIX TO DEFAULT
		if 'transforms' in mode.keys():
			if mode['transforms']:
				#ark_geoCacheMaya_feedback( 'Cleaning transforms...' + geoShp )
				makeIdentity( geo, apply = True )
				xform( geo, worldSpace = True, piv = ( 0, 0, 0 ) )
				maya.mel.eval( 'xform -ws -m 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 ' + geo + ';' )

		# CLEANUP CONTROL POINTS TRANSFORMATIONS
		if 'controlPoints' in mode.keys():
			if mode['controlPoints']:
				#ark_geoCacheMaya_feedback( 'Cleaning controlPoints...' + geoShp )
				tmpShp = createNode( objectType( geoShp ) )
				ark_geoCacheMaya_outIn( geoShp, tmpShp, 0 )

				cpCount = len( ls( geoShp + '.controlPoints[*]', flatten = True ) )
				cmd = 'setAttr ' + geoShp + '.controlPoints[0:' + str( cpCount - 1 ) + ']'
				for i in xrange( 0, cpCount ):
					cmd += ' 0 0 0'
				maya.mel.eval( cmd )

				ark_geoCacheMaya_outIn( tmpShp, geoShp, 0 )
				delete( listRelatives( tmpShp, parent = True ) )

		# CLEANUP PER-FACE SHADERS ASSIGNMENT


# CREATE ORIG SHAPE (RESPECTS MULTIPLE SHAPES UNDER SINGLE TRANSFORM)
def ark_geoCacheMaya_orig( geoShp, connect ):
	dupTmp = duplicate( geoShp, parentOnly = True )[0]
	parent( geoShp, dupTmp, add = True, shape = True, noConnections = True )
	dup = duplicate( dupTmp )[0]
	delete( dupTmp )
	orig = listRelatives( dup, shapes = True, fullPath = True )[0]
	orig = rename( orig, geoShp[:geoShp.rfind( ':' )+1].replace( ':', '_' ).split( '|' )[-1] + geoShp.replace( ':', '|' ).split( '|' )[-1] + '_origCache' )
	orig = parent( orig, listRelatives( geoShp, parent = True, fullPath = True )[0], add = True, shape = True )[0]
	delete( dup )

	if connect:
		ark_geoCacheMaya_outIn( orig, geoShp, 1 )

	setAttr( orig + '.intermediateObject', 1 )

	# CREATE groupId CONNECTIONS IF PRESENT TO KEEP MATERIALS FURTHER ON
	#conns = listConnections( geo, s = True, d = False, c = True, p = True )
	#if conns != None:
	#	for i in xrange( 0, len( conns ), 2 ):
	#		if objectType( conns[i+1] ) == 'groupId':
	#			connectAttr( conns[i+1], orig + conns[i][conns[i].find( '.' ):], force = True )
	
	return orig


# APPLY CACHE
def ark_geoCacheMaya_apply( geoList, filePath, fileName ):
	# IF CACHE SETUP DOESN'T EXIST ALREADY, CREATE IT
	origList = []
	swchList = []
	chanList = []
	for geoShp in geoList:
		# CREATE ORIG SHAPE
		orig = ark_geoCacheMaya_orig( geoShp, 0 )

		# CREATE SWITCH NODE AND MAKE CONNECTIONS
		swchName = geoShp[:geoShp.rfind( ':' )+1].replace( ':', '_' ).split( '|' )[-1] + geoShp.replace( ':', '|' ).split( '|' )[-1]
		swch = createNode( 'historySwitch', name = swchName + '_cacheSwitch' )
		setAttr( swch + '.ihi', 0 )

		connectAttr( orig + '.worldMesh[0]', swch + '.input[0].inputGeometry' )
		connectAttr( orig + '.worldMesh[0]', swch + '.undeformedGeometry[0]' )
		disconnectAttr( orig + '.worldMesh[0]', swch + '.undeformedGeometry[0]' )
		connectAttr( swch + '.outputGeometry[0]', geoShp + '.inMesh', force = True )
		polyEvaluate( geoShp )

		# POPULATE LISTS IN SYNC
		origList.append( orig )
		swchList.append( swch + '.inp[0]' )
		chanList.append( geoShp.replace( '|', ':' ).split( ':' )[-1] )

	# CREATE CACHEFILE
	cacheNode = cacheFile( fileName = fileName, directory = filePath, attachFile = True, channelName = chanList, inAttr = swchList )
	for swch in swchList:
		connectAttr( cacheNode + '.inRange', swch[:swch.rfind( '.' )] + '.playFromCache' )
	setAttr( cacheNode + '.hold', 1000 )
	setAttr( cacheNode + '.multiThread', True )
	setAttr( cacheNode + '.ihi', 2 )

	if getAttr( cacheNode + '.sourceStart' ) == getAttr( cacheNode + '.sourceEnd' ):
		setAttr( cacheNode + '.startFrame', 1 )

	rename( cacheNode, swchName + '_cacheFile' )

	# IF CACHE SETUP EXISTS ALREADY, UPDATE IT

	# IF SOME OBJECTS HAVE CACHE SETUP ALREADY AND OTHERS DON'T, ADD THESE OTHERS TO THE SAME SETUP


# WORK WITH CACHE LIST
def ark_geoCacheMaya_data( geoList ):
	# MAKE A STRING OUT OF SHAPES LIST, STORE ROOT GROUPS
	roots = []
	geoStr = geoList[0].replace( '|', ':' ).split( ':' )[-1]
	for geoShp in geoList[1:]:
		geoStr += ' ' + geoShp.replace( '|', ':' ).split( ':' )[-1]

		root = geoShp.split( '|' )[1]
		roots.append( root )

	# CREATE NEW CACHEDATA NODE, UNLOCK IF IT ALREADY EXISTS
	data = 'cacheData'
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
def ark_geoCacheMaya_timer( startTime ):
	endTime = time.clock()	
	secs = int( (endTime - startTime) % 60 )
	hours = int( (endTime - startTime - secs ) / 3600 )
	mins = int( (endTime - startTime - secs - hours * 3600) / 60 )
	duration = zfill( str( hours ), 2 ) + ':' + zfill( str( mins ), 2 ) + ':' + zfill( str( secs ), 2 )

	return duration


# COLLECT DATA FROM GUI AND RUN FUNCTIONS
def ark_geoCacheMaya_do( mode ):
	# START TIMER
	startTime = time.clock()

	# REMEMBER SELECTION
	selList = ls( sl = True )

	# GET THE FILEPATH AND FILENAME
	path = textFieldButtonGrp( 'ark_geoCacheMaya_path_ctrl', query = True, text = True )
	if path == '':
		path = workspace( query = True, rd = True ) + 'cache/geoCache'
	path = path.replace( '\\', '/' )

	fileName = path.split( '/' )[-1]
	if fileName == '':
		fileName = 'geoCache'
	else:
		fileName = fileName.split( '.' )[0]
	
	filePath = path[:path.rfind( '/' )+1]

	# GET FRAMERANGE FROM TIMELINE, IF CTRL WAS PRESSED - CACHE FRAME 1 ONLY
	startFrame = int( playbackOptions( query = True, minTime = True ) )
	endFrame = int( playbackOptions( query = True, maxTime = True ) )

	# SIMULATION RATE
	simRate = 1

	# SINGLE FRAME FOR STATIC MODE
	if mode == 'static':
		mode = 'cache'
		startFrame = int( currentTime( query = True ) )
		endFrame = startFrame
		simRate = 1
	
	# CHECK IF FILES ARE WRITABLE
	cacheWritable = 0
	if os.path.exists( filePath + fileName + '.mc' ):
		if os.access( filePath + fileName + '.mc', os.W_OK ):
			cacheWritable += 1
	else:
		cacheWritable += 1

	if os.path.exists( filePath + fileName + '.xml' ):
		if os.access( filePath + fileName + '.xml', os.W_OK ):
			cacheWritable += 1
	else:
		cacheWritable += 1

	# RUN PROCEDURE DEPENDING ON THE MODE CHOSEN
	if mode == 'cache':
		# STOP THE SCRIPT IF FILES CAN'T BE OVERWRITTEN
		if cacheWritable < 2:
			ark_geoCacheMaya_confirm( 'Error!', 'CANCEL', 'Can\'t overwrite read-only cache files!' )
			return

		# MAIN CACHING FUNCTION
		ark_geoCacheMaya_cache( ark_geoCacheMaya_select(), filePath, fileName, [startFrame, endFrame], simRate )

		# CALCULATE DURATION AND SHOW FINAL CONFIRMATION
		duration = ark_geoCacheMaya_timer( startTime )
		ark_geoCacheMaya_confirm( 'Caching Complete', 'OK', 'Caching completed successfully in ' + duration )

	elif mode == 'apply':
		# MAIN APPLICATON FUNCTION
		geoList = ark_geoCacheMaya_select()
		ark_geoCacheMaya_cleanup( geoList )
		ark_geoCacheMaya_apply( geoList, filePath, fileName )

		# CALCULATE DURATION AND SHOW FINAL CONFIRMATION
		duration = ark_geoCacheMaya_timer( startTime )
		ark_geoCacheMaya_confirm( 'Cache Applied', 'OK', 'Cache applied successfully in ' + duration )
	
	elif mode == 'data':
		data = ark_geoCacheMaya_data( ark_geoCacheMaya_select() )

		# SHOW FINAL CONFIRMATION WITH CACHEDATA LOCATION
		ark_geoCacheMaya_confirm( 'Data Stored', 'OK', 'Stored ' + str( data[0] ) + ' shape(s) into:', data[1] )
	
	# RESTORE SELECTION
	select( selList, replace = True )


# BROWSE FOR A PATH
def ark_geoCacheMaya_browse():
	origPath = textFieldButtonGrp( 'ark_geoCacheMaya_path_ctrl', query = True, text = True )
	startDir = workspace( query = True, rd = True ) + 'cache'

	flt = 'Cache Description Files .xml (*.xml)'
	path = fileDialog2( fileFilter = flt, 
						dialogStyle = 2, 
						fileMode = 0,
						caption = 'Select File',
						okCaption = 'Select',
						startingDirectory = startDir )

	if path == None:
		textFieldButtonGrp( 'ark_geoCacheMaya_path_ctrl', edit = True, text = origPath )
	else:
		textFieldButtonGrp( 'ark_geoCacheMaya_path_ctrl', edit = True, text = path[0] )


# GUI
def ark_geoCacheMaya():
	tool = 'ark_geoCacheMaya'
	win = tool + '_win'

	if window( win, exists = True ):
		deleteUI( win )
	
	win = window( win, title = 'Cache Geometry', sizeable = False )

	columnLayout( adj = True, columnAttach = ['both', 2] )
	
	textFieldButtonGrp( tool + '_path_ctrl',
						label = 'Cache File: ',
						columnWidth3 = [59, 360, 0],
						text = workspace( query = True, rd = True ) + 'cache/geoCache.xml',
						buttonLabel = '...',
						buttonCommand = tool + '_browse()' )

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
