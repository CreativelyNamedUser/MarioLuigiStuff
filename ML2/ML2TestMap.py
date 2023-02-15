from tkinter import filedialog
try:
    from PIL import Image, ImageDraw
except:
    print("Pillow is not installed! Try pip install pillow")
    raise Exception()
import os

def decodepixel555(pixeldata, offset, array, invisible):
	pixeldata.seek(offset)
	value=int.from_bytes(pixeldata.read(2), "little")
	if value==65535:
		print("Value WARNING! (Outside the palette file)")
		for i in range(3):
			array.append(0)
		a=255
		if invisible==1:
			a=0
		array.append(a)
	else:
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

def decodeimage(w, h, pixeldata, paldata, offset, palshift, swizzleflag, pixeltype):
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
			pixeldata.seek(i+offset)
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
		img=Image.frombuffer("RGBA", (w, h), array)
	return img


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

print("Open an unpacked, raw TestMap folder")
TestDir=filedialog.askdirectory()
os.chdir(TestDir)
for set in range(6):
    PalPath=os.path.join(TestDir, str(set*3))
    GfxPath=os.path.join(TestDir, str(set*3 + 1))
    IndexPath=os.path.join(TestDir, str(set*3 + 2))
    decompress(GfxPath)
    decompress(IndexPath)
    GfxPath=GfxPath+".out"
    IndexPath=IndexPath+".out"
    with open(IndexPath, "rb") as IndexDat:
        IndexDat.seek(0)
        IndexCount=int(os.path.getsize(IndexPath)/2)
        w=512
        tilesw=int(w/8)
        h=int(IndexCount/tilesw)*8
        MapImg=Image.new("RGBA", (w, h))
        for i in range(IndexCount):
            val=int.from_bytes(IndexDat.read(2), "little")
            tileind=val&0b1111111111
            flip=(val>>10)&3
            palshift=(val>>12)&15
            if palshift!=0:
                print("WARNING: Unexpected palshift!")
            #w, h, pixeldata, paldata, offset, palshift, swizzleflag, pixeltype
            with open(PalPath, "rb") as paldata:
                with open(GfxPath, "rb") as pixeldata:
                    Tile=decodeimage(8, 8, pixeldata, paldata, tileind*64, palshift*32, False, 0)
                    if flip==1:
                        Tile=Tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    if flip==2:
                        Tile=Tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    if flip==3:
                        Tile=Tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                        Tile=Tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    tilex=8*(i%tilesw)
                    tiley=8*int(i/tilesw)
                    MapImg.paste(Tile, (tilex, tiley))
    os.remove(GfxPath)
    os.remove(IndexPath)
    MapImg.save("{}.png".format(str(set)))
