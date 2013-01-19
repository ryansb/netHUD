from twisted.internet.defer import Deferred, DeferredQueue, succeed
from collections import defaultdict

class DeferredPriorityQueue(DeferredQueue):

    def __init__(self):
        DeferredQueue.__init__(self, None, None)
        self.pending = defaultdict(list)

    def put(self, priority, obj):
        if self.waiting:
            self.waiting.pop(0).callback(obj)
        else:
            self.pending[priority].append(obj)

    def get(self):
        if self.pending:
            min_ = sorted(self.pending.keys())[0]
            ret_val = self.pending[min_].pop(0)
            if not self.pending[min_]:
                del self.pending[min_]
            return succeed(ret_val)
        else:
            d = Deferred(canceller=self._cancelGet)
            self.waiting.append(d)
            return d

    def peek(self):
        return succeed(heap[0])

    def qsize(self):
        return succeed(len(self.pending))
