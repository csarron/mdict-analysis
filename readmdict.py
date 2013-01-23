from struct import unpack
import zlib
from xml.etree.ElementTree import XMLParser

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

    # integer : number of bytes of header text
    header_text_size = unpack('>I', f.read(4))[0]
    # text in utf-16 encoding
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

    # 4 bytes unknown
    unknown = f.read(4)
    glos['flag2'] = unknown.encode('hex')

    # read unknown block 1
    unknown_block_1 = f.read(unknown_block_1_size)
    glos['unknown_block_1'] = unknown_block_1
    # read key block
    key_block_compressed = f.read(key_block_size)

    # extract key block
    key_list = []

    # \x02\x00\x00\x00 leads each key block
    key_block_list = key_block_compressed.split('\x02\x00\x00\x00')
    for block in key_block_list[1:]:
        # decompress key block
        key_block = zlib.decompress(block[4:])
        # extract one single key block
        key_start_index = 0
        while key_start_index < len(key_block):
            # 8 bytes long long : the corresponding record's offset
            # in record block
            key_id = unpack('>Q', key_block[key_start_index:key_start_index+8])[0]
            # key text ends with '\x00'
            key_end_index = key_start_index + 8
            for a in key_block[key_start_index+8:]:
                key_end_index += 1
                if a == '\x00':
                    break
            key_text = key_block[key_start_index+8:key_end_index-1]
            key_start_index = key_end_index
            key_list += [(key_id, key_text)]

    glos['key_block'] =  key_list

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
        # 8 bytes long long : number of bytes of current record block
        current_record_block_size = unpack('>Q', f.read(8))[0]
        # 8 bytes long long : number of bytes if current record block decompressed
        decompressed_block_size = unpack('>Q', f.read(8))[0]
        record_block_info_list += [(current_record_block_size, decompressed_block_size)]

    # actual record block data
    record_block = []
    for current_record_block_size, unknown_size in record_block_info_list:
        current_record_block = f.read(current_record_block_size)
        current_record_block_text = zlib.decompress(current_record_block[8:])
        #assert(len(current_record_block_text) == decompressed_block_size)
        record_block += current_record_block_text.split('\x00')[:-1]
    glos['record_block'] = record_block

    # merge key_block and record_block
    dict = []
    for key, record in zip(key_list, record_block):
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

    # read mdx file
    glos = readmdx(args.filename)
    print '========', args.filename, '========'
    print '  Number of Entries :', glos['num_entries']
    for key,value in glos['header'].items():
        print ' ', key, ':', value

    # find companion mdd file
    base,ext = os.path.splitext(args.filename)
    mdd_filename = ''.join([base, os.path.extsep, 'mdd'])
    if (os.path.exists(mdd_filename)):
        data = readmdd(mdd_filename)
        print '========', args.filename, '========'
        print ' Number of Entries :', data['num_entries']
        for key,value in glos['header'].items():
            print ' ', key, ':', value
    else:
        data = None

    if args.extract:
        # write out glos
        output_fname = ''.join([base, os.path.extsep, 'txt'])
        f = open(output_fname, 'w')
        for entry in glos['dict']:
            f.write(entry[0])
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
                f = open(fname, 'w')
                f.write(entry[1])
                f.close()
