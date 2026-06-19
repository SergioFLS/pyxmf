import struct, io
from enum import Enum

class StandardField(Enum):
    XMF_FILE_TYPE = 0
    NODE_NAME = 1
    NODE_ID = 2
    RESOURCE_FORMAT = 3
    FILENAME = 4
    FILENAME_EXTENSION = 5
    MACOS_TYPE_CREATOR = 6
    MIME_TYPE = 7
    TITLE = 8
    COPYRIGHT = 9
    COMMENT = 10

class ReadWrapper:
    ENDIAN = '!'
    def __init__(self, f):
        self.f = f

    def read(self, n):
        return self.f.read(n)

    def u8(self):
        return self.read(1)[0]

    def u32(self):
        return struct.unpack(self.ENDIAN+'L', self.read(4))[0]

    def vlq(self):
        raw = self.u8()
        if (raw & 0b10000000) == 0:
            return raw
        output = (raw & 0x7F) << 7

        raw = self.u8()
        output = output | (raw & 0x7F)
        if (raw & 0b10000000) == 0:
            return output

        output = output << 7
        raw = self.u8()
        output = output | (raw & 0x7F)
        if (raw & 0b10000000) == 0:
            return output

        output = output << 7
        raw = self.u8()
        output = output | (raw & 0x7F)
        assert (raw & 0b10000000) != 0
        return output

class XMFNode:
    def __init__(self, rw):
        f = rw.f

        pos = f.tell()
        length = rw.vlq()
        contained_items = rw.vlq()
        header_length = rw.vlq()

        # metadata
        metaio = io.BytesIO(rw.read(rw.vlq()))
        meta = ReadWrapper(metaio)
        assert meta.vlq() == 0 # standard field only for now
        if StandardField(meta.vlq()) == StandardField.XMF_FILE_TYPE:
            print(f'xmf type {meta.vlq()} {meta.vlq()}')
        assert meta.vlq() == 0 # universal only for now

        f.seek(pos + header_length)
        reference_type = rw.vlq()
        #print(reference_type)
        assert reference_type == 1

        if contained_items >= 1:
            # folder node
            self.contents = []
            for i in range(contained_items):
                self.contents.append(XMFNode(rw))
        else:
            # file node
            self.contents = rw.read(length - header_length - 1)


class XMFFile:
    MAGIC = b'XMF_'
    def __init__(self, f):
        rw = ReadWrapper(f)
        assert f.read(4) == self.MAGIC

        assert f.read(4) == b'2.00'
        self.fileTypeID = rw.u32()
        self.fileTypeRevisionID = rw.u32()
        self.fileSize = rw.vlq()

        # metadatatypestable - size should be 0 for now
        assert rw.vlq() == 0
        self.treeStart = rw.vlq()
        self.treeEnd = rw.vlq()

        # parse the first node
        f.seek(self.treeStart)
        self.treeNode = XMFNode(rw)


if __name__ == '__main__':
    with open('Chimps On Mars.mxmf', 'rb') as f:
        breakpoint
        global xmf
        xmf = XMFFile(f)
        #print(xmf.treeStart)
        #print(xmf.treeEnd)
