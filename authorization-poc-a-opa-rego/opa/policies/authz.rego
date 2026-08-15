package authz

import rego.v1

default decision := {
    "decision": "DENY",
    "reason": "no_matching_policy",
    "policy": "authz",
    "version": "poc-a-1"
}

# Administrator can administer resources in their organization.
decision := {
    "decision": "ALLOW",
    "reason": "admin_same_org",
    "policy": "authz",
    "version": "poc-a-1",
} if {
    input.action in {"read", "write", "admin"}
    input.subject.roles[_] == "admin"
    input.subject.org_id == input.resource.org_id
}

# Security officers may read high-sensitivity resources when their clearance is sufficient.
decision := {
    "decision": "ALLOW",
    "reason": "security_clearance",
    "policy": "authz",
    "version": "poc-a-1",
} if {
    input.action == "read"
    input.subject.roles[_] == "security_officer"
    input.subject.clearance >= input.resource.classification
    input.subject.org_id == input.resource.org_id
}

# Developers can read resources in their department, with clearance and event-zone constraints.
decision := {
    "decision": "ALLOW",
    "reason": "developer_department_abac",
    "policy": "authz",
    "version": "poc-a-1",
} if {
    input.action == "read"
    input.subject.roles[_] == "developer"
    input.subject.department_id == input.resource.department_id
    input.subject.clearance >= input.resource.classification
    input.subject.event_zone == input.resource.event_zone
    location_ok
}

location_ok if {
    input.resource.allowed_location == null
}

location_ok if {
    input.resource.allowed_location == input.context.location
}

# Operators can access services/facilities only while physically in the resource's zone.
decision := {
    "decision": "ALLOW",
    "reason": "operator_zone_access",
    "policy": "authz",
    "version": "poc-a-1",
} if {
    input.action in {"read", "write"}
    input.subject.roles[_] == "operator"
    input.resource.type in {"service", "facility"}
    input.subject.event_zone == input.resource.event_zone
    input.context.location == input.subject.location
}

# Viewers may read low-sensitivity resources within their organization.
decision := {
    "decision": "ALLOW",
    "reason": "viewer_same_org",
    "policy": "authz",
    "version": "poc-a-1",
} if {
    input.action == "read"
    input.subject.roles[_] == "viewer"
    input.subject.org_id == input.resource.org_id
    input.resource.classification <= 2
}

# Rich decision endpoint: keep a small explanation payload alongside the decision.
allow := decision.decision == "ALLOW"
