package authz

import rego.v1

test_admin_same_org if {
    decision == {
        "decision": "ALLOW",
        "reason": "admin_same_org",
        "policy": "authz",
        "version": "poc-a-1"
    }
    with input as {
        "subject": {
            "roles": ["admin"],
            "org_id": "org-0001",
            "department_id": "dept-00001",
            "clearance": 5,
            "event_zone": "ZONE-A",
            "location": "DELHI"
        },
        "resource": {
            "org_id": "org-0001",
            "department_id": "dept-00002",
            "classification": 4,
            "event_zone": "ZONE-C",
            "type": "document",
            "allowed_location": null
        },
        "action": "read",
        "context": {"location": "DELHI"}
    }
}

test_denied_wrong_org if {
    decision.decision == "DENY"
    with input as {
        "subject": {
            "roles": ["admin"],
            "org_id": "org-0001",
            "clearance": 5,
            "event_zone": "ZONE-A",
            "location": "DELHI"
        },
        "resource": {
            "org_id": "org-0002",
            "department_id": "dept-00002",
            "classification": 1,
            "event_zone": "ZONE-A",
            "type": "document",
            "allowed_location": null
        },
        "action": "read",
        "context": {"location": "DELHI"}
    }
}

test_security_clearance if {
    decision.reason == "security_clearance"
    with input as {
        "subject": {
            "roles": ["security_officer"],
            "org_id": "org-0001",
            "clearance": 5,
            "event_zone": "ZONE-A",
            "location": "DELHI"
        },
        "resource": {
            "org_id": "org-0001",
            "department_id": "dept-00002",
            "classification": 5,
            "event_zone": "ZONE-D",
            "type": "document",
            "allowed_location": "MUMBAI"
        },
        "action": "read",
        "context": {"location": "MUMBAI"}
    }
}

test_developer_department_abac if {
    decision.reason == "developer_department_abac"
    with input as {
        "subject": {
            "roles": ["developer"],
            "org_id": "org-0001",
            "department_id": "dept-00001",
            "clearance": 4,
            "event_zone": "ZONE-A",
            "location": "DELHI"
        },
        "resource": {
            "org_id": "org-0001",
            "department_id": "dept-00001",
            "classification": 3,
            "event_zone": "ZONE-A",
            "type": "service",
            "allowed_location": "DELHI"
        },
        "action": "read",
        "context": {"location": "DELHI"}
    }
}
