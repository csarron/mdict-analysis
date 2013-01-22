An Analysis of MDX/MDD File Format
==================================

MDict claims "a cross-platform open dictionary platform", which are both questionable. It is not available for every platform, e.g. OS X, Linux. Its  dictionary file format is not open. 

But this has not hindered its popularity, and many dictionaries have been created for it. This is an attempt to reveal MDX/MDD file format, so that my favarite dictionaries, created by MDict users, could be used elsewhere.


MDX File Format
===============
.. image:: mdx.svg

MDD File Format
===============
.. image:: mdd.svg

Example Program
===============
readmdx.py is an example implementation in Python. This program can read/extract mdx/mdd files.
It can be used as a command line tool::

    $ python readmdict.py oald8.mdx

or as a moudle::

    In [1]: from readmdict import readmdx, readmdd

    In [2]: glos = readmdx('/Users/wang/Downloads/oald8.mdx')
    
    In [3]: glos['dict'][0]
    Out[3]:
    ('A',
     '<span style=\'display:block;color:black;\'>.........')

    In [3]: data = readmdd('/Users/wang/Downloads/oald8.mdd')

    In [4]: data['data'][0]
    Out[4]: 
    (u'\\pic\\accordion_concertina.jpg',
    '\xff\xd8\xff\xe0\x00\x10JFIF...........')

