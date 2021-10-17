import os, shutil, requests
from sys import argv, exit, stdout
from colorama import Fore, Style


def download(url):
    print(f"Starting download of URL: {url}")
    filename = url.rsplit('/', 1)[1]
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                stdout.flush()
    stdout.write('\n')


def prepareFiles(lowerChapterName, dataFolderName):
    try:
        os.makedirs(f'temp/{dataFolderName}/StreamingAssets')
        os.mkdir(f'temp/{dataFolderName}/Managed')
        os.mkdir(f'temp/{dataFolderName}/Plugins')
    except:
        pass

    download(f'https://07th-mod.com/higurashi_dlls/{lowerChapterName}/Assembly-CSharp.dll')
    print("Downloaded Unity dll")
    download('https://07th-mod.com/misc/AVProVideo.dll')
    print("Downloaded video plugin")
    download(f'https://github.com/07th-mod/{lowerChapterName}/archive/master.zip')
    print(f"Downloaded {lowerChapterName} repository")

    shutil.unpack_archive('master.zip')
    
    os.remove('master.zip')


def buildPatch(lowerChapterName, dataFolderName):
    # List of all folders used in releases. Dev and misc files are ignored
    folders = [
        "CG",
        "CGAlt",
        "SE",
        "voice",
        "spectrum",
        "BGM",
        "Update"
    ]

    # Iterates the list of folders above looking for valid folders in the master repo
    for folder in folders:
        try:
            shutil.move(f'{lowerChapterName}-master/{folder}', f'temp/{dataFolderName}/StreamingAssets')
        except:
            print(f'{folder} not found (this is ok)')
    
    try:
        shutil.move(f'{lowerChapterName}-master/tips.json', f'temp/{dataFolderName}')
    except:
        print(f'{lowerChapterName}-master/tips.json not found')
    shutil.move('Assembly-CSharp.dll', f'temp/{dataFolderName}/Managed')
    shutil.move('AVProVideo.dll', f'temp/{dataFolderName}/Plugins')


def makeArchive(chapterName):
    # Turns the first letter of the chapter name into uppercase for consistency when uploading a release
    upperChapter = chapterName.capitalize()
    shutil.make_archive(f'{upperChapter}.Voice.and.Graphics.Patch.vX.Y.Z', 'zip', 'temp')


def cleanUp(lowerChapterName):
    shutil.rmtree(f'{lowerChapterName}-master')
    shutil.rmtree('temp')


def main():
    help = """Usage:
            higurashi_release.py (onikakushi | watanagashi | tatarigoroshi | himatsubushi | meakashi | tsumihoroboshi | minagoroshi | matsuribayashi)
           """

    # Enables the chapter name as an argument. Example: Himatsubushi
    if len(argv) < 2:
        raise SystemExit(help)

    chapterName = argv[1]

    # Makes sure the chapter name is lowercase
    lowerChapterName = chapterName.lower()

    # List of supported chapters
    chapterList = {
        "onikakushi": "HigurashiEp01_Data",
        "watanagashi": "HigurashiEp02_Data",
        "tatarigoroshi": "HigurashiEp03_Data",
        "himatsubushi": "HigurashiEp04_Data",
        "meakashi": "HigurashiEp05_Data",
        "tsumihoroboshi": "HigurashiEp06_Data",
        "minagoroshi": "HigurashiEp07_Data",
        "matsuribayashi": "HigurashiEp08_Data"
    }

    # Takes the HigurashiEp_Data folder from the selected chapter and stores it to be used as a path
    dataFolderName = chapterList.get(lowerChapterName)

    if lowerChapterName in chapterList:
        print(f"{Fore.GREEN}Creating folders and downloading necessary files{Style.RESET_ALL}")
        prepareFiles(lowerChapterName, dataFolderName)

        print(f"{Fore.GREEN}Building the patch{Style.RESET_ALL}")
        buildPatch(lowerChapterName, dataFolderName)

        print(f"{Fore.GREEN}Creating Archive{Style.RESET_ALL}")
        makeArchive(chapterName)

        print(f"{Fore.GREEN}Cleaning up the mess{Style.RESET_ALL}")
        cleanUp(lowerChapterName)
    elif lowerChapterName == "-h" or "--help":
        exit(help)
    else:
        exit(help)


if __name__ == "__main__":
    main()
