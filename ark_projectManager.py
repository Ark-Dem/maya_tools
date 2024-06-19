#------------------------------------------------------------------maya-
# file: ark_projectManager.py
# version: 2.1
# date: 2023.03.31
# author: Arkadiy Demchenko
#-----------------------------------------------------------------------
# 2023.03.31 (v2.1) - updated for Python3
# 2022.10.23 (v2.0) - added counters for categories, increase height
# 2020.09.01 (v1.9) - added function to recreate all workspace.mel
# 2020.08.25 (v1.8) - added workspace path for alembicCache
# 2019.06.20 (v1.7) - now works with quoted project paths
# 2018.11.15 (v1.6) - setting project now sets environment variables
# 2018.01.20 (v1.5) - added fileCache file rule to shots
# 2016.03.30 (v1.4) - split assets by type in gui, fixed baseWorkspace
# 2015.11.08 (v1.3) - updated for char/env/prop/rig/shot
# 2012.07.29 (v1.2) - maya.mel import, added try to query baseWorkspace
# 2012.03.18 (v1.1) - corrected listdir for roots of logical drives
# 2011.05.29 (v1.0) - main release
#-----------------------------------------------------------------------
# GUI for creating and managing projects of specific structure.
# Read more thorough explanation in the article attached to Help button.
#
# Update ark_projectManager_prjLocations variable in the following line
# with folders containing your projects.
#
# TO DO:
# - double-click to set project, open dir to button
# - batch asset creation from txt
# - check if workspace.mel belongs to custom project
#-----------------------------------------------------------------------
from maya.cmds import *
import maya.mel
import os, os.path, time, stat, subprocess

# GLOBAL VARIABLES
ark_projectManager_prjLocations = os.environ['PROJECTS'].replace('"', '').split(';')

ark_projectManager_prjDict = {}
ark_projectManager_prjContents = []
ark_projectManager_ctrls = [ 'ark_projectManager_projTSL', 'ark_projectManager_shotTSL', 'ark_projectManager_envTSL', 'ark_projectManager_charTSL', 'ark_projectManager_propTSL', 'ark_projectManager_miscTSL' ]
ark_projectManager_uiCtrl = [ 'ark_projectManager_ui', 'ark_projectManager_uiPrj' ]
ark_projectManager_assDirs = [ 'env', 'char', 'prop', 'rig' ]
ark_projectManager_txt = [ 'ark_projectManager_projTXT', 'ark_projectManager_shotTXT', 'ark_projectManager_envTXT', 'ark_projectManager_charTXT', 'ark_projectManager_propTXT', 'ark_projectManager_miscTXT' ]

# LIST PROJECTS
def ark_projectManager_prjList():
	prjs = {}
	for prjLocation in ark_projectManager_prjLocations:
		if os.path.exists( prjLocation ):
			prjLocationSafe = prjLocation
			if prjLocation[-1] == ':':
				prjLocationSafe += '/'
			contents = os.listdir( prjLocationSafe )

			for item in contents:
				prj = prjLocation + '/' + item
				if os.path.exists( prj + '/workspace.mel' ) :
					# IF PROJECTS WITH SAME NAME EXIST IN DIFFERENT LOCATIONS, ADD PATH TO THE NAME
					prjsItems = []
					for eachItem in prjs.keys():
						prjsItems.append( eachItem.split()[0] )

					if item in prjsItems:
						if item in prjs:
							prjs[ item + ' (' + prjs[ item ] + ')' ] = prjs[ item ]
							del prjs[ item ]
						prjs[ item + ' (' + prj + ')' ] = prj
					else:
						prjs[ item ] = prj

	ark_projectManager_prjDict.clear()
	ark_projectManager_prjDict.update( prjs )


# LIST PROJECT'S SHOTS AND ASSETS
def ark_projectManager_prj( prj ):
	prjPop = False
	if prj == '':
		prjs = ark_projectManager_prjDict
		prj = prjs[ textScrollList( ark_projectManager_ctrls[0], query = True, selectItem = True )[0] ]
		prjPop = True

	# GET CONTENTS OF THE SELECTED PROJECT
	shots = {}
	envs = {}
	chars = {}
	props = {}
	rigs = {}
	if os.path.exists( prj + '/3d/shot' ):
		contents = os.listdir( prj + '/3d/shot' )

		for item in contents:
			shot = prj + '/3d/shot/' + item
			if os.path.exists( shot + '/workspace.mel' ):
				shots[ item ] = shot

	for assDir in ark_projectManager_assDirs:
		if os.path.exists( prj + '/3d/' + assDir ):
			contents = os.listdir( prj + '/3d/' + assDir )

			for item in contents:
				asset = prj + '/3d/' + assDir + '/' + item
				if os.path.exists( asset + '/workspace.mel' ):
					if assDir == ark_projectManager_assDirs[0]:
						envs[ item ] = asset
					elif assDir == ark_projectManager_assDirs[1]:
						chars[ item ] = asset
					elif assDir == ark_projectManager_assDirs[2]:
						props[ item ] = asset
					elif assDir == ark_projectManager_assDirs[3]:
						rigs[ item ] = asset

	del ark_projectManager_prjContents[:]
	ark_projectManager_prjContents.append( shots )
	ark_projectManager_prjContents.append( envs )
	ark_projectManager_prjContents.append( chars )
	ark_projectManager_prjContents.append( props )
	ark_projectManager_prjContents.append( rigs )

	# POPULATE GUI WITH SHOTS AND ASSETS
	if prjPop:
		textScrollList( ark_projectManager_ctrls[1], edit = True, removeAll = True, append = sorted( shots.keys(), key = str.lower ) )
		textScrollList( ark_projectManager_ctrls[2], edit = True, removeAll = True, append = sorted( envs.keys(), key = str.lower ) )
		textScrollList( ark_projectManager_ctrls[3], edit = True, removeAll = True, append = sorted( chars.keys(), key = str.lower ) )
		textScrollList( ark_projectManager_ctrls[4], edit = True, removeAll = True, append = sorted( props.keys(), key = str.lower ) )
		textScrollList( ark_projectManager_ctrls[5], edit = True, removeAll = True, append = sorted( rigs.keys(), key = str.lower ) )

		text( ark_projectManager_txt[1], edit = True, label = '(' + str( len( shots.keys() ) ) + ') Shots:' )
		text( ark_projectManager_txt[2], edit = True, label = '(' + str( len( envs.keys() ) ) + ') Environments:' )
		text( ark_projectManager_txt[3], edit = True, label = '(' + str( len( chars.keys() ) ) + ') Characters:' )
		text( ark_projectManager_txt[4], edit = True, label = '(' + str( len( props.keys() ) ) + ') Props:' )
		text( ark_projectManager_txt[5], edit = True, label = '(' + str( len( rigs.keys() ) ) + ') Rigs:' )


# REBUILD WORKSPACE.MEL FILES
def ark_projectManager_rebuildWorkspaces( prjs = ark_projectManager_prjDict ):
	for prj in prjs:
		path = prjs[prj]
		if os.path.exists( path ):
			os.chmod( path + '/workspace.mel', stat.S_IWRITE )
			wrk = open( path + '/workspace.mel', 'w' )
			wrk.write( '// Created by ' + os.environ[ 'USERNAME' ] + ' from ' + os.environ[ 'COMPUTERNAME' ] + ' on ' + time.strftime('%Y.%m.%d') + ' at ' + time.strftime('%H:%M:%S') + '\n\n' )
			for line in ark_projectManager_masterWRK:
				wrk.write( line + '\n' )
			wrk.close()
			os.chmod( path + '/workspace.mel', stat.S_IREAD )

		ark_projectManager_prj( prjs[prj] )
		for each in ark_projectManager_prjContents:
			for itemPath in each.values():
				os.chmod( itemPath + '/workspace.mel', stat.S_IWRITE )
				wrk = open( itemPath + '/workspace.mel', 'w' )
				wrk.write( '// Created by ' + os.environ[ 'USERNAME' ] + ' from ' + os.environ[ 'COMPUTERNAME' ] + ' on ' + time.strftime('%Y.%m.%d') + ' at ' + time.strftime('%H:%M:%S') + '\n\n' )
				for line in ark_projectManager_projectWRK:
					if itemPath.split('/')[-2] == 'shot':
						wrk.write( line + '\n' )
					else:
						if not 'particles' in line:
							wrk.write( line + '\n' )
				wrk.close()
				os.chmod( itemPath + '/workspace.mel', stat.S_IREAD )


# FILL CURRENT PROJECT FIELD
def ark_projectManager_prjField():
	curPrj = workspace( query = True, openWorkspace = True, rd = True )[:-1]
	textFieldGrp( ark_projectManager_uiCtrl[1], edit = True, text = curPrj )
	

# HIGHLIGHT CURRENT PROJECT IF IT'S IN THE PROJECTS LOCATIONS
def ark_projectManager_prjCurrent():
	curPrj = workspace( query = True, openWorkspace = True, rd = True )[:-1]

	# FIND BASE WORKSPACE
	bwPrj = curPrj
	bwExists = 0
	if len(curPrj.split('/')) > 1:
		for each in curPrj.split('/'):
			bwPrj = bwPrj[:bwPrj.rfind('/')]
			if os.path.exists( bwPrj + '/workspace.mel' ):
				bwExists = 1
				break
	if not bwExists:
		bwPrj = curPrj

	if bwPrj != None:
		for key0, value0 in zip( ark_projectManager_prjDict.keys(), ark_projectManager_prjDict.values() ):
			if value0 == bwPrj:
				textScrollList( ark_projectManager_ctrls[0], edit = True, selectItem = key0 )
				ark_projectManager_prj( '' )

				if curPrj != None:
					for key1, value1 in zip( ark_projectManager_prjContents[0].keys(), ark_projectManager_prjContents[0].values() ):
						if value1 == curPrj:
							textScrollList( ark_projectManager_ctrls[1], edit = True, selectItem = key1 )
							
					for key2, value2 in zip( ark_projectManager_prjContents[1].keys(), ark_projectManager_prjContents[1].values() ):
						if value2 == curPrj:
							textScrollList( ark_projectManager_ctrls[2], edit = True, selectItem = key2 )

					for key3, value3 in zip( ark_projectManager_prjContents[2].keys(), ark_projectManager_prjContents[2].values() ):
						if value3 == curPrj:
							textScrollList( ark_projectManager_ctrls[3], edit = True, selectItem = key3 )

					for key4, value4 in zip( ark_projectManager_prjContents[3].keys(), ark_projectManager_prjContents[3].values() ):
						if value4 == curPrj:
							textScrollList( ark_projectManager_ctrls[4], edit = True, selectItem = key4 )

					for key5, value5 in zip( ark_projectManager_prjContents[4].keys(), ark_projectManager_prjContents[4].values() ):
						if value5 == curPrj:
							textScrollList( ark_projectManager_ctrls[5], edit = True, selectItem = key5 )


# REFRESH GUI
def ark_projectManager_refresh():
	prjs = ark_projectManager_prjDict
	sel = []
	for each in ark_projectManager_ctrls:
		if textScrollList( each, query = True, numberOfSelectedItems = True ):
			if ark_projectManager_ctrls.index( each ):
				sel.append( textScrollList( each, query = True, selectItem = True )[0] )
			else:
				item = textScrollList( each, query = True, selectItem = True )[0]
				sel.append( prjs[ item ] )
		else:
			sel.append( '' )
	
	ark_projectManager( refresh = True )

	if sel[0] in ark_projectManager_prjDict.values():
		for key0, value0 in zip( ark_projectManager_prjDict.keys(), ark_projectManager_prjDict.values() ):
			if value0 == sel[0]:
				textScrollList( ark_projectManager_ctrls[0], edit = True, selectItem = key0 )
				ark_projectManager_prj( '' )

		if sel[1] in ark_projectManager_prjContents[0]:
			textScrollList( ark_projectManager_ctrls[1], edit = True, selectItem = sel[1] )

		if sel[2] in ark_projectManager_prjContents[1]:
			textScrollList( ark_projectManager_ctrls[2], edit = True, selectItem = sel[2] )

		if sel[3] in ark_projectManager_prjContents[2]:
			textScrollList( ark_projectManager_ctrls[3], edit = True, selectItem = sel[3] )

		if sel[4] in ark_projectManager_prjContents[3]:
			textScrollList( ark_projectManager_ctrls[4], edit = True, selectItem = sel[4] )

		if sel[5] in ark_projectManager_prjContents[4]:
			textScrollList( ark_projectManager_ctrls[5], edit = True, selectItem = sel[5] )


# DESELECT SHOT IF ASSET GETS SELECTED AND VICE VERSA
def ark_projectManager_deselect( ctrl ):
	for each in ark_projectManager_ctrls[1:]:
		if each != ctrl.split('|')[-1]:
			textScrollList( each, edit = True, deselectAll = True )


# SET PROJECT
def ark_projectManager_set():
	for each in ark_projectManager_ctrls[1:]:
		if textScrollList( each, query = True, numberOfSelectedItems = True ):
			prj = ark_projectManager_prjContents[ ark_projectManager_ctrls.index( each )-1 ][ textScrollList( each, query = True, selectItem = True )[0] ]
			workspace( prj, openWorkspace = True )

			# PASS MAYA VARS TO ENV VARS
			for var in workspace( query = True, variableList = True ):
				os.environ[var] = workspace( ve = var )

			# REMOVES BROWSER SETTINGS
			allVars = optionVar( list = True )
			for var in allVars:
				if var[:15] == 'browserLocation':
					optionVar( remove = var )

			# ADD TO RECENT PROJECTS LIST
			maya.mel.eval( 'addRecentProject( "' + prj + '" );' )

			ark_projectManager_prjField()

			print( 'Setting project to ' + prj )


# PROMPT FOR NEW PROJECT/SHOT/ASSET NAME
def ark_projectManager_promptName():
    prompt = promptDialog(
            title = 'New Name',
            message = 'Enter Name:',
            button = [ 'Create', 'Cancel' ],
            defaultButton = 'Create',
            cancelButton = 'Cancel',
            dismissString = 'Cancel' )

    name = ''
    if prompt == 'Create':
        name = promptDialog( query = True, text = True )
        
    return name.replace( ' ', '' ).replace( ':', ',' ).replace( ';', ',' ).split( ',' )


# IF PROJECT LOCATIONS ARE MULTIPLE, PROMPT FOR LOCATION TO CREATE NEW PROJECT IN
def ark_projectManager_promptLocation():
	frm = [270, 150]
	btn = [frm[0]/2-1, 20]
	
	columnLayout( adj = True )

	prjTsl = textScrollList(	allowMultiSelection = False, 
								append = ark_projectManager_prjLocations, 
								selectIndexedItem = 1, 
								width = frm[0]-4,
								height = frm[1]-50 ) 

	rowLayout( numberOfColumns = 2, height = btn[1], columnWidth = [ (1, btn[0]), (2, btn[0]) ], columnAttach = [ (1, 'left', 0), (2, 'right', 0) ] )

	selBtn = button(	label = 'Select', 
						width = btn[0],
						height = btn[1],
						command = 'curSel = textScrollList( "' + prjTsl + '", query = True, selectItem = True )[0]; layoutDialog( dismiss = curSel )' )

	cancelBtn = button( label = 'Cancel', 
						width = btn[0], 
						height = btn[1],
						command = 'layoutDialog( dismiss = "dismiss" )' )


# CREATE NEW PROJECT
def ark_projectManager_newProj():
	# ASK FOR LOCATION IF MULTIPLE ARE DEFINED
	location = ark_projectManager_prjLocations[0]
	if len( ark_projectManager_prjLocations ) > 1:
		location = layoutDialog( title = 'Project Location', ui = ark_projectManager_promptLocation )
		if location == 'dismiss':
			return
		else:
			if not os.path.exists( location ):
				os.mkdir( location )
	
	# GET NAME, BUILD DIR STRUCTURE AND CREATE READ-ONLY WORKSPACE.MEL
	names = ark_projectManager_promptName()
	for name in names:
		if name != '':
			path = location + '/' + name
			if os.path.exists( path ):
				confirmDialog( title = 'Warning', message = path + ' already exists!', button = [ 'Close' ] )
			else:
				os.mkdir( path )
				wrk = open( path + '/workspace.mel', 'w' )
				wrk.write( '// Created by ' + os.environ[ 'USERNAME' ] + ' from ' + os.environ[ 'COMPUTERNAME' ] + ' on ' + time.strftime('%Y.%m.%d') + ' at ' + time.strftime('%H:%M:%S') + '\n\n' )
				for line in ark_projectManager_masterWRK:
					wrk.write( line + '\n' )
				wrk.close()
				os.chmod( path + '/workspace.mel', stat.S_IREAD )
						
				for each in ark_projectManager_prjStruct:
					os.mkdir( path + each )

				ark_projectManager_refresh()

				print( 'Creating new project: ' + path )


# CREATE NEW SHOT/ASSET
def ark_projectManager_newShot( prjType ):
	if textScrollList( ark_projectManager_ctrls[0], query = True, numberOfSelectedItems = True ):
		prjs = ark_projectManager_prjDict
		prj = prjs[ textScrollList( ark_projectManager_ctrls[0], query = True, selectItem = True )[0] ]

		names = ark_projectManager_promptName()
		for name in names:
			if name != '':
				path = prj + '/3d/' + prjType + '/' + name

				if os.path.exists( path ):
					confirmDialog( title = 'Warning', message = path + ' already exists!', button = [ 'Close' ] )
				else:
					os.makedirs( path )
					wrk = open( path + '/workspace.mel', 'w' )
					wrk.write( '// Created by ' + os.environ[ 'USERNAME' ] + ' from ' + os.environ[ 'COMPUTERNAME' ] + ' on ' + time.strftime('%Y.%m.%d') + ' at ' + time.strftime('%H:%M:%S') + '\n\n' )
					for line in ark_projectManager_projectWRK:
						if prjType == 'shot':
							wrk.write( line + '\n' )
						else:
							if not 'particles' in line:
								wrk.write( line + '\n' )
					wrk.close()
					os.chmod( path + '/workspace.mel', stat.S_IREAD )

					if prjType == 'shot':
						for each in ark_projectManager_shtStruct:
							os.mkdir( path + each )

						for each in ark_projectManager_shtRootStruct:
							for eachDir in ark_projectManager_shtRootStruct[ each ]:
								rootPath = prj + each + '/' + name + eachDir
								if not os.path.exists( rootPath ):
									os.makedirs( rootPath )
					else:
						for each in ark_projectManager_asstStruct:
							os.mkdir( path + each )

					ark_projectManager_refresh()

					print( 'Creating new ' + prjType + ': ' + path )


# OPEN PROJECT FOLDER
def ark_projectManager_openDir( ctrl ):
	if os.name == 'nt':
		prjs = {}
		if ctrl == 0:
			prjs = ark_projectManager_prjDict
		else:
			prjs = ark_projectManager_prjContents[ ctrl-1 ]

		path = prjs[ textScrollList( ark_projectManager_ctrls[ ctrl ], query = True, selectItem = True )[0] ]

		cmd = 'explorer "' + path.replace( '/', '\\' ) + '"'
		proc = subprocess.Popen( cmd )


# GUI
def ark_projectManager( refresh = False ):
	win = 'ark_projectManager_win'
	if not refresh:
		if window( win, exists = True ):
			deleteUI( win )
		window( win, title = 'Project Manager', sizeable = False )
	else:
		deleteUI( ark_projectManager_uiCtrl[0] )
		setParent( win )

	# DIMENSIONS
	colW = [200, 5, 200, 200, 60]
	ttl = [20, 87, 107, 16, 80]
	tslW = 235
	prjW = [85, sum(colW)-73]
	hght = [218, 452, 335]

	# ROWLAYOUT AT THE TOP SINCE IT DOESN'T BLINK ON REFRESH AS COLUMNLAYOUT DOES
	ui = rowLayout( ark_projectManager_uiCtrl[0], numberOfColumns = 1 )

	columnLayout( adj = True )

	uiPrj = textFieldGrp(	ark_projectManager_uiCtrl[1], 
							label = 'Current Project:', 
							text = '', 
							editable = False, 
							columnWidth2 = [ prjW[0], prjW[1] ] )
	separator(  style = 'in', height = 5 )

	rowLayout( numberOfColumns = 5, columnWidth = [ (1, colW[0]), (2, colW[1]), (3, colW[2]), (4, colW[3]), (5, colW[4]) ], rowAttach = [ (1, 'top', 0), (2, 'top', 0), (3, 'top', 0), (4, 'top', 0), (5, 'bottom', 0) ] )

	# COLUMN 1
	# PROJECTS SECTION
	ark_projectManager_prjList()
	prjs = ark_projectManager_prjDict

	columnLayout( adj = True )

	rowLayout( numberOfColumns = 2, height = ttl[0], columnWidth = [ (1, ttl[1]), (2, ttl[2]) ], columnAttach = [ (1, 'left', 0), (2, 'right', 0) ] )
	projTXT = text( ark_projectManager_txt[0], label = '(' + str( len( prjs.keys() ) ) + ') Projects:' )
	newProjBTN = button( label = 'New Project', height = ttl[3], width = ttl[4] )
	setParent( '..' )
	projTSL = textScrollList( ark_projectManager_ctrls[0], allowMultiSelection = False, height = hght[0], append = sorted( prjs.keys(), key = str.lower ) ) 
	
	# SHOTS SECTION
	rowLayout( numberOfColumns = 2, height = ttl[0], columnWidth = [ (1, ttl[1]), (2, ttl[2]) ], columnAttach = [ (1, 'left', 0), (2, 'right', 0) ] )
	shotTXT = text( ark_projectManager_txt[1], label = '() Shots:' )
	newShotBTN = button( label = 'New Shot', height = ttl[3], width = ttl[4] )
	setParent( '..' )
	shotTSL = textScrollList( ark_projectManager_ctrls[1], allowMultiSelection = False, height = hght[1] )

	setParent( '..' )

	# COLUMN 2
	separator( horizontal = False, style = 'in' )

	# COLUMN 3
	# ENV SECTION
	columnLayout( adj = True )

	rowLayout( numberOfColumns = 2, height = ttl[0], columnWidth = [ (1, ttl[1]), (2, ttl[2]) ], columnAttach = [ (1, 'left', 0), (2, 'right', 0) ] )
	envTXT = text( ark_projectManager_txt[2], label = '() Environments:' )
	newEnvBTN = button( label = 'New Env', height = ttl[3], width = ttl[4] )
	setParent( '..' )
	envTSL = textScrollList( ark_projectManager_ctrls[2], allowMultiSelection = False, height = hght[2] )

	# CHAR SECTION
	rowLayout( numberOfColumns = 2, height = ttl[0], columnWidth = [ (1, ttl[1]), (2, ttl[2]) ], columnAttach = [ (1, 'left', 0), (2, 'right', 0) ] )
	charTXT = text( ark_projectManager_txt[3], label = '() Characters:' )
	newCharBTN = button( label = 'New Char', height = ttl[3], width = ttl[4] )
	setParent( '..' )
	charTSL = textScrollList( ark_projectManager_ctrls[3], allowMultiSelection = False, height = hght[2] )

	setParent( '..' )

	# COLUMN 4
	# PROP SECTION
	columnLayout( adj = True )

	rowLayout( numberOfColumns = 2, height = ttl[0], columnWidth = [ (1, ttl[1]), (2, ttl[2]) ], columnAttach = [ (1, 'left', 0), (2, 'right', 0) ] )
	propTXT = text( ark_projectManager_txt[4], label = '() Props:' )
	newPropBTN = button( label = 'New Prop', height = ttl[3], width = ttl[4] )
	setParent( '..' )
	propTSL = textScrollList( ark_projectManager_ctrls[4], allowMultiSelection = False, height = hght[2] )

	# RIG SECTION
	rowLayout( numberOfColumns = 2, height = ttl[0], columnWidth = [ (1, ttl[1]), (2, ttl[2]) ], columnAttach = [ (1, 'left', 0), (2, 'right', 0) ] )
	rigTXT = text( ark_projectManager_txt[5], label = '() Rigs:' )
	newRigBTN = button( label = 'New Rig', height = ttl[3], width = ttl[4] )
	setParent( '..' )
	rigTSL = textScrollList( ark_projectManager_ctrls[5], allowMultiSelection = False, height = hght[2] )

	setParent( '..' )

	# LISTS CONTENTS COMMANDS
	textScrollList( projTSL, edit = True, selectCommand = 'ark_projectManager_prj( "" )', doubleClickCommand = 'ark_projectManager_openDir( 0 )' )
	textScrollList( shotTSL, edit = True, selectCommand = 'ark_projectManager_deselect( "' + shotTSL + '" )', doubleClickCommand = 'ark_projectManager_openDir( 1 )' )
	textScrollList( envTSL, edit = True, selectCommand = 'ark_projectManager_deselect( "' + envTSL + '" )', doubleClickCommand = 'ark_projectManager_openDir( 2 )' )
	textScrollList( charTSL, edit = True, selectCommand = 'ark_projectManager_deselect( "' + charTSL + '" )', doubleClickCommand = 'ark_projectManager_openDir( 3 )' )
	textScrollList( propTSL, edit = True, selectCommand = 'ark_projectManager_deselect( "' + propTSL + '" )', doubleClickCommand = 'ark_projectManager_openDir( 4 )' )
	textScrollList( rigTSL, edit = True, selectCommand = 'ark_projectManager_deselect( "' + rigTSL + '" )', doubleClickCommand = 'ark_projectManager_openDir( 5 )' )
	button( newProjBTN, edit = True, command = 'ark_projectManager_newProj()' )
	button( newShotBTN, edit = True, command = 'ark_projectManager_newShot( "shot" )' )
	button( newEnvBTN, edit = True, command = 'ark_projectManager_newShot( "env" )' )
	button( newCharBTN, edit = True, command = 'ark_projectManager_newShot( "char" )' )
	button( newPropBTN, edit = True, command = 'ark_projectManager_newShot( "prop" )' )
	button( newRigBTN, edit = True, command = 'ark_projectManager_newShot( "rig" )' )

	# COLUMN 5
	columnLayout( adj = True )

	showBTN = button( label = 'Current', command = 'ark_projectManager_prjCurrent()' )
	separator( style = 'in', height = 10 )
	helpBTN = button( label = 'Help' )
	refrshBTN = button( label = 'Refresh', command = 'ark_projectManager_refresh()' )
	separator( style = 'in', height = 10 )
	setPrjBTN = button( label = 'Set Project', height = 50, command = 'ark_projectManager_set()' )

	setParent( '..' )
	
	# STORE GLOBALS
	del ark_projectManager_ctrls[:]
	ark_projectManager_ctrls.append( projTSL.split( '|' )[-1:][0] )
	ark_projectManager_ctrls.append( shotTSL.split( '|' )[-1:][0] )
	ark_projectManager_ctrls.append( envTSL.split( '|' )[-1:][0] )
	ark_projectManager_ctrls.append( charTSL.split( '|' )[-1:][0] )
	ark_projectManager_ctrls.append( propTSL.split( '|' )[-1:][0] )
	ark_projectManager_ctrls.append( rigTSL.split( '|' )[-1:][0] )
	del ark_projectManager_uiCtrl[:]
	ark_projectManager_uiCtrl.append( ui.split( '|' )[-1:][0] )
	ark_projectManager_uiCtrl.append( uiPrj.split( '|' )[-1:][0] )

	# HIGHLIGHT CURRENT PROJECT AND FILL PROJECT FIELD
	ark_projectManager_prjField()
	if not refresh:
		ark_projectManager_prjCurrent()

	showWindow( win )
	window( win, edit = True, width = sum(colW)+20, height = hght[2]*2+75+3 )


# PROJECT STRUCTURE
ark_projectManager_prjStruct = [ 
'/_in',
'/_in/' + time.strftime('%y%m%d'),
'/_out',
'/_out/_dailies',
'/_out/_dailies/' + time.strftime('%y%m%d'),
'/_out/_final',
'/_out/briefs',
'/_out/concepts',
'/_out/storyboards',
'/2d',
'/2d/concepts',
'/2d/mattes',
'/2d/storyboards',
'/3d',
'/3d/_assets',
'/3d/_textures',
'/audio',
'/comp',
'/edit',
'/result',
'/src',
'/src/docs',
'/src/info',
'/src/music',
'/src/plates',
'/src/refs',
'/src/video',
'/tmp',
'/tmp/maya',
'/tmp/maya/3dPaintTextures',
'/tmp/maya/assets',
'/tmp/maya/autosave',
'/tmp/maya/cache',
'/tmp/maya/cache/fluid',
'/tmp/maya/clips',
'/tmp/maya/data',
'/tmp/maya/fur',
'/tmp/maya/fur/furAttrMap',
'/tmp/maya/fur/furEqualMap',
'/tmp/maya/fur/furFiles',
'/tmp/maya/fur/furImages',
'/tmp/maya/fur/furShadowMap',
'/tmp/maya/images',
'/tmp/maya/mentalray',
'/tmp/maya/particles',
'/tmp/maya/renderData',
'/tmp/maya/renderData/depth',
'/tmp/maya/renderData/iprImages',
'/tmp/maya/renderData/shaders',
'/tmp/maya/renderScenes',
'/tmp/maya/scenes',
'/tmp/maya/scenes/edits',
'/tmp/maya/sound',
'/tmp/maya/sourceimages',
'/tmp/maya/scripts',
'/tmp/maya/textures',
'/tools'
]


# SHOT STRUCTURE
ark_projectManager_shtStruct = [
'/data',
'/images',
'/particles',
'/scenes',
'/scenes/01_previz',
'/scenes/02_anim',
'/scenes/03_dyn',
'/scenes/04_fx',
'/scenes/05_light',
'/textures'
]

# ASSET STRUCTURE
ark_projectManager_asstStruct = [
'/data',
'/images',
'/scenes',
'/textures'
]

ark_projectManager_shtRootStruct = {
'/comp':[ '/comp/_nk', '/comp/v001', '/data', '/render', '/src/v001' ],
#'/src/plates':[ '' ],
#'/result':[ '/comp', '/data', '/renders' ]
}


# MASTER WORKSPACE.MEL
ark_projectManager_masterWRK = [
'string $prj = `workspace -q -rd`;',
'',
'string $base = $prj;',
'',
'string $pathTmp[];',
'tokenize( $base, "/", $pathTmp );',
'',
'string $path[] = {};',
'for( $i = size( $pathTmp ) - 1; $i > 0; $i-- )',
'    $path[ size( $path ) ] = $pathTmp[$i];',
'',
'string $baseDir = "";',
'string $dir = $base;',
'for( $each in $path ) {',
'    $dir = `substring $dir 1 (size( $dir ) - size( $each ) - 1)`;',
'',
'    if( `filetest -e ($dir + "workspace.mel")` == 1 ) {',
'        $baseDir = $dir;',
'        break;',
'    }',
'}',
'',
'if( $baseDir != "" )',
'    $prj = $baseDir;',
'',
'workspace -fr "3dPaintTextures" ($prj + "tmp/maya/3dPaintTextures");',
'workspace -fr "Adobe(R) Illustrator(R)" ($prj + "tmp/maya/data");',
'workspace -fr "Autodesk Packet File" ($prj + "tmp/maya/data");',
'workspace -fr "CATIAV4_DC" ($prj + "tmp/maya/data");',
'workspace -fr "CATIAV5_DC" ($prj + "tmp/maya/data");',
'workspace -fr "CSB_DC" ($prj + "tmp/maya/data");',
'workspace -fr "DAE_FBX export" ($prj + "tmp/maya/data");',
'workspace -fr "DAE_FBX" ($prj + "tmp/maya/data");',
'workspace -fr "DWG_DC" ($prj + "tmp/maya/data");',
'workspace -fr "DWG_DCE" ($prj + "tmp/maya/data");',
'workspace -fr "DXF" ($prj + "tmp/maya/data");',
'workspace -fr "DXF_DC" ($prj + "tmp/maya/data");',
'workspace -fr "DXF_DCE" ($prj + "tmp/maya/data");',
'workspace -fr "DXF_FBX" ($prj + "tmp/maya/data");',
'workspace -fr "DXFexport" ($prj + "tmp/maya/data");',
'workspace -fr "EPS" ($prj + "tmp/maya/data");',
'workspace -fr "FBX export" ($prj + "tmp/maya/data");',
'workspace -fr "FBX" ($prj + "tmp/maya/data");',
'workspace -fr "Fbx" ($prj + "tmp/maya/data");',
'workspace -fr "HIKCharacter" ($prj + "tmp/maya/data");',
'workspace -fr "HIKEffectorSet" ($prj + "tmp/maya/data");',
'workspace -fr "HIKPropertySet" ($prj + "tmp/maya/data");',
'workspace -fr "HIKState" ($prj + "tmp/maya/data");',
'workspace -fr "IGES" ($prj + "tmp/maya/data");',
'workspace -fr "IGES_DC" ($prj + "tmp/maya/data");',
'workspace -fr "IGES_DCE" ($prj + "tmp/maya/data");',
'workspace -fr "IGESexport" ($prj + "tmp/maya/data");',
'workspace -fr "IPT_DC" ($prj + "tmp/maya/data");',
'workspace -fr "IV_DC" ($prj + "tmp/maya/data");',
'workspace -fr "JT_DC" ($prj + "tmp/maya/data");',
'workspace -fr "OBJ" ($prj + "tmp/maya/data");',
'workspace -fr "OBJexport" ($prj + "tmp/maya/data");',
'workspace -fr "PTC_DC" ($prj + "tmp/maya/data");',
'workspace -fr "RIB" ($prj + "tmp/maya/data");',
'workspace -fr "RIBexport" ($prj + "tmp/maya/data");',
'workspace -fr "SPF_DC" ($prj + "tmp/maya/data");',
'workspace -fr "SPF_DCE" ($prj + "tmp/maya/data");',
'workspace -fr "STEP_DC" ($prj + "tmp/maya/data");',
'workspace -fr "STL_DC" ($prj + "tmp/maya/data");',
'workspace -fr "STL_DCE" ($prj + "tmp/maya/data");',
'workspace -fr "SW_DC" ($prj + "tmp/maya/data");',
'workspace -fr "UG_DC" ($prj + "tmp/maya/data");',
'workspace -fr "UG_DCE" ($prj + "tmp/maya/data");',
'workspace -fr "ZPR_DCE" ($prj + "tmp/maya/data");',
'workspace -fr "alembicCache" ($prj + "tmp/maya/cache");',
'workspace -fr "aliasWire" ($prj + "tmp/maya/data");',
'workspace -fr "animExport" ($prj + "tmp/maya/data");',
'workspace -fr "animImport" ($prj + "tmp/maya/data");',
'workspace -fr "audio" ($prj + "tmp/maya/sound");',
'workspace -fr "autoSave" ($prj + "tmp/maya/autosave");',
'workspace -fr "clips" ($prj + "tmp/maya/clips");',
'workspace -fr "depth" ($prj + "tmp/maya/renderData/depth");',
'workspace -fr "diskCache" ($prj + "tmp/maya/cache");',
'workspace -fr "eps" ($prj + "tmp/maya/data");',
'workspace -fr "fluidCache" ($prj + "tmp/maya/cache/fluid");',
'workspace -fr "furAttrMap" ($prj + "tmp/maya/fur/furAttrMap");',
'workspace -fr "furEqualMap" ($prj + "tmp/maya/fur/furEqualMap");',
'workspace -fr "furFiles" ($prj + "tmp/maya/fur/furFiles");',
'workspace -fr "furImages" ($prj + "tmp/maya/fur/furImages");',
'workspace -fr "furShadowMap" ($prj + "tmp/maya/fur/furShadowMap");',
'workspace -fr "illustrator" ($prj + "tmp/maya/data");',
'workspace -fr "image" ($prj + "tmp/maya/images");',
'workspace -fr "images" ($prj + "tmp/maya/images");',
'workspace -fr "iprImages" ($prj + "tmp/maya/renderData/iprImages");',
'workspace -fr "lights" ($prj + "tmp/maya/renderData/shaders");',
'workspace -fr "mayaAscii" ($prj + "tmp/maya/scenes");',
'workspace -fr "mayaBinary" ($prj + "tmp/maya/scenes");',
'workspace -fr "mel" ($prj + "tmp/maya/scripts");',
'workspace -fr "mentalRay" ($prj + "tmp/maya/mentalray");',
'workspace -fr "mentalray" ($prj + "tmp/maya/mentalray");',
'workspace -fr "move" ($prj + "tmp/maya/data");',
'workspace -fr "movie" ($prj + "tmp/maya/images");',
'workspace -fr "offlineEdit" ($prj + "tmp/maya/scenes/edits");',
'workspace -fr "particles" ($prj + "tmp/maya/particles");',
'workspace -fr "renderData" ($prj + "tmp/maya/renderData");',
'workspace -fr "renderScenes" ($prj + "tmp/maya/renderScenes");',
'workspace -fr "scene" ($prj + "tmp/maya/scenes");',
'workspace -fr "scripts" ($prj + "tmp/maya/scripts");',
'workspace -fr "shaders" ($prj + "tmp/maya/renderData/shaders");',
'workspace -fr "sound" ($prj + "tmp/maya/sound");',
'workspace -fr "sourceImages" ($prj + "tmp/maya/sourceimages");',
'workspace -fr "studioImport" ($prj + "tmp/maya/data");',
'workspace -fr "templates" ($prj + "tmp/maya/assets");',
'workspace -fr "textures" ($prj + "tmp/maya/textures");',
'workspace -fr "translatorData" ($prj + "tmp/maya/data");',
'',
'workspace -v "refs" ($prj + "3d/_assets");',
'putenv "refs" ($prj + "3d/_assets");',
'workspace -v "tex" ($prj + "3d/_textures");',
'putenv "tex" ($prj + "3d/_textures");',
'workspace -v "root" $prj;',
'putenv "root" $prj;'
]


# PROJECT WORKSPACE.MEL
ark_projectManager_projectWRK = [
'string $prj = `workspace -q -rd`;',
'',
'string $base = $prj;',
'',
'string $pathTmp[];',
'tokenize( $base, "/", $pathTmp );',
'',
'string $path[] = {};',
'for( $i = size( $pathTmp ) - 1; $i > 0; $i-- )',
'    $path[ size( $path ) ] = $pathTmp[$i];',
'',
'string $baseDir = "";',
'string $dir = $base;',
'for( $each in $path ) {',
'    $dir = `substring $dir 1 (size( $dir ) - size( $each ) - 1)`;',
'',
'    if( `filetest -e ($dir + "workspace.mel")` == 1 ) {',
'        $baseDir = $dir;',
'        break;',
'    }',
'}',
'',
'if( $baseDir != "" )',
'	eval( "source \\\"" + $baseDir + "workspace.mel\\\";" );',
'',
'workspace -fr "3dPaintTextures" "data/3dPaintTextures";',
'workspace -fr "particles" "particles";',
'workspace -fr "diskCache" "data";',
'workspace -fr "fileCache" "cache/nCache";',
'workspace -fr "images" "images";',
'workspace -fr "scene" "scenes";',
'workspace -fr "mayaAscii" "scenes";',
'workspace -fr "mayaBinary" "scenes";',
'workspace -fr "alembicCache" "cache";'
]
