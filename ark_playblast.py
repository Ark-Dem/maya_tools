#------------------------------------------------------------------maya-
# file: ark_playblast.py
# version: 1.08
# date: 2023.11.24
# author: Arkadiy Demchenko
#-----------------------------------------------------------------------
# 2023.11.24 (v1.08) - fix long camera name in HUD
# 2023.03.31 (v1.07) - update for Python3
# 2023.01.11 (v1.06) - added user notes field
# 2021.12.25 (v1.05) - fixed 8AA, crv instead of play
# 2018.02.20 (v1.04) - added frame rendertime, set gateMask to 0.01
# 2017.08.04 (v1.03) - works with sound, improved slates
# 2016.05.13 (v1.02) - fixed for Maya2015 checkBoxGroup/playblast cmds
# 2016.04.12 (v1.01) - force fps for quicktime
# 2016.03.22 (v1.00) - initial version
#-----------------------------------------------------------------------
# Playblast utility.
# - if range is not used, check timeslider on button press
# - grid & other
# - color management for viewport
# - vendor & project from batch
# - option to keep original format
#-----------------------------------------------------------------------
from maya.cmds import *
import maya.mel
import os, os.path, time, inspect, re, ctypes


# UPDATE PYTHON3 RENAMED MODULE TO KEEP IT WORKING WITH PYTHON2
try:
	import __builtin__
except:
	import builtins as __builtin__

# UPDATE PYTHON3 RENAMED FUNCTION TO KEEP IT WORKING WITH PYTHON2
try:
	xrange(1)
except:
	xrange = range


# VARIABLES
ark_playblast_vendor = ''
ark_playblast_project = 'RELICTS'
ark_playblast_projRes = [1920, 818]
ark_playblast_projFps = 24
ark_playblast_pbRes = [1920, 1080]

ark_playblast_fpsDict = { 'game': 15, 'film': 24, 'pal': 25, 'ntsc': 30, 'show': 48, 'palf': 50, 'ntscf': 60 }

ark_playblast_storage = 'defaultRenderGlobals' 

ark_playblast_timer = 0

# CREATE HUDS AND MAKE PLAYBLAST
def ark_playblast_do( *args ):
	outFormat, vendor, project, scene, outDir, shotName, task, version, userNotes, artist, host, pbDate, pbTime, frames, fps, slates, textures, shadows, crv = args

	# VARIABLES
	projRes = ark_playblast_projRes
	pbRes = ark_playblast_pbRes

	# WORKVERSION
	workVersion = task + version
	if workVersion[0:2] == '__':
		workVersion = workVersion[2:]

	# SET PROJECT RESOLUTION
	resOrig = [getAttr('defaultResolution.width'), getAttr('defaultResolution.height')]

	setAttr( 'defaultResolution.aspectLock', False )
	setAttr( 'defaultResolution.lockDeviceAspectRatio', False )

	setAttr( 'defaultResolution.width', projRes[0] )
	setAttr( 'defaultResolution.deviceAspectRatio', float(projRes[0]) / float(resOrig[1]) )

	setAttr( 'defaultResolution.height', projRes[1] )
	setAttr( 'defaultResolution.deviceAspectRatio', float(projRes[0]) / float(projRes[1]) )

	setAttr( 'defaultResolution.pixelAspect', 1.0 )

	# FIND MODELPANEL AND CAMERA TO PLAYBLAST
	viewPanel = getPanel( withFocus = True )
	if not getPanel( typeOf = viewPanel ) == 'modelPanel':
		viewPanel = getPanel( withLabel = 'Persp View' )
	
	viewCam = modelEditor( viewPanel, query = True, camera = True )
	if len(ls( viewCam.split( '|' )[-1] )) < 2:
		viewCam = viewCam.split( '|' )[-1]

	# DISABLE OVERSCAN
	ovsOrig = getAttr( viewCam + '.overscan' )
	setAttr( viewCam + '.overscan', 1.0 )

	for attr in ['horizontalFilmAperture', 'verticalFilmAperture', 'filmFit']:
		setAttr( viewCam + '.' + attr, lock = False )
		conns = listConnections( viewCam + '.' + attr, s = True, d = False, c = False, p = True )
		if conns:
			try:
				disconnectAttr( conns[0], viewCam + '.' + attr )
			except:
				confirmDialog( title = 'ERROR!', message = attr + ' of the ' + viewCam + ' is locked!' )
				return

	setAttr( viewCam + '.filmFit', 1 )
	for attr in ['horizontalFilmAperture', 'verticalFilmAperture', 'filmFit']:
		setAttr( viewCam + '.' + attr, lock = True )

	dspOrig = [getAttr(viewCam + '.displayFilmGate'), getAttr(viewCam + '.displayResolution'), getAttr(viewCam + '.displayGateMask')]
	setAttr( viewCam + '.displayResolution', 1 )
	setAttr( viewCam + '.displayFilmGate', 1 )
	setAttr( viewCam + '.displayGateMask', 1 )

	mskOrig = list(getAttr( viewCam + '.displayGateMaskColor' )[0])
	mskOrig.append( getAttr( viewCam + '.displayGateMaskOpacity' ) )
	setAttr( viewCam + '.displayGateMaskColor', 0.01, 0.01, 0.01, type = 'double3' )
	setAttr( viewCam + '.displayGateMaskOpacity', 1.0 )

	# CALCULATE ASPECTS
	aspect = '%.2f' % (float(projRes[0]) / float(projRes[1])) + ' [' + str(projRes[0]) + 'x' + str(projRes[1]) + ']'

	# SET TIMECODE BASED ON 1001 FRAME
	timeCode( mayaStartFrame = 1000 )

	# SET VIEWPORT 2.0
	dispOrig = [modelEditor( viewPanel, query = True, displayAppearance = True ), modelEditor( viewPanel, query = True, wireframeOnShaded = True )]
	modelEditor( viewPanel, edit = True, displayAppearance = 'smoothShaded', wireframeOnShaded = False )

	modelEditor( viewPanel, edit = True, rendererName = 'vp2Renderer' )

	texOrig = modelEditor( viewPanel, query = True, displayTextures = True )
	modelEditor( viewPanel, edit = True, displayTextures = textures )

	aoOrig = getAttr( 'hardwareRenderingGlobals.ssaoEnable' )
	#setAttr( 'hardwareRenderingGlobals.ssaoEnable', shadows )
	#setAttr( 'hardwareRenderingGlobals.ssaoAmount', 2 )

	shdOrig = modelEditor( viewPanel, query = True, shadows = True )
	modelEditor( viewPanel, edit = True, shadows = shadows )

	aaOrig = [getAttr( 'hardwareRenderingGlobals.multiSampleEnable' ), getAttr( 'hardwareRenderingGlobals.lineAAEnable' )]
	setAttr( 'hardwareRenderingGlobals.multiSampleEnable', 1 )
	setAttr( 'hardwareRenderingGlobals.lineAAEnable', 1 )
	setAttr( 'hardwareRenderingGlobals.multiSampleCount', 8 )

	crvOrig = modelEditor( viewPanel, query = True, nurbsCurves = True )
	modelEditor( viewPanel, edit = True, nurbsCurves = crv )

	locOrig = modelEditor( viewPanel, query = True, locators = True )
	modelEditor( viewPanel, edit = True, locators = False )

	lgtOrig = modelEditor( viewPanel, query = True, lights = True )
	modelEditor( viewPanel, edit = True, lights = False )

	defOrig = modelEditor( viewPanel, query = True, deformers = True )
	modelEditor( viewPanel, edit = True, deformers = False )

	nclOrig = modelEditor( viewPanel, query = True, nCloths = True )
	modelEditor( viewPanel, edit = True, nCloths = False )

	#setAttr( 'hardwareRenderingGlobals.enableTextureMaxRes', 1 )
	#setAttr( 'hardwareRenderingGlobals.textureMaxResolution', 2048 )

	# REMEMBER CURRENT FRAME
	frameOrig = currentTime( query = True )

	# REPLACE HUDS WITH SLATES
	if slates:
		ark_playblast_HUDclear()
		ark_playblast_HUDcreate( vendor, project, scene, shotName, workVersion, userNotes, artist, host, pbDate, pbTime, frames, viewCam, aspect, fps )

	# PLAYBLAST
	if outFormat == 2:
		outPath = outDir + shotName + task + version
		if not os.path.exists( outPath ):
			os.makedirs( outPath )

		pbOut = outPath + '/' + shotName + task + version
		pbPlay = True
		renum = 0

	elif outFormat == 1:
		tmpDir = 'C:/Temp/maya/'
		if os.getenv( 'TEMP' ):
			tmpDir = os.getenv( 'TEMP' ).replace( '\\', '/' )
			if tmpDir[-1] != '/':
				tmpDir += '/'
		tmpDir += 'playblasts/'
		if not os.path.exists( tmpDir ):
			os.makedirs( tmpDir )
		
		#for root, dirs, files in os.walk( tmpDir, topdown = False ):
		#	for name in files:
		#		os.remove(os.path.join(root, name))

		pbOut = tmpDir + shotName + task + version + '.' + time.strftime('%y%m%d') + '-' + time.strftime('%H%M%S') 
		pbPlay = 0
		renum = 1

	select( clear = True )
	refresh( force = True )
	out = playblast( filename = pbOut, 
					format = 'image',
					offScreen = False,
					sequenceTime = 0,
					forceOverwrite = True,
					startTime = frames[0],
					endTime = frames[1], 
					viewer = pbPlay,
					clearCache = 1,
					showOrnaments = slates, 
					framePadding = 4,
					percent = 100,
					compression = 'png',
					quality = 100, 
					indexFromZero = renum,
					widthHeight = pbRes )

	# QUICKTIME CONVERSION
	if outFormat == 1:
		pyPath = inspect.getframeinfo(inspect.currentframe()).filename
		pyPath = pyPath.replace( '\\', '/' )
		ffmpeg = pyPath[:pyPath.rfind('/')] 
		ffmpeg = ffmpeg[:ffmpeg.rfind('/')] + '/bin/ffmpeg.exe'

		outDir += 'playblasts/'
		if not os.path.exists( outDir ):
			os.makedirs( outDir )

		# AUDIO
		aFile = outDir + shotName + task + version + '_audio.wav'

		aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
		snd = timeControl( aPlayBackSliderPython, query = True, sound = True )
		if snd != '':
			sndFile = getAttr( snd + '.filename' )
			sndOff = getAttr( snd + '.offset' )
			sndSil = getAttr( snd + '.silence' )
			sndStt = getAttr( snd + '.sourceStart' )
			sndEnd = getAttr( snd + '.sourceEnd' )
			sndDelay = round((sndOff+sndSil-(sndStt-1.0)-frames[0])/fps, 4)
			sndLength = sndOff+sndSil-sndStt+sndEnd-frames[0]

			if sndDelay > 0.0:
				qtCmd = ffmpeg + ' -f lavfi -i "aevalsrc=0|0:d=' + str(sndDelay) + '" -i ' + sndFile + ' -filter_complex "[0:0] [1:0] concat=n=2:v=0:a=1" -y ' + aFile
			elif sndDelay < 0.0:
				qtCmd = ffmpeg + ' -i ' + str(sndFile) + ' -ss ' + str(sndDelay*-1) + ' -codec copy -y ' + aFile
			else:
				qtCmd = ffmpeg + ' -i ' + str(sndFile) + ' -codec copy -y ' + aFile
			os.system( qtCmd )

		qtCmd = ffmpeg + ' -framerate ' + str(fps) + ' -i ' + out.replace( '\\', '/' ).replace( '####', '%04d' )
		if os.path.exists( aFile ):
			qtCmd += ' -i ' + aFile + ' -acodec copy'
			if sndLength > (frames[1]-frames[0]+1):
				qtCmd += ' -shortest'
		qtCmd += ' -vcodec mjpeg -qmin 0 -qmax 1 -framerate ' + str(fps) + ' -y ' + outDir + shotName + task + version + '.mov'
		os.system( qtCmd )

		if play:
			os.system( 'start '+ outDir + shotName + task + version + '.mov' ) 

		# DELETE TEMP IMG FILES
		for root, dirs, files in os.walk( tmpDir, topdown = False ):
			for name in files:
				os.remove(os.path.join(root, name))

		if snd != '':
			os.remove( aFile )

	# REINIT HUDS
	if slates:
		ark_playblast_HUDclear()
		ark_playblast_HUDinit()

	# RESTORE SETTINGS
	currentTime( frameOrig )

	setAttr( viewCam + '.overscan', ovsOrig )
	#setAttr( viewCam + '.displayFilmGate', dspOrig[0] )
	setAttr( viewCam + '.displayResolution', 1 )
	setAttr( viewCam + '.displayGateMask', 1 )
	#setAttr( viewCam + '.displayGateMaskColor', mskOrig[0], mskOrig[1], mskOrig[2], type = 'double3' )
	#setAttr( viewCam + '.displayGateMaskOpacity', mskOrig[3] )

	modelEditor( viewPanel, edit = True, displayAppearance = dispOrig[0], wireframeOnShaded = dispOrig[1] )
	modelEditor( viewPanel, edit = True, displayTextures = texOrig )
	#setAttr( 'hardwareRenderingGlobals.ssaoEnable', aoOrig )
	setAttr( 'hardwareRenderingGlobals.multiSampleEnable', aaOrig[0] )
	setAttr( 'hardwareRenderingGlobals.lineAAEnable', aaOrig[1] )
	modelEditor( viewPanel, edit = True, shadows = shdOrig )
	modelEditor( viewPanel, edit = True, nurbsCurves = crvOrig )
	modelEditor( viewPanel, edit = True, locators = locOrig )
	modelEditor( viewPanel, edit = True, lights = lgtOrig )
	modelEditor( viewPanel, edit = True, deformers = defOrig )
	modelEditor( viewPanel, edit = True, nCloths = nclOrig )


# REMOVES ALL HUDS
def ark_playblast_HUDclear():
	for i in xrange( 0, 10 ):
		for k in xrange( 0, 100 ):
			headsUpDisplay( rp = (i, k) )


# REINIT ALL HUDS
def ark_playblast_HUDinit():
	maya.mel.eval( 'source initHUD.mel;' )


# PROCEDURES FOR HUDS UPDATE
def ark_playblast_HUDpassThrough( *args ):
	return args[0]

def ark_playblast_HUDframes( *args ):
	fr = str.zfill( str(int(currentTime( query = True ))), 4 ) + ' of ' + str.zfill( str(int(args[0])), 4 )
	return fr

def ark_playblast_HUDfocal( *args ):
	focal = '%.0f' % getAttr( args[0] + '.focalLength' ) + ' mm'
	camShape = args[0]
	if objectType( camShape ) == 'transform':
		camShape = listRelatives( args[0], shapes = True )[0]
	if attributeQuery( 'aiFocusDistance', node = camShape, exists = True ):
		focal += '  ( ' + '%.2f' % getAttr( camShape + '.aiFocusDistance' ) + ' )'
	return focal

def ark_playblast_ms():
    tics = ctypes.c_int64()
    freq = ctypes.c_int64()

    ctypes.windll.Kernel32.QueryPerformanceCounter(ctypes.byref(tics)) 
    ctypes.windll.Kernel32.QueryPerformanceFrequency(ctypes.byref(freq)) 

    ms = tics.value*1e3/freq.value
    return ms

def ark_playblast_HUDrtime():
	global ark_playblast_timer

	startTime = ark_playblast_timer
	if startTime == 0:
		startTime = ark_playblast_ms()

	endTime = ark_playblast_ms()
	sec = int(endTime - startTime)*0.001

	ark_playblast_timer = ark_playblast_ms()

	return "{:.2f}".format(sec) + ' sec'

def ark_playblast_HUDdate( *args ):
	if args[0] == 'date':
		out = time.strftime('%Y.%m.%d')
	elif args[0] == 'time':
		out = time.strftime('%H:%M')

	return out


# CREATE HUD SLATES
def ark_playblast_HUDcreate( *args ):
	vendor, project, scene, shotName, workVersion, userNotes, artist, host, pbDate, pbTime, frames, viewCam, aspect, fps = args

	offset = 1

	# VENDOR
	headsUpDisplay( 'HUDPlayblastVendor',
					section = 0,
					block = 1 + offset,
					label = vendor,
					labelFontSize = 'large' )

	# PROJECT
	headsUpDisplay( 'HUDPlayblastProject',
					section = 0,
					block = 2 + offset,
					label = project,
					dataFontSize = 'large',
					labelFontSize = 'large' )				
	# SCENE
	headsUpDisplay( 'HUDPlayblastScene',
					section = 2,
					block = 0 + offset,
					label = scene,
					labelFontSize = 'small',
					blockAlignment = 'center' )
					
	# SHOT NAME
	headsUpDisplay( 'HUDPlayblastShotName',
					section = 2,
					block = 1 + offset,
					label = shotName,
					labelFontSize = 'large',
					blockAlignment = 'center' )

	# VERSION
	headsUpDisplay( 'HUDPlayblastVersion',
					section = 2,
					block = 2 + offset,
					label = workVersion,
					labelFontSize = 'large',
					blockAlignment = 'center' )

	# NOTES
	headsUpDisplay( 'HUDPlayblastNotes',
					section = 2,
					block = 3 + offset,
					label = userNotes,
					labelFontSize = 'large',
					blockAlignment = 'center' )

	# ARTIST
	headsUpDisplay( 'HUDPlayblastArtist',
					section = 4,
					block = 1 + offset,
					label = artist,
					labelFontSize = 'large',
					blockAlignment = 'center' )

	# HOST
	headsUpDisplay( 'HUDPlayblastHost',
					section = 4,
					block = 2 + offset,
					label = host,
					labelFontSize = 'large',
					blockAlignment = 'center' )

	# DATE
	headsUpDisplay( 'HUDPlayblastDate',
					section = 5,
					block = 2 + offset,
					dataFontSize = 'large',
					command = 'ark_playblast_HUDdate( "date" )',
					attachToRefresh = True )

	# TIME
	headsUpDisplay( 'HUDPlayblastTime',
					section = 5,
					block = 1 + offset,
					dataFontSize = 'large',
					command = 'ark_playblast_HUDdate( "time" )',
					attachToRefresh = True )

	# RENDERTIME
	headsUpDisplay( 'HUDPlayblastRendertime',
					section = 5,
					block = 0 + offset,
					dataFontSize = 'small',
					command = 'ark_playblast_HUDrtime()',
					attachToRefresh = True )

	# ASPECT
	headsUpDisplay( 'HUDPlayblastAspect',
					section = 7,
					block = 0 + offset,
					label = 'Image Aspect:',
					labelFontSize = 'small',
					dataFontSize = 'small',
					labelWidth = 100,
					dataWidth = 100,
					command = 'ark_playblast_HUDpassThrough( "' + aspect + '" )',
					attachToRefresh = True )

	# CAMERA
	headsUpDisplay( 'HUDPlayblastCamera',
					section = 7,
					block = 2 + offset,
					label = 'Camera:',
					labelFontSize = 'large',
					dataFontSize = 'large',
					labelWidth = 100,
					dataWidth = 100,
					command = 'ark_playblast_HUDpassThrough( "' + viewCam + '" )',
					attachToRefresh = True )

	# FOCAL LENGTH
	headsUpDisplay( 'HUDPlayblastFocal',
					section = 7,
					block = 1 + offset,
					label = 'Focal Length:',
					labelFontSize = 'large',
					dataFontSize = 'large',
					labelWidth = 100,
					dataWidth = 100,
					command = 'ark_playblast_HUDfocal( "' + viewCam + '" )',
					attachToRefresh = True )

	# FRAMES
	headsUpDisplay( 'HUDPlayblastFrames',
					section = 9,
					block = 2 + offset,
					label = 'Frame:',
					labelFontSize = 'large',
					dataFontSize = 'large',
					labelWidth = 80,
					dataWidth = 100,
					command = 'ark_playblast_HUDframes( ' + str(frames[1]) + ' )',
					attachToRefresh = True )
					
	# TIMECODE
	headsUpDisplay( 'HUDPlayblastTimecode',
					section = 9,
					block = 1 + offset,
					label = 'Timecode:',
					labelFontSize = 'large',
					dataFontSize = 'large',
					labelWidth = 80,
					dataWidth = 100,
					preset = 'sceneTimecode' )

	# FPS
	headsUpDisplay( 'HUDPlayblastFps',
					section = 9,
					block = 0 + offset,
					label = 'Framerate:',
					labelFontSize = 'small',
					dataFontSize = 'small',
					labelWidth = 80,
					dataWidth = 100,
					command = 'ark_playblast_HUDpassThrough( "' + str(fps) + ' fps" )',
					attachToRefresh = True )


# COLLECT DATA FROM GUI AND PASS TO MAIN PROCEDURE
def ark_playblast_collect():
	scene = file( query = True, expandName = True )

	outFormat = radioButtonGrp( 'ark_playblast_format_rbg', query = True, select = True )
	vendor = textFieldButtonGrp( 'ark_playblast_vendor_tfbg', query = True, text = True )
	project = textFieldButtonGrp( 'ark_playblast_project_tfbg', query = True, text = True )
	artist = textFieldButtonGrp( 'ark_playblast_artist_tfbg', query = True, text = True )
	frames = [intFieldGrp( 'ark_playblast_frames_ifg', query = True, value1 = True ), intFieldGrp( 'ark_playblast_frames_ifg', query = True, value2 = True )]

	outDir = textFieldButtonGrp( 'ark_playblast_outPath_tfbg', query = True, text = True ).replace( '\\', '/' )
	if outDir[-1] != '/':
		outDir += '/'

	shotName, task, version = ark_playblast_outNameUpdate()

	userNotes = textFieldButtonGrp( 'ark_playblast_userNotes_tfbg', query = True, text = True )

	host = os.getenv( 'COMPUTERNAME' )
	pbDate = time.strftime('%Y.%m.%d')
	pbTime = time.strftime('%H:%M')
	fps = ark_playblast_fpsDict[ currentUnit( query = True, time = True ) ]

	slates = checkBoxGrp( 'ark_playblast_options_cbg', query = True, value1 = True )
	textures = checkBoxGrp( 'ark_playblast_options_cbg', query = True, value2 = True )
	shadows = checkBoxGrp( 'ark_playblast_options_cbg', query = True, value3 = True )
	crv = checkBoxGrp( 'ark_playblast_options_cbg', query = True, value4 = True ) 

	ark_playblast_do( outFormat, vendor, project, scene, outDir, shotName, task, version, userNotes, artist, host, pbDate, pbTime, frames, fps, slates, textures, shadows, crv )


# TEXT FIELD EDIT TOGGLE
def ark_playblast_fieldEdit( ctrlName ):
	ctrl = ctrlName.split('_')[-1]

	shotName, task, version, userNotes, outPath, vendor, project, artist, frames = ark_playblast_defaults()

	if ctrl == 'tfbg':
		state = textFieldButtonGrp( ctrlName, query = True, editable = True )
		textFieldButtonGrp( ctrlName, edit = True, editable = 1-state )
		if state:
			val = ''
			if 'shotName' in ctrlName:
				val = shotName
			elif 'task' in ctrlName:
				val = task
			elif 'version' in ctrlName:
				val = version
			elif 'userNotes' in ctrlName:
				val = userNotes
			elif 'outPath' in ctrlName:
				val = outPath
			elif 'vendor' in ctrlName:
				val = vendor
			elif 'project' in ctrlName:
				val = project
			elif 'artist' in ctrlName:
				val = artist
			textFieldButtonGrp( ctrlName, edit = True, text = val )

	elif ctrl == 'ifg':
		state = intFieldGrp( ctrlName, query = True, enable1 = True )
		intFieldGrp( ctrlName, edit = True, enable1 = 1-state, enable2 = 1-state )
		if state:
			intFieldGrp( ctrlName, edit = True, value1 = frames[0], value2 = frames[1] )
	

# OUTPUT NAME UPDATE
def ark_playblast_outNameUpdate():
	ctrlName = 'ark_playblast_outName_txt'

	shotName = textFieldButtonGrp( 'ark_playblast_shotName_tfbg', query = True, text = True )
	task = textFieldButtonGrp( 'ark_playblast_task_tfbg', query = True, text = True )
	if task != '' and shotName != '':
		task = '__' + task

	version = textFieldButtonGrp( 'ark_playblast_version_tfbg', query = True, text = True )
	if version != '':
		try:
			version = 'v' + str.zfill( str(int(version)), 3 )
		except:
			version = version
		if shotName != '' or task != '':
			version = '__' + version

	if shotName + task + version == '':
		shotName = 'untitled'

	outFormatVal = radioButtonGrp( 'ark_playblast_format_rbg', query = True, select = True )
	outFormat = '.mov'
	if outFormatVal == 2:
		outFormat = '.####.png'

	text( ctrlName, edit = True, label = shotName + task + version + outFormat )

	return [shotName, task, version]


# STORE/RESTORE SETTINGS TO/FROM THE SCENE
def ark_playblast_settings( restore=False ):
	storage = ark_playblast_storage
	pref = 'ark_playblast_'

	for attr in [ 'shotName', 'task', 'version', 'userNotes', 'outPath', 'vendor', 'project', 'artist' ]:
		if restore:
			if attributeQuery( pref + attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + pref + attr )
				if val != '':
					textFieldButtonGrp( pref + attr + '_tfbg', edit = True, editable = True )
					textFieldButtonGrp( pref + attr + '_tfbg', edit = True, text = val )
		else:
			if not attributeQuery( pref + attr, node = storage, exists = True ):
				addAttr( storage, ln = pref + attr, dt = 'string' )
			if textFieldButtonGrp( pref + attr + '_tfbg', query = True, editable = True ):
				setAttr( storage + '.' + pref + attr, textFieldButtonGrp( pref + attr + '_tfbg', query = True, text = True ), type = 'string' )
			else:
				setAttr( storage + '.' + pref + attr, '', type = 'string' )

	for attr in [ 'options' ]:
		if restore:
			if attributeQuery( pref + attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + pref + attr )
				checkBoxGrp( pref + attr + '_cbg', edit = True, valueArray4 = [int(val[0]), int(val[1]), int(val[2]), int(val[3])] )
		else:
			if not attributeQuery( pref + attr, node = storage, exists = True ):
				addAttr( storage, ln = pref + attr, dt = 'string' )
			val = checkBoxGrp( pref + attr + '_cbg', query = True, valueArray4 = True )
			val = (str(val[0])+str(val[1])+str(val[2])+str(val[3])).replace('True','1').replace('False','0')
			setAttr( storage + '.' + pref + attr, val, type = 'string' )
	
	for attr in [ 'frames' ]:
		if restore:
			if attributeQuery( pref + attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + pref + attr )
				if val != '':
					val = val.split('-')
					intFieldGrp( pref + attr + '_ifg', edit = True, enable1 = True, enable2 = True )
					intFieldGrp( pref + attr + '_ifg', edit = True, value1 = int(val[0]), value2 = int(val[1]) )
		else:
			if not attributeQuery( pref + attr, node = storage, exists = True ):
				addAttr( storage, ln = pref + attr, dt = 'string' )
			if intFieldGrp( pref + attr + '_ifg', query = True, enable1 = True ):
				val = str(intFieldGrp( pref + attr + '_ifg', query = True, value1 = True )) + '-' + str(intFieldGrp( pref + attr + '_ifg', query = True, value2 = True ))
				setAttr( storage + '.' + pref + attr, val, type = 'string' )
			else:
				setAttr( storage + '.' + pref + attr, '', type = 'string' )
	
	for attr in [ 'format' ]:
		if restore:
			if attributeQuery( pref + attr, node = storage, exists = True ):
				val = getAttr( storage + '.' + pref + attr )
				radioButtonGrp( pref + attr + '_rbg', edit = True, select = int(val) )
		else:
			if not attributeQuery( pref + attr, node = storage, exists = True ):
				addAttr( storage, ln = pref + attr, dt = 'string' )
			val = radioButtonGrp( pref + attr + '_rbg', query = True, select = True )
			setAttr( storage + '.' + pref + attr, val, type = 'string' )


# COLLECT DEFAULT DATA FROM THE SCENE
def ark_playblast_defaults():
	scene = file( query = True, expandName = True )
	outPath = workspace( expandName = workspace( fileRuleEntry = 'images' ) )
	if not os.path.exists( outPath ):
		outPath = scene[:scene.rfind('/')+1]

	shotPattern = re.compile('^([a-zA-Z]{3}[0-9]{3}_[0-9]{4}){1}$')
	shotName = list(__builtin__.filter( shotPattern.match, scene.split('/') ))
	if shotName == []:
		shotName = 'untitled'
	else:
		shotName = shotName[0]

	task = scene.split('/')[-1].split('.')[0]
	taskRe = re.findall( '[a-zA-Z]+', task )
	if taskRe != []:
		task = taskRe[0]

	version = 1
	userNotes = ''
	artist = os.getenv( 'USERNAME' )

	frames = [playbackOptions( query = True, minTime = True ), playbackOptions( query = True, maxTime = True )]

	return shotName, task, version, userNotes, outPath, ark_playblast_vendor, ark_playblast_project, artist, frames


# GUI
def ark_playblast():
	# CHECK FPS
	fps = ark_playblast_fpsDict[ currentUnit( query = True, time = True ) ]
	if fps != ark_playblast_projFps:
		confirmDialog( title = 'WARNING!', message = 'Scene FPS is ' + str(fps) + '. Project FPS is ' + str(ark_playblast_projFps) + '!', button = 'CANCEL' )
		return

	# DEFAULT DATA
	shotName, task, version, userNotes, outPath, vendor, project, artist, frames = ark_playblast_defaults()

	# WINDOW
	winName = 'ark_playblast_window'

	if window( winName, exists = True ):
		deleteUI( winName )
	
	win = window( winName, title = 'Playblast', sizeable = False )

	columnLayout( adj = True )

	dim = [80, len(outPath)*8, 32]
	dimWidth = dim[0] + dim[1] + dim[2]

	text(				'ark_playblast_outName_txt',
						label = shotName + '__' + task + '__v' + str.zfill( str(version), 3 ) + '.mov', 
						height = 30 )

	separator( style = 'in' )

	radioButtonGrp(		'ark_playblast_format_rbg',
						numberOfRadioButtons = 2, 
						height = 25,
						label = ' ',
						labelArray2=['QuickTime', 'Image Sequence'],
						select = 1,
						columnWidth3 = [dim[0], dim[1]*0.5, dim[1]*0.5],
						changeCommand = 'ark_playblast_outNameUpdate()' )

	separator( style = 'in' )

	textFieldButtonGrp( 'ark_playblast_shotName_tfbg',
						label = 'Shot:',
						text = shotName,
						editable = False,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						textChangedCommand = 'ark_playblast_outNameUpdate()',
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_shotName_tfbg" )' )

	textFieldButtonGrp( 'ark_playblast_task_tfbg',
						label = 'Task:',
						text = task,
						editable = False,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						textChangedCommand = 'ark_playblast_outNameUpdate()',
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_task_tfbg" )' )

	textFieldButtonGrp( 'ark_playblast_version_tfbg',
						label = 'Version:',
						text = version,
						editable = True,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						textChangedCommand = 'ark_playblast_outNameUpdate()',
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_version_tfbg" )' )

	textFieldButtonGrp( 'ark_playblast_userNotes_tfbg',
						label = 'Notes:',
						editable = False,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_userNotes_tfbg" )' )

	rowLayout( numberOfColumns = 2, columnWidth2 = [dim[0]+dim[1]+2, dim[2]] )
	intFieldGrp(		'ark_playblast_frames_ifg',
						numberOfFields = 2, 
						label = 'Frame Range:', 
						value1 = frames[0],
						value2 = frames[1],
						enable1 = False,
						enable2 = False,
						columnWidth3 = [dim[0]-1, dim[1]*0.5-1, dim[1]*0.5-1] )

	button(				'ark_playblast_framesEdit_btn',
						label = 'edit',
						command = 'ark_playblast_fieldEdit( "ark_playblast_frames_ifg" )' )
	setParent( '..' )

	textFieldButtonGrp( 'ark_playblast_outPath_tfbg',
						label = 'Output Dir:',
						text = outPath,
						editable = False,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_outPath_tfbg" )' )

	textFieldButtonGrp( 'ark_playblast_vendor_tfbg',
						label = 'Vendor:',
						text = ark_playblast_vendor,
						editable = False,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_vendor_tfbg" )' )

	textFieldButtonGrp( 'ark_playblast_project_tfbg',
						label = 'Project:',
						text = ark_playblast_project,
						editable = False,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_project_tfbg" )' )

	textFieldButtonGrp( 'ark_playblast_artist_tfbg',
						label = 'Artist:',
						text = artist,
						editable = False,
						buttonLabel = 'edit',
						columnWidth3 = dim,
						buttonCommand = 'ark_playblast_fieldEdit( "ark_playblast_artist_tfbg" )' )

	separator( style = 'in' )

	chbWidth = (dim[1]+dim[2])*0.25
	checkBoxGrp(		'ark_playblast_options_cbg',
						numberOfCheckBoxes = 4,
						height = 24,
						label = 'Options:',
						labelArray4 = ['Info', 'Textures', 'Shadows', 'Curves'],
						valueArray4 = [True, True, False, False],
						columnWidth5 = [dim[0], chbWidth-10, chbWidth+3, chbWidth+7, chbWidth],
						columnAttach5 = ['right', 'left', 'left', 'left', 'left'],
						columnOffset5 = [0, 1, 0, 0, 0] )

	separator( style = 'in' )

	rowLayout( numberOfColumns = 2, columnWidth2 = [dimWidth*0.5, dimWidth*0.5] )
	button(				'ark_playblast_do_btn',
						label = 'Playblast',
						width = dimWidth*0.5,
						command = 'ark_playblast_settings();ark_playblast_collect();deleteUI( "' + winName + '" )' )

	button(				'ark_playblast_cancel_btn',
						label = 'Cancel',
						width = dimWidth*0.5,
						command = 'deleteUI( "' + winName + '" )' )
	setParent( '..' )

	# RESTORE TOOL SETTINGS IF ANY
	ark_playblast_settings( restore=True )

	showWindow( win )
	window( win, edit = True, width = dimWidth+6, height = 318+25 )
