"""
MPI where each process takes a portion of corpus (1 text) and searches for pattern throughout its chunk.

Using the Parallel RK paper to divide up text.

Input:
--preprocessed corpus (1 text) that's been divided into K (= #processes) parts using MRhash_word.py
--pattern - just normal text

Output: prints to screen the matches found

Future:
--make processMatches smarter so that it can append exisiting full chunks of texts rather than one word at a time

"""


import sys
import string
import pandas as pd
from mpi4py import MPI
from MRhash import letsHash
from itertools import izip, groupby
from operator import itemgetter


########
def processData(hashedData, pat, m, rank, comm):

  """ Each process hashes the pattern and searches through part of corpus for matches of length m words"""


  # Hash words in pattern
  pHashed = []
  pProcessed = []
  matches = []

  for word in (pat.split()):
    new = word.translate(string.maketrans("",""), string.punctuation).upper()
    pProcessed.append(new)
    pHashed.append(letsHash(new, q=1009, d=26))


  # for each m-tuple in corpus
  for k,txtMtuple in enumerate(izip(*[iter(hashedData[i:]) for i in xrange(m)])):

    # for m-tuples in pattern -- might just use izip here
    for i in range(len(pHashed)-m+1): # first word in seqs

      seq = pHashed[i:i+m]

      broken = m # not broken
      for j,hashedWord in enumerate(seq):

        if hashedWord != txtMtuple[j]:
          broken = j
          break

      if broken == m: # was not redefined
          matches.append((k,' '.join(pProcessed[i:i+m])))

  if len(matches) > 0:
    processMatches(matches,m) # print out matches

########



########
def processMatches(matches,m):

  # data frame with tuple number and associated text
  df = pd.DataFrame({'tupleNum': [x[0] for x in matches],'txt': [x[1] for x in matches]})
  #print 'tup', df.tupleNum.values

  # for text with consecutive tuples, I don't want to print out each of these tuples; I want to merge them so I'm not repeating the words in the middle. Try printing out in processData after a match has been found to see the difference.
  for key,group in groupby(enumerate(df.tupleNum), lambda (index, item): index-item):

    # turn group into list of consecutive tuples
    group = map(itemgetter(1), group)

    matchedTxt = list(df[df.tupleNum==group[0]].txt.values)

    # append new words from consecutive tuples
    for val in group[1:]:

      # split the chunk of text into words
      words = df[df.tupleNum==val].txt.values[0].split()
      matchedTxt.append(words[-1])

    print
    print 'Match found of length ', m, '+', len(group)-1,' words'
    print ' '.join(matchedTxt)
    print

########





if __name__ == '__main__':
  comm = MPI.COMM_WORLD
  size = comm.Get_size()
  rank = comm.Get_rank()

  m = 20 # pattern size (unit: words)

  hashedtxt, pattxt = sys.argv[1:]

  # this is the pattern in whih we're searching for plagiarism
  with open(pattxt,"r") as patfile:
    pat=patfile.read().replace('\n',' ') ### Clean up punc, etc?


  # this is the file with preprocessed hashed values of corpus text
  # try scattering
  with open(hashedtxt, "r" ) as htxt:
    txt = htxt.readlines()
  mytxt = txt[rank]

  # convert from string to list of tuples of form (lineNum, [#...#])
  processNum, sep, data = mytxt.partition('[')

  hashedLine = [int(x) for x in data[:-2].split(", ")] # don't include ] \n in data

  start_time = MPI.Wtime()
  processData(hashedLine, pat, m, rank, comm)
  end_time = MPI.Wtime()

  if rank == 0:
    print "Time: %f secs" % (end_time - start_time)
    print


####
