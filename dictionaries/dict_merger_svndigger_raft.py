#!/usr/bin/env python
"""
2013/05/08 - Bharadwaj Machiraju (@tunnelshade) - Initial merge script creation
"""
import os, urllib, codecs

#Order of the files in the list is important
raft_lowercase = [
                    'raft-small-directories-lowercase.txt',
                    'raft-small-files-lowercase.txt',
                    'raft-medium-directories-lowercase.txt',
                    'raft-medium-files-lowercase.txt',
                    'raft-large-directories-lowercase.txt',
                    'raft-large-files-lowercase.txt'
                ]

raft_mixedcase = [
                    'raft-small-directories.txt',
                    'raft-small-files.txt',
                    'raft-medium-directories.txt',
                    'raft-medium-files.txt',
                    'raft-large-directories.txt',
                    'raft-large-files.txt'
                ]

case_dict = {'lowercase':raft_lowercase,'mixedcase':raft_mixedcase}
abs_path = os.path.dirname(os.path.abspath(__file__))
raft_path = os.path.join(abs_path,'restricted/raft')
svndigger_path = os.path.join(abs_path,'restricted/svndigger')
output_path = os.path.join(abs_path,'restricted/combined')

# Two files will be formed
for case in ['lowercase','mixedcase']:
    f = codecs.open(os.path.join(output_path,'combined_'+case+'.txt'),'w','UTF-8')
    merged_list = {}

    # The svndigger list is added at the beginning
    for line in codecs.open(os.path.join(svndigger_path,'all.txt'),'r','UTF-8').readlines():
        line = line.rstrip()
        f.write(line+'\n')
        merged_list[line] = 1
    # Non repeated entries from raft dicts are added
    for file_path in case_dict[case]:
        for line in codecs.open(os.path.join(raft_path,file_path),'r','ISO-8859-1').readlines():
            try:
                line = line.rstrip()
                a = merged_list[line]
            except KeyError:  # Error happens if this line is not already added
                merged_list[line] = 1
                f.write(line+'\n')

    f.close()
    # Prepare filtered version for using with dirbuster
    f = codecs.open(os.path.join(output_path,'filtered_combined_'+case+'.txt'),'w','UTF-8')
    for line in codecs.open(os.path.join(output_path,'combined_'+case+'.txt'),'r','UTF-8').readlines():
        f.write(urllib.quote_plus(line.encode('utf-8'),'./\r\n'))
    f.close()
