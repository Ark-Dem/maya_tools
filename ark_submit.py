#------------------------------------------------------------------maya-
# file: ark_submit.py
# version: 0.10
# date: 2016.03.13
# author: Arkadiy Demchenko (sagroth@sigillarium.com)
#-----------------------------------------------------------------------
# 2016.03.13 (v0.10) - initial release, basic functionality
#-----------------------------------------------------------------------
# Utility for exporting scene from Maya and sending it to farm.
# - replace _browse with Maya dialogs
# - update project specific paths
# - perTaskShaders
# - multiLayer
# - byFrame
# - perFrame submit
#-----------------------------------------------------------------------
from maya.cmds import *
from string import zfill
import maya.mel
import os, os.path, time, re


# VARIABLES
deadCmd = 'deadlineCommand' # PATH TO DEADLINE BINARIES
if os.getenv( 'DEADLINE_PATH' ) != None:
	deadCmd = os.getenv( 'DEADLINE_PATH' ).replace( '\\', '/' ) + '/' + deadCmd

deadTempPath = 'c:/Temp/deadline/' # PATH TO DEADLINE JOB SUBMISSION FILES
if os.getenv( 'DEAD_TEMP_PATH' ) != None:
	deadTempPath = os.getenv( 'DEAD_TEMP_PATH' ).replace( '\\', '/' ) 
	if deadTempPath[-1] != '/':
		deadTempPath += '/'

infoFileNameBase = 'mentalray_plugin_info' # NAME OF THE FILE TO STORE INFO ABOUT THE JOB
jobFileNameBase = 'mentalray_plugin_job' # NAME OF THE FILE TO STORE THE JOB DATA

sceneOutputDir = 'm:/' # DEFAULT SCENE STORAGE
outputDir = 'x:/BABA_YAGA/result/' # DEFAULT RENDERED IMAGES STORAGE
dataDir = 'x:/BABA_YAGA/data/' # DEFAULT DATA STORAGE
tempDir = 'c:/Temp/' # TEMP DIR

ark_submit_storage = 'defaultRenderGlobals' # NODE TO STORE USER SETTINGS


# VERSION CHECK
def ark_submit_version():
	version = '0.10'
	confirmDialog( title = 'Version', message = 'ark_submit v' + version, button = [ 'OK' ] )


# BROWSE PATHS
def ark_submit_browse( ctrl, mode ):
	curDir = textFieldButtonGrp( ctrl, query = True, text = True ).replace( '\\', '/' )
	if mode == 'dir':
		newDir = maya.mel.eval( "system( \"" + deadCmd + " -GetDirectory \\\"" + curDir + "\\\"\" )" ).split()
	if mode == 'file':
		newDir = maya.mel.eval( "system( \"" + deadCmd + " -SelectFilenameLoad \\\"" + curDir + "\\\"\" )" ).split()

	if newDir != []:
		newDir = newDir[0].replace( '\\', '/' )
		if newDir[-1:] != '/' and mode == 'dir':
			newDir += '/'
		textFieldButtonGrp( ctrl, edit = True, text = newDir )


# PROJECT SPECIFIC PATHS
def ark_submit_projPath():
	projectPathName = workspace( query = True, fullName = True )

	projectPathNameSplit = projectPathName.split( '/' )
	projPath = ''
	if projectPathNameSplit[0] == 'S:' and projectPathNameSplit[1] == 'BABA_YAGA':
		for each in projectPathNameSplit[3:]:
			if re.match( 'P[0-9]*', each ) or re.match( 'Ep[0-9]*', each ):
				projPath += each + '_'
			else:
				if each == 'LAYOUTS':
					each = 'Feature'
				projPath += each + '/'
	else:
		projPath += '_tmp/'
	
	return projPath 


# LISTS ALL RENDERABLE CAMERAS
def ark_submit_renderCams():
	cams = ls( type = 'camera' )

	renderCams = []
	for eachCam in cams:
		if getAttr( eachCam + '.renderable' ):
			renderCams.append( eachCam )

	return renderCams


# LISTS ALL RENDERABLE LAYERS EXCEPT REFERENCED ONES
def ark_submit_renderLays():
	lays = ls( type = 'renderLayer' )

	renderLays = []
	for eachLay in lays:
		if getAttr( eachLay + '.renderable' ) and eachLay.find( ':' ) < 0:
			renderLays.append( eachLay )

	return renderLays


# STORE SETTINGS
def ark_submit_store():
	storage = ark_submit_storage

	if not attributeQuery( 'submit_jobName', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_jobName', dt = 'string' )
	setAttr( storage + '.submit_jobName', textFieldGrp( 'ark_submit_jobName_ctrl', query = True, text = True ), type = 'string' )

	if not attributeQuery( 'submit_group', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_group', dt = 'string' )
	setAttr( storage + '.submit_group', optionMenuGrp( 'ark_submit_group_ctrl', query = True, value = True ), type = 'string' )

	if not attributeQuery( 'submit_priority', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_priority', at = 'long' )
	setAttr( storage + '.submit_priority', intSliderGrp( 'ark_submit_priority_ctrl', query = True, value = True ) )

	if not attributeQuery( 'submit_frameList', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_frameList', dt = 'string' )
	setAttr( storage + '.submit_frameList', textFieldGrp( 'ark_submit_frameList_ctrl', query = True, text = True ), type = 'string' )

	if not attributeQuery( 'submit_framesPerHost', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_framesPerHost', at = 'long' )
	setAttr( storage + '.submit_framesPerHost', intSliderGrp( 'ark_submit_framesPerHost_ctrl', query = True, value = True ) )

	if not attributeQuery( 'submit_plug', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_plug', dt = 'string' )
	setAttr( storage + '.submit_plug', optionMenuGrp( 'ark_submit_plugin_ctrl', query = True, value = True ), type = 'string' )

	if not attributeQuery( 'submit_taskSize', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_taskSize', at = 'long' )
	setAttr( storage + '.submit_taskSize', intSliderGrp( 'ark_submit_taskSize_ctrl', query = True, value = True ) )

	if not attributeQuery( 'submit_commandLine', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_commandLine', dt = 'string' )
	setAttr( storage + '.submit_commandLine', textFieldGrp( 'ark_submit_commandLine_ctrl', query = True, text = True ), type = 'string' )

	if not attributeQuery( 'submit_fileName', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_fileName', dt = 'string' )
	setAttr( storage + '.submit_fileName', textFieldGrp( 'ark_submit_fileName_ctrl', query = True, text = True ), type = 'string' )

	if not attributeQuery( 'submit_out', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_out', dt = 'string' )
	setAttr( storage + '.submit_out', textFieldGrp( 'ark_submit_out_ctrl', query = True, text = True ), type = 'string' )

	if not attributeQuery( 'submit_scene', node = storage, exists = True ):
		addAttr( storage, ln = 'submit_scene', dt = 'string' )
	setAttr( storage + '.submit_scene', textFieldGrp( 'ark_submit_scene_ctrl', query = True, text = True ), type = 'string' )


# RESTORE SETTINGS
def ark_submit_restore():
	storage = ark_submit_storage

	rLayer = editRenderLayerGlobals( query = True, currentRenderLayer = True )
	if rLayer == 'defaultRenderLayer':
		rLayer = 'masterLayer'

	if attributeQuery( 'submit_jobName', node = storage, exists = True ):
		jobName = getAttr( storage + '.submit_jobName' )
	else:
		jobName = file( query = True, sceneName	= True, shortName = True )[:-3]
	if jobName == '':
		jobName = 'untitled'

	if attributeQuery( 'submit_group', node = storage, exists = True ):
		group = getAttr( storage + '.submit_group' )
		groupItems = optionMenuGrp( 'ark_submit_group_ctrl', query = True, ill = True )
		groupList = []
		for eachGroup in groupItems:
			groupList.append( menuItem( eachGroup, query = True, label = True ) )
		if not group in groupList:
			group = 'none'
	else:
		group = 'none'

	if attributeQuery( 'submit_priority', node = storage, exists = True ):
		priority = getAttr( storage + '.submit_priority' )
	else:
		priority = 50

	if attributeQuery( 'submit_frameList', node = storage, exists = True ):
		frameList = getAttr( storage + '.submit_frameList' )
	else:
		startFrame = int( getAttr( 'defaultRenderGlobals.startFrame' ) )
		endFrame = int( getAttr( 'defaultRenderGlobals.endFrame' ) )
		frameList = str(startFrame) + '-' + str(endFrame)

	if attributeQuery( 'submit_framesPerHost', node = storage, exists = True ):
		framesPerHost = getAttr( storage + '.submit_framesPerHost' )
	else:
		framesPerHost = 1

	if attributeQuery( 'submit_plug', node = storage, exists = True ):
		plug = getAttr( storage + '.submit_plug' )
		plugItems = optionMenuGrp( 'ark_submit_plugin_ctrl', query = True, ill = True )
		plugList = []
		for eachPlug in plugItems:
			plugList.append( menuItem( eachPlug, query = True, label = True ) )
		if not plug in plugList:
			plug = '5.0.2.4'
	else:
		plug = '5.0.2.4'

	if attributeQuery( 'submit_taskSize', node = storage, exists = True ):
		taskSize = getAttr( storage + '.submit_taskSize' )
	else:
		taskSize = 64

	if attributeQuery( 'submit_commandLine', node = storage, exists = True ):
		commandLine = getAttr( storage + '.submit_commandLine' )
	else:
		commandLine = ''

	projectPathName = workspace( query = True, fullName = True )
	projectPath = projectPathName + '/' + jobName + '/' + jobName + '.ass.gz'
	projPath = ark_submit_projPath()

	if attributeQuery( 'submit_fileName', node = storage, exists = True ):
		fileName = getAttr( storage + '.submit_fileName' )
	else:
		if rLayer != 'masterLayer':
			fileName = rLayer[rLayer.rfind( ':' )+1:]
		else:
			fileName = jobName

	if attributeQuery( 'submit_out', node = storage, exists = True ):
		out = getAttr( storage + '.submit_out' )
	else:
		out = outputDir + projPath + 'render/'

	if attributeQuery( 'submit_scene', node = storage, exists = True ):
		scene = getAttr( storage + '.submit_scene' )
	else:
		scene = sceneOutputDir + projPath

	textFieldGrp( 'ark_submit_jobName_ctrl', edit = True, text = jobName )

	optionMenuGrp( 'ark_submit_group_ctrl', edit = True, value = group )
	intSliderGrp( 'ark_submit_priority_ctrl', edit = True, value = priority )

	textFieldGrp( 'ark_submit_frameList_ctrl', edit = True, text = frameList )
	intSliderGrp( 'ark_submit_framesPerHost_ctrl', edit = True, value = framesPerHost )

	optionMenuGrp( 'ark_submit_plugin_ctrl', edit = True, value = plug )
	intSliderGrp( 'ark_submit_taskSize_ctrl', edit = True, value = taskSize )
	textFieldGrp( 'ark_submit_commandLine_ctrl', edit = True, text = commandLine )

	textFieldGrp( 'ark_submit_fileName_ctrl', edit = True, text = fileName )
	textFieldGrp( 'ark_submit_out_ctrl', edit = True, text = out )
	textFieldGrp( 'ark_submit_scene_ctrl', edit = True, text = scene )


# SUBMIT JOB
def ark_submit_submitJob( *args ): 
	sceneName, comment, group, priority, machineLimit, concur, suspended, frames, framesPerHost, plug, taskSize, cmd, fileName, output, scene = args

	# SET UNIQUE INFO/JOB FILE NAMES
	infoFileName = infoFileNameBase + '_' + sceneName + '.' + time.strftime('%y%m%d') + '-' + time.strftime('%H%M%S')
	jobFileName = jobFileNameBase + '_' + sceneName + '.' + time.strftime('%y%m%d') + '-' + time.strftime('%H%M%S')
	
	# CREATE DEADLINE TEMP DIR IF IT DOESN'T EXIST ALREADY
	if not os.path.exists( deadTempPath ):
		os.makedirs( deadTempPath )
		print 'Creating Deadline temp dir: ' + deadTempPath

	# DEFINE DEADLINE JOB PLUGIN
	plugs = { '5.0.2.4':'Arnold5' }
	plug = plugs[ plug ]

	# ARNOLD PLUGIN PATHS
	if os.getenv( 'ARNOLD_PLUGIN_PATH' ):
		varVal = os.getenv( 'ARNOLD_PLUGIN_PATH' ).replace( '\\', '/' )
		if varVal != '':
			for each in varVal.split(';'):
				cmd += ' -l "' + each + '"'
	
	# ADDITIONAL ENVIRONMENT VARIABLES
	pathVar = ''
	for eachVar in [ 'YETI_HOME', 'MISC_DIR' ]:
		if os.getenv( eachVar ):
			varVal = os.getenv( eachVar ).replace( '\\', '/' )
			if varVal != '':
				if pathVar != '':
					if pathVar[-1] != ';':
						pathVar += ';'
				if varVal[-1] != '/':
					varVal += '/'
				pathVar += varVal + 'bin'

	# CREATE BATCH FILE WITH SUBMIT COMMAND FOR MANUAL SUBMISSION IF NEEDED
	batFile = open( deadTempPath + 'submitJob.bat', 'w' )

	# CREATE DEADLINE INFO FILE
	infoDict = { 'Name':sceneName,
				 'Comment':comment, 
				 'Frames':','.join( str(fr) for fr in frames ), 
				 'Plugin':plug, 
				 'Group':group,
				 'Priority':priority, 
				 'ChunkSize':framesPerHost,
				 'ConcurrentTasks':concur,
				 'MachineLimit':machineLimit }

	infoDictSort = [ 'Name', 'Comment', 'Frames', 'Plugin', 'Group', 'Priority', 'ChunkSize', 'ConcurrentTasks', 'MachineLimit' ]

	if suspended == 1:
		infoDict[ 'InitialStatus' ] = 'Suspended'
		infoDictSort.append( 'InitialStatus' )
	
	if pathVar != '':
		infoDict[ 'EnvironmentKeyValue0' ] = 'PATH=' + pathVar
		infoDictSort.append( 'EnvironmentKeyValue0' )

	infoFile = open( deadTempPath + infoFileName + '.job', 'w' )
	for each in infoDictSort:
		infoFile.write( each + '=' + infoDict[each] + '\n' )
	infoFile.close()

	# CREATE DEADLINE JOB FILE
	jobDict = { 'InputFile':scene + '.' + zfill( frames[0], 4 ) + '.ass.gz', 
				'OutputFile':output + fileName + '..exr', 
				'Verbose':'4',
				'Threads':'0', 
				'Build':'None', 
				'CommandLineOptions':cmd }
	
	jobDictSort = [ 'InputFile', 'OutputFile', 'Verbose', 'Threads', 'Build', 'CommandLineOptions' ]

	jobFile = open( deadTempPath + jobFileName + '.job', 'w' )
	for each in jobDictSort:
		jobFile.write( each + '=' + jobDict[each] + '\n' )
	jobFile.close()

	batFile.write( deadCmd + ' "' + deadTempPath + infoFileName + '.job" "' + deadTempPath + jobFileName + '.job"\r\n' )

	procCmd = 'system( "' + deadCmd + ' \\"' + deadTempPath + infoFileName + '.job\\" \\"' + deadTempPath + jobFileName + '.job\\"" );'
	process = maya.mel.eval( procCmd )

	batFile.close()


# EXPORT SCENE, RUN SUBMIT
def ark_submit_exportScene( *args ):
	sceneName, comment, group, priority, machineLimit, concur, suspended, frameList, framesPerHost, plug, taskSize, cmd, multiLayer, fileName, output, scene, feedDialog = args

	# STORE ORIGINAL SETTINGS
	curFrame = currentTime( query = True )
	startFrame = int( getAttr( 'defaultRenderGlobals.startFrame' ) )
	endFrame = int( getAttr( 'defaultRenderGlobals.endFrame' ) )
	anim = getAttr( 'defaultRenderGlobals.animation' )
	byFrameStep = getAttr( 'defaultRenderGlobals.byFrameStep' )
	imageFilePrefix = getAttr( 'defaultRenderGlobals.imageFilePrefix' )
	if imageFilePrefix == None:
		imageFilePrefix = ''

	# SET FIXED SETTINGS
	setAttr( 'defaultRenderGlobals.animation', 1 )
	setAttr( 'defaultRenderGlobals.outFormatControl', 0 )
	setAttr( 'defaultRenderGlobals.pff', 1 )
	setAttr( 'defaultRenderGlobals.extensionPadding', 4 )
	setAttr( 'defaultRenderGlobals.byFrameStep', 1 )

	# IF MULTIPLE RENDERABLE CAMERAS EXIST OR THE ONLY RENDERABLE CAMERA IS A PART OF STEREO RIG, ADD CAMERA NAME TO FILE NAME
	renderCams = ark_submit_renderCams()
	addCamName = ''
	refCams = 0
	if len( renderCams ) > 1:
		addCamName = '_<Camera>'
		if fileName[-2:] == '_L' or fileName[-2:] == '_R':
			fileName = fileName[:-2]
	else:
		camConns = listConnections( listRelatives( renderCams[0], parent = True )[0] + '.message', s = False, d = True )
		if camConns != None:
			for eachConn in camConns:
				if objectType( eachConn ) == 'stereoRigTransform':
					addCamName = '_<Camera>'
					if fileName[-2:] == '_L' or fileName[-2:] == '_R':
						fileName = fileName[:-2]

	setAttr( 'defaultRenderGlobals.imageFilePrefix', fileName + addCamName, type = 'string' )

	# PREPARE THE LIST OF FRAMES TO RENDER
	frames = []
	for frame in frameList.split(','):
		if '-' in frame:
			frames += range( int(frame.split('-')[0]), int(frame.split('-')[1])+1 )
		else:
			frames.append( int(frame) )
	frames = list( set( frames ) )
	frames.sort()

	# ENABLE PROGRESS BAR UPDATE
	progressBar( 'ark_submit_progBar_ctrl', edit = True, maxValue = len( frames ), progress = 0 )

	# START TIMER
	startTime = time.clock()

	# EXPORT
	for fr in frames:
		currentTime( fr, update = True )
		refresh()
		#print 'Exporting frame ' + str(fr)
		progressBar( 'ark_submit_progBar_ctrl', edit = True, step = 1 )
		arnoldExportAss( filename = scene, mask = 255, lightLinks = 1, shadowLinks = 1, startFrame = fr, endFrame = fr, frameStep = 1, compressed = 1 )
	
	# SUBMIT
	ark_submit_submitJob( sceneName, comment, group, priority, machineLimit, concur, suspended, frames, framesPerHost, plug, taskSize, cmd, fileName, output, scene )

	# RETURN TO ORIGINAL FRAME
	currentTime( curFrame, update = True )

	# CALCULATE DURATION
	endTime = time.clock()	
	secs = int( (endTime - startTime) % 60 )
	hours = int( (endTime - startTime - secs ) / 3600 )
	mins = int( (endTime - startTime - secs - hours * 3600) / 60 )
	exportTime = zfill( str( hours ), 2 ) + ':' + zfill( str( mins ), 2 ) + ':' + zfill( str( secs ), 2 )

	# RESET PROGRESS BAR
	progressBar( 'ark_submit_progBar_ctrl', edit = True, progress = 0 )

	# RESTORE ORIGINAL RENDER SETTINGS
	setAttr( 'defaultRenderGlobals.imageFilePrefix', imageFilePrefix, type = 'string' )
	setAttr( 'defaultRenderGlobals.byFrameStep', byFrameStep )
	setAttr( 'defaultRenderGlobals.startFrame', startFrame )
	setAttr( 'defaultRenderGlobals.endFrame', endFrame )
	setAttr( 'defaultRenderGlobals.animation', anim )

	# FEEDBACK
	feedback = ' Deadline job "' + sceneName + '" successfully submitted at ' + time.strftime('%H:%M:%S') + ' ' + time.strftime('%d.%m.%Y')
	liner = '#'
	for i in xrange( 0, len( feedback ) ):
		liner += '#'
	print ''
	print liner
	print feedback
	print ' Mi generation time: ' + exportTime
	print liner
	print ''
	
	if feedDialog:
		confirmDialog( title = 'Submitted', message = ' Deadline job "' + sceneName + '" successfully submitted in ' + exportTime, button = [ 'OK' ] )


# COLLECT GUI DATA, RUN EXPORT
def ark_submit_do( updateOnly, feedDialog ):
	# CHECK IF AT LEAST ONE RENDERABLE CAMERA EXISTS
	renderCams = ark_submit_renderCams()
	if len( renderCams ) < 1:
		confirmDialog( title = 'Error', message = 'No renderable cameras!', button = [ 'CANCEL' ] )
		return

	# GET DATA FROM SCENE
	rLayer = editRenderLayerGlobals( query = True, currentRenderLayer = True )
	if rLayer == 'defaultRenderLayer':
		rLayer = 'masterLayer'

	projPath = ark_submit_projPath()

	startFrame = int( getAttr( 'defaultRenderGlobals.startFrame' ) )
	endFrame = int( getAttr( 'defaultRenderGlobals.endFrame' ) )

	# GET DATA FROM GUI
	sceneName = textFieldGrp( 'ark_submit_jobName_ctrl', query = True, text = True )
	if sceneName == '':
		sceneName = 'untitled'
	comment = textFieldGrp( 'ark_submit_comment_ctrl', query = True, text = True )

	group = optionMenuGrp( 'ark_submit_group_ctrl', query = True, value = True )
	priority = str( intSliderGrp( 'ark_submit_priority_ctrl', query = True, value = True ) )
	machineLimit = str( intSliderGrp( 'ark_submit_machineLimit_ctrl', query = True, value = True ) )
	concur = str( intSliderGrp( 'ark_submit_concur_ctrl', query = True, value = True ) )
	suspended = checkBox( 'ark_submit_suspended_ctrl', query = True, value = True )

	frameList = textFieldGrp( 'ark_submit_frameList_ctrl', query = True, text = True )
	if frameList == '':
		frameList = (str(startFrame) + '-' + str(endFrame)) 
	framesPerHost = str( intSliderGrp( 'ark_submit_framesPerHost_ctrl', query = True, value = True ) )
	
	plug = optionMenuGrp( 'ark_submit_plugin_ctrl', query = True, value = True )
	taskSize = str( intSliderGrp( 'ark_submit_taskSize_ctrl', query = True, value = True ) )
	cmd = textFieldGrp( 'ark_submit_commandLine_ctrl', query = True, text = True )
	multiLayer = checkBox( 'ark_submit_multiLayer_ctrl', query = True, value = True )

	fileName = textFieldGrp( 'ark_submit_fileName_ctrl', query = True, text = True )
	if fileName == '':
		fileName = rLayer[rLayer.rfind( ':' )+1:]

	scene = textFieldButtonGrp( 'ark_submit_scene_ctrl', query = True, text = True ).replace( '\\', '/' )
	if scene == '':
		scene = sceneOutputDir + projPath
	else:
		if scene[-1:] != '/':
			scene += '/'
		if not os.path.exists( scene ):
			os.makedirs( scene )
			print 'Creating mi-file dir: ' + scene
	scene += sceneName + '__' + fileName + '.' + time.strftime('%y%m%d') + '-' + time.strftime('%H%M%S')

	output = textFieldGrp( 'ark_submit_out_ctrl', query = True, text = True ).replace( '\\', '/' )
	if output == '':
		output = outputDir + projPath + 'render/_preview/'
	else:
		if output[-1:] != '/':
			output += '/'
		if not os.path.exists( output ):
			os.makedirs( output )
			print 'Creating render output dir: ' + output

	if not updateOnly:
		ark_submit_exportScene( sceneName, comment, group, priority, machineLimit, concur, suspended, frameList, framesPerHost, plug, taskSize, cmd, multiLayer, fileName, output, scene, feedDialog )


# GUI
def ark_submit():
	if window( 'ark_submit_win', exists = True ):
		deleteUI( 'ark_submit_win' )
	
	win = window( 'ark_submit_win', title = 'Submit Scene to Farm', sizeable = False )

	textWidth = 90
	fieldWidth = 500
	sliderFieldWidth = 50
	fieldButtonWidth = 75
	doubleButton = 304

	columnLayout( adj = True )
	
	# JOB INFO
	frameLayout( label = ' Job Info', 
				 labelVisible = True, 
				 borderVisible = False, 
				 collapsable = False )

	columnLayout( adj = True, rowSpacing = 4, columnAttach = [ 'both', 4 ] )

	textFieldGrp( 'ark_submit_jobName_ctrl',
				  label = 'Job Name ', 
				  columnWidth2 = [ textWidth, fieldWidth ] )

	textFieldGrp( 'ark_submit_comment_ctrl',
				  label = 'Comment ', 
				  columnWidth2 = [ textWidth, fieldWidth ] )

	setParent( '..' )
	setParent( '..' )

	# RENDER SETTINGS
	frameLayout( label = ' Render Settings ', 
				 labelVisible = True, 
				 borderVisible = False, 
				 collapsable = False )

	columnLayout( adj = True, rowSpacing = 4, columnAttach = [ 'both', 4 ] )

	optionMenuGrp( 'ark_submit_group_ctrl',
				   label = 'Group ',
				   columnWidth2 = [ textWidth, fieldWidth ],
				   columnAlign = [ 1, 'right' ] )
	groupList = maya.mel.eval( 'system( "' + deadCmd + ' -groups" )' )
	if groupList[:4] == 'none':
		for group in groupList.split():
			menuItem( label = group )
	else:
		menuItem( label = 'none' )

	intSliderGrp( 'ark_submit_priority_ctrl',
				  label = 'Priority ',
				  minValue = 0,
				  maxValue = 100,
				  field = True,
				  fieldMinValue = 0,
				  fieldMaxValue = 100,
				  columnWidth3 = [ textWidth, 50, fieldWidth - 50 ] )

	intSliderGrp( 'ark_submit_machineLimit_ctrl',
				  label = 'Machine Limit ',
				  minValue = 0,
				  maxValue = 10,
				  field = True,
				  fieldMinValue = 0,
				  fieldMaxValue = 1000,
				  value = 0,
				  columnWidth3 = [ textWidth, sliderFieldWidth, fieldWidth - sliderFieldWidth ] )

	intSliderGrp( 'ark_submit_concur_ctrl',
				  label = 'Concurrent Tasks ',
				  minValue = 1,
				  maxValue = 4,
				  field = True,
				  fieldMinValue = 1,
				  fieldMaxValue = 24,
				  value = 1,
				  columnWidth3 = [ textWidth, sliderFieldWidth, fieldWidth - sliderFieldWidth ] )

	checkBox( 'ark_submit_suspended_ctrl', label = 'Submit Suspended', value = 0, align = 'left' )			  

	separator( style = 'in' )

	textFieldGrp( 'ark_submit_frameList_ctrl',
				  label = 'Frame List ',
				  columnWidth2 = [ textWidth, fieldWidth ] )

	intSliderGrp( 'ark_submit_framesPerHost_ctrl',
				  label = 'Frames per Host ',
				  minValue = 1,
				  field = True,
				  fieldMinValue = 1,
				  columnWidth3 = [ textWidth, sliderFieldWidth, fieldWidth - sliderFieldWidth ] )

	separator( style = 'in' )

	optionMenuGrp( 'ark_submit_plugin_ctrl',
				   label = 'Version ',
				   columnWidth2 = [ textWidth, fieldWidth ],
				   columnAlign = [ 1, 'right' ] )
	pluginList = [ '5.0.2.4' ]
	for eachPlugin in pluginList:
		menuItem( label = eachPlugin )

	intSliderGrp( 'ark_submit_taskSize_ctrl',
				  label = 'Task Size ',
				  enable = True,
				  minValue = 8,
				  field = True,
				  fieldMinValue = 8,
				  columnWidth3 = [ textWidth, sliderFieldWidth, fieldWidth - sliderFieldWidth ] )

	textFieldGrp( 'ark_submit_commandLine_ctrl', 
				  label = 'Command Line ',
				  columnWidth2 = [ textWidth, fieldWidth ] )

	checkBox( 'ark_submit_multiLayer_ctrl', label = 'Export Render Layers', value = 0, align = 'left' )

	setParent( '..' )	
	setParent( '..' )	

	# OUTPUT SETTINGS
	frameLayout( label = ' Output Settings', 
				 labelVisible = True, 
				 borderVisible = False, 
				 collapsable = False )

	columnLayout( adj = True, rowSpacing = 4, columnAttach = [ 'both', 4 ] )

	textFieldGrp( 'ark_submit_fileName_ctrl',
				  label = 'Image Name ', 
				  columnWidth2 = [ textWidth, fieldWidth ] )

	textFieldButtonGrp( 'ark_submit_out_ctrl',
						label = 'Output Path ', 
						buttonLabel = '...',
						buttonCommand = 'ark_submit_browse( "ark_submit_out_ctrl", "dir" )',
						columnWidth3 = [ textWidth, fieldWidth, fieldButtonWidth ] )

	textFieldButtonGrp( 'ark_submit_scene_ctrl',
						label = 'Scene Path ', 
						buttonLabel = '...',
						buttonCommand = 'ark_submit_browse( "ark_submit_scene_ctrl", "dir" )',
						columnWidth3 = [ textWidth, fieldWidth, fieldButtonWidth ] )

	setParent( '..' )
	setParent( '..' )

	separator( style = 'none', height = 5 )

	# BUTTONS
	rowLayout( numberOfColumns = 2, columnWidth2 = [ doubleButton + 6, doubleButton + 6 ], columnAlign2 = [ 'center', 'center' ] )

	button( label = 'Submit', 
			width = doubleButton + 6,
			height = 50,
			command = 'ark_submit_do( 0, 1 );ark_submit_store()' )

	button( label = 'Store and Close', 
			width = doubleButton + 6,
			height = 50,
			command = 'ark_submit_do( 1, 1 );ark_submit_store();deleteUI( "ark_submit_win" )' )

	setParent( '..' )

	# PROGRESS BAR
	separator( style = 'none', height = 5 )

	progressBar( 'ark_submit_progBar_ctrl', height = 30 )

	# FINAL COMMANDS
	ark_submit_restore()

	showWindow( win )

	window( win, edit = True, width = 627, height = 585 ) 
