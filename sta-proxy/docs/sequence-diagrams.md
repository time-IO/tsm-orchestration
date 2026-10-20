# STA Proxy Diagrams

Specific error responses and most [*unhappy paths*](https://en.wikipedia.org/wiki/Happy_path#Unhappy_path) are left out, see the [README](../README.md) for details.

## Components

```mermaid
flowchart LR
    U[Browser] -->|/sta-proxy/| N[nginx]
    S[Script] -->|/sta/| N
    U -->|/sta/| N
    U -->|login| KC[Keycloak]
    N -->|/sta-proxy/| FE[sta-proxy-frontend]
    N -->|/sta/| API[sta-proxy-api]
    API -->|user, permission groups, ingests| DSM[DSM API]
    API -->|public data| FP[frost]
    API -->|internal data| FI[frost-internal]
```

The frontend runs in the browser, so its api calls and opened endpoint URLs pass nginx under `/sta/` as well.

## Layers of the api

A data request passing all layers. The other routes (`endpoints`, `ingests`, `me`, `session`) use the same layers.
See following diagrams for specific use cases.

```mermaid
sequenceDiagram
    participant C as Client
    participant N as nginx
    participant R as routers/<br/>(HTTP)
    participant S as services/<br/>(logic)
    participant CL as clients<br/>(dsm_api, FrostServer)
    participant UP as upstream<br/>(DSM API, FROST)

    C->>N: GET /sta/{endpoint}/v1.1/...
    N->>R: GET /{endpoint}/v1.1/...
    R->>R: validate path,<br/>token from header or cookie
    R->>S: endpoint, query, token
    opt token present, not cached
        S->>CL: fetch own permission groups
        CL->>UP: DSM API: GET /permission-group/
        UP-->>CL: permission groups
        CL-->>S: permission groups (cached for 60 s)
    end
    S->>S: choose public or internal FROST
    S->>CL: forward request
    CL->>UP: FROST: GET /{endpoint}/v1.1/...
    UP-->>CL: data
    CL-->>S: response, headers filtered,<br/>links rewritten (explicit routes only)
    S-->>R: response
    R-->>N: response
    N-->>C: response
```

## Login and session cookie

```mermaid
sequenceDiagram
    actor U as User
    participant FE as sta-proxy-frontend
    participant KC as Keycloak
    participant API as sta-proxy-api
    participant DSM as DSM API

    U->>FE: login
    FE->>KC: OIDC authorization code flow
    KC-->>FE: access token

    Note over FE,API: on login and on every token refresh
    FE->>API: PUT /sta/session (Bearer token)
    API->>DSM: GET /me/ (Bearer token)
    DSM-->>API: user
    API-->>FE: Set-Cookie sta_session (HttpOnly)

    Note over FE,API: on logout or token expiry
    FE->>API: DELETE /sta/session
    API-->>FE: cookie removed
```

## Listing endpoints

```mermaid
sequenceDiagram
    participant FE as sta-proxy-frontend
    participant API as sta-proxy-api
    participant DSM as DSM API
    participant FP as frost

    FE->>API: GET /sta/endpoints (Bearer token)
    API->>FP: endpoint listing
    FP-->>API: endpoints
    API->>DSM: own permission groups (cached)
    DSM-->>API: permission groups
    API-->>FE: endpoints with is_internal and URL
```

## Requesting data

The default route chooses the FROST server by the token.

```mermaid
sequenceDiagram
    participant C as Browser tab or script
    participant API as sta-proxy-api
    participant DSM as DSM API
    participant FI as frost-internal
    participant FP as frost

    C->>API: GET /sta/{endpoint}/v1.1/...<br/>token, session cookie or nothing
    opt token or cookie present
        API->>DSM: own permission groups (cached)
        DSM-->>API: permission groups
    end
    alt endpoint in own permission groups
        API->>FI: forward request (without token)
        FI-->>API: internal data
    else anonymous or not a member
        API->>FP: forward request (without token)
        FP-->>API: public data
    end
    API-->>C: data
```

## Explicit routes

`/public` and `/internal` pin the FROST server. Links in the response are rewritten, so pagination stays on the route.

```mermaid
sequenceDiagram
    participant C as Browser tab or script
    participant API as sta-proxy-api
    participant DSM as DSM API
    participant FI as frost-internal
    participant FP as frost

    C->>API: GET /sta/public/{endpoint}/v1.1/...
    API->>FP: forward request
    FP-->>API: public data
    API-->>C: data with links to /sta/public/...

    C->>API: GET /sta/internal/{endpoint}/v1.1/...<br/>token or session cookie
    API->>DSM: own permission groups (cached)
    DSM-->>API: permission groups
    alt endpoint in own permission groups
        API->>FI: forward request (without token)
        FI-->>API: internal data
        API-->>C: data with links to /sta/internal/...
    else no access
        API-->>C: error, no fallback to public data
    end
```
