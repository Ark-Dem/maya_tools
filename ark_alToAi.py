from maya.cmds import *

def ark_alToAi():
    hasAls = 0

    types = [ 'alRemapColor', 'alLayerFloat', 'alLayerColor', 'alCombineFloat', 'alCombineColor' ]

    for each in ls():
        nt = nodeType( each )
        if nt[:2] == 'al' and not nt in types:
            print '!!! Unsupported alShaders node: ' + each
            hasAls = 1

    for typ in types:
        lsTyp = ls( type = typ )
        if len( lsTyp ) > 0:
            print( typ + ': ' + str( lsTyp ) )
            hasAls = 2

    if not hasAls:
        print 'No alShaders nodes...'
    elif hasAls > 1:
        # alRemapColor
        attrDict = { 'input':'input',
                    'inputR':'inputR',
                    'inputG':'inputG',
                    'inputB':'inputB',
                    'gamma':'gamma', 
                    'saturation':'saturation', 
                    'hueOffset':'hueShift', 
                    'contrast':'contrast', 
                    'contrastPivot':'contrastPivot', 
                    'gain':'multiply', 
                    'exposure':'exposure', 
                    'mask':'mask' }
                    
        lst = ls( type = 'alRemapColor' )
        
        for each in lst:
            #print( 'Processing ' + each )
            if 'remap' in each:
                ai = each.replace( '__remap', '__CC' )
            else:
                ai = each + '__CC'
            ai = shadingNode( 'aiColorCorrect', asUtility = True, name = ai )
            
            attrConn = []
            conns = listConnections( each, s = True, d = False, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                attr = conns[i].split('.')[-1]
        
                attrConn.append( attr )        
                if attr == 'input':
                    attrConn.append( 'inputR' )
                    attrConn.append( 'inputG' )
                    attrConn.append( 'inputB' )
                elif attr in ['inputR', 'inputG', 'inputB']:
                    attrConn.append( 'input' )
                    
                if not '.message' in conns[i]:
                    if attr == 'gain':
                        connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attr, '.' + attrDict[attr] + 'R' ), force = True )
                        connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attr, '.' + attrDict[attr] + 'G' ), force = True )
                        connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attr, '.' + attrDict[attr] + 'B' ), force = True )
                    else:
                        connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attr, '.' + attrDict[attr] ), force = True )
                    disconnectAttr( conns[i+1], conns[i] )
        
            conns = listConnections( each, s = False, d = True, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                if not '.message' in conns[i]:
                    connectAttr( conns[i].replace( each, ai ), conns[i+1], force = True )
        
            for attr in attrDict.keys():
                attrVal = getAttr( each + '.' + attr )
                if attr == 'gain' and not attr in attrConn:
                    setAttr( ai + '.' + attrDict[attr], attrVal, attrVal, attrVal, type = 'double3' )
                elif attr == 'saturation' and attrVal < 1.0:
                    inp = listConnections( ai + '.input', s = True, d = False, c = True, p = True )[1]
                    
                    satLum = shadingNode( 'aiColorToFloat', asUtility = True, name = ai.replace( '__CC', '__lum' ) )
                    setAttr( satLum + '.mode', 4 )
                    connectAttr( inp, satLum + '.input' )
                    
                    satLay = shadingNode( 'aiLayerRgba', asUtility = True, name = ai.replace( '__CC', '__layer' ) )
                    connectAttr( inp, satLay + '.input1' )
                    connectAttr( satLum + '.outValue', satLay + '.input2R' )
                    connectAttr( satLum + '.outValue', satLay + '.input2G' )
                    connectAttr( satLum + '.outValue', satLay + '.input2B' )
                    setAttr( satLay + '.name1', 'base', type = 'string' )
                    setAttr( satLay + '.name2', 'desaturated', type = 'string' )
                    setAttr( satLay + '.enable2', True )
                    setAttr( satLay + '.operation2', 0 )
                    setAttr( satLay + '.clamp', True )
                    connectAttr( satLay + '.outColor', ai + '.input', force = True )
                    if not attr in attrConn:
                        setAttr( satLay + '.mix2', (1.0-attrVal) )
                    else:
                        satRev = shadingNode( 'reverse', asUtility = True, name = ai.replace( '__CC', '__reverse' ) )
                        satConn = listConnections( ai + '.saturation', s = True, d = False, c = True, p = True )
                        disconnectAttr( satConn[1], satConn[0] )
                        setAttr( ai + '.saturation', 1 )
                        connectAttr( satConn[1], satRev + '.inputX' )
                        connectAttr( satRev + '.outputX', satLay + '.mix2' )
                    if 'mask' in attrConn:
                        satMult = shadingNode( 'multiplyDivide', asUtility = True, name = ai.replace( '__CC', '__satMult' ) )
                        mskConn = listConnections( ai + '.mask', s = True, d = False, c = True, p = True )[1]
                        connectAttr( mskConn, satMult + '.input1X' )
                        connectAttr( satMult + '.outputX',  satLay + '.mix2', force = True )
                        if not attr in attrConn:
                            setAttr( satMult + '.input2X', (1.0-attrVal) )
                        else:
                            connectAttr( satRev + '.outputX', satMult + '.input2X' )
                elif not attr in attrConn:
                    setAttr( ai + '.' + attrDict[attr], attrVal )
                
            delete( each )
        
        
        
        # alLayerFloat
        attrDict = { 'layer1':'input1', 'layer2':'input2', 'layer3':'input3', 'layer4':'input4', 'layer5':'input5', 'layer6':'input6', 'layer7':'input7', 'layer8':'input8',
                    'layer1name':'name1', 'layer2name':'name2', 'layer3name':'name3', 'layer4name':'name4', 'layer5name':'name5', 'layer6name':'name6', 'layer7name':'name7', 'layer8name':'name8',
                    'layer1enabled':'enable1', 'layer2enabled':'enable2', 'layer3enabled':'enable3', 'layer4enabled':'enable4', 'layer5enabled':'enable5', 'layer6enabled':'enable6', 'layer7enabled':'enable7', 'layer8enabled':'enable8',
                    'layer1a':'mix1', 'layer2a':'mix2', 'layer3a':'mix3', 'layer4a':'mix4', 'layer5a':'mix5', 'layer6a':'mix6', 'layer7a':'mix7', 'layer8a':'mix8' }
                    
        lst = ls( type = 'alLayerFloat' )
        
        for each in lst:
            #print( 'Processing ' + each )
            if 'layer' in each:
                ai = each.replace( '__layer', '__layerFloat' )
            else:
                ai = each + '__layerFloat'
            ai = shadingNode( 'aiLayerFloat', asUtility = True, name = ai )
            
            attrConn = []
            conns = listConnections( each, s = True, d = False, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                attr = conns[i].split('.')[-1]
        
                attrConn.append( attr )        
                    
                if not '.message' in conns[i]:
                    connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attr, '.' + attrDict[attr] ), force = True )
                    disconnectAttr( conns[i+1], conns[i] )
        
            conns = listConnections( each, s = False, d = True, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                if not '.message' in conns[i]:
                    connectAttr( conns[i].replace( each, ai ), conns[i+1], force = True )
                    
            for attr in attrDict.keys():
                if not attr in attrConn:
                    attrVal = getAttr( each + '.' + attr )
                    if 'name' in attr:
                        setAttr( ai + '.' + attrDict[attr], attrVal, type = 'string' )
                    else:
                        setAttr( ai + '.' + attrDict[attr], attrVal )
    
            delete( each )
    
    
        
        # alLayerColor
        attrDict = { 'layer1':'input1', 'layer2':'input2', 'layer3':'input3', 'layer4':'input4', 'layer5':'input5', 'layer6':'input6', 'layer7':'input7', 'layer8':'input8',
                    'layer1name':'name1', 'layer2name':'name2', 'layer3name':'name3', 'layer4name':'name4', 'layer5name':'name5', 'layer6name':'name6', 'layer7name':'name7', 'layer8name':'name8',
                    'layer1enabled':'enable1', 'layer2enabled':'enable2', 'layer3enabled':'enable3', 'layer4enabled':'enable4', 'layer5enabled':'enable5', 'layer6enabled':'enable6', 'layer7enabled':'enable7', 'layer8enabled':'enable8',
                    'layer1a':'mix1', 'layer2a':'mix2', 'layer3a':'mix3', 'layer4a':'mix4', 'layer5a':'mix5', 'layer6a':'mix6', 'layer7a':'mix7', 'layer8a':'mix8',
                    'layer1blend':'operation1', 'layer2blend':'operation2', 'layer3blend':'operation3', 'layer4blend':'operation4', 'layer5blend':'operation5', 'layer6blend':'operation6', 'layer7blend':'operation7', 'layer8blend':'operation8',
                    'clampResult':'clamp' }
        
        modeDict = { 0:0, 3:23, 5:30, 6:22, 10:32, 14:5, 11:27, 2:21, 1:20 }
                    
        lst = ls( type = 'alLayerColor' )
        
        for each in lst:
            #print( 'Processing ' + each )
            if 'layer' in each:
                ai = each.replace( '__layer', '__layerRgba' )
            else:
                ai = each + '__layerRgba'
            ai = shadingNode( 'aiLayerRgba', asUtility = True, name = ai )
            
            attrConn = []
            conns = listConnections( each, s = True, d = False, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                attr = conns[i].split('.')[-1]
        
                attrConn.append( attr )
                if attr in [ 'layer1', 'layer2', 'layer3', 'layer4', 'layer5', 'layer6', 'layer7', 'layer8' ]:
                    attrConn.append( attr + 'R' )
                    attrConn.append( attr + 'G' )
                    attrConn.append( attr + 'B' )
                elif attr[-1] in ['R', 'G', 'B']:
                    attrConn.append( attr[:-1] )
                    
                if not '.message' in conns[i]:
                    attrRep = attr
                    if attr[-1] in [ 'R', 'G', 'B' ]:
                        attrRep = attr[:-1]
                    connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attrRep, '.' + attrDict[attrRep] ), force = True )
                    disconnectAttr( conns[i+1], conns[i] )
        
            conns = listConnections( each, s = False, d = True, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                if not '.message' in conns[i]:
                    connectAttr( conns[i].replace( each, ai ), conns[i+1], force = True )
                    
            for attr in attrDict.keys():
                if not attr in attrConn:
                    attrVal = getAttr( each + '.' + attr )
                    if 'name' in attr:
                        setAttr( ai + '.' + attrDict[attr], attrVal, type = 'string' )
                    elif 'blend' in attr:
                        setAttr( ai + '.' + attrDict[attr], modeDict[attrVal] )
                    elif 'enabled' in attr or attr == 'clampResult':
                        setAttr( ai + '.' + attrDict[attr], attrVal )
                    elif attr[-1] == 'a':
                        if attrVal < 0.0 and getAttr( each + '.' + attr[:-1] + 'blend' ) == 5:
                            setAttr( each + '.' + attr[:-1] + 'blend', 6 )
                            setAttr( each + '.' + attr, -attrVal )
                            setAttr( ai + '.' + attrDict[attr], -attrVal )
                            setAttr( ai + '.operation' + attr[-2], 22 )
                        else:
                            setAttr( ai + '.' + attrDict[attr], attrVal )                    
                    else:
                        setAttr( ai + '.' + attrDict[attr], attrVal[0][0], attrVal[0][1], attrVal[0][2], type = 'double3' )
    
            delete( each ) 
        
    
    
        # alCombineFloat
        attrDict = { 'input1':'input1',
                    'input2':'input2',
                    'input3':'mix2' }
                  
        lst = ls( type = 'alCombineFloat' )
        
        for each in lst:
            #print( 'Processing ' + each )
            if 'combine' in each:
                ai = each.replace( '__combine', '__layerFloat' )
            else:
                ai = each + '__layerFloat'
            ai = shadingNode( 'aiLayerFloat', asUtility = True, name = ai )
            
            attrConn = []
            conns = listConnections( each, s = True, d = False, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                attr = conns[i].split('.')[-1]
        
                attrConn.append( attr )        
                    
                if not '.message' in conns[i]:
                    connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attr, '.' + attrDict[attr] ), force = True )
                    disconnectAttr( conns[i+1], conns[i] )
        
            conns = listConnections( each, s = False, d = True, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                if not '.message' in conns[i]:
                    connectAttr( conns[i].replace( each, ai ), conns[i+1], force = True )
                    
            for attr in attrDict.keys():
                setAttr( ai + '.enable2', True )
                if not attr in attrConn:
                    attrVal = getAttr( each + '.' + attr )
                    setAttr( ai + '.' + attrDict[attr], attrVal )
    
            delete( each )
        
        
        
        # alCombineColor
        attrDict = { 'input1':'input1', 'input1R':'input1R', 'input1G':'input1G', 'input1B':'input1B',
                    'input2':'input2', 'input2R':'input2R', 'input2G':'input2G', 'input2B':'input2B',
                    'input3':'mix2' }
                  
        lst = ls( type = 'alCombineColor' )
        
        for each in lst:
            if getAttr( each + '.combineOp' ) != 4:
                print( 'Unsupported alCombineColor mode: ' + each )
            #print( 'Processing ' + each )
            if 'combine' in each:
                ai = each.replace( '__combine', '__layerRgba' )
            else:
                ai = each + '__layerRgba'
            ai = shadingNode( 'aiLayerRgba', asUtility = True, name = ai )
            
            attrConn = []
            
            conns = listConnections( each, s = True, d = False, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                attr = conns[i].split('.')[-1]
        
                attrConn.append( attr )        
                if attr in [ 'input1', 'input2' ]:
                    attrConn.append( attr + 'R' )
                    attrConn.append( attr + 'G' )
                    attrConn.append( attr + 'B' )
                elif attr[-1] in ['R', 'G', 'B']:
                    attrConn.append( attr[:-1] )
                                
                if not '.message' in conns[i]:
                    connectAttr( conns[i+1], conns[i].replace( each, ai ).replace( '.' + attr, '.' + attrDict[attr] ), force = True )
                    disconnectAttr( conns[i+1], conns[i] )
        
            conns = listConnections( each, s = False, d = True, c = True, p = True )
            for i in xrange(0, len(conns), 2):
                if not '.message' in conns[i]:
                    connectAttr( conns[i].replace( each, ai ), conns[i+1], force = True )
                    
            for attr in attrDict.keys():
                setAttr( ai + '.enable2', True )
                setAttr( ai + '.operation2', 0 )
                setAttr( ai + '.clamp', True )
                if not attr in attrConn:
                    attrVal = getAttr( each + '.' + attr )
                    if getAttr( ai + '.' + attrDict[attr], type = True ) == 'float' :
                        setAttr( ai + '.' + attrDict[attr], attrVal )
                    else:
                        setAttr( ai + '.' + attrDict[attr], attrVal[0][0], attrVal[0][1], attrVal[0][2], type = 'double3' )
    
            delete( each )
