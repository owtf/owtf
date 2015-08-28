#!/usr/bin/env sh
#
# Description: Installation script for dictionaries with licensing issues.

IsInstalled() {
	directory=$1
	if [ -d $directory ]; then
		return 1
	else
		return 0
	fi
}

DecompressTBZ2() {
	bunzip2 *
	tar xvf *
	rm -f *.tar 2> /dev/null
}

DecompressTGZ() {
	tar xvfz *
	rm -f *.tar.gz 2> /dev/null
	rm -f *.tgz 2> /dev/null
}

DecompressZIP() {
	unzip *.zip
	rm -f *.zip
}

Chmod700() {
	chmod 700 *
}

WgetInstall() {
	download_url=$1
	directory=$2
	decompress_method="tar.gz"
	if [ $3 ]; then
		decompress_method=$3
	fi

	IsInstalled "$directory"
	if [ $? -eq 0 ]; then # Not installed
		mkdir -p $directory
		(
			cd $directory
			echo "$directory not found, downloading it.."
			wget -A "MSIE 6.0" $download_url
			if [ "$decompress_method" = "tar.gz" ]; then
				DecompressTGZ
			elif [ "$decompress_method" = "tar.bz2" ]; then
				DecompressTBZ2
			elif [ "$decompress_method" = "zip" ]; then
				DecompressZIP
			elif [ "$decompress_method" = "chmod700" ]; then
				Chmod700
			fi
		)
	else
		echo "WARNING : $directory ($download_url) is already installed, skipping"
	fi
}

# This script needs to be run to download dictionaries with potentially restrictive licensing (cannot be redistributed)
DICTS_DIRECTORY="$(dirname $0)"
INSTALL_DIR="$DICTS_DIRECTORY/restricted"
mkdir -p $INSTALL_DIR
(
	cd $DICTS_DIRECTORY
	DICTS_DIRECTORY=$(pwd) # Ensuring full path to avoid symbolic link issues below
    IsInstalled "$INSTALL_DIR/raft"
	if [ $? -eq 0 ]; then # Not installed
        # Copying raft dicts from shipped files in OWTF
        echo "[*] Linking RAFT dictionaries from Fuzz DB"
        mkdir -p $INSTALL_DIR/raft
        for file in $(ls $DICTS_DIRECTORY/fuzzdb/fuzzdb-1.09/Discovery/PredictableRes/ | grep raft); do
            #cp $DICTS_DIRECTORY/fuzzdb/fuzzdb-1.09/Discovery/PredictableRes/$file $DICTS_DIRECTORY/restricted/raft/
            ln -s $DICTS_DIRECTORY/fuzzdb/fuzzdb-1.09/Discovery/PredictableRes/$file $DICTS_DIRECTORY/restricted/raft/$file
        done
        echo "[*] Done"
    else
        echo "WARNING: RAFT dictionaries are already installed, skipping"
    fi

    IsInstalled "$INSTALL_DIR/cms"
    if [ $? -eq 0 ]; then # Not installed
        # Fetching cms-explorer dicts, update them and copy the updated dicts
        WgetInstall "http://cms-explorer.googlecode.com/files/cms-explorer-1.0.tar.bz2" "cms-explorer" "tar.bz2"
        mkdir -p $INSTALL_DIR/cms
        "$DICTS_DIRECTORY/update_convert_cms_explorer_dicts.sh"
        # Instead of deleting, the cms-explorer is copied to tools by the wrapper install script
        #echo "[*] Cleaning Up"
        #rm -rf cms-explorer
        echo "[*] Done"
    else
        echo "WARNING: CMS dictionaries are already installed, skipping"
    fi
    
	cd $INSTALL_DIR

    IsInstalled "svndigger" # Not using $INSTALL_DIR because we did a cd into $INSTALL_DIR
    if [ $? -eq 0 ]; then # Not installed
        #Fetching svndigger dicts
        echo "\n[*] Fetching SVNDigger dictionaries"
        WgetInstall "http://www.mavitunasecurity.com/s/research/SVNDigger.zip" "svndigger" "zip"
        echo "[*] Done"
    else
        echo "WARNING: SVNDIGGER dictionaries are already installed, skipping"
    fi

    IsInstalled "dirbuster"
    if [ $? -eq 0 ]; then # Not installed    
        # Copying dirbuster dicts
        echo "\n[*] Copying Dirbuster dictionaries"
        mkdir -p dirbuster
        cp -r /usr/share/dirbuster/wordlists/. dirbuster/.
        echo "[*] Done"
    else
        echo "WARNING: Dirbuster dictionaries are already installed, skipping"
    fi

	# Returning to parent directory
	cd ..

    IsInstalled "$INSTALL_DIR/combined"
    if [ $? -eq 0 ]; then # Not installed
        # Merging svndigger and raft dicts to form hybrid dicts based on case
        echo "\n[*] Please wait while dictionaries are merged, this may take a few minutes.."
        mkdir -p $INSTALL_DIR/combined
        "./dict_merger_svndigger_raft.py"
        echo "[*] Done"
    else
        echo "WARNING: Combined dictionaries are already installed, skipping"
    fi
)
