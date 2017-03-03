#!/usr/bin/env python

import uuid

def register_nova_default_limits_for_endpoint():
    # operator registers the limits in keystone
    # for a Nova end point
    end_point_project_limit_defaults = [
        {
            "resource_class": "compute:VCPU",
            "max": 5,
        },
        {
            "resource_class": "compute:RAM",
            "max": 5,
        },
    ]
    # if no limits are set on a project, the above
    # limits are returned

"""

  A -----
  |     |
  B     C

Project A has two children B and C.

Lets consider operator adds limits to project A,
10 VPUs and 10 RAM.

POST /keystone/limits/nova_endpoint_uuid/a
{
    "limits": [
        {
            "resource_class": "compute:VCPU",
            "max": 10,
        },
        {
            "resource_class": "compute:RAM",
            "max": 10,
        }
    ]
}

This means project B and C default to the limit -1, i.e they can
use all of their parents quota. Indeed project A is also allowed
to use all of its quota.

Note: this is in the default no overbook mode
"""

def _get_default_limits(project_id):
    default_limits = [
        {
            "resource_class": "compute:VCPU",
            "max": 5,
            "count_scope": [
                {"project_id": project_id},
            ]
        },
        {
            "resource_class": "compute:RAM_GB",
            "max": 5,
            "count_scope": [
                {"project_id": project_id},
            ]
        }
    ]
    return default_limits

def get_limits_from_keystone(project_id, endpoint="nova_staging_3"):
    # consider project A, with children B and C
    # there is a limit on project A, we default project B and C
    # to have unlimited use of the same scope.
    # ... so we get something like this
    limits_a_b_c = [
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
        return limits_a_b_c
    else:
        return _get_default_limits(project_id)

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

POST /keystone/limits/nova_endpoint_uuid/a
{
    "limits": [
        {
            "resource_class": "compute:VCPU",
            "max": 2,
        },
    ]
}

#TODO maybe you always have to set all limits?
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
        return _get_default_limits(project_id)


callbacks = {}
resource_callback_uuids = {}


def register_count(resources, callback):
    callback_uuid = uuid.uuid4().hex
    callbacks[callback_uuid] = callback
    for resource in resources:
        resource_callback_uuids[resource] = callback_uuid


def check_usage(project_id, additional_resource=None):
    limits = get_limits_from_keystone(project_id)

    for limit in limits:
        resource_class = limit["resource_class"]
        max_count = limit["max"]
        scope = limit["count_scope"]

        callback_uuid = resource_callback_uuids.get(resource_class)
        callback = callbacks[callback_uuid]

        # FIXME - very wasteful
        sub_counts = callback(scope)
        existing_resource_count = None
        for sub_count in sub_counts:
            sub_count_resource_class = sub_count["resource_class"]
            if resource_class == sub_count_resource_class:
                existing_resource_count = sub_count["count"]
                break

        if not existing_resource_count:
            raise Exception("missing expected counts")

        # TODO - add in count from additional_resource
        additional_resource_count = 0
        if additional_resource is None:
            additional_resource = []
        for sub_count in additional_resource:
            sub_count_resource_class = sub_count["resource_class"]
            if resource_class == sub_count_resource_class:
                additional_resource_count = sub_count["count"]
                break

        count = existing_resource_count + additional_resource_count
        is_over_quota = count > max_count

        result_string = ("for resource:'%(resource_class)s' "
            "and project:'%(project_id)s' "
            "max allowed is %(max_count)s for scope %(scope)s "
            "existing %(existing_resource_count)s "
            "with extra of %(additional_resource_count)s "
            "actual scope count is %(count)s") % locals()
        if is_over_quota:
            raise Exception("over quota " + result_string)
        else:
            print "passed quota check " + result_string


def main():
    import pprint
    print
    print "***********************************"
    print "First operators sets default limits"
    print "get limits for random project x"
    pprint.pprint(get_limits_from_keystone("x"))
    print

    print "***********************************"
    print "Project a has children b and c"
    print "Then operator sets limits for a of 10 and 10"
    print "Then a sets limits for b of 2 vCPUs"
    print
    print "Project B:"
    pprint.pprint(get_limits_from_keystone("b"))
    print
    print "Project A and C get the same limits:"
    pprint.pprint(get_limits_from_keystone("a"))
    pprint.pprint(get_limits_from_keystone("c"))
    print
    print "Project X still gets the default limits"
    pprint.pprint(get_limits_from_keystone("x"))
    print

    def count_instances(project_ids):
        if len(project_ids) != 1 and project_ids[0] != "x":
            raise NotImplemented()
        return [
            {
                "resource_class": "compute:VCPU",
                "count": 2
            },
            {
                "resource_class": "compute:RAM_GB",
                "count": 3
            },
        ]
    register_count(
        ["compute:VCPU", "compute:RAM_GB"],
        count_instances)

    print "***********************************"
    print "Project x has usage of 2 VCPUs and 3 RAM_GB"
    print "check the usage against limits"
    print "expecting a pass"
    print
    check_usage("x")

    print
    print "***********************************"
    print "Project x has usage of 2 VCPUs and 3 RAM_GB"
    print "consider booting an instance"
    print "check the usage against after extra 3 VPU and 5 RAM"
    print "expecting overlimit on RAM_GB"
    print
    check_usage("x", additional_resource=[
            {
                "resource_class": "compute:VCPU",
                "count": 3
            },
            {
                "resource_class": "compute:RAM_GB",
                "count": 5
            },
    ])

if __name__ == "__main__":
    main()
