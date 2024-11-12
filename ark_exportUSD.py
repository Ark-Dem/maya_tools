#------------------------------------------------------------------maya-
# file: ark_exportUSD.py
# version: 0.20
# date: 2023.12.29
# author: Arkadiy Demchenko
#-----------------------------------------------------------------------
# 2023.12.29 (v0.20) - initial version
#-----------------------------------------------------------------------
# Exports USD structure.
#
# TODO:
# - should work if objects with same name exist in the scene
# - better yeti export
# - remesh before reduce
# - revert scene back to what it was
# - __geo/intermed/etc in groups
# - instances
# - references
# - proxy material selection dropdown
#-----------------------------------------------------------------------
from maya.cmds import *
import os, os.path, time, math
from pxr import Usd, UsdGeom, Sdf, UsdShade, Kind
	
# EULER ANGLE TO QUATERNION
def ang_to_q( ang ):
    x = ang[0]
    y = ang[1]
    z = ang[2]
    
    x = math.radians(x)
    y = math.radians(y)
    z = math.radians(z)

    chr = math.cos(x/2)
    shr = math.sin(x/2)
    chp = math.cos(y/2)
    shp = math.sin(y/2)
    chd = math.cos(z/2)
    shd = math.sin(z/2)

    return( (chd*chp*shr-shd*shp*chr), (chd*shp*chr+shd*chp*shr), (shd*chp*chr-chd*shp*shr), (chd*chp*chr+shd*shp*shr) )	


# (TMP) CONVERT TO POINTINSTANCER
def ark_exportUSD_pInst( nm ):
	selList = ls( sl=True )

	ids = []
	positions = []
	orientations = []
	scales = []
	protoIndices = []

	i = 0
	for sel in selList:
		ids.append( i )
		i = i + 1
		val = pointPosition( sel + '.rotatePivot' )
		positions.append( (round(val[0],3),round(val[1],3),round(val[2],3)) )
		val = ang_to_q( getAttr( sel + '.r' )[0] )
		orientations.append( (round(val[3],6), round(val[0],6), round(val[1],6), round(val[2],6)) )
		val = getAttr( sel + '.s' )[0]
		scales.append( (round(val[0],3),round(val[1],3),round(val[2],3)) )
		protoIndices.append( int(sel[sel.find(nm)+len(nm)+1:sel.find(nm)+len(nm)+2])-1 )

	bbox = exactWorldBoundingBox( selList )

	filePath = workspace( q=True, rd=True ) + 'instancer.txt'
	f = open( filePath, 'w' )
	f.write( 'float3[] extent = [' + str((round(bbox[0],3), round(bbox[1],3), round(bbox[2],3))) + ', ' + str((round(bbox[3],3), round(bbox[4],3), round(bbox[5],3))) + ']' + '\n' )
	f.write( 'int64[] ids = ' + str(ids) + '\n' )
	f.write( 'quath[] orientations = ' + str(orientations) + '\n' )
	f.write( 'point3f[] positions = ' + str(positions) + '\n' )
	f.write( 'int[] protoIndices = ' + str(protoIndices) + '\n' )
	f.write( 'float3[] scales = ' + str(scales) + '\n' )
	f.close()

	print( filePath )


# EXPORT GEO
def ark_exportUSD_geo( assetName, geoPath, fmt ):
	file( geoPath, options=';exportDisplayColor=1;exportColorSets=0;mergeTransformAndShape=1;exportComponentTags=0;defaultUSDFormat=' + fmt + ';jobContext=[Arnold];materialsScopeName=mtl', typ='USD Export', pr=True, ch=True, chn=True, exportSelected=True, f=True, de=False )
	
	stage = Usd.Stage.Open( geoPath )
	rootLayer = stage.GetRootLayer()
	
	proc = 0
	# REMOVE EVERYTHING BUT GEO
	primList = []
	for prim in stage.TraverseAll():
		primList.append( prim )
	
	for prim in primList:
		try:
			if prim.GetTypeName() not in ['Xform', 'Scope', 'Mesh'] or prim.GetName() in ['mtl', 'fur']:
				if prim.GetTypeName() == 'ArnoldProceduralCustom' or prim.GetName() == 'fur':
					proc = 1
				stage.RemovePrim( prim.GetPath() )
			else:
				for primProperty in prim.GetAuthoredProperties():
					if primProperty.GetName() in ['material:binding']:
						prim.RemoveProperty( primProperty.GetName() )
		except:
			pass
	
	# TURN XFORMS INTO SCOPES AND ADD BBOX
	prim = stage.GetPrimAtPath('/' + assetName + '/geo')
	prim.SetTypeName('Scope')
	
	bbox_cache = UsdGeom.BBoxCache( Usd.TimeCode.Default(), ['default', 'render'] )
	root_geom_model_API = UsdGeom.ModelAPI.Apply( prim )
	extentsHint = root_geom_model_API.ComputeExtentsHint( bbox_cache )
	root_geom_model_API.SetExtentsHint( extentsHint )
	
	stage.GetPrimAtPath('/' + assetName + '/geo/render').SetTypeName('Scope')
	stage.GetPrimAtPath('/' + assetName + '/geo/proxy').SetTypeName('Scope')
	
	# SAVE GEO
	rootLayer.Save()

	return proc
	

# EXPORT FUR
def ark_exportUSD_proc( assetName, procPath ):
	select( assetName, replace=True )
	file( procPath, options=';exportDisplayColor=1;exportColorSets=0;mergeTransformAndShape=1;exportComponentTags=0;defaultUSDFormat=usda;jobContext=[Arnold];materialsScopeName=mtl', typ='USD Export', pr=True, ch=True, chn=True, exportSelected=True, f=True, de=False )
	#file( procPath, options='-boundingBox;-mask 8', typ='Arnold-USD', pr=True, ch=True, chn=True, exportSelected=True, f=True, de=False )
	
	stage = Usd.Stage.Open( procPath )
	rootLayer = stage.GetRootLayer()
	
	# REMOVE EVERYTHING BUT PROC
	primList = []
	for prim in stage.TraverseAll():
		primList.append( prim )
	
	for prim in primList:
		try:
			if prim.GetTypeName() not in ['Xform', 'Scope', 'ArnoldProceduralCustom'] or prim.GetName() in ['geo', 'mtl']:
				stage.RemovePrim( prim.GetPath() )
			else:
				for primProperty in prim.GetAuthoredProperties():
					if primProperty.GetName() in ['material:binding']:
						prim.RemoveProperty( primProperty.GetName() )
		except:
			pass
	
	# TURN XFORMS INTO SCOPES
	stage.GetPrimAtPath('/' + assetName + '/fur').SetTypeName('Scope')
	
	# SAVE GEO
	rootLayer.Save()
	

# EXPORT MTL
def ark_exportUSD_mtl( assetName, mtlPath, previewTex, previewRough, previewCvr ):
	select( assetName, replace=True )
	file( mtlPath, options=';exportDisplayColor=1;exportColorSets=0;mergeTransformAndShape=1;exportComponentTags=0;defaultUSDFormat=usda;jobContext=[Arnold];materialsScopeName=mtl', typ='USD Export', pr=True, ch=True, chn=True, exportSelected=True, f=True, de=False )
	
	stage = Usd.Stage.Open( mtlPath )
	rootLayer = stage.GetRootLayer()
	
	# REMOVE EVERYTHING BUT MATERIALS AND SHADERS
	primList = []
	for prim in stage.TraverseAll():
		primList.append( prim )
	
	for prim in primList:
		try:
			if prim.GetTypeName() not in ['Material', 'Shader'] and prim.GetName() not in [assetName, 'mtl'] or prim.GetName() in ['initialShadingGroup', 'ai_bad_shader']:
				stage.RemovePrim( prim.GetPath() )
		except:
			pass
	
	# CREATE PREVIEW MATERIAL
	mtl = UsdShade.Material.Define( stage, '/' + assetName + '/mtl/preview_SG' )
	shd = UsdShade.Shader.Define( stage, '/' + assetName + '/mtl/preview_SG/preview_SHD' )
	shd.CreateIdAttr( 'UsdPreviewSurface' )
	shd.CreateInput( 'roughness', Sdf.ValueTypeNames.Float ).Set( previewRough )
	mtl.CreateSurfaceOutput().ConnectToSource( shd.ConnectableAPI(), 'surface' )

	if str(type(previewTex)) == "<class 'tuple'>":
		shd.CreateInput( 'diffuseColor', Sdf.ValueTypeNames.Color3f ).Set( previewTex )
	else:
		st = UsdShade.Shader.Define( stage, '/' + assetName + '/mtl/preview_SG/preview_ST' )
		st.CreateIdAttr( 'UsdPrimvarReader_float2' )
		
		tex = UsdShade.Shader.Define( stage, '/' + assetName + '/mtl/preview_SG/preview_TEX' )
		tex.CreateIdAttr( 'UsdUVTexture' )
		tex.CreateInput( 'file', Sdf.ValueTypeNames.Asset ).Set( previewTex )
		
		if previewCvr > 1.0:
			t2d = UsdShade.Shader.Define( stage, '/' + assetName + '/mtl/preview_SG/preview_T2D' )
			t2d.CreateIdAttr( 'UsdTransform2d' )
			t2d.CreateInput( 'in', Sdf.ValueTypeNames.Float2 ).ConnectToSource( st.ConnectableAPI(), 'result' )
			t2d.CreateInput( 'scale', Sdf.ValueTypeNames.Float2 ).Set( (1.0/previewCvr, 1.0) )
			tex.CreateInput( 'st', Sdf.ValueTypeNames.Float2 ).ConnectToSource( t2d.ConnectableAPI(), 'result' )
		else:
			tex.CreateInput( 'st', Sdf.ValueTypeNames.Float2 ).ConnectToSource( st.ConnectableAPI(), 'result' )
			
		tex.CreateOutput( 'rgb', Sdf.ValueTypeNames.Float3 )
		shd.CreateInput( 'diffuseColor', Sdf.ValueTypeNames.Color3f ).ConnectToSource( tex.ConnectableAPI(), 'rgb' )
		
		stInput = mtl.CreateInput( 'frame:stPrimvarName', Sdf.ValueTypeNames.Token )
		stInput.Set( 'st' )
		st.CreateInput( 'varname', Sdf.ValueTypeNames.Token ).ConnectToSource( stInput )
			
	# SAVE MTL
	rootLayer.Save()
	
	
# CREATE ASSET
def ark_exportUSD_asset( assetName, assetPath, scenePath, geoPath, mtlPath, procPath, mtlList ):
	assetLayer = Sdf.Layer.CreateNew( assetPath, args = {'format':'usda'} )
	stage = Usd.Stage.Open( assetPath )
	rootLayer = stage.GetRootLayer()
	
	defaultPrim = UsdGeom.Xform.Define( stage, Sdf.Path('/' + assetName) )
	geoPrim = defaultPrim.GetPrim()
	
	stage.SetDefaultPrim( geoPrim )
	UsdGeom.SetStageUpAxis( stage, UsdGeom.Tokens.y )
	geoPrim.SetMetadata( 'assetInfo', {'identifier': Sdf.AssetPath(assetPath.split('/')[-1])} )
	geoPrim.SetMetadata( 'customData', {'Exported_from': scenePath, 'Exported_date': time.strftime('%Y.%m.%d') + ' ' + time.strftime('%H:%M'), 'Exported_host': os.getenv( 'COMPUTERNAME' ) } )
	geoPrim.SetAssetInfoByKey( 'name', assetName )
	
	geoPrim.GetReferences().AddReference( assetPath = './usd/' + geoPath.split('/')[-1], primPath = '/' + assetName )
	
	model_API = Usd.ModelAPI( geoPrim )
	model_API.SetKind( Kind.Tokens.component )
		
	bbox_cache = UsdGeom.BBoxCache( Usd.TimeCode.Default(), ['default', 'render'] )
	root_geom_model_API = UsdGeom.ModelAPI.Apply( geoPrim )
	extentsHint = root_geom_model_API.ComputeExtentsHint( bbox_cache )
	root_geom_model_API.SetExtentsHint( extentsHint )
	
	variant_sets = geoPrim.GetVariantSets().AddVariantSet( 'display' )
	
	variant_sets.AddVariant( 'final' )
	variant_sets.SetVariantSelection( 'final' )
	with variant_sets.GetVariantEditContext():
		renderPrim = stage.DefinePrim( Sdf.Path('/' + assetName + '/geo/render') )
		renderPrim.SetSpecifier(Sdf.SpecifierOver)
		UsdGeom.Imageable( renderPrim ).CreatePurposeAttr().Set(UsdGeom.Tokens.default_)
		
		proxyPrim = stage.DefinePrim( Sdf.Path('/' + assetName + '/geo/proxy') )
		proxyPrim.SetSpecifier(Sdf.SpecifierOver)
		UsdGeom.Imageable( proxyPrim ).CreatePurposeAttr().Set(UsdGeom.Tokens.guide)
		
	variant_sets.AddVariant( 'preview' )
	variant_sets.SetVariantSelection( 'preview' )
	with variant_sets.GetVariantEditContext():
		renderPrim = stage.DefinePrim( Sdf.Path('/' + assetName + '/geo/render') )
		renderPrim.SetSpecifier(Sdf.SpecifierOver)
		UsdGeom.Imageable( renderPrim ).CreatePurposeAttr().Set(UsdGeom.Tokens.render)
		
		proxyPrim = stage.DefinePrim( Sdf.Path('/' + assetName + '/geo/proxy') )
		proxyPrim.SetSpecifier(Sdf.SpecifierOver)
		UsdGeom.Imageable( proxyPrim ).CreatePurposeAttr().Set(UsdGeom.Tokens.proxy)
		
	geoPrim.GetReferences().AddReference( assetPath = './usd/' + mtlPath.split('/')[-1], primPath = '/' + assetName )

	if procPath != '':
		geoPrim.GetReferences().AddReference( assetPath = './usd/' + procPath.split('/')[-1], primPath = '/' + assetName )
	
	# BIND MATERIALS TO GEO
	for each in mtlList:
		prim = UsdGeom.Mesh.Get( stage, each[0].replace('|', '/') )
		prim.GetPrim().ApplyAPI( UsdShade.MaterialBindingAPI )
		mtl = UsdShade.Material.Get( stage, '/' + assetName + '/mtl/' + each[1] )
		UsdShade.MaterialBindingAPI( prim ).Bind( mtl )
		
	# BIND PREVIEW MATERIAL TO PROXY
	for each in stage.GetPrimAtPath( '/' + assetName + '/geo/proxy' ).GetChildren():
		prim = UsdGeom.Mesh.Get( stage, each.GetPath() )
		each.ApplyAPI( UsdShade.MaterialBindingAPI )
		mtl = UsdShade.Material.Get( stage, '/' + assetName + '/mtl/preview_SG' )
		UsdShade.MaterialBindingAPI( prim ).Bind( mtl )
	
	# SAVE ASSET
	rootLayer.Save()


# EDIT MTL
def ark_exportUSD_fixMtl( mtlPath ):
	os.rename( mtlPath, mtlPath + '_backup' )
	fIn = open( mtlPath + '_backup', 'r' )
	fOut = open( mtlPath, 'w' )

	shd = ''
	layerEnableLoop = 0
	for line in fIn:
		if '"preview_SG"' in line:
			shd = 'preview'
		elif '"preview_TEX"' in line:
			shd = 'preview_tex'

		if 'remap_outValue' in line:
			line = line.replace('remap_outValue', 'remap')

		if 'token outputs:arnold:surface.connect' in line:
			fOut.write( line.replace(':surface>', ':out>') )
		elif 'token outputs:surface' in line and shd not in ['preview']:
			fOut.write( line.replace('token outputs:surface', 'string outputs:out') )
		elif '"UsdUVTexture"' in line and shd in ['preview_tex']:
			fOut.write( line )
			fOut.write( line[:line.find('uniform')] + 'string inputs:sourceColorSpace = "sRGB"' + '\n' )
		elif 'aiImage"' in line:
			tab = line[:line.find('def')]
			fOut.write( line[:-1] + ' (' + '\n' )
			fOut.write( tab + '    ' + 'customData = {' + '\n' )
			fOut.write( tab + '    ' + '    ' + 'dictionary Autodesk = {' + '\n' )
			fOut.write( tab + '    ' + '    ' + '    ' + 'token ignoreColorManagementFileRules = "true"' + '\n' )
			fOut.write( tab + '    ' + '    ' + '}' + '\n' )
			fOut.write( tab + '    ' + '}' + '\n' )
			fOut.write( tab + ')' + '\n' )
		elif 'asset inputs:filename = @' in line and shd not in ['preview_tex']:
			fOut.write( line.replace('asset inputs', 'string inputs').replace('@', '"') )
		elif 'token inputs:mode' in line or 'token inputs:operation' in line or 'token inputs:wrap_frame' in line:
			fOut.write( line.replace('token inputs', 'string inputs') )
		elif 'bool inputs:enable' in line:
				en = line[line.find('enable')+6:line.find('enable')+7]
				for i in range( layerEnableLoop+1, int(en) ):
					fOut.write( line.replace('enable' + en + ' = 0', 'enable' + str(i) + ' = 1' ) )
				if int(en) < 8:
					layerEnableLoop = int(en)
				else:
					layerEnableLoop = 0
				fOut.write( line )
		elif 'token outputs:displacement.connect' in line or 'float inputs:displacement' in line or 'token outputs:displacement' in line:
			pass
		elif 'asset inputs:file = @./textures/' in line:
			fOut.write( line.replace('@./', '@../') )
		else:
			fOut.write( line )
	fIn.close()
	fOut.close()

	os.remove( mtlPath + '_backup' )


# MAIN PROCEDURE
def ark_exportUSD( createHierarchy=True, createProxy=True, fixNames=True, geoFmt='usdc' ):
	rootDir = workspace( q=True, rd=True )
	assetName = rootDir.split('/')[-2]
	filePath = rootDir + assetName
	scenePath = file( q=True, sn=True )
	
	# CREATE GEO HIERARCHY
	selList = ls( sl=True )
	
	if createHierarchy:
		renderGrp = group( selList, world=True, name='render' )
		xform( renderGrp, os = True, piv = (0, 0, 0) )
		proxyGrp = group( empty=True, world=True, name='proxy' )
		geoGrp = group( (renderGrp, proxyGrp), world=True, name='geo' )
		xform( geoGrp, os = True, piv = (0, 0, 0) )
		assetGrp = group( geoGrp, world=True, name=assetName )
		xform( assetGrp, os = True, piv = (0, 0, 0) )
		
		for each in selList:
			if each[-5:] != '__geo':
				rename( each, each[:-4] + '__geo' )
	else:
		assetGrp = selList[0]

	# IF ASSET NAME DOESN'T MATCH ROOT NAME, COMBINE THEM FOR USD FILE NAMES
	if assetName != assetGrp:
		assetName = assetGrp
		if fixNames:
			filePath += '__' + assetGrp
		else:
			filePath = filePath[:filePath.rfind('/')+1] + assetGrp

	usdDir = filePath[:filePath.rfind('/')] + '/usd'
	usdPath = usdDir + filePath[filePath.rfind('/'):]

	if not os.path.exists( usdDir ):
		os.mkdir( usdDir )

	geoPath = usdPath + '__geo.usd'
	furPath = usdPath + '__fur.usda'
	mtlPath = usdPath + '__mtl.usda'
	assetPath = filePath + '.usda'

	# CHECK FOR INTERMEDIATES
	intermediateObjects = ls( listRelatives( '|' + assetName + '|geo|render', allDescendents=True, type='mesh' ), intermediateObjects=True )
	if intermediateObjects != []:
		confirmDialog( title='Warning!', message='Deleting intermediate objects:\n' + '\n'.join(intermediateObjects), button=['OK'], defaultButton='OK' )
		delete( intermediateObjects )

	# GET MATERIAL ASSIGNMENTS
	mtlList = []
	sgList = []
	geoList = listRelatives( '|' + assetName + '|geo|render', allDescendents=True, type='mesh', noIntermediate=True )
	for each in geoList:
		setAttr( each + '.aiOpaque', 1 )
		eachParent = listRelatives( each, parent=True, fullPath=True )[0]
		sg = listConnections( each, type='shadingEngine' )[0]
		mtlList.append( [eachParent, sg] )
		if sg not in sgList:
			sgList.append( sg )
	
	# CREATE PROXY GEO
	if createProxy:
		if len(geoList) > 1:
			dupGrp = duplicate( assetGrp )[0]
			proxyGeo = polyUnite( dupGrp )[0]
			delete( proxyGeo, ch=True )
			delete( dupGrp )
		else:
			proxyGeo = duplicate( geoList[0] )[0]
		
		polyReduce( proxyGeo, version=1, keepBorder=1, keepMapBorder=1, keepColorBorder=0, keepFaceGroupBorder=0, keepHardEdge=0, keepCreaseEdge=0, keepQuadsWeight=1, cachingReduce=1, ch=0, p=95, replaceOriginal=1 )
		parent( proxyGeo, '|' + assetName + '|geo|proxy' )
		proxyGeo = rename( proxyGeo, 'proxy__geo' )
	
		sg = sgList[0]
		if len(sgList) > 1:
			prompt = promptDialog( title='Material for proxy', message='\n'.join(sgList), button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel' )
			if prompt == 'OK':
				sg = promptDialog( q=True, text=True ) 
		
		hyperShade( assign=sg, geo=proxyGeo )
		
		select( assetGrp, replace=True )
	
	# GET PREVIEW TEXTURE OR COLOR
	proxy = listRelatives( '|' + assetName + '|geo|proxy', allDescendents=True, type='mesh' )[0]
	sg = listConnections( proxy, type='shadingEngine' )[0]
	shd = listConnections( sg + '.surfaceShader' )[0]
	clrAttr = 'color'
	if nodeType( shd ) == 'aiStandardSurface':
		clrAttr = 'baseColor'
	tex = listConnections( shd + '.' + clrAttr )

	previewCvr = 1.0
	if tex == None:
		previewTex = getAttr( shd + '.' + clrAttr )[0]
	else:
		fileAttr = 'fileTextureName'
		if nodeType( tex[0] ) == 'aiImage':
			fileAttr = 'filename'
		previewTex = getAttr( tex[0] + '.' + fileAttr ).replace( rootDir, './' )	
		
		if previewTex[-4:] != '.jpg':
			confirmDialog( title='Warning!', message=previewTex[-4:] + ' as preview texture!', button=['OK'], defaultButton='OK' )
			
		if nodeType( tex[0] ) == 'file':
			p2d = listConnections( tex[0] + '.uvCoord' )[0]
			previewCvr = getAttr( p2d + '.coverageU' )
		
	previewRough = 0.7
	try:
		previewRough = getAttr( shd + '.eccentricity' )
	except:
		try:
			previewRough = max( min( 10.0/getAttr( shd + '.cosinePower' ), 0.8), 0.1)
		except:
			pass
	
	# DISCONNECT PREVIEW SHADERS
	reconnectShd = []
	for sg in sgList:
		if listConnections( sg + '.aiSurfaceShader' ) != None:
			shd = listConnections( sg + '.surfaceShader' )[0]
			disconnectAttr( shd + '.outColor', sg + '.surfaceShader' )
			reconnectShd.append( [shd, sg] )
	
	# EXPORT USD FILES
	if ark_exportUSD_geo( assetName, geoPath, geoFmt ):
		ark_exportUSD_proc( assetName, furPath )
	else:
		furPath = ''

	ark_exportUSD_mtl( assetName, mtlPath, previewTex, previewRough, previewCvr )
	
	ark_exportUSD_asset( assetName, assetPath, scenePath, geoPath, mtlPath, furPath, mtlList )

	ark_exportUSD_fixMtl( mtlPath )
	
	# RECONNECT PREVIEW SHADERS
	for each in reconnectShd:
		connectAttr( each[0] + '.outColor', each[1] + '.surfaceShader' )
