from string import zfill

fPath = 'd:/_temp/arnold/'
fName = 'female'
startFrame = 1
endFrame = 10

for i in xrange( startFrame, endFrame+1, 1 ):
    fIn = open( fPath + fName + '.' + zfill( i, 4 ) + '.ass', 'r' )
    fOut = open( fPath + fName + '__tmp.' + zfill( i, 4 ) + '.ass', 'w' )
    for line in fIn:
        fOut.write( line.replace('-file D','-file \\"D').replace('-geom D','-geom \\"D').replace('xgen -palette','xgen\\" -palette').replace('abc -patch','abc\\" -patch') )
    fOut.close()
    fIn.close()

