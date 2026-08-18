package hybrid.authz

import rego.v1

test_allow_read if {
  decision with input as {
    "relationship_allowed": true,
    "action": "read",
    "subject": {
      "organization": "org-0001",
      "clearance": 5,
      "role": "developer",
      "event_zone": "ZONE-A"
    },
    "resource": {
      "organization": "org-0001",
      "classification": 4,
      "allowed_location": null,
      "event_zone": "ZONE-A"
    },
    "context": {
      "location": "BENGALURU"
    }
  } == {
    "decision": "ALLOW",
    "reason": "relationship_and_attribute_policy",
    "relationship_allowed": true,
    "attribute_allowed": true
  }
}

test_deny_attribute if {
  decision with input as {
    "relationship_allowed": true,
    "action": "read",
    "subject": {
      "organization": "org-0001",
      "clearance": 2,
      "role": "developer",
      "event_zone": "ZONE-A"
    },
    "resource": {
      "organization": "org-0001",
      "classification": 4,
      "allowed_location": null,
      "event_zone": "ZONE-A"
    },
    "context": {
      "location": "BENGALURU"
    }
  } == {
    "decision": "DENY",
    "reason": "attribute_policy_denied",
    "relationship_allowed": true,
    "attribute_allowed": false
  }
}

test_deny_relationship if {
  decision with input as {
    "relationship_allowed": false,
    "action": "read",
    "subject": {},
    "resource": {},
    "context": {}
  } == {
    "decision": "DENY",
    "reason": "relationship_denied",
    "attribute_allowed": false
  }
}
