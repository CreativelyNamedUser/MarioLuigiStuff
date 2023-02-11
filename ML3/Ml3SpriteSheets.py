#Extracts sprites from M&L 3 and creates large spritesheets!
#My discord: CreativelyNamedUser#1903
from tkinter import filedialog
from PIL import Image, ImageDraw
import os
from math import ceil # <- There's probably a better way to scale up the 3bit channel values, but this will do for now


#---Change these however you like---
InitString=str(input("Enter an InitString for the top of the sheet... "))
ExtendFilenames=True
PixelSpacing=2
InitSheetX=96
MaxRowImages=24

TestInputs=False


#Decompressed file is outputted to the default folder
def decompress(ComPath):
    filename=os.path.basename(ComPath)+".out"
    with open (ComPath, "rb") as dat:
        with open(filename, "w+b") as dump:
            #Read compressed sizes
            header=int.from_bytes(dat.read(1), "little")
            extsize=header >> 6
            size=(header&0b111111)
            if extsize>0:
                size=size|(int.from_bytes(dat.read(1), "little")<<6)
                if extsize>1:
                    size=size|(int.from_bytes(dat.read(1), "little")<<12)
                    if extsize>2:
                        size=size|(int.from_bytes(dat.read(1), "little")<<18)
            print("Decompressed size", size)
            
            block_header=int.from_bytes(dat.read(1), "little")
            block_extsize=block_header >> 6
            block_count=(block_header&0b111111)
            if block_extsize>0:
                block_count=block_count|(int.from_bytes(dat.read(1), "little")<<6)
                if block_extsize>1:
                    block_count=block_count|(int.from_bytes(dat.read(1), "little")<<12)
                    if block_extsize>2:
                        block_count=block_count|(int.from_bytes(dat.read(1), "little")<<18)
            block_count=block_count+1
            ##print("Compressed blocks", block_count)
            
            #Not sure why they use this block system
            for block in range(block_count):
                #Useless? Tells you how large this block is, not counting this header
                compedsize=int.from_bytes(dat.read(2))
                while True:
                    instructions=int.from_bytes(dat.read(1))
                    for i in range(4):
                        #4 cases this time
                        instruction=instructions&3
                        instructions=instructions>>2
                        if instruction==0:
                            #Marks the end of this block
                            break
                        elif instruction==1:
                            #Just copy the next byte
                            dump.write(dat.read(1))
                        elif instruction==2:
                            #Go back x bytes in the decompressed data and copy y+2 bytes
                            #Length is only the last 4 bits, the rest is distance
                            back=int.from_bytes(dat.read(1), "little")
                            byte2=int.from_bytes(dat.read(1), "little")
                            count=(byte2&15) + 2
                            back=back+(16*(byte2&0xF0))
                            dump.seek(-(back), 2)
                            data=dump.read(count)
                            dump.seek(0, 2)
                            dump.write(data)
                        else:
                            #Copy the second byte x+2 times
                            count=int.from_bytes(dat.read(1), "little") + 2
                            byte=dat.read(1)
                            for x in range(count):
                                dump.write(byte)
                    else:
                        continue
                    break
                ##print("Finished block", block, "@", dat.tell())
        oursize=os.path.getsize(filename)
        ##print("Our decompressed size", oursize)
        if oursize==size:
            print("Success!!")
        else:
            print("Something went wrong")


#Offsets are based on bytes, not pixels
def decodepixel555(pixeldata, offset, array, invisible):
    pixeldata.seek(offset)
    value=int.from_bytes(pixeldata.read(2), "little")
    b=value>>10
    b=(b<<3)|(b>>2)
    g=value>>5 & 0b11111
    g=(g<<3)|(g>>2)
    r=value & 0b11111
    r=(r<<3)|(r>>2)
    a=255
    if invisible==1:
        a=0
    array.append(r)
    array.append(g)
    array.append(b)
    array.append(a)

def decodepixelalpha(pixeldata, offset, array, alpha):
    pixeldata.seek(offset)
    value=int.from_bytes(pixeldata.read(2), "little")
    b=value>>10
    b=(b<<3)|(b>>2)
    g=value>>5 & 0b11111
    g=(g<<3)|(g>>2)
    r=value & 0b11111
    r=(r<<3)|(r>>2)
    array.append(r)
    array.append(g)
    array.append(b)
    array.append(alpha)

def addspace(Sheet, X, Y):
    firstx=Sheet.width
    firsty=Sheet.height
    st=Image.new("RGBA", (firstx+X, firsty+Y), (30, 30, 50))
    st.paste(Sheet)
    Sheet=st
    return Sheet

#---Returns an image as "part", can deal with DS tiled graphics---
#Palshift is the bytes offset into a palette file
def decodeimage(w, h, pixeldata, paldata, palshift, offset, swizzleflag, pixeltype):
    array=bytearray()
    pixeldata.seek(offset)
    if swizzleflag==True:
        tiles=int((w*h)/64)
        tilesw=int(w/8)
        part=Image.new("RGBA", (w, h))
        for i in range(tiles):
            #1 pixel is half of a byte
            if pixeltype==3:
                for x in range(32):
                    pixel=int.from_bytes(pixeldata.read(1), "little")
                    index=pixel & 0b1111
                    if index==0:
                        decodepixel555(paldata, (index*2+palshift), array, 1)
                    else:
                        decodepixel555(paldata, (index*2+palshift), array, 0)
                    index=pixel>>4
                    if index==0:
                        decodepixel555(paldata, (index*2+palshift), array, 1)
                    else:
                        decodepixel555(paldata, (index*2+palshift), array, 0)
            #1 pixel is 1 byte
            if pixeltype==0:
                for x in range(64):
                    index=int.from_bytes(pixeldata.read(1), "little")
                    if index==0:
                        decodepixel555(paldata, (index*2+palshift), array, 1)
                    else:
                        decodepixel555(paldata, (index*2+palshift), array, 0)
            #AI35
            if pixeltype==1:
                for x in range(64):
                    byte=int.from_bytes(pixeldata.read(1), "little")
                    atemp=byte>>5
                    index=byte&0b00011111
                    a=ceil(0xFF*(atemp/7))
                    decodepixelalpha(paldata, (index*2+palshift), array, a)
            #AI53
            if pixeltype==2:
                for x in range(64):
                    byte=int.from_bytes(pixeldata.read(1), "little")
                    atemp=byte>>3
                    index=byte&0b00000111
                    a=(atemp<<3)|(atemp>>2)
                    decodepixelalpha(paldata, (index*2+palshift), array, a)
            tile=Image.frombuffer("RGBA", (8, 8), array)
            x=(i%tilesw)*8
            y=int(i/tilesw)*8
            part.paste(tile, (x, y))
            array=bytearray()
    else:
        pixels=w*h
        for i in range(pixels):
            #1 pixel is half of a byte
            if pixeltype==3:
                pixel=int.from_bytes(pixeldata.read(1), "little")
                index=pixel & 0b1111
                if index==0:
                    decodepixel555(paldata, (index*2+palshift), array, 1)
                else:
                    decodepixel555(paldata, (index*2+palshift), array, 0)
                index=pixel>>4
                if index==0:
                    decodepixel555(paldata, (index*2+palshift), array, 1)
                else:
                    decodepixel555(paldata, (index*2+palshift), array, 0)
            #1 pixel is 1 byte
            if pixeltype==0:
                index=int.from_bytes(pixeldata.read(1), "little")
                if index==0:
                    decodepixel555(paldata, (index*2+palshift), array, 1)
                else:
                    decodepixel555(paldata, (index*2+palshift), array, 0)
            #AI35
            if pixeltype==1:
                byte=int.from_bytes(pixeldata.read(1), "little")
                atemp=byte>>5
                index=byte&0b00011111
                a=ceil(0xFF*(atemp/7))
                decodepixelalpha(paldata, (index*2+palshift), array, a)
            #AI53
            if pixeltype==2:
                byte=int.from_bytes(pixeldata.read(1), "little")
                atemp=byte>>3
                index=byte&0b00000111
                a=(atemp<<3)|(atemp>>2)
                decodepixelalpha(paldata, (index*2+palshift), array, a)
        part=Image.frombuffer("RGBA", (w, h), array)
    return part


def getdimensions(partsizetype):
        if partsizetype == 0:
            w=8
            h=8
        if partsizetype == 1:
            w=16
            h=16
        if partsizetype == 2:
            w=32
            h=32
        if partsizetype == 3:
            w=64
            h=64
        if partsizetype == 4:
            w=16
            h=8
        if partsizetype == 5:
            w=32
            h=8
        if partsizetype == 6:
            w=32
            h=16
        if partsizetype == 7:
            w=64
            h=32
        if partsizetype == 8:
            w=8
            h=16
        if partsizetype == 9:
            w=8
            h=32
        if partsizetype == 10:
            w=16
            h=32
        if partsizetype == 11:
            w=32
            h=64
        if partsizetype > 11:
            w=64
            h=64
            print("Unknown image size! Outputting 64x64...")
        return(w, h)

#Other functions would go here


def addpalette(palfile, Sheet, CursX, CursY, PixelSpacing):
    with open(palfile, "rb") as paldata:
        paldata.seek(4)
        pixels=int((os.path.getsize(palfile)-4)/2)
        offset=4
        array=bytearray()
        for p in range(pixels):
            decodepixel555(paldata, offset, array, 0)
            offset=offset+2
        pal=Image.frombuffer("RGBA", (pixels, 1), array)
        Sheet=addspace(Sheet, (pixels+PixelSpacing), 0)
        Sheet.paste(pal, (CursX, CursY))
    return Sheet

def addparts(animfile, graphicsfile, palfile, num, extend, Sheet, CursX, CursY, PixelSpacing, MaxRowImages):
    
    Sheet=addspace(Sheet, 0, PixelSpacing)
    CursY=CursY+PixelSpacing
    biggesth=0
    
    with open(animfile, "rb") as obj:
        obj.seek(1)
        AnimCount=int.from_bytes(obj.read(1), "little")
        SettingsByte=int.from_bytes(obj.read(1), "little")
        if (SettingsByte>>3) & 1==1:
            swizzleflag=False
        else:
            swizzleflag=True
        pixeltype=SettingsByte & 0b00000011
        obj.seek(1, 1)
        AnimOffset=int.from_bytes(obj.read(4), "little")
        PartOffset=int.from_bytes(obj.read(4), "little")
        AffineOffset=int.from_bytes(obj.read(4), "little")
        obj.seek(5, 1)
        TileByte=int.from_bytes(obj.read(1), "little")
        obj.seek(2, 1)
        LocationOffset=int.from_bytes(obj.read(4), "little")
        
        partcount=int((LocationOffset-PartOffset)/8)
        partoffsetlist=[]
        partsizelist=[]
        partshiftlist=[]
        obj.seek(PartOffset)
        for part in range(partcount):
            flag=0
            OamByte1=int.from_bytes(obj.read(1), "little")
            OamByte2=int.from_bytes(obj.read(1), "little")
            OamByte3=int.from_bytes(obj.read(1), "little")
            OamByte4=int.from_bytes(obj.read(1), "little")
            obj.seek(4, 1)
            shape=OamByte1>>6
            size=OamByte2>>2 & 0b00000011
            shiftbase=OamByte2>>6
            oamplus=OamByte3 & 0b00000011
            partsizetype=(shape*4)+size
            (w, h)=getdimensions(partsizetype)
            
            cur=obj.tell()
            obj.seek(LocationOffset + (part*2))
            OffsetBytes=int.from_bytes(obj.read(2), "little")
            obj.seek(cur)
            #Expand the offsets from the data
            if TileByte==7:
                partoffset=OffsetBytes*128 + 4
            else:
                partoffset=OffsetBytes*8 + 4
            
            palshift=4 + (32*shiftbase)
            palshift=palshift+(oamplus*128)
            
            for z in range(len(partoffsetlist)):
                if partoffsetlist[z]==partoffset and partsizelist[z]==partsizetype and partshiftlist[z]==palshift:
                    flag=1
            if flag==1:
                continue
            partoffsetlist.append(partoffset)
            partsizelist.append(partsizetype)
            partshiftlist.append(palshift)
            
            
            #Hooray, now we decode and Paste the image!
            with open(palfile, "rb") as paldata:
                with open(graphicsfile, "rb") as gdata:
                    partimage=decodeimage(w, h, gdata, paldata, palshift, partoffset, swizzleflag, pixeltype)
            
            
            if part%MaxRowImages==0 and part!=0:
                Sheet=addspace(Sheet, 0, biggesth+PixelSpacing)
                CursY=CursY+biggesth+PixelSpacing
                biggesth=0
                CursX=PixelSpacing
            if h>biggesth:
                biggesth=h
            
            if CursX+w+PixelSpacing>Sheet.width:
                Sheet=addspace(Sheet, (CursX+w+PixelSpacing)-Sheet.width, 0)
            if CursY+h+PixelSpacing>Sheet.height:
                Sheet=addspace(Sheet, 0, (CursY+h+PixelSpacing)-Sheet.height)
            Sheet.paste(partimage, (CursX, CursY))
            CursX=CursX+w+PixelSpacing
            
    return Sheet

def extractsprites(animfile, graphicsfile, palfile, num, extend, Sheet, CursX, CursY, PixelSpacing, MaxRowImages):
    #There's no way to calculate the frame count, so we will have to jump around in the animation data
    with open(animfile, "rb") as obj:
        obj.seek(1)
        AnimCount=int.from_bytes(obj.read(1), "little")
        SettingsByte=int.from_bytes(obj.read(1), "little")
        if (SettingsByte>>3) & 1==1:
            swizzleflag=False
        else:
            swizzleflag=True
        pixeltype=SettingsByte & 0b00000011
        if pixeltype==1 or pixeltype==2:
            print("Alpha pixels in", animfile, graphicsfile)
        obj.seek(1, 1)
        AnimOffset=int.from_bytes(obj.read(4), "little")
        PartOffset=int.from_bytes(obj.read(4), "little")
        AffineOffset=int.from_bytes(obj.read(4), "little")
        obj.seek(5, 1)
        TileByte=int.from_bytes(obj.read(1), "little")
        obj.seek(2, 1)
        LocationOffset=int.from_bytes(obj.read(4), "little")
        partcount=int((LocationOffset-PartOffset)/8)
        #Temporary!!!
        fsclwarning=0
        
        #Add part data to lists for use later
        PartSizeTypes=[]
        PartFlipTypes=[]
        PartOffsets=[]
        PartXs=[]
        PartYs=[]
        PartShifts=[]
        PartAffineIndexes=[]
        for p in range(partcount):
            obj.seek(PartOffset+(p*8))
            OamByte1=int.from_bytes(obj.read(1), "little")
            OamByte2=int.from_bytes(obj.read(1), "little")
            OamByte3=int.from_bytes(obj.read(1), "little")
            OamByte4=int.from_bytes(obj.read(1), "little")
            PartXs.append(int.from_bytes(obj.read(2), "little", signed=True))
            #Reversed
            PartYs.append(-int.from_bytes(obj.read(2), "little", signed=True))
            shape=OamByte1>>6
            if OamByte1&1==1:
                print("Note: Part", p, "in anim file", extend, "is transformed")
                PartAffineIndexes.append(OamByte3>>2)
            else:
                PartAffineIndexes.append(-1)
            size=OamByte2>>2 & 0b00000011
            PartSizeTypes.append((shape*4)+size)
            PartFlipTypes.append(OamByte2&3)
            shiftbase=OamByte2>>6
            oamplus=OamByte3 & 0b00000011
            palshift=4 + (32*shiftbase)
            PartShifts.append(palshift+(oamplus*128))
            cur=obj.tell()
            obj.seek(LocationOffset + (p*2))
            OffsetBytes=int.from_bytes(obj.read(2), "little")
            obj.seek(cur)
            if TileByte==7:
                partoffset=OffsetBytes*128 + 4
            else:
                partoffset=OffsetBytes*8 + 4
            PartOffsets.append(partoffset)
            
        #The most complicated part of the script starts here!
        for anim in range(AnimCount):
            MaxFrameX=0
            MaxFrameY=0
            
            obj.seek(AnimOffset+(8*anim))
            FrameStartPointer=int.from_bytes(obj.read(2), "little")
            obj.seek(2, 1)
            FramePullCount=int.from_bytes(obj.read(2), "little")
            if FramePullCount==0:
                continue
            obj.seek(FrameStartPointer)
            for frame in range(FramePullCount):
                PartPullStart=int.from_bytes(obj.read(2), "little")
                obj.seek(1, 1)
                PartPullCount=int.from_bytes(obj.read(1), "little")
                obj.seek(4, 1)
                if PartPullCount==0:
                    if frame==0:
                        RightX=0
                        TopY=0
                        LeftX=0
                        BottomY=0
                    continue
                #Calculate the size of the animation frames, this is the first of 2 read cycles of the part data
                for i in range((PartPullStart+PartPullCount)-1, PartPullStart-1, -1):
                    #Calculate affine transforms when necessary
                    (w, h)=getdimensions(PartSizeTypes[i])
                    cur=obj.tell()
                    if PartAffineIndexes[i]!=-1:
                        obj.seek(AffineOffset+(8*PartAffineIndexes[i]))
                        print("Index", PartAffineIndexes[i])
                        Affine1=int.from_bytes(obj.read(2), "little", signed=True)
                        Affine2=int.from_bytes(obj.read(2), "little", signed=True)
                        Affine3=int.from_bytes(obj.read(2), "little", signed=True)
                        Affine4=int.from_bytes(obj.read(2), "little", signed=True)
                        print(Affine1, Affine2, Affine3, Affine4)#Debug
                    obj.seek(cur)
                    if frame==0 and i==(PartPullStart+PartPullCount)-1:
                        RightX=PartXs[i]+int(w/2)
                        TopY=PartYs[i]+int(h/2)
                        LeftX=PartXs[i]-int(w/2)
                        BottomY=PartYs[i]-int(h/2)
                    if PartXs[i]+int(w/2)>RightX:
                        RightX=PartXs[i]+int(w/2)
                    if PartYs[i]+int(h/2)>TopY:
                        TopY=PartYs[i]+int(h/2)
                    if PartXs[i]-int(w/2)<LeftX:
                        LeftX=PartXs[i]-int(w/2)
                    if PartYs[i]-int(h/2)<BottomY:
                        BottomY=PartYs[i]-int(h/2)
                    
                    if RightX-LeftX>MaxFrameX:
                        MaxFrameX=RightX-LeftX
                    if TopY-BottomY>MaxFrameY:
                        MaxFrameY=TopY-BottomY
            obj.seek(FrameStartPointer)
            
            #Adds the initial sheet space or create new Y space
            #Default font has a height of 10
            Sheet=addspace(Sheet, 0, 10)
            draw=ImageDraw.Draw(Sheet)
            draw.text((CursX, CursY), text=(str(LeftX)+", "+str(TopY)), fill=(0, 255, 0))
            Sheet=addspace(Sheet, 0, 2)
            CursY=CursY+12
            Sheet=addspace(Sheet, 0, MaxFrameY+PixelSpacing)
            
            for frame in range(FramePullCount):
                #These are colours to indicate affine sprites
                fscl=255
                pscl=255
            
                PartPullStart=int.from_bytes(obj.read(2), "little")
                obj.seek(1, 1)
                PartPullCount=int.from_bytes(obj.read(1), "little")
                FrameTiming=int.from_bytes(obj.read(2), "little")
                #Not finished
                FrameScaleIndex=int.from_bytes(obj.read(2), "little")
                if FrameScaleIndex!=0:
                    fsclwarning=1
                    fscl=127
                if PartPullCount==0:
                    if frame==0:
                        MaxX=0
                        MaxY=0
                        MinX=0
                        MinY=0
                    continue
                #Loop through the parts that make up the frame
                for i in range((PartPullStart+PartPullCount)-1, PartPullStart-1, -1):
                    (w, h)=getdimensions(PartSizeTypes[i])
                    if frame==0 and i==(PartPullStart+PartPullCount)-1:
                        MaxX=PartXs[i]+int(w/2)
                        MaxY=PartYs[i]+int(h/2)
                        MinX=PartXs[i]-int(w/2)
                        MinY=PartYs[i]-int(h/2)
                    
                    if PartXs[i]+int(w/2)>MaxX:
                        MaxX=PartXs[i]+int(w/2)
                    if PartYs[i]+int(h/2)>MaxY:
                        MaxY=PartYs[i]+int(h/2)
                    if PartXs[i]-int(w/2)<MinX:
                        MinX=PartXs[i]-int(w/2)
                    if PartYs[i]-int(h/2)<MinY:
                        MinY=PartYs[i]-int(h/2)
                    
                    if PartAffineIndexes[i]!=-1:
                        pscl=127
                    
                DiffX=MinX-LeftX
                DiffY=TopY-MaxY
                FrameImg=Image.new("RGBA", (MaxFrameX, MaxFrameY))
                for i in range((PartPullStart+PartPullCount)-1, PartPullStart-1, -1):
                    #Now we can actually build the frames!
                    (w, h)=getdimensions(PartSizeTypes[i])
                    PartLocX=DiffX+PartXs[i]-MinX-int(w/2)
                    PartLocY=DiffY+MaxY-PartYs[i]-int(h/2)
                    
                    with open(palfile, "rb") as paldata:
                        with open(graphicsfile, "rb") as gdata:
                            PartImg=decodeimage(w, h, gdata, paldata, PartShifts[i], PartOffsets[i], swizzleflag, pixeltype)
                    if PartFlipTypes[i]==1:
                        PartImg=PartImg.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    if PartFlipTypes[i]==2:
                        PartImg=PartImg.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    if PartFlipTypes[i]==3:
                        PartImg=PartImg.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                        PartImg=PartImg.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    FrameImg.paste(PartImg, (PartLocX, PartLocY), PartImg)
                #if ExtendFilenames==False:
                #    FrameImg.save("{0}-{1}-{2}.png".format(num, anim, frame), "PNG")
                #else:
                #    FrameImg.save("{0}--{1}-{2}-{3}.png".format(extend, num, anim, frame), "PNG")
                
                #This occurs after each frame is generated
                
                if frame%MaxRowImages==0 and frame!=0:
                    Sheet=addspace(Sheet, 0, MaxFrameY+PixelSpacing)
                    CursY=CursY+MaxFrameY+PixelSpacing
                    CursX=PixelSpacing
                
                #if CursX+MaxFrameX+(PixelSpacing*2)+6>Sheet.width:
                #    #Sheet=addspace(Sheet, MaxFrameX+PixelSpacing, 0)
                #    Sheet=addspace(Sheet, (CursX+MaxFrameX+(PixelSpacing*2)+6)-Sheet.width, 0)
                if CursX+MaxFrameX+PixelSpacing>Sheet.width:
                    Sheet=addspace(Sheet, (CursX+MaxFrameX+PixelSpacing)-Sheet.width, 0)
                Sheet.paste(FrameImg, (CursX, CursY))
                
                CursX=CursX+MaxFrameX+PixelSpacing
                
                #Write frame position text
                numspacing=18
                
                if MaxFrameY>7:
                    if CursX+PixelSpacing+numspacing>Sheet.width:
                        Sheet=addspace(Sheet, (CursX+PixelSpacing+numspacing)-Sheet.width, 0)
                    draw=ImageDraw.Draw(Sheet)
                    CursY=CursY+int(MaxFrameY/3)
                    draw.text((CursX, CursY), text=str(FrameTiming), fill=(fscl, 255, pscl))
                    CursY=CursY-int(MaxFrameY/3)
                    CursX=CursX+PixelSpacing+numspacing
                
                
                
            #This happens after an animation strip has been pasted
            CursY=CursY+MaxFrameY+PixelSpacing
            CursX=PixelSpacing
                
        if fsclwarning==1:
            print("Note: Frame scaling is used in anim file", extend)
    return Sheet

#To do: Make sure all Obj data is decoded

print("This tool is experimental! Make sure to get the required info from the game data.\n")

#--Main code: get the game data that should be passed into the extract functions
print("Open an unpacked raw Obj folder containing numbered files...")
objdir=str(filedialog.askdirectory())
print("Open a blank folder for output...")
outdir=str(filedialog.askdirectory())
os.chdir(outdir)
print("Open an overlay containing sprite indexes...")
maininfo=str(filedialog.askopenfilename())
if TestInputs==True:
    palstart=26128
    sprstart=34008
    sprend=42096
    sprentrysize=24
else:
    palstart=int(input("Enter the offset of the palette data: "))
    sprstart=int(input("Enter the offset of the sprite data: "))
    sprend=int(input("Enter the end offset of the sprite data: "))
    sprentrysize=int(input("Enter the size in bytes of each sprite info entry: "))
sprcount=int((sprend-sprstart)/sprentrysize)

with open(maininfo, "rb") as coredata:
    coredata.seek(sprstart)
    
    for i in range(sprcount):
        num=str(i)
        os.chdir(objdir)
        animfile=int.from_bytes(coredata.read(2), "little")
        decompress(os.path.join(objdir, "{}".format(animfile)))
        graphicsfile=int.from_bytes(coredata.read(2), "little")
        decompress(os.path.join(objdir, "{}".format(graphicsfile)))
        os.chdir(outdir)
        palentryindex=int.from_bytes(coredata.read(2), "little")
        check=int.from_bytes(coredata.read(2), "little")
        if check==0:
            coredata.seek(sprentrysize-8, 1)
            continue
        coredata.seek(sprentrysize-8, 1)
        cur=coredata.tell()
        coredata.seek(palstart+((palentryindex)*4))
        palindex=int.from_bytes(coredata.read(2), "little")
        palanimindex=int.from_bytes(coredata.read(2), "little")
        if palanimindex!=65535:
            print(animfile, "uses palette animation file", palanimindex)
        coredata.seek(cur)
        
        Sheet=Image.new("RGBA", (InitSheetX, 16), (30, 30, 50))
        draw=ImageDraw.Draw(Sheet)
        draw.text((PixelSpacing, PixelSpacing), text=(InitString+" "+str(animfile)+"-"+num), fill=(255, 255, 0))
        
        CursX=InitSheetX
        CursY=6
        Sheet=addpalette(os.path.join(objdir, "{0}".format(palindex)), Sheet, CursX, CursY, PixelSpacing)
        CursX=PixelSpacing
        CursY=16
        
        #Add the frames, this leads to the interesting part
        Sheet=extractsprites(os.path.join(objdir, "{0}.out".format(animfile)), os.path.join(objdir, "{0}.out".format(graphicsfile)), os.path.join(objdir, "{0}".format(palindex)), num, animfile, Sheet, CursX, CursY, PixelSpacing, MaxRowImages)
        
        CursX=PixelSpacing
        CursY=Sheet.height
        Sheet=addparts(os.path.join(objdir, "{0}.out".format(animfile)), os.path.join(objdir, "{0}.out".format(graphicsfile)), os.path.join(objdir, "{0}".format(palindex)), num, animfile, Sheet, CursX, CursY, PixelSpacing, MaxRowImages)
        
        if ExtendFilenames==True:
            Sheet.save("{0}-{1}.png".format(animfile, num), "PNG")
        else:
            Sheet.save("{0}.png".format(num), "PNG")
        os.remove(os.path.join(objdir, "{}.out".format(animfile)))
        os.remove(os.path.join(objdir, "{}.out".format(graphicsfile)))
