import os
import stat
import shutil
import string
import subprocess
import sys
import argparse
import time
import traceback
import glob
from sys import argv, exit, stdout
from typing import List

class Globals:
    SEVEN_ZIP_EXECUTABLE = None

def findWorkingExecutablePath(executable_paths, flags):
	#type: (List[str], List[str]) -> str
	"""
	Try to execute each path in executable_paths to see which one can be called and returns exit code 0
	The 'flags' argument is any extra flags required to make the executable return 0 exit code
	:param executable_paths: a list [] of possible executable paths (eg. "./7za", "7z")
	:param flags: a list [] of any extra flags like "-h" required to make the executable have a 0 exit code
	:return: the path of the valid executable, or None if no valid executables found
	"""
	with open(os.devnull, 'w') as os_devnull:
		for path in executable_paths:
			try:
				if subprocess.call([path] + flags, stdout=os_devnull, stderr=os_devnull) == 0:
					return path
			except:
				pass

	return None

def isWindows():
    return sys.platform == "win32"

def call(args, **kwargs):
    print(f"running: {args} kwargs: {kwargs}")
    retcode = subprocess.call(args, shell=isWindows(), **kwargs)  # use shell on windows
    if retcode != 0:
        # don't print args here to avoid leaking secrets
        raise Exception(f"ERROR: The last call() failed with retcode {retcode}")

def tryRemoveTree(path):
    attempts = 5
    for i in range(attempts):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return

        except FileNotFoundError:
            return
        except Exception:
            print(f'Warning: Failed to remove "{path}" attempt {i}/{attempts}')
            traceback.print_exc()

        time.sleep(1)


def sevenZipMakeArchive(input_path, output_filename):
    tryRemoveTree(output_filename)
    call([Globals.SEVEN_ZIP_EXECUTABLE, "a", output_filename, input_path])


def sevenZipExtract(input_path, outputDir=None):
    args = [Globals.SEVEN_ZIP_EXECUTABLE, "x", input_path, '-y']
    if outputDir:
        args.append('-o' + outputDir)

    call(args)


def download(url):
    print(f"Starting download of URL: {url}")
    call(['curl', '-OJLf', url])


class ChapterInfo:
    def __init__(self, name, episodeNumber, uiArchiveURL: str, baseName=None, dllFolderName=None):
        self.name = name
        self.episodeNumber = episodeNumber
        self.dataFolderName = f'HigurashiEp{episodeNumber:02}_Data'
        if uiArchiveURL:
            self.uiArchiveURL = uiArchiveURL
            self.uiArchiveName = uiArchiveURL.split('/')[-1]
        else:
            self.uiArchiveURL = None
            self.uiArchiveName = None

        self.baseName = baseName if baseName is not None else self.name
        self.dllFolderName = dllFolderName if dllFolderName is not None else self.name

def compileScripts(chapter: ChapterInfo):
    """
    Compiles scripts for the given chapter.

    Expects:
        - HigurashiScriptCompiler.exe placed adjacent to this script (built from the current chapter's engine code)
        - Associated DLLs (Antlr3.Runtime.dll, System.Core.dll (might not be required, but include to be safe))
    """
    scriptCompilerPath = os.path.abspath(f'bin/ScriptCompiler/HigurashiScriptCompiler.exe')

    if not os.path.exists(scriptCompilerPath):
        raise Exception(f"Missing {scriptCompilerPath} - if running script manually, you must put it there yourself!")

    baseFolderName = f'{chapter.baseName}_base'

    print(f"\n\n>> Compiling [{chapter.name}] scripts...")

    # - Define the folder where the update scripts are stored, and where they will be compiled to
    compileSrcFolder = os.path.abspath(f'{baseFolderName}/{chapter.dataFolderName}/StreamingAssets/Update')
    compileDestFolder = os.path.abspath(f'{baseFolderName}/{chapter.dataFolderName}/StreamingAssets/CompiledUpdateScripts')
    os.makedirs(compileDestFolder, exist_ok=True)

    # - Copy the Update folder containing the scripts to be compiled to the base folder, so the game can find it
    shutil.copytree(f'Update', compileSrcFolder, dirs_exist_ok=True)

    # - Remove status file if it exists
    statusFilePath = f'higu_script_compile_status.txt'
    if os.path.exists(statusFilePath):
        os.remove(statusFilePath)

    # Make sure script compiler is executable
    st = os.stat(scriptCompilerPath)
    os.chmod(scriptCompilerPath, st.st_mode | stat.S_IEXEC)

    # - Run the game with 'quitaftercompile' as argument
    # Note: generated artifacts currently exclude the 'bin' folder
    call([scriptCompilerPath, compileSrcFolder, compileDestFolder])

    # - Check compile status file
    if not os.path.exists(statusFilePath):
        raise Exception("Script Compile Failed: Script compilation status file not found")

    with open(statusFilePath, "r") as f:
        status = f.read().strip()
        print(f'Game Script Compile Result: {status}')
        if not status.startswith("Compile OK"):
            raise Exception(f"Script Compile Failed: Script compilation status indicated status {status}")

    os.remove(statusFilePath)

    # - Copy the CompiledUpdateScripts folder to the expected final build dir
    shutil.copytree(compileDestFolder, f'temp/{chapter.dataFolderName}/StreamingAssets/CompiledUpdateScripts', dirs_exist_ok=True)

    # Clean up
    tryRemoveTree(baseFolderName)

def prepareFiles(dllFolderName, dataFolderName):
    os.makedirs(f'temp/{dataFolderName}/StreamingAssets', exist_ok=True)
    os.makedirs(f'temp/{dataFolderName}/Managed', exist_ok=True)
    os.makedirs(f'temp/{dataFolderName}/Plugins', exist_ok=True)


def buildPatch(dataFolderName):
	# Note: The modded DLL must be generated in a previous build step
    shutil.copy('bin/Release/Assembly-CSharp.dll', f'temp/{dataFolderName}/Managed/Assembly-CSharp.dll')

    print("Downloading video plugin...")
    if os.path.exists('AVProVideo.dll'):
        os.remove('AVProVideo.dll')
    download('https://github.com/07th-mod/patch-releases/releases/download/developer-v1.0/AVProVideo.dll')
    tempVideoDLLPath = f'temp/{dataFolderName}/Plugins/AVProVideo.dll'
    print(f"Moving video plugin to {tempVideoDLLPath}...")
    shutil.move('AVProVideo.dll', tempVideoDLLPath)

    try:
        shutil.copy('bin/Release/Assembly-CSharp.version.txt', f'temp/{dataFolderName}/Managed/Assembly-CSharp.version.txt')
    except:
        print("Warning: Failed to copy DLL version information file 'Assembly-CSharp.version.txt'")

    rootJSONFiles = glob.glob('*.json')

    # Except for certain ignored files, copy everything in the current directory to the 'temp/Higurashi_Ep0X/StreamingAssets' folder
    source_folder = '.'

    def ignoreFilter(folderPath, folderContents):
        # Case is ignored for these paths!
        ignoreList = [
            '.git',
            '.github',
            '.gitignore',
            '.gitconfig',
            'readme.md',
            'deploy_higurashi.py',
            'dev',
            'temp',
            'output',
            'src',
            'bin',
            'dll',
            dataFolderName
        ] #type: list[str]

        ignoreList = [p.lower() for p in ignoreList]

        ignored_children = []

        for child in folderContents:
            fullPath = os.path.join(folderPath, child)
            realPath = os.path.realpath(fullPath)
            relPath = os.path.relpath(realPath, start=source_folder)
            nPath = os.path.normcase(os.path.normpath(relPath))
            if nPath.lower() in ignoreList or nPath in rootJSONFiles:
                ignored_children.append(child)

        for child in ignored_children:
            print(f' - Ignored [{child}]')

        return ignored_children

    print("Copying files to StreamingAssets folder, but ignoring the following paths:")
    shutil.copytree(source_folder, f'temp/{dataFolderName}/StreamingAssets', ignore=ignoreFilter, dirs_exist_ok=True)

    # Copy all top level .json files
    print("Copying top level *.json files...")
    for jsonFilePath in rootJSONFiles:
        print(f"Copying {jsonFilePath} to data folder...")
        shutil.copy(jsonFilePath, f'temp/{dataFolderName}')


def makeArchive(chapterName, dataFolderName):
    # Turns the first letter of the chapter name into uppercase for consistency when uploading a release
    upperChapter = string.capwords(chapterName, '-')

    # Console arcs archive name is different from chapter name
    if chapterName == 'console':
        upperChapter = 'ConsoleArcs'

    os.makedirs(f'output', exist_ok=True)
    shutil.make_archive(base_name=f'output/{upperChapter}.Voice.and.Graphics.Patch',
                        format='zip',
                        root_dir='temp',
                        base_dir=dataFolderName
                        )


def main():
    if sys.version_info < (3, 8):
        raise Exception(f"""ERROR: This script requires Python >= 3.8 to run (you have {sys.version_info.major}.{sys.version_info.minor})!

This script uses 3.8's 'dirs_exist_ok=True' argument for shutil.copy.""")

    argparser = argparse.ArgumentParser(usage='deploy_higurashi.py (onikakushi | watanagashi | tatarigoroshi | himatsubushi | meakashi | tsumihoroboshi | minagoroshi | matsuribayashi | [higurashi-rei/rei] | [hou-pluse/hou] | [higurashi-console-arcs/console])',
                                        description='This script creates the "script" archive used in the Higurashi mod. It expects to be run from the root of one of the Higurashi mod repositories.')

    argparser.add_argument("chapter", help="The name of the chapter to be deployed.")
    argparser.add_argument(
        "--nocompile",
        dest="noCompile",
        action='store_true',
        help='Skips the script compilation step (archive will not have a CompiledUpdateScripts folder)',
    )

    args = argparser.parse_args()

    Globals.SEVEN_ZIP_EXECUTABLE = findWorkingExecutablePath(["7za", "7z"], ['-h'])

    # Get Git Tag Environment Variables
    GIT_REF = os.environ.get("GITHUB_REF",  "unknown/unknown/X.Y.Z")    # Github Tag / Version info
    GIT_TAG = GIT_REF.split('/')[-1]
    print(f"--- Starting build for Git Ref: {GIT_REF} Git Tag: {GIT_TAG} ---")

    chapterList = [
        ChapterInfo("onikakushi",       1, "https://github.com/07th-mod/patch-releases/releases/download/onikakushi-v1.0/Onikakushi-UI_5.2.2f1_win.7z"),
        ChapterInfo("watanagashi",      2, "https://github.com/07th-mod/patch-releases/releases/download/watanagashi-v1.0/Watanagashi-UI_5.2.2f1_win.7z"),
        ChapterInfo("tatarigoroshi",    3, "https://github.com/07th-mod/patch-releases/releases/download/tatarigoroshi-v1.0/Tatarigoroshi-UI_5.4.0f1_win.7z"),
        ChapterInfo("himatsubushi",     4, "https://github.com/07th-mod/patch-releases/releases/download/himatsubushi-v1.0/Himatsubushi-UI_5.4.1f1_win.7z"),
        ChapterInfo("console",          4, "https://github.com/07th-mod/patch-releases/releases/download/himatsubushi-v1.0/Himatsubushi-UI_5.4.1f1_win.7z", baseName="himatsubushi", dllFolderName="consolearcs"), # Console uses same base archive as Himatsubushi
        ChapterInfo("meakashi",         5, "https://github.com/07th-mod/patch-releases/releases/download/meakashi-v1.0/Meakashi-UI_5.5.3p3_win.7z"),
        ChapterInfo("tsumihoroboshi",   6, "https://github.com/07th-mod/patch-releases/releases/download/tsumihoroboshi-v1.0/Tsumihoroboshi-UI_5.5.3p3_win.7z"),
        ChapterInfo("minagoroshi",      7, "https://github.com/07th-mod/patch-releases/releases/download/minagoroshi-v1.0/Minagoroshi-UI_5.6.7f1_win.7z"),
        ChapterInfo("matsuribayashi",   8, "https://github.com/07th-mod/patch-releases/releases/download/matsuribayashi-v1.0/Matsuribayashi-UI_2017.2.5_win.7z"),
        ChapterInfo("rei",              9, "https://github.com/07th-mod/patch-releases/releases/download/rei-v1.0/Rei-UI_2019.4.3_win.7z"),
        # TODO: Remove UI files from https://07th-mod.com/misc/script_building/hou_base.7z archive, and use mod UI file
        ChapterInfo("hou",             10, None), #"Hou-UI_2019.4.3_win.7z") # Skip Hou UI for now
    ]

    chapterDict = dict((chapter.name, chapter) for chapter in chapterList)

    chapter = chapterDict.get(args.chapter)

    # Add special case for chapters where the repo name doesn't match the chapter name
    if chapter is None:
        if args.chapter.lower() == 'higurashi-rei':
            print(f"Converting chapter argument '{args.chapter}' to 'rei'")
            chapter = chapterDict.get('rei')

    if chapter is None:
        if args.chapter.lower() == 'hou-plus':
            print(f"Converting chapter argument '{args.chapter}' to 'hou'")
            chapter = chapterDict.get('hou')

    if chapter is None:
        if args.chapter.lower() == 'higurashi-console-arcs':
            print(f"Converting chapter argument '{args.chapter}' to 'console'")
            chapter = chapterDict.get('console')

    if chapter is None:
        raise Exception(f"Error: Unknown Chapter '{args.chapter}' Selected\n\n{help}")

    # Compile every chapter's scripts before building archives
    if not args.noCompile:
        compileScripts(chapter)

    print(f">>> Creating folders and downloading necessary files")
    prepareFiles(chapter.dllFolderName, chapter.dataFolderName)

    print(f">>> Building the patch")
    buildPatch(chapter.dataFolderName)

    print(f">>> Creating Archive")
    makeArchive(chapter.name, chapter.dataFolderName)

    print(f">>> Cleaning up the mess")
    tryRemoveTree('temp')

    # Set a Github Actions output "release_name" for use by the release step
    capitalized_name = string.capwords(chapter.name, '-')
    GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT", "github-output-dummy.txt")
    with open(GITHUB_OUTPUT, "w") as f:
        f.write(f"release_name={capitalized_name} Voice and Graphics Patch {GIT_TAG}")

if __name__ == "__main__":
    main()
