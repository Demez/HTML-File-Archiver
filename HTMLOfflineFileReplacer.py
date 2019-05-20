import os, sys, shutil
import re # ew
import time, datetime
import urllib3
urllib3.disable_warnings()
http = urllib3.PoolManager()

# This is script is meant to be used with an html file exported from: https://github.com/Tyrrrz/DiscordChatExporter/releases
# it may work with other html files though, never tested

# maybe re-add the download queue and store it in a txt file or something, and continue from there if it finds that txt file?

# hopefully this has enough comments to make it explainable and is clean enough, seems i did a decent job at it

# this will end up downloading the same image multiple times sometimes, only because it was uploaded multiple times, so it will have a different URL
# im thinking of adding a way to check the image if it's the same, but im worried that would be REALLY slow.

if os.name == 'nt':
    import ctypes
    # rename the window (windows only)
    ctypes.windll.kernel32.SetConsoleTitleW("Demez Awful HTML File Archiver - Setting Up")

    # change the window size
    os.system( 'mode con: cols=140 lines=100' )
    
    # hide the cursor (should i remove this?)
    class _CursorInfo( ctypes.Structure ):
        _fields_ = [ ( "size", ctypes.c_int ),
                    ( "visible", ctypes.c_byte ) ]
        
    ci = _CursorInfo()
    handle = ctypes.windll.kernel32.GetStdHandle( -11 )
    ctypes.windll.kernel32.GetConsoleCursorInfo( handle, ctypes.byref( ci ) )
    ci.visible = False
    ctypes.windll.kernel32.SetConsoleCursorInfo( handle, ctypes.byref( ci ) )
    
elif os.name == 'posix':
    # hide the cursor
    sys.stdout.write( "\033[?25l" )
    sys.stdout.flush()

def FindArgument( search, return_value ):
    if search in sys.argv:
        index = 0
        for arg in sys.argv:
            if search == sys.argv[ index ]:
                if return_value:
                    return sys.argv[ index + 1 ]
                else:
                    return True
            index += 1
    else:
        return False

def GetNumberOfLines( file ):
    total_num_lines = 0
    with open( file, 'r', encoding="utf8" ) as f:
        print( "Getting Total Number of Lines in:   " + file )
        for line in f:
            total_num_lines += 1
    print( "Finished:   " + str( total_num_lines ) + " Lines." )
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
                            if ( os.path.isfile( file_path ) ) and not ( file_path.endswith( reserved ) ):
                                os.unlink( file_path )
                        #elif os.path.isdir(file_path): shutil.rmtree(file_path)
                    except Exception as e:
                        print(e)

# ew
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

def GetURL( line, type ):    
    line_split = line.split( type + '=')

    if type == "src":
        line_split = line_split[1].split('/>')
    elif type == "href":
        line_split = line_split[1].split('>')
    else:
        # i currently have never got this YET, watch, ill get this somehow, like on a non-discord archived html file (what?)
        print("what the fuck how did you get this")
        input()
    
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
# checks for specific discord files
# and returns the folder root if it's not found
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

# now THIS, is an abomination
# this can end up just mashing a complex url into one name
# ex: watchvYnJ1fyMPbzMfeatureyoutu.be
# i don't know what i can add here to prevent against that though
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

# just a faster check so we don't potentially end up searching through 10,000 images that are all the same name
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
# i could try using a dictionary for a download queue again, and store it in a txt file, idk
# though then i would need to create in a reader for that file, ugh
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

        # below i don't really understand much of what i did 
        # i did try to counter that with more comments, but it can only help so much
        # at least it works lol

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

        # try seeing if an auto renamed version of that file already exists through a while loop that
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
    
# the http request is THE slowest, along with reading it
# 2nd slowest is copyfileobj
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
                    "Download Failed\n" +
                    "URL: " + url + "\n" + 
                    str( error ) +
                    "\n-------------------------------------------------------------------------------------------------------------\n" )

    print( error_message )
    logfile.write( error_message + "\n" )

def ReplaceDateModified( input_date, file_to_update ):

    # 
    date_modified_utime = time.mktime( ConvertDateIntoDateTime( input_date ).timetuple() )

    # change the date modified of the file to the "new" one
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
    
    # now throw it into datetime and return it
    return datetime.datetime( year, month, day, hour = hour, minute = min, second = sec )

def ReplaceFileDirectory( line, url, filepath ):
    # remove the url from the line
    line_split = line.split( url, 1 )

    # now add the file path where the url was
    # need to do something about that github user image
    line_split[1] = filepath + line_split[1]

    # now join the new line together and return it
    return ''.join(line_split)
    
# ------------------------------------------------------------------------------------------
# Starting Point

input_html = FindArgument( "--input_file", True )
output_html = FindArgument( "--output_file", True )
folder_root = FindArgument( "--output_folder", True )

if input_html == None:
    print(  "You need to add the input html file:\n"
            "--input_file \"FILE\"" )
    quit()

if output_html == None:
    # change this a bit, since what if we used a file that's not in the current directory?
    output_html = "Offline - " + input_html

if folder_root == None:
    folder_root = input_html.split( ".html" )[0] + " files"

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

found_urls = []

DeletePath( folder_root + "/" )
DeletePath( folder_root + "/attachments/" )
CreatePath( folder_root + "/" )

# get the total number of lines
total_num_lines = GetNumberOfLines( input_html )
current_line = 0

#HTMLFileIn = open( input_html, "r", encoding="utf8" )

#print("WARNING: DO NOT DO ANYTHING. This mass file re-write will slow down the system to a crawl just due to the amount of shit it has to do")
print("Starting rewrite of HTML file with offline paths and downloading the file as well.")

log_file_name = input_html.rsplit( ".html", 1 )[0] + ".log"

try:
    # not in the current directory
    input_html_file = input_html.rsplit( "\\", 1 )[1]
except:
    # in the current directory
    input_html_file = input_html

# set to file
with open( input_html, 'r', encoding="utf8" ) as HTMLFileIn:
    with open( output_html, 'w', encoding="utf8" ) as HTMLFileOut:
        with open( log_file_name, 'w', encoding="utf8" ) as log_file:

            for line in HTMLFileIn:

                current_line += 1

                # find the percentage
                percent = ( current_line / total_num_lines ) * 100
                percent = round( percent, 3 )

                # update the current line and the percentage in the title (add a linux option and move this to a seperate function next time you use this)
                if os.name == "nt":
                    ctypes.windll.kernel32.SetConsoleTitleW("Demez Awful HTML File Archiver - File: '" + input_html_file + "' - Line: " + str(current_line) + " / " + str(total_num_lines) + " - " + str(percent) + "%" )

                # only to remove all the extra lines in the file lmao
                if line == "\n":
                    continue

                # search for src= or href=, since those can only contain a url we can download
                containerFound = FindURLContainer( line )

                if containerFound != False:
                    url = GetURL( line, containerFound )
                    # check if we have already gotten that url before
                    dupURL = CheckForDuplicateURL( url )

                    # check if it's a discord link and update the folder path
                    folder = GetFolderPath( url )
                    filename = GetFileName( url, containerFound, folder, dupURL )
                    
                    # there is a file at the end of the url
                    if filename != None:
                        
                        if dupURL == False:
                            # we haven't seen this url before, so download it
                            download_result = DownloadFile( url, folder, filename, log_file )
                            
                            # download succeeded
                            if download_result == True: 
                                # replace it with the changed filename
                                line = ReplaceFileDirectory( line, url, folder + filename )
                        
                        else:
                            # we have seen this url before, so don't change the filename and replace it
                            line = ReplaceFileDirectory( line, url, folder + filename )

                HTMLFileOut.write( line )
        
#HTMLFileOut.close()
    
#input( "\nFinished. Press any key to exit . . ." )

sys.exit()