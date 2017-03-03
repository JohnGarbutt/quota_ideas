
get_limits_from_keystone(project_id, endpoint="nova_staging_3"):
    # consider project A, with children B and C
    # there is a limit on project A, we default project B and C
    # to have unlimited use of the same scope.
    # ... so we get something like this
    limits = [
        {
            "scope": [{"project_id": project_id},
                      {"project_id": project_id_sibling},
                      {"project_id": project_id_parent}
            ],
            "limits": [
                {
                    "resource_class": "compute:VCPU",
                    "max": 10
                }
            ]
    ]
    return limits
