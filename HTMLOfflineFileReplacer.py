import os, sys
import shutil
import re # ew
import textwrap
import time, datetime

# seperate install needed
import requests # for requesting downloading files, need to install seperately, and is slows the script down the most
import argparse

import io

import urllib3
urllib3.disable_warnings()
http = urllib3.PoolManager()

# This is script is meant to be used with an html file exported from: https://github.com/Tyrrrz/DiscordChatExporter/releases
# it may work with other html files though, never tested

if os.name == 'nt':
    import msvcrt
    import ctypes
    # rename the window (windows only)
    ctypes.windll.kernel32.SetConsoleTitleW("Demez Awful HTML File Archiver - Setting Up")

    # change the window size (windows only i think, never tried on posix)
    #os.system( 'mode con: cols=' + str( 140 ) + ' lines=' + str( 15 ) )
    os.system( 'mode con: cols=140 lines=1500' )
    
    # hide the cursor
    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int),
                    ("visible", ctypes.c_byte)]
        
    ci = _CursorInfo()
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
    ci.visible = False
    ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    
elif os.name == 'posix':
    # hide the cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    
max_width = 140

def PrintBreak( line, break_length ):
    # get number of characters in line
    line_length = len( str( line ) ) + 4

    global max_width

    if ( line_length > max_width ) and ( break_length != 0 ):
        # split the line by the length of the window, and then add the split length onto the text after it
        
        new_line = [ "", "" ]
        char_counter = 0
        line_char_list = []
        for character in line:
            char_counter += 1
            #new_line[0] = new_line[0] + character
            line_char_list.append( character )

            if len( line_char_list ) < max_width - 8:
                new_line[0] = new_line[0] + character
            else:
                new_line[1] = new_line[1] + character

        del line_char_list

            #new_line[0].append( " " )

        # convert break_length into multiple spaces
        space_length = []
        count = 0
        while ( count < break_length ):
            count += 1
            space_length.append( " " )

        new_line[1] = ''.join( space_length ) + new_line[1]
        print( new_line[0] )
        print( new_line[1] )

    else:
        print( line )

# C:\Users\Demez\AppData\Local\Programs\Python\Python37-32\python.exe -m pip install requests
# python -m pip install requests
#from shutil import copyfile

parser = argparse.ArgumentParser(description='Creates an Offline version of an HTML file with all files downloaded')
parser.add_argument('--input_file', type=str, help='the video file you want modified', nargs='+' )
parser.add_argument('--output_file', type=str, default="", help="the output file.", nargs='+')
parser.add_argument('--output_folder', type=str, default="", help="folder where everything will be saved in", nargs='+')

args = parser.parse_args()

try:
    input_html = ' '.join( args.input_file )
    output_html = ' '.join( args.output_file )
    folder_root = ' '.join( args.output_folder )
except:
    print(  "Not all input arguments were defined. You need:\n"
            "--input_file 'FILE' --output_file 'FILE' --output_folder 'FOLDER' " )
    input()

def GetNumberOfLines( file ):
    total_num_lines = 0
    with open( file, 'r', encoding="utf8" ) as f:
        print( "Getting Total Number of Lines in:   " + file )
        for line in f:
            total_num_lines += 1
    print( "Finished:   " + str(total_num_lines) + " Lines." )
    return total_num_lines

def CreatePath( folder ):
    try:
        os.mkdir( folder + "/" )
    except:
        pass

# check if one of the folders is a discord folder
def DeletePath( folder ):
        # delete directory and all its contents
        if folder != ( folder_root + "/" ):
            if os.path.isdir( folder ):
                shutil.rmtree( folder ) 

        # will only delete files, no folders
        else: 
            if os.path.isdir( folder ):
                for file in os.listdir( folder ):
                    file_path = os.path.join( folder, file )
                    try:
                        for reserved in discord_folders:
                            if ( os.path.isfile(file_path) ) and not ( file_path.endswith( reserved ) ):
                                os.unlink( file_path )
                        #elif os.path.isdir(file_path): shutil.rmtree(file_path)
                    except Exception as e:
                        print(e)

# list of common names for files, just catch these so it doesn't check through like 10,000 files of the same name for these
duplicate_list = [ "magik.png", "unknown.png", "maxresdefault.jpg", "maxresdefault.png", "hqdefault.jpg", "header.jpg"  ]
duplicate_list_counter = [ 0, 0, 0, 0, 0, 0 ]

# not including attachments, since those can be different
# this is only for files we know will be the same
discord_folders = [ "avatars", "emojis", "emojis_default", "icons", "embed" ]

# this will have a LOT of extensions in this tuple
valid_file_ext = ( "png", "jpg", "gif" )

# this might be faster
ext_split_chars = [ "?", "&" ]

DeletePath( folder_root + "/" )
DeletePath( folder_root + "/attachments/" )
CreatePath( folder_root + "/" )

# ew
# write is slow here somehow?
def FindURLContainer( line ):
    try:
        line_split = line.split( "src=" )[1]
        return "src"
    except:
        try:
            line_split = line.split( "href=" )[1]
            return "href"
        except:
            return False

found_urls = []

def GetURL( line, type ):    
    line_split = line.split( type + '=')

    if type == "src":
        line_split = line_split[1].split('/>')
    elif type == "href":
        line_split = line_split[1].split('>')
    else:
        print("what the fuck how did you get this")
    
    # remove the quotes wrapped around the url
    url = line_split[0].split('"')
    
    return url[1]

def CheckForDuplicateURL( url ):
    if url in found_urls:
        return True
    else:
        found_urls.append( url )
        return False

# ok i am calling this too many times lmao
# works only on discord images
# maybe add a common files folder?
def GetFolderPath( url ):    
    try:
        # discord file url
        discord_split = url.split("https://cdn.discordapp.com/")[1]
        folder_append = folder_root + "/" + ( discord_split.split('/') )[0]
        CreatePath( folder_append )
        return folder_append + "/"
    except:
        try:
            # default discord emoji url
            emoji_split = url.split("https://twemoji.maxcdn.com/")[1]
            folder_append = folder_root + "/emojis_default"
            CreatePath( folder_append )
            return folder_append + "/"
        except:
            return folder_root + "/"


# would be nice if we also returned a folder for the file to be in
# but i don't feel like adding that in atm
def GetFileName( url, type, folder, duplicate_url ):
    filename = url.rsplit('/', 1)
    filename = filename[1].rsplit('"')[0]

    # check for anything after the file extension
    try:
        # if the filename does not have a period, this will throw an exception
        file_split = filename.rsplit('.', 1)
        file_ext = file_split[1].lower()

        # maybe it has extra characters added onto it
        if not ( file_ext ).endswith( valid_file_ext ):
            # maybe it has invalid characters
            if not file_ext.isalnum():
                for split_char in ext_split_chars:
                    if split_char in file_ext:
                        file_ext = file_ext.split( split_char )[0]
                        break
            # add the "correct" file extension on
            filename = file_split[0] + "." + file_ext

        if not ( file_split[0] ).isalnum():
            filename = re.sub( '[^-a-zA-Z0-9_() ]+', '', file_split[0] ) + "." + file_ext

        filename = SearchForDuplicateFileName( folder, filename, type, duplicate_url )

        return filename

    except:
        return None

# the old method, much faster, but you need to manually add names to the list
# bug with this, will create name (0).png on the first one everytime if href was used before
# not that big of a deal, but a bit annoying
def CheckForCommonFileName( filename, type ):
    if filename in duplicate_list:
        for entry in duplicate_list:
            if filename == entry:
                index = duplicate_list.index( entry )
                if type == "href": duplicate_list_counter[ index ] += 1

                # may break, idk
                if ( type == "src" ) and ( duplicate_list_counter[ index ] == 0 ) :
                    return filename
                else:
                    # makes unknown (x).png
                    return filename.split('.')[0] + " (" + str(duplicate_list_counter[ index ]) + ")." + filename.split('.')[1]
    return None

# 2nd slowest function, only because of os.path.isfile
# plus you need to delete all files in the folder before running the script if you use this anyway
# it at least searches by extension, so thats better
def SearchForDuplicateFileName( folder, filename, type, dup_url ):
    
    # only run this monstrosity if the file already exists
    if os.path.isfile( folder + filename ):

        #if dup_url == True:
        discord_folder = folder.rsplit( "/", 2 )[1]

        # skip these folders
        if discord_folder in discord_folders:
            return filename

        # to avoid counting 1500 unknown.png files
        commonFilename = CheckForCommonFileName( filename, type )

        if commonFilename != None:
            return commonFilename
        else:
            del commonFilename

        # src only, since the file may of been given a number in href right before it
        if type == "src":
            # can this be sped up any further? it is a mess
            filename_split = filename.split(".")
            last_file_number = 0

            for file in os.listdir( folder ):
                if file.startswith( filename_split[0] ):
                    if file.endswith( ")." + filename_split[1] ):

                        # split it to only get the number from it
                        file_number = file.split("(")[1]
                        file_number = file_number.split(")")[0]

                        # check to prevent a lower number being used instead of a higher number file
                        if int(file_number) > last_file_number:
                            last_file_number = int(file_number)

                        # store that name since it fits, and try the next name
                        # since the next one may be the same, but have a higher count number
                        last_file_numbered = file
                        continue
                    elif file == filename:
                        last_file = file
                        continue

                # the file either isn't found yet or all versions of it with similar names were passed
                else:
                    # now try returning the last saved numbered filename
                    try: return last_file_numbered
                    except:
                        # maybe the numbered one wasn't defined/doesn't exist, so try returning the file without a number
                        try: return last_file
                        except: continue # neither were defined

            # there are no more files in the folder, try returning any of the stored filenames
            # now try returning the last saved numbered filename
            try: return last_file_numbered
            except:
                # just return the filename as-is since no numbered one exists
                return filename 

        # try seeing if an auto renamed version of that file already exists by making a while loop that
        # adds a number in parentheses to filename, checks if that exists, if it does, keep going
        # otherwise, use that name
        count = 0
        while True:
            count += 1
            filename_counter = filename.split('.')[0] + " (" + str( count ) + ")." + filename.split('.')[1]

            if not os.path.isfile( folder + filename_counter ):
                return filename_counter
    else:
        return filename
    
# this is insanely slow
def DownloadFile( url, folder, filename, logfile ):
    # check if the file exists already, this module can be really slow

    folder_dest = folder.split( folder_root + "/" )[1]

    if not os.path.isfile( folder + filename ):
        try:
            # need to request to download it
            r = http.request( 'GET', url, preload_content=False )

            if r.status == 200:
                #PrintBreak( "Downloading:    " + folder_dest + filename, 16 )
                print( "Downloading:    " + folder_dest + filename )
                logfile.write( "Downloading:    " + folder_dest + filename + "\n" )
                with open( folder + filename, 'wb') as f:
                    # takes up 43% of time, ugh
                    shutil.copyfileobj( r, f )
                    
                # try to get the date modified of the file
                try:
                    #file_date = r.headers._store[ "last-modified" ][1]
                    file_date = r.headers._container[ "last-modified" ][1]

                    # now replace it in the file
                    # this slows the script down, oof
                    ReplaceDateModified( file_date, folder + filename )
                except:
                    # it does not have a last modified date available then
                    return True

        except urllib3.exceptions.MaxRetryError:
            WriteErrorMessage( "Max Retry Error: Failed to connect", url, logfile )
            return False

        except Exception as error:
            WriteErrorMessage( error, url, logfile )
            return str( error ) #False
    return True

def WriteErrorMessage( error, url, logfile ):
    error_message = ( "\n-------------------------------------------------------------------------------------------------------------\n" +
                    "Download Failed:\n" +
                    "URL: " + url + "\n" + 
                    str( error ) +
                    "\n-------------------------------------------------------------------------------------------------------------\n" )

    print( error_message )
    logfile.write( error_message )

def ReplaceDateModified( input_date, file_to_update ):

    date_modified_utime = time.mktime( ConvertDateIntoDateTime( input_date ).timetuple() )
    os.utime( file_to_update, ( date_modified_utime, date_modified_utime ) )

def ConvertDateIntoDateTime( input_date ):

    date_split = input_date.split( " " )
    time_split = date_split[4].split( ":" )

    # subtract 4 hours to it to convert it from GMT to EST
    time_split[0] = int( time_split[0] ) - 4
    
    # ew
    day = int( date_split[1] )
    year = int( date_split[3] )
    hour = int( time_split[0] )
    min = int( time_split[1] )
    sec = int( time_split[2] )
    month = int( datetime.datetime.strptime( date_split[2], '%b' ).month ) # convert from "Feb" to "2"
    
    # now throw it into datetime
    return datetime.datetime( year, month, day, hour = hour, minute = min, second = sec )

def ReplaceFileDirectory( line, url, filepath ):
    # remove the url from the line
    line_split = line.split( url, 1 )

    # now add the file path where the url was
    # need to do something about that github user image
    line_split[1] = filepath + line_split[1]

    # now join the new line together and return it
    return ''.join(line_split)
    
# get the total number of lines
total_num_lines = GetNumberOfLines( input_html )
current_line = 0

#HTMLFileIn = open( input_html, "r", encoding="utf8" )

#print("WARNING: DO NOT DO ANYTHING. This mass file re-write will slow down the system to a crawl just due to the amount of shit it has to do")
print("Starting rewrite of HTML file with offline paths and downloading the file as well.")

log_file_name = input_html.strip( "html" ) + "log"

input_html_file = input_html.rsplit( "\\", 1 )[1]

# set to file
with open( input_html, 'r', encoding="utf8" ) as HTMLFileIn:
    with open( output_html, 'w', encoding="utf8" ) as HTMLFileOut:
        with open( log_file_name, 'w', encoding="utf8" ) as log_file:

            for line in HTMLFileIn:

                current_line += 1

                # find the percentage
                percent = ( current_line / total_num_lines ) * 100
                percent = round( percent, 3 )

                # update the current line and the percentage in the title (windows only atm)
                ctypes.windll.kernel32.SetConsoleTitleW("Demez Awful HTML File Archiver - File: '" + input_html_file + "' - Line: " + str(current_line) + " / " + str(total_num_lines) + " - " + str(percent) + "%" )

                # only to remove all the extra lines in the file lmao
                if line == "\n":
                    continue

                containerFound = FindURLContainer( line )

                if containerFound != False:
                    url = GetURL( line, containerFound )
                    # check if we have already gotten that url before
                    dupURL = CheckForDuplicateURL( url )

                    # check if it's a discord link and update the folder path
                    folder = GetFolderPath( url )
                    filename = GetFileName( url, containerFound, folder, dupURL )
                    
                    # there is no file in the url
                    if filename != None:
                        
                        if dupURL == False:
                            download_result = DownloadFile( url, folder, filename, log_file )
                        
                            if download_result == True: # download succeeded
                                line = ReplaceFileDirectory( line, url, folder + filename )
                        
                        else:
                            line = ReplaceFileDirectory( line, url, folder + filename )

                HTMLFileOut.write( line )
        
#HTMLFileOut.close()
    
#input( "\nFinished. Press any key to exit . . ." )

sys.exit()