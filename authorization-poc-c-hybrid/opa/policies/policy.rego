package hybrid.authz

import rego.v1

# Rego default values must be ground values.
# Dynamic references such as input.relationship_allowed cannot be used
# inside a default rule value.
default decision := {
  "decision": "DENY",
  "reason": "relationship_denied",
  "attribute_allowed": false
}

decision := {
  "decision": "ALLOW",
  "reason": "relationship_and_attribute_policy",
  "relationship_allowed": true,
  "attribute_allowed": true
} if {
  input.relationship_allowed == true
  attribute_allowed
}

decision := {
  "decision": "DENY",
  "reason": "attribute_policy_denied",
  "relationship_allowed": true,
  "attribute_allowed": false
} if {
  input.relationship_allowed == true
  not attribute_allowed
}

attribute_allowed if {
  input.action == "read"
  input.subject.organization == input.resource.organization
  input.subject.clearance >= input.resource.classification
  location_allowed
  input.subject.event_zone == input.resource.event_zone
}

attribute_allowed if {
  input.action == "write"
  input.subject.organization == input.resource.organization
  input.subject.clearance >= input.resource.classification
  input.subject.role == "admin"
  location_allowed
  input.subject.event_zone == input.resource.event_zone
}

location_allowed if {
  input.resource.allowed_location == null
}

location_allowed if {
  input.resource.allowed_location == input.context.location
}
