"""Bounded row pool for the Inspector's in-window context dropdown."""
def capacity_for(bottom,count):
    available=max(1,min(8,int((bottom-6)//24)))
    if count<=available:return available
    return max(1,min(8,int((bottom-30)//24)))

def placement_for(bottom,top,height,count):
    desired=4+24*min(8,count)+(24 if count>8 else 0)+2
    below=bottom;above=height-top
    direction='below' if below>=desired or below>=above else 'above'
    return direction,capacity_for(below if direction=='below' else above,count)

def editor_space_for(bottom,count,available=None):
    """Use all pooled choices when existing height fits; otherwise four rows."""
    full=max(1,min(8,count))
    full_height=4+24*full+(24 if count>full else 0)
    capacity=full if available is not None and available>=full_height+4 else max(1,min(4,count))
    height=4+24*min(count,capacity)+(24 if count>capacity else 0)
    return max(0,height+4-bottom),capacity

class Dropdown:
    def __init__(self,items,details,checked=(),capacity=8):
        self.items=tuple(items);self.details=details;self.checked=frozenset(checked)
        self.capacity=max(1,min(8,int(capacity)));self.first=0
        selected=next((i for i,item in enumerate(self.items) if item in self.checked),0)
        self.first=min(selected,max(0,len(self.items)-self.capacity))
    def rows(self):return self.items[self.first:self.first+self.capacity]
    def item(self,slot):
        if type(slot)is not int or not 0<=slot<len(self.rows()):raise ValueError('Invalid menu row')
        return self.rows()[slot]
    def move(self,delta):
        previous=self.first;self.first=max(0,min(max(0,len(self.items)-self.capacity),self.first+int(delta)))
        return self.first!=previous
    def count_label(self):return '%d–%d / %d'%(self.first+1,min(len(self.items),self.first+self.capacity),len(self.items))
