#!/usr/bin/env python3

import pytest
from timeio.qc.qctest import QcTest, StreamInfo, Param
from timeio.qc.utils import filter_thing_funcs

data = """
[
  {
    "result_quality": {"annotation": "0.0", "properties": {"measure": "flagUnflagged", "version": "2.6.0", "userLabel": "p1", "configuration": 38}, "annotationType": "SaQC"}
  },
  {
    "result_quality": {"annotation": "0.0", "properties": {"measure": "flagUnflagged", "version": "2.6.0", "userLabel": "p1", "configuration": 38}, "annotationType": "SaQC"}
  },
]
"""


f1 = StreamInfo("field", "f1", thing_id=1, stream_id=1)
f2 = StreamInfo("field", "f2", thing_id=2, stream_id=2)
t1 = StreamInfo("target", "t1", thing_id=1, stream_id=1)
t2 = StreamInfo("target", "t2", thing_id=2, stream_id=2)
t3 = StreamInfo("target", "t4", thing_id=1, stream_id=None)

q1 = QcTest(
    name="F1",
    func_name="flagRange",
    context_window=20,
    params=[f1, t1],
)

q2 = QcTest(
    name="F2",
    func_name="flagRange",
    context_window=20,
    params=[f2, t2],
)

q3 = QcTest(
    name="F3",
    func_name="calculateMean",
    context_window=20,
    params=[f1, f2, t3]
)
# f4 = QcTest(
#     name="F4",
#     func_name="calculateMean",
#     context_window=20,
#     params=[
#         StreamInfo("field", "t1", thing_id=1, stream_id=None),
#         StreamInfo("target", "t1", thing_id=1, stream_id=None),
#     ],
# )
# f5 = QcTest(
#     name="F5",
#     func_name="calculateMean",
#     context_window=20,
#     params=[
#         StreamInfo("field", "t1", thing_id=1, stream_id=None),
#         StreamInfo("target", "t1", thing_id=1, stream_id=None),
#     ],
# )

def test_function_resolution():
    xxx =  filter_thing_funcs([q1, q2, q3], thing_id=1)
    import ipdb; ipdb.set_trace()

