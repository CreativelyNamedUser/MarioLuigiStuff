from tkinter import filedialog
import os

#Superstar Saga sprite decompressor! My first go at decompressing stuff....
print("Open a compressed file")
ComPath=filedialog.askopenfilename()
print("Open output folder")
os.chdir(filedialog.askdirectory())
with open (ComPath, "rb") as dat:
    with open("Decomp.bin", "w+b") as dump:
        #Skip decompressed file size? Looks like 2bit+6bit+size
        header=int.from_bytes(dat.read(1), "little")
        extsize=header >> 6
        size=(header&0b111111) + 0x40*int.from_bytes(dat.read(extsize), "little") + 1
        print("Decompressed size", size)
        #Loop until we hit EndOfFile flag
        while True:
            #For each command: Case 3 bits, Param 5 bits
            #5 special cases that can be used
            Command=int.from_bytes(dat.read(1), "little")
            Case=Command>>5
            Length=Command & 0b11111
            ##print("Case", Case, "Length", Length)
            if Case==4:
                #Read bytes
                for i in range(0, Length+1):
                    Byte=dat.read(1)
                    dump.write(Byte)
            elif Case==5:
                #Add zero before each byte
                for i in range(0, Length+1):
                    Byte=dat.read(1)
                    dump.write(b"\x00")
                    dump.write(Byte)
            elif Case==6:
                #Repeat the next byte n times, don't forget to +1
                Byte=dat.read(1)
                for i in range(0, Length+2):
                    dump.write(Byte)
            elif Case==7:
                #Attack of the zeroes, if FF use next byte as length
                for i in range(0, Length+1):
                    dump.write(b"\x00")
                if Command==255:
					print("Warning: Got to adding extra zeroes, this has not been tested!")
                    Extra=int.from_bytes(dat.read(1), "little")
                    for i in range(0, Extra):
                        dump.write(b"\x00")
            else:
                #Repeat bytes or stop decompressing
                Param=int.from_bytes(dat.read(1), "little")
                if Command==127 and Param==255:
					finalsize=os.path.getsize(ComPath)
                    print("Final size", finalsize)
					if size!=finalsize:
						print("Warning: There was an error during data decompression! Sizes do not match")
					break
                else:
                    length=Command>>2
                    dist=Param + (256*(Command&3))
					if Command&2==0:
						print("Warning: positive repeat offset, this was not expected!")
                    dist=0x400-dist
                    #Debug
                    ##print("Dist", dist)
                    start=dump.tell()
                    for i in range(0, length+2):
                        cur=dump.tell()
                        dump.seek(start-dist)
                        Byte=dump.read(1)
                        dist=dist-1
                        dump.seek(cur)
                        dump.write(Byte)
