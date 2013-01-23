An Analysis of MDX/MDD File Format
==================================

    MDict is a multi-platform open dictionary
    
which are both questionable. It is not available for every platform, e.g. OS X, Linux. Its  dictionary file format is not open. But this has not hindered its popularity, and many dictionaries have been created for it.

This is an attempt to reveal MDX/MDD file format, so that my favarite dictionaries, created by MDict users, could be used elsewhere.


MDict Files
===========
MDict stores the dictionary definitions, i.e. (key word, explanation) in MDX file and the dictionary reference data, e.g. images, pronunciations, stylesheets in MDD file. Although holding different contents, these two file formats share the same structure.

MDX File Format
===============
.. image:: MDX.svg


MDD File Format
===============
.. image:: MDD.svg

Example Program
===============
readmdict.py is an example implementation in Python. This program can read/extract mdx/mdd files.

It can be used as a command line tool. Suppose one has oald8.mdx and oald8.mdd::

    $ python readmdict.py -x oald8.mdx

This will creates *oald8.txt* dictionary file and creates a folder *data* for images, pronunciation audio files.

Or as a module::

    In [1]: from readmdict import readmdx, readmdd

Read MDX file and print the first entry::

    In [2]: glos = readmdx('oald8.mdx')
    
    In [3]: glos['dict'][0]
    Out[3]:
    ('A',
     '<span style=\'display:block;color:black;\'>.........')
``glos`` is a python dict having all info from MDX file. ``glos['dict']`` item is a list of 2-item tuples.
Of each tuple, the first element is the entry text and the second is the explanation.

Read MDD file and print the first entry::

    In [4]: data = readmdd('oald8.mdd')

    In [5]: data['data'][0]
    Out[5]: 
    (u'\\pic\\accordion_concertina.jpg',
    '\xff\xd8\xff\xe0\x00\x10JFIF...........')

``data`` is a python dict having all info from a MDD file. ``glos['data']`` item is a list of 2-item tuples. 
Of each tuple, the first element is the file name and the second element is the corresponding file content.
