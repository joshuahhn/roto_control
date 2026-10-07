"""Bounded summaries for finite native replacement acceptance probes."""
from collections import deque

def summary(values):
    values=sorted(values)
    if not values:return dict(samples=0)
    return dict(samples=len(values),mean=sum(values)/len(values),p95=values[int((len(values)-1)*.95)],maximum=values[-1])

def bounded(stats,targets):
    return (stats['subscribers']==2 and stats['cache_contexts']<=4 and stats['source_contexts']<=4
            and stats['pending_contexts']<=4 and stats['pending_slots']<=64 and not stats['subscriber_errors']
            and targets['pages']<=32 and targets['entries']<=4096 and targets['jobs']<=2 and targets['pending']<=2 and not targets['errors'])

class Samples:
    def __init__(self,limit=3600):self.values=deque(maxlen=limit);self.total=0
    def add(self,value):self.values.append(float(value));self.total+=1
    def result(self):return dict(summary(self.values),total_samples=self.total,retained_limit=self.values.maxlen)
