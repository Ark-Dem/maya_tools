#--------------------------------------------------------------------maya-
# file: ark_mtoa.py
# version: 1.15
# date: 2023.03.31
# author: Arkadiy Demchenko
#-------------------------------------------------------------------------
# 2023.03.31 (v1.15) - update for Python3
# 2022.03.23 (v1.14) - mask 6399 (includes operators)
# 2021.09.24 (v1.13) - reverse option
# 2021.04.01 (v1.12) - cmd line, progBar by frame, split batch
# 2021.03.30 (v1.11) - batch file gets created completely after first ass
# 2021.01.03 (v1.10) - added Output Color Transform flag to kick
# 2020.05.15 (v1.09) - added expand procedurals checkbox (not storable)
# 2020.05.09 (v1.08) - %rlay% variable uses current render layer
# 2017.07.13 (v1.07) - runs process with low priority
# 2017.06.15 (v1.06) - writes log automatically to temp dir
# 2017.04.22 (v1.05) - update for Arnold 5
# 2017.03.12 (v1.04) - paths now understand variables (e.g. %root%)
# 2017.03.11 (v1.03) - added region file (frame xmin ymin xmax ymax) nuke 
# 2016.09.28 (v1.02) - prints feedback to script editor
# 2016.07.08 (v1.01) - initial release, all functions added
#-------------------------------------------------------------------------
# Exports and kicks ASS from Maya with some handy options.
#
# Usage:
#   Define ARNOLD_TEMP environment variable or fix path in GLOBAL VARS.
#   Settings are saved to arnoldDefaultRenderOptions node.
#
#   ark_mtoa()                  - starts GUI
#   ark_mtoa( mode = 'frame' )  - executes render of the current frame 
#                                 without gui with default/saved settings
#   ark_mtoa( mode = 'anim' )   - same, but with frame range from 
#                                 Render Settings
#   ark_mtoa_do()               - check kwargs for custom usage
#
# TO DO:
#	- check if renderable camera exists
#   - enable interactive mode
#   - modes (amboccl, notex, dot, grey)
#   - threads
#   - noice option
#   - cleanup after each frame option
#-------------------------------------------------------------------------
from maya.cmds import *
import os, os.path, time
import mtoa.core


# UPDATE PYTHON3 RENAMDED FUNCTION TO KEEP IT WORKING WITH PYTHON2
try:
	xrange(1)
except:
	xrange = range


# GLOBAL VARS
ark_mtoa_assPath = 'C:/_temp/arnold/'


# FEEDBACK FORM
def ark_mtoa_feedback( *msg ):
	feedback = ' ' + msg[0]
	feedLen = len( feedback )
	for each in msg[1:]:
		feedback += '\r\n ' + each
		feedLen = max( feedLen, len( each ) )

	liner = '#'
	for i in xrange( 0, feedLen+1 ):
		liner += '#'
	print( '' )
	print( liner )
	print( feedback )
	print( liner )


# MAIN PROCEDURE
def ark_mtoa_do( verbose=4, gamma=2.2, disableWin=False, outName='', outPath='', progr=True, expand=False, autoVer=True, uname=False, exportOnly=False, cleanup=True, split=False, splitNum=2, reverse=False, cmdLine='', anim=False, region=False, gui=False ):
	# GET MTOA PLUGIN VERSION
	mtoaVer = pluginInfo( 'mtoa.mll', query = True, version = True )

	# START TIMER
	startTime = time.time()

	# PATH FOR ASS FILES
	assPath = ark_mtoa_assPath
	if os.getenv('ARNOLD_TEMP'):
		assPath = os.getenv('ARNOLD_TEMP').replace( '\\', '/' )
		if assPath[-1] != '/':
			assPath += '/'
	# CREATE PATH IF IT DOESN'T EXIST
	if not os.path.exists( assPath ):
		os.makedirs( assPath )

	# GET OUTPUT NAME FROM RENDER SETTINGS
	assName = assNameOrig = getAttr( 'defaultRenderGlobals.imageFilePrefix' )
	# GET CUSTOM OUTPUT NAME IF GIVEN
	if outName != '':
		if '%' in outName:
			line = outName
			assName = ''
			while( '%' in line ):
				varIn = line.find('%')
				varOut = line.find('%',line.find('%')+1)
				var = line[varIn+1:varOut]
				assName += line[:varIn]
				line = line[varOut+1:]
				if var == 'rlay':
					assName += editRenderLayerGlobals( query = True, currentRenderLayer = True )
				else:
					varVal = workspace( variableEntry = var )
					if varVal != '' and varVal != None:
						assName += varVal
					else:
						varVal = os.getenv( var )
						if varVal != '' and varVal != None:
							assName += varVal
						else:
							confirmDialog( title = 'Error!', message = 'No project or environment variable: %' + var + '%', button = 'CANCEL' )
							return
			assName += line
		else:
			assName = outName.replace( '\\', '_' ).replace( '/', '_' ).replace( '.', '_' )
	# IF OUTPUT NAME IS NOT DEFINED, USE SCENE NAME (IF IT'S NOT SAVED, USE UNTITLED)
	if assName in [None,'']:
		assName = file( query = True, sceneName	= True, shortName = True )[:-3]
	if assName == '':
		assName = 'untitled'

	# IF CUSTOM OUTPUT PATH IS GIVEN, CHECK IF IT NEEDS TO BE CREATED
	if outPath != '':
		outPath = ark_mtoa_outPathConvert( outPath )

		if os.path.isabs( outPath ):
			if not os.path.exists( outPath ):
				os.makedirs( outPath )
		else:
			outPath = ''

	# AUTO VERSIONING
	if autoVer:
		verPath = outPath
		if verPath == '':
			verPath = ark_mtoa_output()[1]

		ver = ark_mtoa_autoVer( name = assName, path = verPath )

		assName += ver

	# IF UNIQUE NAME IS ENABLED, ADD TIME-DATE TO THE FILE NAME
	if uname:
		assName += '_' + time.strftime('%y%m%d') + '-' + time.strftime('%H%M%S')

	# PUT OUTPUT NAME INTO RENDER SETTINGS
	setAttr( 'defaultRenderGlobals.imageFilePrefix', assName, type = 'string' )

	# GET FRAME RANGE
	startFrame = int(currentTime( query = True ))
	endFrame = startFrame
	frameStep = 1
	padding = int(getAttr( 'defaultRenderGlobals.extensionPadding' ))
	if not getAttr( 'defaultRenderGlobals.animation' ):
		anim = False
	if anim:
		startFrame = int(getAttr( 'defaultRenderGlobals.startFrame' ))
		endFrame = int(getAttr( 'defaultRenderGlobals.endFrame' ))
		frameStep = int(getAttr( 'defaultRenderGlobals.byFrameStep' ))

	# CREATE BATCH FILE AND FILL IT WITH MAIN ENVIRONMENT VARIABLES FOR RUNNING OUTSIDE OF MAYA
	if not split or startFrame == endFrame:
		splitNum = 1

	bfList = []
	for bF in xrange( 0, splitNum ):
		bNum = ''
		if split and startFrame != endFrame:
			bNum = '_' + str(bF+1)

		batchFilePath = assPath + assName + bNum + '.bat'
		batchFile = open( batchFilePath, 'w' )
		batchFile.write( 'cd /d "' + assPath + '"\n' )
		if os.getenv('ARNOLD_PATH'):
			batchFile.write( '\nset PATH=' + os.getenv('ARNOLD_PATH').replace('\\','/') + '/bin;' + os.getenv('MAYA_LOCATION') + '/bin' )
		else:
			batchFile.write( '\nset PATH=' + os.getenv('PATH') )
		if os.getenv('YETI_HOME'):
			batchFile.write( ';' + os.getenv('YETI_HOME').replace('\\','/') + '/bin' )
		if os.getenv('XGEN_LOCATION'):
			batchFile.write( ';' + os.getenv('XGEN_LOCATION').replace('\\','/') + 'bin' )
		if os.getenv('BIFROST_LOCATION'):
			batchFile.write( ';' + os.getenv('BIFROST_LOCATION').replace('\\','/') + 'bin' )
		batchFile.write( '\n' )
		batchFile.write( 'set ARNOLD_PLUGIN_PATH=' + os.getenv('ARNOLD_PLUGIN_PATH').replace('\\','/') + '\n' )
		if os.getenv('MTOA_EXTENSIONS_PATH'):
			batchFile.write( 'set MTOA_EXTENSIONS_PATH=' + os.getenv('MTOA_EXTENSIONS_PATH').replace('\\','/') + '\n' )
		# FIX BIFROST ISSUE OF NOT LOADING THROUGH MAYA BY EMPTYING BIFROST_LOCATION VARIABLE
		if os.getenv('BIFROST_LOCATION'):
			batchFile.write( 'set BIFROST_LOCATION=' + '\n' )
		if os.getenv('peregrinel_LICENSE'):
			batchFile.write( 'set peregrinel_LICENSE=' + os.getenv('peregrinel_LICENSE').replace('\\','/') + '\n' )
		if os.getenv('solidangle_LICENSE'):
			batchFile.write( 'set solidangle_LICENSE=' + os.getenv('solidangle_LICENSE').replace('\\','/') + '\n' )
		if os.getenv('PG_IMAGE_PATH'):
			batchFile.write( 'set PG_IMAGE_PATH=' + os.getenv('PG_IMAGE_PATH').replace('\\','/') + '\n' )
		if os.getenv('root'):
			batchFile.write( 'set root=' + os.getenv('root').replace('\\','/') + '\n' )
		batchFile.write( '\n' )

		bfList.append( batchFile )


	# PREPARE ARNOLD OPTIONS
	opt = ' -v ' + str(verbose) + ' -nw 100'
	if int(mtoaVer[0]) < 2:
		opt += ' -g ' + str(gamma) 
	if not progr or anim:
		opt += ' -dp'
	if disableWin or anim:
		opt += ' -dw'
	if cmdLine != '':
		if cmdLine[0] != ' ':
			cmdLine = ' ' + cmdLine
		opt += cmdLine
	opt += ' -ocs "' + colorManagementPrefs( query = True, viewTransformName = True ) + '"'
	
	# GET OUTPUT FORMAT
	outFormat = getAttr( 'defaultRenderGlobals.imfPluginKey' )

	# ENABLE PROGRESS BAR UPDATE
	if gui:
		progressBar( 'ark_mtoa_progBar', edit = True, maxValue = endFrame-startFrame+1, progress = 0 )

	# MANUAL EXPORT LOOP
	cleanList = []
	batched = False
	
	if reverse and anim:
		tmp = startFrame
		startFrame = endFrame
		endFrame = tmp-2
		frameStep = -frameStep
		
	for fr in xrange( startFrame, endFrame+1, frameStep ):
		# SET FRAME AND REFRESH
		currentTime( fr, update = True )
		refresh()
		if gui:
			progressBar( 'ark_mtoa_progBar', edit = True, step = 1*abs(frameStep) )

		# EXPORT ASS
		outAss = arnoldExportAss( filename = assPath + assName, mask = 6399, lightLinks = 1, shadowLinks = 1, startFrame = fr, endFrame = fr, frameStep = 1, expandProcedurals = expand, exportAllShadingGroups = 1 )[0]

		# WRITE BATCH
		if not batched:
			bFi = 0
			for frB in xrange( startFrame, endFrame+1, frameStep ):
				frInd = outAss.rfind( str.zfill( str(fr), padding ) )
				outAssB = outAss[:frInd] + str.zfill( str(frB), padding ) + outAss[frInd+padding:]

				outAssOrig = outAssB
				if outAssB[-4:] != '.ass':
					outAssB += '.ass'

				cmd = 'start /B /LOW /WAIT '
				cmd += 'kick "' + outAssB + '"'
				if outPath != '':
					outImg = outAssOrig.split('/')[-1].replace('.ass', '.' + outFormat)
					# FIX INCONSISTENCY FOR NAME.EXT OUTPUT FORMAT
					if not getAttr( 'defaultRenderGlobals.animation' ) and getAttr( 'defaultRenderGlobals.outFormatControl' ) == 0:
						outImg = '.'.join( outImg.split('.')[:-2] ) + '.' + outFormat

					cmd += ' -o "' + outPath + outImg + '"'
				cmd += opt + ' -logfile ' + outAssB[:-4] + '.log'

				# ADD RENDER REGION DATA
				if region:
					if type(region) == list:
						cmd += ' -rg'
						for val in region:
							cmd += ' ' + str(val)
					elif type(region) == dict:
						if fr in region.keys():
							cmd += ' -rg'
							for val in region[frB]:
								cmd += ' ' + str(val)
						else:
							print( 'WARNING! Frame ' + str(frB) + ' is not in region data file!' )

				cmd += '\n'

				bfList[bFi].write( cmd )
				bFi = (bFi+1)%len(bfList)

				# PREPARE LINES FOR CLEANUP
				cleanList.append( '\ndel "' + outAssB.replace( '/', '\\' ) + '"' )

			# WRITE CLEANUP LINES
			if cleanup:
				for bfFile in bfList:
					bfFile.write( '\n@echo off\n' )
				
				bFi = 0
				for line in cleanList:
					bfList[bFi].write( line )
					bFi = (bFi+1)%len(bfList)

				for bfFile in bfList:
					bfFile.write( '\n\n(goto) 2>nul & del "%~f0"' )
				if not anim:
					for bfFile in bfList:
						bfFile.write( ' & exit' )
			elif not anim:
				for bfFile in bfList:
					bfFile.write( '\nexit' )
			
			for bfFile in bfList:
				bfFile.close()

			batched = True

	# RESTORE ORIGINAL IMAGE NAME
	if assNameOrig == None:
		assNameOrig = ''
	setAttr( 'defaultRenderGlobals.imageFilePrefix', assNameOrig, type = 'string' )

	# RESET PROGRESS BAR
	if gui:
		progressBar( 'ark_mtoa_progBar', edit = True, minValue = -1, progress = -1 )
		progressBar( 'ark_mtoa_progBar', edit = True, minValue = 0 )

	# CALCULATE DURATION
	endTime = time.time()	
	secs = int( (endTime - startTime) % 60 )
	hours = int( (endTime - startTime - secs ) / 3600 )
	mins = int( (endTime - startTime - secs - hours * 3600) / 60 )
	exportTime = str.zfill( str( hours ), 2 ) + ':' + str.zfill( str( mins ), 2 ) + ':' + str.zfill( str( secs ), 2 )

	# FEEDBACK
	ark_mtoa_feedback(  'ARK_MTOA EXPORT INFO',
						'Scene exported at: ' + time.strftime('%H:%M:%S') + ' ' + time.strftime('%d.%m.%Y'),
						'Export path: ' + assPath + assName,
						'Export time: ' + exportTime )

	# RUN BATCH
	if not exportOnly:
		for bfFile in bfList:
			print( 'start ' + str(bfFile).split('\'')[1] )
			os.system( 'start ' + str(bfFile).split('\'')[1] )


# CONVERT OUTPUT PATH TO PROPER FORMAT
def ark_mtoa_outPathConvert( outPath ):
	outPath = outPath.replace( '\\', '/' )
	if outPath.find( '%' ) > -1:
		if outPath[-1] == '/':
			outPath = outPath[:-1]
		for eachOutPath in outPath.split( '/' ):
			if eachOutPath[0] == '%' and eachOutPath[-1] == '%':
				if eachOutPath == '%rlay%':
					conv = editRenderLayerGlobals( query = True, currentRenderLayer = True )
				else:
					conv = workspace( variableEntry = eachOutPath[1:-1] )

				if conv == '':
					conv = os.getenv( eachOutPath[1:-1] )

				if conv != '' and conv != None:
					conv = conv.replace( '\\', '/' )
					if conv[-1] == '/':
						conv = conv[:-1]
					outPath = outPath.replace( eachOutPath, conv )
				else:
					confirmDialog( title = 'Error!', message = 'No project or environment variable: ' + eachOutPath, button = 'CANCEL' )
					return

	if outPath[-1] != '/':
		outPath += '/'

	return outPath


# DEFINE A STORAGE FOR CUSTOM SETTINGS
def ark_mtoa_storage():
	storage = 'defaultArnoldRenderOptions'
	# CREATE ARNOLD NODES IF THEY DON'T EXIST
	if not objExists( storage ):
		mtoa.core.createOptions()
	
	return storage


# CALCULATE AUTOMATIC VERSION FOR THE OUTPUT NAME
def ark_mtoa_autoVer( name='', path='' ):
	storage = ark_mtoa_storage()

	upVer = 0
	for each in os.listdir( path ):
		nameComp = each.split('.')[0][:len(name)] + '_v'
		if name + '_v' == nameComp:
			try:
				upVer = max( upVer, int(each.split('.')[0][len(nameComp):len(nameComp)+3]) )
			except:
				pass
	val = '_v' + str.zfill( str(upVer+1), 3 )

	return val


# GET RENDER REGION FROM MAYA RENDER VIEW AND CONVERT TO ARNOLD FORMAT
def ark_mtoa_region( region=False ):
	ht = getAttr( 'defaultResolution.height' )
	wd = getAttr( 'defaultResolution.width' )

	if not region:
		region = []
		if renderWindowEditor( renderWindowEditor( query = True, editorName = True ), query = True, mq = True ):
			for dim in ['leftRegion', 'topRegion', 'rightRegion', 'bottomRegion']:
				val = getAttr( 'defaultRenderGlobals.' + dim )
				if dim in ['bottomRegion', 'topRegion']:
					val = getAttr( 'defaultResolution.height' ) - getAttr( 'defaultRenderGlobals.' + dim ) - 1
				region.append( val )
		else:
			region = [0, 0, wd-1, ht-1]
	else:
		region = [region[0], getAttr( 'defaultResolution.height' ) - region[1], region[2], getAttr( 'defaultResolution.height' ) - region[3] ]

	return region


# PUT RENDER REGION VALUES INTO GUI
def ark_mtoa_getRegion( ctrl ):
	mode = button( ctrl[1], query = True, label = True )
	if mode == 'bbox':
		region = ark_mtoa_region()
		intFieldGrp( ctrl[0], edit = True, value1 = region[0], value2 = region[1], value3 = region[2], value4 = region[3] )
	elif mode == 'file':
		fileDialogHere = True


# SWITCH REGION DATA MODE
def ark_mtoa_regionMode( ctrl ):
	mode = 'bbox'
	if button( ctrl[1], query = True, label = True ) == 'bbox':
		mode = 'file'
	button( ctrl[1], edit = True, label = mode )	

	if mode == 'file':
		intFieldGrp( ctrl[0], edit = True, manage = False )
		textField( ctrl[2], edit = True, manage = True )
	elif mode == 'bbox':
		intFieldGrp( ctrl[0], edit = True, manage = True )
		textField( ctrl[2], edit = True, manage = False )


# GET OUTPUT PATH AND IMAGE NAME FROM RENDER SETTINGS
def ark_mtoa_output():
	outName = getAttr( 'defaultRenderGlobals.imageFilePrefix' )
	# IF OUTPUT NAME IS NOT DEFINED, USE SCENE NAME (IF IT'S NOT SAVED, USE UNTITLED)
	if outName in [None,'']:
		outName = file( query = True, sceneName	= True, shortName = True )[:-3]
	if outName == '':
		outName = 'untitled'

	outPath = renderSettings( fullPath = True, firstImageName = True )[0]
	outPath = outPath[:outPath.rfind('/')+1]

	return outName, outPath


# GUI CONTROLS DEPENDENCIES
def ark_mtoa_guiSwitch( ctrls, val ):
	for ctrl in ctrls:
		if ctrl[-3:] == 'CHB':
			checkBox( ctrl, edit = True, enable = val )
		elif ctrl[-3:] == 'IFG':
			intFieldGrp( ctrl, edit = True, enable = val )
		elif ctrl[-2:] == 'IF':
			intField( ctrl, edit = True, enable = val )
		elif ctrl[-3:] == 'BTN':
			if 'kick' in ctrl:
				button( ctrl, edit = True, label = val )
			else:
				button( ctrl, edit = True, enable = val )
		elif ctrl[-3:] == 'TFB':
			state = textFieldButtonGrp( ctrl, query = True, editable = True )
			textFieldButtonGrp( ctrl, edit = True, editable = 1-state )
			if state:
				val, val1 = ark_mtoa_output()
				if 'outPath' in ctrl:
					val = val1
				textFieldButtonGrp( ctrl, edit = True, text = val )
		elif ctrl[-2:] == 'TF':
			state = textField( ctrl, query = True, enable = True )
			textField( ctrl, edit = True, enable = 1-state )


# STORE/RESTORE SETTINGS TO/FROM THE SCENE
def ark_mtoa_settings( restore=False ):
	storage = ark_mtoa_storage()

	for attr in [ 'ark_mtoa_outName', 'ark_mtoa_outPath' ]:
		if restore:
			if attributeQuery( attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + attr )
				if val != '':
					textFieldButtonGrp( attr + '_TFB', edit = True, editable = True )
					textFieldButtonGrp( attr + '_TFB', edit = True, text = val )
		else:
			if not attributeQuery( attr, node = storage, exists = True ):
				addAttr( storage, ln = attr, dt = 'string' )
			if textFieldButtonGrp( attr + '_TFB', query = True, editable = True ):
				setAttr( storage + '.' + attr, textFieldButtonGrp( attr + '_TFB', query = True, text = True ), type = 'string' )
			else:
				setAttr( storage + '.' + attr, '', type = 'string' )

	for attr in [ 'ark_mtoa_progr', 'ark_mtoa_autoVer', 'ark_mtoa_uname' ]:
		if restore:
			if attributeQuery( attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + attr )
				checkBox( attr + '_CHB', edit = True, value = val )
				if attr == 'ark_mtoa_region':
					ark_mtoa_guiSwitch( [ "ark_mtoa_region_IFG", "ark_mtoa_region_BTN" ], val )
		else:
			if not attributeQuery( attr, node = storage, exists = True ):
				addAttr( storage, ln = attr, at = 'bool' )
			val = checkBox( attr + '_CHB', query = True, value = True )
			if attr == 'ark_mtoa_progr':
				if checkBox( 'ark_mtoa_anim_CHB', query = True, value = True ):
					val = True
			setAttr( storage + '.' + attr, val )

	for attr in [ 'ark_mtoa_regions' ]:
		if restore:
			if attributeQuery( attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + attr )
				intFieldGrp( attr[:-1] + '_IFG', edit = True, value = [int(v) for v in val.split()] )
		else:
			if not attributeQuery( attr, node = storage, exists = True ):
				addAttr( storage, ln = attr, dt = 'string' )
			setAttr( storage + '.' + attr, str(intFieldGrp( attr[:-1] + '_IFG', query = True, value = True ))[1:-1].replace( 'L', ',' ).replace( ',', '' ), type = 'string' )
	
	for attr in [ 'ark_mtoa_regionFile' ]:
		if restore:
			if attributeQuery( attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + attr )
				textField( attr + '_TF', edit = True, text = val )
		else:
			if not attributeQuery( attr, node = storage, exists = True ):
				addAttr( storage, ln = attr, dt = 'string' )
			setAttr( storage + '.' + attr, textField( attr + '_TF', query = True, text = True ), type = 'string' )
	
	for attr in [ 'ark_mtoa_regionMode' ]:
		if restore:
			if attributeQuery( attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + attr )
				if val == 'file':
					val = 'bbox'
				else:
					val = 'file'
				button( attr + '_BTN', edit = True, label = val )
				exec( button( attr + '_BTN', query = True, command = True ) )
		else:
			if not attributeQuery( attr, node = storage, exists = True ):
				addAttr( storage, ln = attr, dt = 'string' )
			setAttr( storage + '.' + attr, button( attr + '_BTN', query = True, label = True ), type = 'string' )
	

# COLLECT DATA FROM GUI AND RUN THE MAIN PROCEDURE
def ark_mtoa_collect():
	outName = ''
	if textFieldButtonGrp( 'ark_mtoa_outName_TFB', query = True, editable = True ):
		outName = textFieldButtonGrp( 'ark_mtoa_outName_TFB', query = True, text = True )
	outPath = ''
	if textFieldButtonGrp( 'ark_mtoa_outPath_TFB', query = True, editable = True ):
		outPath = textFieldButtonGrp( 'ark_mtoa_outPath_TFB', query = True, text = True )
	
	progr = checkBox( 'ark_mtoa_progr_CHB', query = True, value = True )

	expand = checkBox( 'ark_mtoa_expand_CHB', query = True, value = True )

	autoVer = checkBox( 'ark_mtoa_autoVer_CHB', query = True, value = True )

	uname = checkBox( 'ark_mtoa_uname_CHB', query = True, value = True )

	exportOnly = checkBox( 'ark_mtoa_exportOnly_CHB', query = True, value = True )

	cleanup = checkBox( 'ark_mtoa_cleanup_CHB', query = True, value = True )

	split = checkBox( 'ark_mtoa_split_CHB', query = True, value = True )
	splitNum = intField( 'ark_mtoa_splitNum_IF', query = True, value = True )

	reverse = checkBox( 'ark_mtoa_reverse_CHB', query = True, value = True )

	cmdLine = textFieldGrp( 'ark_mtoa_cmd_TFG', query = True, text = True )

	anim = checkBox( 'ark_mtoa_anim_CHB', query = True, value = True )

	region = False
	if checkBox( 'ark_mtoa_region_CHB', query = True, value = True ):
		mode = button( 'ark_mtoa_regionMode_BTN', query = True, label = True )
		if mode == 'bbox':
			region = [	intFieldGrp( 'ark_mtoa_region_IFG', query = True, value1 = True ),
						intFieldGrp( 'ark_mtoa_region_IFG', query = True, value2 = True ), 
						intFieldGrp( 'ark_mtoa_region_IFG', query = True, value3 = True ), 
						intFieldGrp( 'ark_mtoa_region_IFG', query = True, value4 = True ) ]
		elif mode == 'file':
			regionFile = textField( 'ark_mtoa_regionFile_TF', query = True, text = True ).replace( '\\', '/' )
			if regionFile != '':
				regionFile = ark_mtoa_outPathConvert( regionFile[:regionFile.rfind('/')] ) + regionFile[regionFile.rfind('/')+1:]
				if os.path.isfile( regionFile ):
					region = {}
					reg_f = open( regionFile, 'r' )
					for line in reg_f:
						regData = line.split()
						try:
							region[int(float(regData[0]))] = ark_mtoa_region( [ int(float(regData[1])), int(float(regData[4])), int(float(regData[3])), int(float(regData[2])) ] )
						except:
							region = False
							print( 'WARNING! Incorrect region line format: ' + line )
					reg_f.close()

	ark_mtoa_do( outName = outName, outPath = outPath, progr = progr, expand = expand, autoVer = autoVer, uname = uname, exportOnly = exportOnly, cleanup = cleanup, split = split, splitNum = splitNum, reverse = reverse, cmdLine = cmdLine, anim = anim, region = region, gui=True )


# (NON)GUI
def ark_mtoa( mode='gui' ):
	if mode in [ 'frame', 'anim' ]:
		storage = ark_mtoa_storage()

		outName = ''
		if attributeQuery( 'ark_mtoa_outName', node = storage, exists = True ):
			outName = getAttr( storage + '.ark_mtoa_outName' )

		outPath = ''
		if attributeQuery( 'ark_mtoa_outPath', node = storage, exists = True ):
			outPath = getAttr( storage + '.ark_mtoa_outPath' )

		progr = True
		if attributeQuery( 'ark_mtoa_progr', node = storage, exists = True ):
			progr = getAttr( storage + '.ark_mtoa_progr' )

		autoVer = True
		if attributeQuery( 'ark_mtoa_autoVer', node = storage, exists = True ):
			autoVer = getAttr( storage + '.ark_mtoa_autoVer' )

		uname = False
		if attributeQuery( 'ark_mtoa_uname', node = storage, exists = True ):
			uname = getAttr( storage + '.ark_mtoa_uname' )

		region = False
		if attributeQuery( 'ark_mtoa_region', node = storage, exists = True ):
			if getAttr( storage + '.ark_mtoa_region' ):
				region = [int(v) for v in getAttr( storage + '.ark_mtoa_regions' ).split()]

		anim = False
		if mode == 'anim':
			anim = True

		ark_mtoa_do( outName = outName, outPath = outPath, progr = progr, autoVer = autoVer, uname = uname, exportOnly = False, cleanup = True, anim = anim, region = region, gui=False )
	else:
		guiWidth = 450

		outName, outPath = ark_mtoa_output()
		
		if window( 'ark_mtoa_win', exists = True ):
			deleteUI( 'ark_mtoa_win' )

		win = window( 'ark_mtoa_win', title = 'Kick Maya ASS', sizeable = False )

		columnLayout( adj = True, width = 400, columnAttach = ['both', 3] )

		textFieldButtonGrp( 'ark_mtoa_outName_TFB',
							label = 'Name:',
							annotation = 'Custom output file name. Press "edit" to enable, otherwise Render Settings will be used.',
							text = outName,
							editable = False,
							buttonLabel = 'edit',
							columnWidth3 = [52, 354, 32],
							buttonCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_outName_TFB" ], False )' )

		textFieldButtonGrp( 'ark_mtoa_outPath_TFB',
							label = 'Path:',
							annotation = 'Custom output path. Press "edit" to enable, otherwise Render Settings will be used.',
							text = outPath,
							editable = False,
							buttonLabel = 'edit',
							columnWidth3 = [52, 354, 32],
							buttonCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_outPath_TFB" ], False )' )

		separator( style = 'in' )


		rowLayout( numberOfColumns = 8, height = 25 )

		checkBox(	'ark_mtoa_progr_CHB', 
					label = 'Progressive',
					annotation = 'Enables Progressive Mode, defined in Render Settings. Gets disabled automatically for animations.',
					width = 81,
					value = True,
					enable = True )

		checkBox(	'ark_mtoa_expand_CHB', 
					label = 'Expand',
					annotation = 'Enables Expand Procedurals option.',
					width = 56,
					value = False,
					enable = True )

		separator( style = 'single', horizontal = False, height = 20, width = 10 )

		checkBox(	'ark_mtoa_autoVer_CHB', 
					label = 'Version',
					annotation = 'Adds _v### to the output file name. Increments with every render and if the version already exists in the output path.',
					width = 63,
					value = True,
					enable = True )

		checkBox(	'ark_mtoa_uname_CHB', 
					label = 'Unique',
					annotation = 'Adds date and time to the file name to make it unique (up to a second).',
					width = 57,
					value = False )

		separator( style = 'single', horizontal = False, height = 20, width = 10 )

		checkBox(	'ark_mtoa_exportOnly_CHB', 
					label = 'Export Only',
					annotation = 'Disables execution of the created batch file.',
					width = 86,
					value = False )

		checkBox(	'ark_mtoa_cleanup_CHB', 
					label = 'Cleanup',
					annotation = 'Deletes ASS and batch files after rendering.',
					width = 86,
					value = True )

		setParent( '..' )
		separator( style = 'in' )


		rowLayout( numberOfColumns = 6, height = 25 )

		checkBox(	'ark_mtoa_split_CHB', 
					label = 'Split Batch',
					annotation = 'Split batch into several files to render on different hosts.',
					width = 80,
					value = False,
					enable = False,
					onCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_splitNum_IF" ], True )',
					offCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_splitNum_IF" ], False )' )

		intField(	'ark_mtoa_splitNum_IF',
					annotation = 'Number of files to split batch into.',
					width = 20,
					minValue = 1,
					value = 2,
					enable = False )

		separator( style = 'single', horizontal = False, height = 20, width = 10 )

		checkBox(	'ark_mtoa_reverse_CHB', 
					label = 'Reverse',
					annotation = 'Reverse frame range - start rendering from the last frame.',
					width = 60,
					value = False,
					enable = False )

		separator( style = 'single', horizontal = False, height = 20, width = 10 )

		textFieldGrp( 'ark_mtoa_cmd_TFG',
					label = 'Cmd:',
					annotation = 'Command line options.',
					columnWidth2 = [ 25, 223 ],
					editable = True )

		setParent( '..' )
		separator( style = 'in' )


		rowLayout( numberOfColumns = 7, height = 25 )

		checkBox(	'ark_mtoa_anim_CHB',
					label = 'Animation',
					annotation = 'If disabled, current frame will be rendered. If enabled, frame settings from Render Settings (enable animation there to render frame sequence).',
					value = False,
					width = 78,
					onCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_kick_BTN" ], "Kick Frame Range" ); ark_mtoa_guiSwitch( [ "ark_mtoa_progr_CHB" ], False ); ark_mtoa_guiSwitch( [ "ark_mtoa_split_CHB" ], True ); ark_mtoa_guiSwitch( [ "ark_mtoa_splitNum_IF" ], checkBox( "ark_mtoa_split_CHB", query = True, value = True ) ); ark_mtoa_guiSwitch( [ "ark_mtoa_reverse_CHB" ], True )',
					offCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_kick_BTN" ], "Kick Current Frame" ); ark_mtoa_guiSwitch( [ "ark_mtoa_progr_CHB" ], True ); ark_mtoa_guiSwitch( [ "ark_mtoa_split_CHB" ], False ); ark_mtoa_guiSwitch( [ "ark_mtoa_splitNum_IF" ], False ); ark_mtoa_guiSwitch( [ "ark_mtoa_reverse_CHB" ], False )' )

		separator( style = 'single', horizontal = False, height = 20, width = 10 )

		checkBox(	'ark_mtoa_region_CHB',
					label = 'Region:',
					annotation = 'Enables render region. Order of values is: left, top, right, bottom with starting point in top left corner.',
					value = False,
					width = 59,
					onCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_region_IFG", "ark_mtoa_region_BTN", "ark_mtoa_regionMode_BTN", "ark_mtoa_regionFile_TF" ], True )',
					offCommand = 'ark_mtoa_guiSwitch( [ "ark_mtoa_region_IFG", "ark_mtoa_region_BTN", "ark_mtoa_regionMode_BTN", "ark_mtoa_regionFile_TF" ], False )' )

		columnLayout()
		fieldWidth = 53
		intFieldGrp( 'ark_mtoa_region_IFG',
					annotation = 'Render region. Order of values is: left, top, right, bottom with starting point in top left corner.',
					numberOfFields = 4,
					width = 219,
					columnWidth4 = [fieldWidth, fieldWidth, fieldWidth, fieldWidth],
					manage = True,
					enable = False )

		textField( 'ark_mtoa_regionFile_TF',
					annotation = 'Render region file. Format for each line: frame xmin ymin xmax ymax.',
					width = 219,
					manage = False,
					enable = False )
		setParent( '..' )


		button(		'ark_mtoa_region_BTN',
					label = 'get',
					annotation = 'Takes render region from Maya Render View. Order of values is: left, top, right, bottom with starting point in top left corner. Or loads file.',
					width = 30,
					enable = False,
					command = 'ark_mtoa_getRegion( [ "ark_mtoa_region_IFG", "ark_mtoa_regionMode_BTN", "ark_mtoa_regionFile_TF" ] )' )

		button(		'ark_mtoa_regionMode_BTN',
					label = 'bbox',
					annotation = 'Choose mode for region data.',
					width = 32,
					enable = False,
					command = 'ark_mtoa_regionMode( [ "ark_mtoa_region_IFG", "ark_mtoa_regionMode_BTN", "ark_mtoa_regionFile_TF" ] )' )

		ark_mtoa_getRegion( [ "ark_mtoa_region_IFG", "ark_mtoa_regionMode_BTN", "ark_mtoa_regionFile_TF" ] )

		setParent( '..' )

		separator( style = 'in' )

		rowLayout( numberOfColumns = 2 )

		button(		'ark_mtoa_kick_BTN', 
					label = 'Kick Current Frame',
					annotation = 'Kicks ASS... And save settings.',
					width = guiWidth/2-6,
					command = 'ark_mtoa_settings();ark_mtoa_collect()' )

		button(		'ark_mtoa_saveClose_BTN', 
					label = 'Save && Close',
					annotation = 'Closes the tool, but saves settings. Use window controls to close without saving.',
					width = guiWidth/2-6,
					command = 'ark_mtoa_settings();deleteUI( "ark_mtoa_win" )' )

		setParent( '..' )

		# PROGRESS BAR
		progressBar( 'ark_mtoa_progBar', height = 15 )

		# RESTORE TOOL SETTINGS IF ANY
		ark_mtoa_settings( restore=True )

		showWindow( win )
		window( win, edit = True, width = guiWidth, height = 180 )
		setFocus( win )
