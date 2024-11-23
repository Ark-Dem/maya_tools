from maya.cmds import *
import maya.mel

# UPDATE PYTHON3 RENAMED FUNCTION TO KEEP IT WORKING WITH PYTHON2
try:
	xrange(1)
except:
	xrange = range


def ark_menu_subMenu( menuList ):
	menuItem( l = menuList[0], subMenu = True, tearOff = True )

	skip = False
	for i in xrange( 1, len( menuList ) ):
		if not skip:
			if menuList[i].__class__ == list:
				ark_menu_subMenu( menuList[i] )
			else:
				skip = ark_menu_item( [menuList[i], menuList[i+1]] )
		else:
			skip = False
	
	setParent( '..', menu = True )


def ark_menu_item( items ):
	skip = False
	if items[0] == '----':
		menuItem( divider = True )
	else:
		menuItem( l = items[0], c = items[1] )
		skip = True
	return skip


def ark_menu_create( menuList ):
	if menu( menuList[1], exists = True ):
		deleteUI( menuList[1] )

	gMainWindow = maya.mel.eval( '$tmpVar = $gMainWindow' )
	ark_menu = menu( menuList[1], p = gMainWindow, l = menuList[0], to = True )

	skip = False
	for i in xrange( 2, len( menuList ) ):
		if not skip:
			if menuList[i].__class__ == list:
				ark_menu_subMenu( menuList[i] )
			else:
				skip = ark_menu_item( [menuList[i], menuList[i+1]] )
		else:
			skip = False
