#!/usr/bin/env python
""" 
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

2013/05/08 - Bharadwaj Machiraju (@tunnelshade) - Initial merge script creation
"""
import os

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
    f = open(os.path.join(output_path,'combined_'+case+'.txt'),'w')
    merged_list = []

    # The svndigger list is added at the beginning
    for line in open(os.path.join(svndigger_path,'all.txt'),'r').readlines():
        f.write(line)
        merged_list.append(line[:-2])
    # Non repeated entries from raft dicts are added
    for file_path in case_dict[case]:
        for line in open(os.path.join(raft_path,file_path),'r').readlines():
            if line[:-2] not in merged_list:
                f.write(line)

    f.close()
