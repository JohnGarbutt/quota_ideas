#!/usr/bin/env python
"""

  A -----
  |     |
  B     C

Project A has two children B and C.

Lets consider operator adds limits to project A,
10 VPUs and 10 RAM.

This means project B and C default to the limit -1, i.e they can
use all of their parents quota. Indeed project A is also allowed
to use all of its quota.

Note: this is in the default no overbook mode
"""

def get_limits_from_keystone(project_id, endpoint="nova_staging_3"):
    # consider project A, with children B and C
    # there is a limit on project A, we default project B and C
    # to have unlimited use of the same scope.
    # ... so we get something like this
    limits = [
        {
            "resource_class": "compute:VCPU",
            "max": 10,
            "count_scope": [
                {"project_id": "a"},
                {"project_id": "b"},
                {"project_id": "c"}
            ]
        },
        {
            "resource_class": "compute:RAM_GB",
            "max": 10,
            "count_scope": [
                {"project_id": "a"},
                {"project_id": "b"},
                {"project_id": "c"}
            ]
        }
    ]
    if project_id in ["a", "b", "c"]:
        return limits
    else:
        return []

"""

  A -----
  |     |
  B     C

Note: this is assuming we only support no overbook for now.

Project A has two children B and C.

As before, operator adds limits to project A of 10 vCPUs.

Now project A wants to share resources out between its-self and
its children B and C.

If project A sets a limit of 2 vCPUs on project B,
we get different results:

"""
def get_limits_from_keystone(project_id, endpoint="nova_staging_3"):
    # consider project A, with children B and C
    # there is a limit on project A, we default project B and C
    # to have unlimited use of the same scope.
    # ... so we get something like this
    limits_b = [
        {
            "resource_class": "compute:VCPU",
            "max": 2,
            "count_scope": [
                {"project_id": "b"},
            ]
        },
        {
            "resource_class": "compute:RAM_GB",
            "max": 10,
            "count_scope": [
                {"project_id": "a"},
                {"project_id": "b"},
                {"project_id": "c"}
            ]
        }
    ]
    limits_a_c = [
        {
            "resource_class": "compute:VCPU",
            "max": 8,  # NOTE A subtree has 10, B has 2 dedicated, so 8 left
            "count_scope": [
                {"project_id": "a"},
                {"project_id": "c"},
            ]
        },
        {
            "resource_class": "compute:RAM_GB",
            "max": 10,
            "count_scope": [
                {"project_id": "a"},
                {"project_id": "b"},
                {"project_id": "c"}
            ]
        }
    ]
    if project_id in ["b"]:
        return limits_b
    elif project_id in ["a", "c"]:
        return limits_a_c
    else:
        return []
