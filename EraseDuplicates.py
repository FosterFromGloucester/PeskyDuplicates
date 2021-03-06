import os.path
import hashlib
import sys
import os
import shutil
import eyed3
from pyechonest import track
import pyechonest.config as config
import pyechonest.song as song

config.CODEGEN_BINARY_OVERRIDE = os.path.abspath("../echoprint-codegen")
config.ECHO_NEST_API_KEY='' #Developer key replace with your own

InfoCheckCount = 0;
DuplicateCount = 0;
Extensions = ('.MP3', '.WAV', '.MP4') #Supported Formats

def md5TheFile(filename,trackList):#Md5s the audio file. Ensures no duplicates are possible. Maintains a tracklist containing tuples
    with open(filename) as fileToMd5:
        m = hashlib.md5()
        chunk_sz = m.block_size * 128
        data = fileToMd5.read(chunk_sz)
        while data:
            m.update(data)
            data = fileToMd5.read(chunk_sz)
        trackList.append((filename, m.hexdigest()))#Tuples in the form of (filepath,MD5Hash)

def is_sound_file(filename):#Checks the validity of the audio extension takes in the filename
    extension = os.path.splitext(filename)[1].upper()
    return extension in Extensions

def getDuplicates(trackList):#Goes through the tracklist looking for duplicates
    seen = set()#Maintains a set
    duplicates = []
    for x in trackList:
        if x[1] in seen:#check if the hash is already in the list
            duplicates.append(x)#If seen add to duplicates
            global DuplicateCount
            DuplicateCount = DuplicateCount+1#Duplicate count reported to user
        seen.add(x[1])
    return duplicates
    
def deleteDuplicates(duplicates):#Goes through list of duplciates deleting them based on filepath
    for extra in duplicates:
        try:
            os.remove(extra[0])
        except OSError:
            pass
        
def init(trackList):
    md5TheFile.trackList = trackList

def checkForMetaData(filepath):#Checks whether the audio file has associated meta data
    audiofile = eyed3.load(filepath)
    if(audiofile.tag.artist == None or audiofile.tag.title == None):#This is where EyeD3 comes in handy
        aquireTrackInfo(filepath,audiofile)
        
def aquireTrackInfo(filepath,loadedAudio):#If not meta data present then retrieve it. pyechonest comes in here
    print('Retrieving...')
    pytrack = track.track_from_filename(filepath)
    setTrackInfo(loadedAudio,pytrack,filepath)
    
def setTrackInfo(loadedAudio,pytrack,filepath):#Update the audio file meta data 
    loadedAudio.tag.artist  = pytrack.artist if hasattr(pytrack, 'artist') else 'Unknown'
    loadedAudio.tag.title  = pytrack.title if hasattr(pytrack, 'title') else 'Unknown'
    loadedAudio.tag.save()
    if(loadedAudio.tag.title != "Unknown"):#dont change the title if it failed to retrieve
        global InfoCheckCount
        InfoCheckCount = InfoCheckCount+1
        filenameAndExe = os.path.splitext(filepath)
        filename, exe = filenameAndExe
        try:
            dest = filepath[0:filepath.rfind('/')+1] + loadedAudio.tag.title + exe
            os.rename(filepath,dest)
        except:
            print("Failed to rename file")
 
 
def checkForEmpties(path):#Check for empty direcctories that may have resulted from deleteing duplicates
       for dirpath, dirnames, filenames in os.walk(path):
           files =0
           folders = 0
           for path, directories, audiofiles in os.walk(dirpath):
               files += len(audiofiles)
               folders += len(directories)
           if(files == 0 and folders == 0):
               shutil.rmtree(dirpath)
            
def main():
    
    meta = raw_input('Would you like to find missing meta data on files? (Y/N)') 
    checkMeta = False
    
    if(meta == 'Y'):
        checkMeta = True
        
    trackList = list() 
    print('Processing...')
    toSearchIn  = os.path.dirname(os.path.realpath(__file__))+"/Music"
    for dirpath, dirnames, filenames in os.walk(toSearchIn):
        for filename in filenames:
            filepath = os.path.join(dirpath,filename)
            if(is_sound_file(filepath)):
                filepath = os.path.join(dirpath,filename)
                md5TheFile(filepath,trackList)
                if(checkMeta):
                    try:
                        checkForMetaData(filepath)
                    except:
                        print("Failed to aquire meta data")
    
    duplicates = getDuplicates(trackList)
   
    if(len(duplicates) > 0):
        print("Found " +str(DuplicateCount)+" duplicates")
        disDup = raw_input("Display duplicates? (Y/N)") 
        if(disDup):
            for dup in duplicates:
                print(dup[0])
        ans = raw_input('Would you like to delete them? (Y/N)') 
        if(ans == 'Y'):
            deleteDuplicates(duplicates)
        else:
            sys.exit()
    else:
        print("No duplicates to delete")
        
    if InfoCheckCount > 0:
        print("Retrieved meta data for " + str(InfoCheckCount)+ " audio files")
        
    empty = raw_input('Would you like to delete empty directories? (Y/N)') 
    if(empty):
        try:
            checkForEmpties(toSearchIn)
        except:
            print("Failed to clean up directories")
        
if __name__ == '__main__':
    sys.exit(main())
