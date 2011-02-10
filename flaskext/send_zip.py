from werkzeug import Headers


from flask import Response
import os
class IterFile(object):
    def __init__(self):
        from cStringIO import StringIO
        self.buf = StringIO()
        self.offset = 0
    def write(self, d):
        self.buf.write(d)
    def flush(self):
        pass
    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            assert offset >= self.offset
            return self.buf.seek(offset - self.offset, whence)
        return self.buf.seek(offset, whence)
    def tell(self):
        return self.buf.tell() + self.offset
    def rotate(self):
        self.offset += self.buf.tell()
        result = self.buf.getvalue()
        from cStringIO import StringIO
        self.buf = StringIO()
        return result

class DummyIterFile(object):
    def __init__(self):
        from cStringIO import StringIO
        self.buf = StringIO()
        self.offset = 0
        self.pos = 0
    def write(self, d):
        self.buf.write(d)
        self.pos += len(d)
    def flush(self):
        pass
    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            assert offset >= self.offset
            return self.buf.seek(offset - self.offset, whence)
        return self.buf.seek(offset, whence)
    def tell(self):
        return self.buf.tell() + self.offset
    def rotate(self):
        self.offset += self.buf.tell()
        result = self.buf.getvalue()
        from cStringIO import StringIO
        self.buf = StringIO()
        return result

from zipfile import ZipFile
def zip_iter(filename_path_list):
    buf = IterFile()
    z = ZipFile4Stream(buf, "w")
    #offset = 0
    for filename, filepath in filename_path_list:
        for x in z.write_iter(filepath, filename):
            yield x
            #print "1"
            buf.offset += len(x)
            #z.fp.write(x)
        #zip_write(z, filepath, filename)
        #print "write",filepath, filename
        #yield buf.rotate()
    #buf.rotate()
    z.close()
    yield buf.rotate()

def old_zip_iter(filename_path_list):
    from zipfile import ZipFile
    buf = IterFile()
    z = ZipFile(buf, "w")
    for filename, filepath in filename_path_list:
        z.write(filepath, filename)
        print "write",filepath, filename
        yield buf.rotate()
    z.close()
    yield buf.rotate()

from flask.globals import current_app
def send_zip(zipfilename, filename_path_list):
    #s = "<body><h1>HELLO</h1></body>"
    #response = iter(list(s))
    response = zip_iter(filename_path_list)
    headers = Headers()
    attachment_filename = zipfilename
    headers.add('Content-Disposition', 'attachment',
                filename=attachment_filename)
    
    mimetype = 'application/zip'
    return current_app.response_class(
        response=response,
        mimetype=mimetype,
        headers=headers,
        direct_passthrough=True
        )

class ZipFile4Stream(ZipFile):
    def write_iter(self, filename, arcname=None, compress_type=None):
        """Put the bytes from filename into the archive under the name
        arcname."""
        from zipfile import stat, time, ZipInfo, ZIP_DEFLATED, crc32, struct
        if not self.fp:
            raise RuntimeError(
                  "Attempt to write to ZIP archive that was already closed")

        st = os.stat(filename)
        isdir = stat.S_ISDIR(st.st_mode)
        mtime = time.localtime(st.st_mtime)
        date_time = mtime[0:6]
        # Create ZipInfo instance to store file information
        if arcname is None:
            arcname = filename
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]
        if isdir:
            arcname += '/'
        zinfo = ZipInfo(arcname, date_time)
        zinfo.external_attr = (st[0] & 0xFFFF) << 16L      # Unix attributes
        if compress_type is None:
            zinfo.compress_type = self.compression
        else:
            zinfo.compress_type = compress_type

        zinfo.file_size = st.st_size
        zinfo.flag_bits = 0x00
        zinfo.header_offset = self.fp.tell()    # Start of header bytes

        self._writecheck(zinfo)
        self._didModify = True

        if isdir:
            zinfo.file_size = 0
            zinfo.compress_size = 0
            zinfo.CRC = 0
            self.filelist.append(zinfo)
            self.NameToInfo[zinfo.filename] = zinfo
            yield zinfo.FileHeader()
            #self.fp.write(zinfo.FileHeader())
            return

        with open(filename, "rb") as fp:
            # Must overwrite CRC and sizes with correct data later
            zinfo.CRC = CRC = 0
            zinfo.compress_size = compress_size = 0
            zinfo.file_size = file_size = 0
            cmpr = None
            while 1:
                buf = fp.read(1024 * 8)
                if not buf:
                    break
                file_size = file_size + len(buf)
                CRC = crc32(buf, CRC) & 0xffffffff
            zinfo.compress_size = file_size
            zinfo.file_size = file_size
            zinfo.CRC = CRC
            #self.fp.write(zinfo.FileHeader())
            yield zinfo.FileHeader()
            fp.seek(0)
            while 1:
                buf = fp.read(1024 * 8)
                if not buf:
                    break
                #self.fp.write(buf)
                yield buf
        self.filelist.append(zinfo)
        self.NameToInfo[zinfo.filename] = zinfo



def test_files():
    for pth, dirs, files in os.walk(os.path.join("../myojin", "sample_files")):
        for filename in files:
            fullpath = os.path.join(pth,filename)
            yield filename, fullpath
    
if __name__=="__main__":
    fs = test_files()
    fs = list(fs)[:4]
    with open("testout2.zip","wb") as f:
        for x in zip_iter(fs):
            f.write(x)

            #with open(fullpath,'rb') as file:
