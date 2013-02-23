#!/usr/bin/env python
# -*- coding: utf-8 -*-
## readmdict.py
## Octopus MDict Dictionary File (.mdx) and Resource File (.mdd) Analyser
##
## Copyright (C) 2012, 2013 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, version 3 of the License.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.

from struct import pack, unpack

# zlib compression is used for engine version >=2.0
import zlib
# LZO compression is used for engine version < 2.0
try:
    import lzo
    HAVE_LZO = True
except:
    HAVE_LZO = False
    print "LZO compression support is not available"

from xml.etree.ElementTree import XMLParser

def _split_key_block(key_block, number_format, number_width):
    key_list = []
    key_start_index = 0
    while key_start_index < len(key_block):
        # the corresponding record's offset in record block
        key_id = unpack(number_format, key_block[key_start_index:key_start_index+number_width])[0]
        # key text ends with '\x00'
        key_end_index = key_start_index + number_width
        for a in key_block[key_start_index+number_width:]:
            key_end_index += 1
            if a == '\x00':
                break
        key_text = key_block[key_start_index+number_width:key_end_index-1]
        key_start_index = key_end_index
        key_list += [(key_id, key_text)]
    return key_list

def _decode_key_block_info_v1(key_block_info):
    key_block_info_size = len(key_block_info)
    # decode
    key_block_info_list = []
    i = 0
    while i < key_block_info_size:
        # 4 bytes unknow
        unpack('>I', key_block_info[i:i+4])[0]
        i += 4
        # 1 byte
        text_head_size = unpack('>B', key_block_info[i:i+1])[0]
        i += 1
        # text head
        i += text_head_size
        # 1 byte
        text_tail_size = unpack('>B', key_block_info[i:i+1])[0]
        i += 1
        # text tail
        i += text_tail_size
        # 4 bytes of key block compressed size
        key_block_compressed_size = unpack('>I', key_block_info[i:i+4])[0]
        i += 4
        # 4 bytes of key block decompressed size
        key_block_decompressed_size = unpack('>I', key_block_info[i:i+4])[0]
        i += 4
        key_block_info_list += [(key_block_compressed_size, key_block_decompressed_size)]
    return key_block_info_list

def _decode_key_block_info_v2(key_block_info_compressed):
    # \x02\x00\x00\x00
    assert(key_block_info_compressed[:4] == '\x02\x00\x00\x00')
    # 4 bytes as a checksum
    assert(key_block_info_compressed[4:8] == key_block_info_compressed[-4:])
    # decompress
    key_block_info = zlib.decompress(key_block_info_compressed[8:])
    key_block_info_size = len(key_block_info)
    # decode
    key_block_info_list = []
    i = 0
    while i < key_block_info_size:
        # 8 bytes unknow
        unpack('>Q', key_block_info[i:i+8])[0]
        i += 8
        # 2 bytes
        text_head_size = unpack('>H', key_block_info[i:i+2])[0]
        i += 2
        # text head
        i += text_head_size + 1
        # 2 bytes
        text_tail_size = unpack('>H', key_block_info[i:i+2])[0]
        i += 2
        # text tail
        i += text_tail_size + 1
        # 8 bytes of key block compressed size
        key_block_compressed_size = unpack('>Q', key_block_info[i:i+8])[0]
        i += 8
        # 4 bytes of key block decompressed size
        key_block_decompressed_size = unpack('>Q', key_block_info[i:i+8])[0]
        i += 8
        key_block_info_list += [(key_block_compressed_size, key_block_decompressed_size)]
    return key_block_info_list


def readmdd(fname):
    glos = {}
    f = open(fname, 'rb')

    ################################################################################
    #      Header Block
    ################################################################################

    # 4 bytes integer : number of bytes of header text
    header_text_size = unpack('>I', f.read(4))[0]
    # text in utf-16
    header_text = f.read(header_text_size)[:-2]
    parser = XMLParser(encoding='utf-16')
    parser.feed(header_text)
    header_tag = parser.close()
    glos['header'] = header_tag.attrib

    # 4 bytes unknown
    glos['flag1'] = f.read(4).encode('hex')

    ################################################################################
    #      Key Block
    ################################################################################

    # 8 bytes long long : number of key blocks
    num_key_blocks = unpack('>Q', f.read(8))[0]
    glos['num_key_blocks'] =  num_key_blocks
    # 8 bytes long long : number of entries
    num_entries =  unpack('>Q', f.read(8))[0]
    glos['num_entries'] = num_entries
    # 8 bytes long long : unkown
    unknown = unpack('>Q', f.read(8))[0]
    glos['num1'] = unknown
    # 8 bytes long long : number of bytes of unknown block 1
    unknown_block_1_size = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of bytes of key block
    key_block_size = unpack('>Q', f.read(8))[0]

    # 4 bytes : unknown
    unknown = f.read(4)
    glos['flag2'] = unknown.encode('hex')

    # read unknown block 1
    unknown_block_1 = f.read(unknown_block_1_size)
    glos['unknown_block_1'] = unknown_block_1

    # read key block
    key_block_compressed = f.read(key_block_size)

    # extract key block
    key_block_list = []

    # \x02\x00\x00\x00 leads each key block
    for block in key_block_compressed.split('\x02\x00\x00\x00')[1:]:
        # decompress key block
        key_block = zlib.decompress(block[4:])
        # extract one single key block
        key_start_index = 0
        while key_start_index < len(key_block):
            # 8 bytes long long : the corresponding record's offset
            # in record block
            key_id = unpack('>Q', key_block[key_start_index:key_start_index+8])[0]
            # key text ends with '\x00\x00'
            for key_end_index in range(key_start_index + 8, len(key_block), 2):
                if key_block[key_end_index:key_end_index + 2] == '\x00\x00':
                    break

            key_text = key_block[key_start_index+8:key_end_index]
            key_start_index = key_end_index + 2
            key_block_list += [(key_id, key_text.decode('utf-16'))]

    ################################################################################
    #      Record Block
    ################################################################################

    # 8 bytes long long : number of record blocks
    num_record_blocks = unpack('>Q', f.read(8))[0]
    glos['num_record_blocks'] = num_record_blocks
    # 8 bytes long long : number of entries
    num_entries = unpack('>Q', f.read(8))[0]
    assert(num_entries == glos['num_entries'])
    # 8 bytes long long : number of bytes of record blocks info section
    num_record_block_info_bytes = unpack('>Q', f.read(8))[0]
    # 8 bytes long long : number of byets of actual record blocks
    total_record_block_bytes = unpack('>Q', f.read(8))[0]

    # record block info section
    record_block_info_list = []
    for i in range(num_record_blocks):
        # 8 bytes long long : number of bytes of record block
        current_record_block_size = unpack('>Q', f.read(8))[0]
        # 8 bytes long long : number of bytes of record block decompressed
        decompressed_block_size = unpack('>Q', f.read(8))[0]
        record_block_info_list += [(current_record_block_size, decompressed_block_size)]

    # actual record block
    record_block = ''
    for current_record_block_size, decompressed_block_size in record_block_info_list:
        current_record_block = f.read(current_record_block_size)
        current_record_block_text = zlib.decompress(current_record_block[8:])
        assert(len(current_record_block_text) == decompressed_block_size)
        record_block = record_block + current_record_block_text

    # merge record block and key_block_list
    data = []
    for i, (key_start, key_text) in enumerate(key_block_list):
        if i < len(key_block_list)-1:
            key_end = key_block_list[i+1][0]
        else:
            key_end = None
        data += [(key_text, record_block[key_start:key_end])]

    glos['data'] = data

    return glos

def readmdx(fname):
    glos = {}
    f = open(fname, 'rb')

    ################################################################################
    #      Header Block
    ################################################################################

    # number of bytes of header text
    header_text_size = unpack('>I', f.read(4))[0]
    # text in utf-16 encoding
    header_text = f.read(header_text_size)[:-2]
    parser = XMLParser(encoding='utf-16')
    parser.feed(header_text)
    header_tag = parser.close()
    glos['header'] = header_tag.attrib

    # before version 2.0, number is 4 bytes integer
    # version 2.0 and above uses 8 bytes
    version = float(header_tag.attrib['GeneratedByEngineVersion'])
    if version < 2.0:
        number_width = 4
        number_format = '>I'
    else:
        number_width = 8
        number_format = '>Q'

    # 4 bytes unknown
    glos['flag1'] = f.read(4).encode('hex')

    ################################################################################
    #      Key Block
    ################################################################################

    # number of key blocks
    num_key_blocks = unpack(number_format, f.read(number_width))[0]
    glos['num_key_blocks'] =  num_key_blocks
    # number of entries
    num_entries =  unpack(number_format, f.read(number_width))[0]
    glos['num_entries'] = num_entries
    # unkown
    if version >= 2.0:
        unknown = unpack(number_format, f.read(number_width))[0]
        glos['num1'] = unknown
    # number of bytes of key block info
    key_block_info_size = unpack(number_format, f.read(number_width))[0]
    # number of bytes of key block
    key_block_size = unpack(number_format, f.read(number_width))[0]

    # 4 bytes unknown
    if version >= 2.0:
        unknown = f.read(4)
        glos['flag2'] = unknown.encode('hex')


    # read key block info, which indicates block's compressed and decompressed size
    key_block_info = f.read(key_block_info_size)
    if version < 2.0:
        key_block_info_list = _decode_key_block_info_v1(key_block_info)
    else:
        key_block_info_list = _decode_key_block_info_v2(key_block_info)

    # read key block
    key_block_compressed = f.read(key_block_size)

    # extract key block
    key_list = []

    i = 0
    for compressed_size, decompressed_size in key_block_info_list:
        start = i;
        end = i + compressed_size
        # 4 bytes : compression type
        key_block_type = key_block_compressed[start:start+4]
        if key_block_type == '\x00\x00\x00\x00':
            # extract one single key block into a key list
            key_list += _split_key_block(key_block_compressed[start+8:end], number_format, number_width)
        elif key_block_type == '\x01\x00\x00\x00':
            if not HAVE_LZO:
                print "LZO compression is not supported"
                break
            # 4 bytes as adler32 checksum
            adler32 = unpack('>I', key_block_compressed[start+4:start+8])[0]
            # decompress key block
            header = '\xf0' + pack('>I', decompressed_size)
            key_block = lzo.decompress(header + key_block_compressed[start+8:end])
            assert(adler32 == lzo.adler32(key_block))
            # extract one single key block into a key list
            key_list += _split_key_block(key_block, number_format, number_width)
        elif key_block_type == '\x02\x00\x00\x00':
            # 4 bytes same as end of block
            assert(key_block_compressed[start+4:start+8] == key_block_compressed[end-4:end])
            # decompress key block
            key_block = zlib.decompress(key_block_compressed[start+number_width:end])
            # extract one single key block into a key list
            key_list += _split_key_block(key_block, number_format, number_width)
        i += compressed_size
    glos['key_block'] =  key_list

    ################################################################################
    #      Record Block
    ################################################################################

    # number of record blocks
    num_record_blocks = unpack(number_format, f.read(number_width))[0]
    glos['num_record_blocks'] = num_record_blocks
    # number of entries
    num_entries = unpack(number_format, f.read(number_width))[0]
    assert(num_entries == glos['num_entries'])
    # number of bytes of record blocks info section
    record_block_info_size = unpack(number_format, f.read(number_width))[0]
    # number of byets of actual record blocks
    record_block_size = unpack(number_format, f.read(number_width))[0]

    # record block info section
    record_block_info_list = []
    for i in range(num_record_blocks):
        # number of bytes of current record block
        compressed_size = unpack(number_format, f.read(number_width))[0]
        # number of bytes if current record block decompressed
        decompressed_size = unpack(number_format, f.read(number_width))[0]
        record_block_info_list += [(compressed_size, decompressed_size)]

    # actual record block data
    record_list = []
    for compressed_size, decompressed_size in record_block_info_list:
        record_block = f.read(compressed_size)
        # 4 bytes indicates block compression type
        record_block_type = record_block[:4]
        # no compression
        if record_block_type == '\x00\x00\x00\x00':
            record_list += record_block[8:].split('\x00')[:-1]
        # lzo compression
        elif record_block_type == '\x01\x00\x00\x00':
            if not HAVE_LZO:
                print "LZO compression is not supported"
                break
            # 4 bytes adler32 checksum
            # decompress
            header = '\xf0' + pack('>I', decompressed_size)
            record_block_text = lzo.decompress(header + record_block[8:])
            record_list += record_block_text.split('\x00')[:-1]
        # zlib compression
        elif record_block_type == '\x02\x00\x00\x00':
            # 4 bytes as checksum
            assert(record_block[4:8] == record_block[-4:])
            # compressed contents
            record_block_text = zlib.decompress(record_block[8:])
            assert(len(record_block_text) == decompressed_size)
            record_list += record_block_text.split('\x00')[:-1]
    glos['record_block'] = record_list

    # merge key_block and record_block
    dict = []
    for key, record in zip(key_list, record_list):
        dict += [(key[1], record)]
    glos['dict'] = dict
    f.close()

    return glos
if __name__ == '__main__':
    import os
    import os.path
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--extract', action="store_true",
                        help='extract mdx to source format and extract files from mdd')
    parser.add_argument('-d', '--datafolder', default="data",
                        help='folder to extract data files from mdd')
    parser.add_argument("filename", help="mdx file name")
    args = parser.parse_args()

    base,ext = os.path.splitext(args.filename)

    # read mdx file
    if ext == os.path.extsep + 'mdx':
        glos = readmdx(args.filename)
        print '========', args.filename, '========'
        print '  Number of Entries :', glos['num_entries']
        for key,value in glos['header'].items():
            print ' ', key.encode('utf-8'), ':', value.encode('utf-8')
    else:
        glos = None

    # find companion mdd file
    mdd_filename = ''.join([base, os.path.extsep, 'mdd'])
    if (os.path.exists(mdd_filename)):
        data = readmdd(mdd_filename)
        print '========', args.filename, '========'
        print ' Number of Entries :', data['num_entries']
        for key,value in data['header'].items():
            print ' ', key.encode('utf-8'), ':', value.encode('utf-8')
    else:
        data = None

    if args.extract:
        # write out glos
        if glos:
            output_fname = ''.join([base, os.path.extsep, 'txt'])
            f = open(output_fname, 'wb')
            for entry in glos['dict']:
                f.write(entry[0])
                f.write('\r\n')
                f.write(entry[1])
                f.write('</>\r\n')
            f.close()
        # write out optional data files
        if data:
            if not os.path.exists(args.datafolder):
                os.makedirs(args.datafolder)
            for entry in data['data']:
                fname = ''.join([args.datafolder, entry[0].replace('\\', os.path.sep)]);
                if not os.path.exists(os.path.dirname(fname)):
                    os.makedirs(os.path.dirname(fname))
                f = open(fname, 'wb')
                f.write(entry[1])
                f.close()
