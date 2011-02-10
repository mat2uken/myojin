from flufl.lock import Lock, AlreadyLockedError
import flufl.lock 

class CustomLock(Lock):
    def lock(self, timeout=None):
        while True:
            try:
                result = Lock.lock(self, timeout)
            except AlreadyLockedError, e:
                self._sleep()
            else:
                return result
