import os
import pwd
def run_and_seteuid_with_name(func, name):
    uid = pwd.getpwnam(name).pw_uid
    _run_and_seteuid(func, uid)

def _run_and_seteuid(func, uid):
    ruid = os.geteuid()
    try:
        os.seteuid(uid)
        func()
    finally:
        os.seteuid(ruid)
