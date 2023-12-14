from protobuf3.message import Message
from protobuf3.fields import DoubleField, UInt64Field, Int64Field, Int32Field, StringField, MessageField


class Timestamp(Message):
    pass


class Sample(Message):

    class TagsEntry(Message):
        pass

    class AnnotationsEntry(Message):
        pass


class Samples(Message):
    pass

Timestamp.add_field('seconds', Int64Field(field_number=1, optional=True))
Timestamp.add_field('nanos', Int32Field(field_number=2, optional=True))
Sample.TagsEntry.add_field('key', StringField(field_number=1, optional=True))
Sample.TagsEntry.add_field('value', StringField(field_number=2, optional=True))
Sample.AnnotationsEntry.add_field('key', StringField(field_number=1, optional=True))
Sample.AnnotationsEntry.add_field('value', StringField(field_number=2, optional=True))
Sample.add_field('Name', StringField(field_number=1, optional=True))
Sample.add_field('Value', DoubleField(field_number=2, optional=True))
Sample.add_field('Timestamp', MessageField(field_number=3, optional=True, message_cls=Timestamp))
Sample.add_field('Tags', MessageField(field_number=4, repeated=True, message_cls=Sample.TagsEntry))
Sample.add_field('SequenceID', UInt64Field(field_number=5, optional=True))
Sample.add_field('Annotations', MessageField(field_number=6, repeated=True, message_cls=Sample.AnnotationsEntry))
Samples.add_field('Samples', MessageField(field_number=1, repeated=True, message_cls=Sample))
