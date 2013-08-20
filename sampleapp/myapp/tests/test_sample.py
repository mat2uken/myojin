if __name__==u"__main__":
    import sys,os
    os.chdir("../../")
    from subprocess import Popen, call
    call('python manage.py test -s myojin/tests/ -p test_sample.py'.split())
    sys.exit()

import unittest 

def open_filename(filename):
    fullpath  = os.path.join(os.path.dirname(__file__), "testfiles", filename)
    return open(fullpath,'rb')

class TestCase(unittest.TestCase): 
    def setUp(self):
        print "setUp"

    def tearDown(self):
        pass

    def test_add_base(self):
        print "abc"
        pass
    
