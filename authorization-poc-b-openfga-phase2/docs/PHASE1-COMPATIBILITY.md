# Phase-1 compatibility note

The original Phase-1 model contains tuple-to-userset relations on resource:

- `viewer ... member from team`
- `viewer ... member from department`
- `viewer ... member from organization`
- `editor ... lead from team`

Therefore resource grants through teams/departments/organizations must be
represented by tuples on the corresponding relation:

- `team:<id> team resource:<id>`
- `department:<id> department resource:<id>`
- `organization:<id> organization resource:<id>`

They must not be emitted as:

`team:<id> viewer resource:<id>`

The Phase-1 resource permission tuples using role objects also needed the
userset form:

`role:viewer#member viewer resource:<id>`

rather than:

`role:viewer viewer resource:<id>`

The corrected Phase-2 data preserves the logical Phase-1 dataset while fixing
only these tuple encodings.
