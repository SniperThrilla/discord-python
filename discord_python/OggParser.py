
from typing import (
    IO
)

import struct

class OggStream():
    stream : IO[bytes] = None
    segtable : bytes = None

    def __init__(self, stream : IO[bytes]) -> None:
        self.stream = stream

    def parse_ogg_page(self):
        #print(f'SEGTABLE: {self.segtable}')
        if not self.segtable:
            # HEADER - Check if starts with "OggS" (4 bytes)
            header = self.stream.read(4)
            #print(header)
            #if header == b"OggS":
            #    print("WE HAVE A PAGE!")
            #else:
            #    print(f"OggS header not found. Header was: {header}")
            #    return b'', True
            if header != b'OggS':
                return b'', True
            version = self.stream.read(1)
            #print(f"VERSION: {version}")
            flags = self.stream.read(1)
            #print(f"FLAGS: {flags}")
            #if flags[0] & 0x01 != 0:
            #    print("contains continued data")
            #if flags[0] & 0x02 != 0:
            #    print("first page of logical bitstream")
            #if flags[0] & 0x04 != 0:
            #    print("last page of logical bitstream")
            granule = self.stream.read(8)
            #print(f"GRANULE: {granule}")
            bitstream_serial_number = self.stream.read(4)
            #print(f"SERIAL_NO: {bitstream_serial_number}")
            page_sequence_number = self.stream.read(4)
            #print(f"PAGE_SEQ_NO: {page_sequence_number}")
            checksum = self.stream.read(4)
            #print(f"CRC_CHECKSUM: {checksum}")
            number_page_segments = self.stream.read(1)
            #print(number_page_segments)
            seg_table_length = int.from_bytes(number_page_segments, byteorder="little")
            #print(f"PAGE_SEGMENTS_NO: {seg_table_length}")
            segment_table = self.stream.read(seg_table_length)
            #print(f"SEG_TABLE: {segment_table}")
            self.segtable = segment_table

        total_size = 0
        final = 0
        index = 0
        for byte in self.segtable:
            index += 1
            #print(byte)
            total_size += byte
            final = byte
            if byte != 255:
                # This packet is only this big. Remove these packets from the list to read.
                self.segtable = self.segtable[index:]
                break

        body = self.stream.read(total_size)

        #print(body)
        if final == 255:
            return (body, False)
        return (body, True)


    def iterate_pages(self):
        partial = b''
        page, complete = self.parse_ogg_page()
        while page:
            partial += page
            if complete:
                yield partial
                partial = b''
            page, complete = self.parse_ogg_page()
            

    def iterate_packets(self):
        # Get a new page
        for page in self.iterate_pages():
            yield page