"""Organization services - bootstrap, role seeding, etc."""
from django.utils import timezone

from apps.accounts.models import Role, RoleAssignment
from .models import Organization, Company, Branch


def create_organization_with_owner(organization_name: str, owner, **kwargs) -> Organization:
    """
    Create an organization with the default company/branch and assign the
    owner the org_owner role. Used by the signup flow.
    """
    org = Organization.objects.create(
        name=organization_name,
        legal_name=kwargs.get("legal_name", organization_name),
        email=owner.email,
        phone=owner.phone or "",
        created_by=owner,
        updated_by=owner,
        subscription_plan="trial",
        trial_ends_at=timezone.now() + timezone.timedelta(days=14),
    )
    # Default company
    company = Company.objects.create(
        organization=org,
        name=organization_name,
        created_by=owner,
        updated_by=owner,
    )
    # Default branch
    Branch.objects.create(
        company=company,
        name="Head Office",
        code="HO",
        is_head_office=True,
        created_by=owner,
        updated_by=owner,
    )
    # Seed system roles for this org
    _seed_org_roles(org)
    # Assign owner role
    owner_role = Role.objects.get(organization=org, name="org_owner")
    RoleAssignment.objects.create(
        user=owner, role=owner_role, organization=org,
        company=company, assigned_by=owner,
    )
    return org


def _seed_org_roles(org: Organization):
    """Create the standard set of roles for a new organization."""
    from django.contrib.auth.models import Permission
    descriptions = {
        "org_owner": "Full access to the organization",
        "business_admin": "Configure organization settings, users, and integrations",
        "finance_manager": "Manage receivables, payments, and reports",
        "accountant": "Reconciliation and receipt posting",
        "collection_manager": "Manage collection team and escalations",
        "collection_executive": "Follow up on assigned customers",
        "sales_manager": "View salesperson collection performance",
        "salesperson": "Manage assigned customers and collections",
        "auditor": "Read-only access to financial and activity records",
        "customer": "Customer self-service portal access",
    }
    for role_name, label in Role.SYSTEM_ROLES:
        if role_name == "super_admin":
            continue
        Role.objects.create(
            organization=org,
            name=role_name,
            label=label,
            description=descriptions.get(role_name, ""),
            is_system=True,
        )


def get_default_company(org: Organization) -> Company:
    return org.companies.first()


def get_default_branch(company: Company) -> Branch:
    return company.branches.first() or company.branches.order_by("-is_head_office").first()
