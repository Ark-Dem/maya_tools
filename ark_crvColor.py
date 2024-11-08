from maya.cmds import *

def ark_crvColor_sel():
	selList = ls( sl = True, long = True )

	crvList = []
	for each in selList:
		selType = objectType( each )
		if selType == 'nurbsCurve':
			crvList.append( each )
		if selType == 'transform':
			shps = listRelatives( each, shapes = True, fullPath = True )
			for shp in shps:
				if objectType( shp ) == 'nurbsCurve':
					crvList.append( shp )

	return crvList


def ark_crvColor_hlight( mode ):
	viewPanel = getPanel( withFocus = True )
	if not getPanel( typeOf = viewPanel ) == 'modelPanel':
		viewPanel = getPanel( withLabel = 'Persp View' )

	modelEditor( viewPanel, edit = True, sel = mode )


def ark_crvColor_clr( ctrl, mode ):
	crvList = ark_crvColor_sel()
	ark_crvColor_hlight( 0 )

	clr = colorSliderGrp( ctrl, query = True, rgb = True )
	use = 2
	for crv in crvList:
		if mode == 'reset':
			clr = [0, 0, 0]
			use = 0
		setAttr( crv + '.useObjectColor', use )
		setAttr( crv + '.wireColorRGB', clr[0], clr[1], clr[2], type = 'double3' )


def ark_crvColor_pick( ctrl ):
	clr = colorSliderGrp( ctrl, query = True, rgb = True )
	crvList = ls( type = 'nurbsCurve' )

	selList = []
	for crv in crvList:
		if getAttr( crv + '.useObjectColor' ) == 2 and list(getAttr( crv + '.wireColorRGB' )[0]) == clr:
			for par in listRelatives( crv, parent = True, fullPath = True ):
				selList.append( par )
	
	ark_crvColor_hlight( 1 )
	select( selList, replace = True )


def ark_crvColor_upd( ctrl ):
	crvList = ark_crvColor_sel()

	if crvList != []:
		clr = getAttr( crvList[0] + '.wireColorRGB' )[0]
		colorSliderGrp( ctrl, edit = True, rgb = clr )
	
	ark_crvColor_hlight( 1 )


def ark_crvColor():
	pref = 'ark_crvColor'
	win = pref + '_win'
	if window( win, exists = True ):
		deleteUI( win )
	
	selJob = scriptJob( event = ['SelectionChanged', 'ark_crvColor_upd( "' + pref + '_clr_CSG' + '" )'], killWithScene = False )

	window( win, title = 'Curve Color Tools', closeCommand = 'ark_crvColor_hlight( 1 ); scriptJob( kill = ' + str(selJob) + ' )', sizeable = False )

	columnLayout( adj = True )

	colorSliderGrp( pref + '_clr_CSG',
					label = 'Color  ',
					columnWidth3 = (0, 100, 200),
					rgb = (0, 0, 0),
					changeCommand = 'ark_crvColor_clr( "' + pref + '_clr_CSG' + '", "set" )' )

	rowLayout( numberOfColumns = 2, columnWidth2 = [200, 100] )

	button(			label = 'Select by Color', 
					width = 200,
					command = 'ark_crvColor_pick( "' + pref + '_clr_CSG' + '" )' )

	button(			label = 'Reset Colors', 
					width = 100-6,
					command = 'ark_crvColor_clr( "' + pref + '_clr_CSG' + '", "reset" )' )

	setParent( '..' )

	showWindow( win )
	window( win, edit = True, width = 300, height = 44 )

	ark_crvColor_upd( pref + '_clr_CSG' )
