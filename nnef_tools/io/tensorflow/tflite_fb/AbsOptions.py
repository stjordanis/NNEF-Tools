# automatically generated by the FlatBuffers compiler, do not modify

# namespace: tflite_fb

import flatbuffers

class AbsOptions(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAsAbsOptions(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = AbsOptions()
        x.Init(buf, n + offset)
        return x

    # AbsOptions
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

def AbsOptionsStart(builder): builder.StartObject(0)
def AbsOptionsEnd(builder): return builder.EndObject()