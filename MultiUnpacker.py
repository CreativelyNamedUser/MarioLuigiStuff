#Multi-use unpacker for M&L games
import sys
import os
from tkinter import filedialog

while True:
    mode=int(input("Please select the mode, see script header!: "))

    print("Current mode is", mode)
    #0=Partners in time
    #1=Bowser's inside story, requires code file
    #2=Bowser's inside story, PIT method for certain files
    #3=Dream Team (Bros.), requires code file
    #4=BG4 raw file (3DS)
    #5=BG4 with separate header file

    print("Select an output folder...")
    os.chdir(filedialog.askdirectory())

    if mode==0:
        print("Open the file...")
        datpath=filedialog.askopenfilename()
        datsize=os.path.getsize(datpath)
        with open(datpath, "rb") as dat:
            i=0
            dat.seek(0)
            while True:
                offset=int.from_bytes(dat.read(4), "little")
                if offset==datsize:
                    print("Done!")
                    break
                offset2=int.from_bytes(dat.read(4), "little")
                filesize=offset2-offset
                dat.seek(-4, 1)
                cur=dat.tell()
                #[
                dat.seek(offset)
                outdata=dat.read(filesize)
                with open(str(i), "wb") as outfile:
                    outfile.write(outdata)
                #]
                dat.seek(cur)
                i=i+1
    if mode==1:
        print("Open the file...")
        datpath=filedialog.askopenfilename()
        print("Open the code file...")
        codepath=filedialog.askopenfilename()
        o=int(input("Start offset: "))
        with open(datpath, "rb") as dat:
            with open(codepath, "rb") as code:
                i=0
                dat.seek(0)
                code.seek(o)
                tablesize=int.from_bytes(code.read(4), "little")
                filecount=int(((tablesize-4)/4)-1)
                for i in range(filecount):
                    offset=int.from_bytes(code.read(4), "little")
                    offset2=int.from_bytes(code.read(4), "little")
                    filesize=offset2-offset
                    code.seek(-4, 1)
                    dat.seek(offset)
                    outdata=dat.read(filesize)
                    with open(str(i), "wb") as outfile:
                        outfile.write(outdata)
                print("Done!")
    ask=str(input("Unpack again? (Y/N): "))
    if ask.upper() == "N":
        break
