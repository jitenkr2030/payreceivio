"""
Tenant middleware.

For PayReceivio we use a "session-based tenant" model: an authenticated user
belongs to one organization (their primary org). On login, the active
organization/company/branch is stashed in the session so subsequent requests
have a clear tenant context for filtering data.

If a user has access to multiple organizations (e.g. an auditor), they can
switch via the organization switcher in the navbar.
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    """Attach active tenant context to request."""

    def process_request(self, request):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            request.tenant = None
            request.active_organization = None
            request.active_company = None
            request.active_branch = None
            return

        session = request.session
        org_id = session.get(settings.TENANT_SESSION_KEY)
        user_orgs = list(request.user.organizations.all())

        if not user_orgs:
            request.tenant = None
            request.active_organization = None
            request.active_company = None
            request.active_branch = None
            return

        # If session org is invalid, fall back to the first user org
        active_org = next((o for o in user_orgs if o.pk == org_id), None)
        if active_org is None:
            active_org = user_orgs[0]
            session[settings.TENANT_SESSION_KEY] = active_org.pk

        company_id = session.get(f"{settings.TENANT_SESSION_KEY}_company")
        active_company = None
        if company_id:
            active_company = active_org.companies.filter(pk=company_id).first()

        branch_id = session.get(f"{settings.TENANT_SESSION_KEY}_branch")
        active_branch = None
        if branch_id and active_company:
            active_branch = active_company.branches.filter(pk=branch_id).first()

        request.tenant = active_org
        request.active_organization = active_org
        request.active_company = active_company
        request.active_branch = active_branch
