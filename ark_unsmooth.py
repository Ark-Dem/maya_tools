from maya.cmds import *

def ark_unsmooth_do( each, selList ):
	edgeNums = []
	for eachEdge in selList:
		edgeNums.append( int(eachEdge.replace(':','[').replace(']','[').split('[')[1]) )
	edges = polySelect( each, edgeLoopOrBorder = edgeNums, noSelection = True )
	edges = polySelect( each, edgeRing = edges, everyN = 2 )
	polyDelEdge( cv = True )


def ark_unsmooth( mode = 'auto' ):
	selList = ls( sl = True )

	if mode == 'auto':
		for each in selList:
			vCount = polyEvaluate( each, v = True )
			ark_unsmooth_do( each, polyListComponentConversion( each + '.vtx[' + str(vCount) + ']', fv = True, te = True ) )
		select( selList, r = True )

	elif mode == 'sel':
		each = ls( sl = True, o = True )[0]
		ark_unsmooth_do( each, selList )
		select( listRelatives( each, parent = True ), r = True )		
