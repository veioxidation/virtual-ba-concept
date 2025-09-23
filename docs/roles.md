# Role design recommendations

The platform differentiates between two layers of authorization:

## Azure Active Directory integration

Bearer tokens issued by Azure Active Directory are validated against the tenant and
audience configured via `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, or
`AZURE_AUDIENCE`. The FastAPI stack downloads the tenant's OpenID metadata and
JWKS to verify signatures and rejects tokens that do not match the configured
tenant or audience. When the token carries application roles (for example
`admin`, `project_maintainer`, or `process_creator`), the highest matching role
is synced onto the local user record so subsequent API calls can continue to
reuse the existing role-based decorators.

Users are matched to existing rows through their Azure object identifier (OID)
when available, otherwise by global personnel number (GPN) or email address.
Make sure the collaborators exist in the local `users` table so that role checks
and project-level permissions remain effective.

## Global (platform-wide) roles

| Role | Typical responsibilities |
| ---- | ------------------------ |
| `admin` | Full administrative control. Can manage users, processes, and override any project permissions. Ideal for the small operations/platform owner group. |
| `process_creator` | Trusted analysts who can register new processes, curate process metadata, and trigger runs. They cannot manage global user accounts but own the process lifecycle. |
| `project_maintainer` | Leads or senior analysts responsible for coordinating work inside existing projects. They can manage project metadata, reports, and assign project-level access. |
| `viewer` | Regular consumers with read-only visibility into data that has been shared with them (either because the project is public or through explicit project access). |

These global roles gate the FastAPI routers and administrative actions. They are meant to be coarse-grained and map to organizational duties rather than project-specific collaboration.

## Project-level roles

| Role | Meaning | Typical use |
| ---- | ------- | ----------- |
| `owner` | Canonical owner of the project (usually set automatically when the project is created). This role is not assignable through the access API. | Project creation/transfer workflows. |
| `editor` | Read/write access inside the project. Holders can upload artefacts, add reports, or update project content. | Core working team members. |
| `viewer` | Read-only access to the project. Can inspect outputs but cannot mutate anything. | Stakeholders or reviewers. |

Use the project access endpoints to share projects with additional colleagues as either `editor` (write) or `viewer` (read). The `owner` role stays reserved for project creation flows and cannot be granted through the sharing endpoints.
