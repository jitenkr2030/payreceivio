"""Context processor for tenant."""
def tenant_context(request):
    return {
        "active_organization": getattr(request, "active_organization", None),
        "active_company": getattr(request, "active_company", None),
        "active_branch": getattr(request, "active_branch", None),
        "user_organizations": list(getattr(request.user, "organizations", []).all()) if hasattr(request, "user") and request.user.is_authenticated else [],
    }
