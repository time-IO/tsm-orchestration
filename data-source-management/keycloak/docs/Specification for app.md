# Specification for App configuration

## Environment Variables

```
frontend:
    OIDC_CLIENT_ID: "${OIDC_CLIENT_ID:-dev-client}"
    OIDC_IDP_URL: "${OIDC_IDP_URL:-http://localhost/keycloak/realms/local-dev}" #url to idp without .well-known
api:
    OIDC_WELL_KNOWN: "${OIDC_WELL_KNOWN:-http://nginx/keycloak/realms/local-dev/.well-known/openid-configuration}"
    OIDC_ISSUER: "${OIDC_ISSUER:-http://localhost/keycloak/realms/local-dev}"
    OIDC_AUDIENCE: "${OIDC_AUDIENCE:-dev-client}"
    ALLOWED_VOS: "${ALLOWED_VOS:-UFZ-TSM,VO}"
```

## Created groups:

- `a:a:a:group:VO:Group1#`
- `a:a:a:group:VO:Group2#`
- `a:a:a:group:VO2:Group1#` (can be used as a not allowed VO)

- **Note**:

  - Please note that the `VO` name must be added to the `ALLOWED_VOS` environment variable

## Created user:

- **Note**: All users have the password `password`

| Username | Groups                                             | Purpose                                    |
| -------- | -------------------------------------------------- | ------------------------------------------ |
| `user1`  | `a:a:a:group:VO:Group1#`, `a:a:a:group:VO:Group2#` | a user in two valid groups                 |
| `user2`  | `a:a:a:group:VO:Group1#`                           | a user in one valid group, same as `user1` |
| `user3`  | `a:a:a:group:VO2:Group1#`                          | a user in a not valid virtual organization |
| `user4`  | -                                                  | a user not in any group                    |
