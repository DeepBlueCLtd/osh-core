# Security

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Users, roles, hierarchical permissions, the hub security manager, HTTP authentication on the
embedded Jetty server, and the permission checks made by service modules and the admin UI.

| Concern | Main types | Where |
|---|---|---|
| Security manager (registry of pluggable parts) | `org.sensorhub.api.security.ISecurityManager`, `org.sensorhub.impl.security.SecurityManagerImpl` | `sensorhub-core` |
| Users, roles, authorizer | `org.sensorhub.api.security.IUserRegistry`, `org.sensorhub.api.security.IRoleRegistry`, `org.sensorhub.api.security.IAuthorizer`, `org.sensorhub.impl.security.BasicSecurityRealm`, `org.sensorhub.impl.security.DefaultAuthorizerImpl` | `sensorhub-core` |
| Permission model | `org.sensorhub.api.security.IPermission`, `org.sensorhub.api.security.IPermissionPath`, `org.sensorhub.impl.security.*Permission`, `PermissionSetting`, `PermissionRequest` | `sensorhub-core` |
| Per-module checks | `org.sensorhub.impl.module.ModuleSecurity` and subclasses `SOSSecurity`, `SPSSecurity`, `ConSysApiSecurity`, `AdminUISecurity` | core, service-swe, service-consys, webui-core |
| HTTP authentication | `org.sensorhub.impl.service.HttpServer`, `org.sensorhub.impl.service.OshLoginService`, `org.sensorhub.impl.service.HttpLogoutWrapper` | `sensorhub-core` |
| Outgoing HTTP credentials | `org.sensorhub.impl.security.ClientAuth` | `sensorhub-core` |

Source folders:
- API: [`sensorhub-core/.../api/security/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security)
- Implementation: [`sensorhub-core/.../impl/security/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security)
- HTTP side: [`sensorhub-core/.../impl/service/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service) (see also [Comms & network](comms-network.md))

## Key types

### API (`org.sensorhub.api.security`)

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`ISecurityManager`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/ISecurityManager.java#L29) | interface, extends `IAuthorizer` | Javadoc: "Management interface for SensorHub security". Register/unregister one `Authenticator` (Jetty), one `IUserRegistry`, one `IAuthorizer`, and module permission trees. Constant [`ANONYMOUS_USER`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/ISecurityManager.java#L31) = `"anonymous"` |
| [`IAuthorizer`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IAuthorizer.java#L27) | interface | `isAuthorized(IUserInfo, IPermissionPath)` |
| [`IUserInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IUserInfo.java#L30) | interface | `getId()`, `getPassword()`, `getRoles()`, `getAttributes()`; plus allow/deny lists from `IUserPermissions` |
| [`IUserRole`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IUserRole.java#L28) | interface | Javadoc: "Roles are sets of allowed and denied permissions that are associated to users" |
| [`IUserPermissions`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IUserPermissions.java#L20) | interface | `getAllowList()`, `getDenyList()` (read-only `Collection<IPermissionPath>`) |
| [`IUserRegistry`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IUserRegistry.java#L20) / [`IRoleRegistry`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IRoleRegistry.java#L20) | interfaces | `Map<String, IUserInfo>` / `Map<String, IUserRole>` plus `IPermissionUpdates` |
| [`IPermissionUpdates`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IPermissionUpdates.java#L20) | interface | `add/removeAllowPermissions`, `add/removeDenyPermissions` by user or role ID |
| [`IPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IPermission.java#L20) | interface | Tree node: `getName()`, `getParent()`, `getChildren()`, `getFullName()`, `implies(IPermission)`. `WILDCARD = "*"` |
| [`IPermissionPath`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IPermissionPath.java#L20) | interface | `Collection<IPermission>` with `implies(IPermissionPath)` |
| [`IParameterizedPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/IParameterizedPermission.java#L28) | interface | Javadoc: "This is used for temporal and geofencing for instance." |
| [`SecurityConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/SecurityConfig.java#L28) | config class | `enableAccessControl = false`, `requireAuth = true` (see [Configuration](#configuration)) |
| [`SecurityModuleConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/security/SecurityModuleConfig.java#L29) | config class | Javadoc: "Tagging interface to be extended by config classes of security related modules" (it is a class, not an interface) |

### Implementation (`org.sensorhub.impl.security`)

| Type | Role |
|---|---|
| [`SecurityManagerImpl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/SecurityManagerImpl.java#L43) | The only `ISecurityManager`. Holds `AtomicReference`s for user registry and authorizer, an `AuthenticatorWrapper`, and a synchronized `LinkedHashMap` of module permission trees keyed by root name |
| [`BasicSecurityRealm`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/BasicSecurityRealm.java#L42) | Module ("Config Based Security Realm"). Builds `UserStore`/`RoleStore` from config; on start registers them as user registry and a `DefaultAuthorizerImpl` as authorizer |
| [`BasicSecurityRealmConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/BasicSecurityRealmConfig.java#L34) | `users` (`UserConfig`) and `roles` (`RoleConfig`), each with string `allow`/`deny` lists |
| [`DefaultAuthorizerImpl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/DefaultAuthorizerImpl.java#L24) | Role-then-user allow/deny evaluation (see [Authorization](#authorization-decision)) |
| [`AbstractPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/AbstractPermission.java#L31) | Base node. Constructor with a parent [adds itself](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/AbstractPermission.java#L52-L54) to `parent.getChildren()`. `equals`/`hashCode` use `name` only |
| [`ModulePermissions`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ModulePermissions.java#L34) | Root node named `<alias>[<moduleLocalID>]`; [`cloneAsTemplatePermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ModulePermissions.java#L101) deep-clones it as `<alias>[*]` |
| [`ItemPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ItemPermission.java#L31) | Javadoc: "Basic named permission used to build hierarchical permission sets." Supports `item_name[prop=value]` qualifiers |
| [`ItemWithIdPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ItemWithIdPermission.java#L28), [`ItemWithParentPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ItemWithParentPermission.java#L28) | Per-resource nodes used by ConSys: name `<id>` and `<type>[parent=<id>]` |
| [`WildcardPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/WildcardPermission.java#L28) | Javadoc: "Wildcard permission used for "Allow All" and "Deny All" patterns". `implies` always `true` |
| [`PermissionSetting`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/PermissionSetting.java#L23) | A granted path (from config). Implements the path-matching rule |
| [`PermissionRequest`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/PermissionRequest.java#L22) | A requested path: the permission plus all its ancestors. Its own `implies` always returns `false` |
| [`PermissionFactory`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/PermissionFactory.java#L22) | Parses `"a/b/c"` strings into `PermissionSetting`s and back |
| [`ClientAuth`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ClientAuth.java#L34) | `java.net.Authenticator` singleton for outgoing HTTP. Javadoc: "Authenticator used by HTTP clients" |
| `BboxPermission`, `TimeRangePermission` | `IParameterizedPermission` implementations. **No references elsewhere in this repo** (searched all `.java` files) |

## How it works

### Wiring at hub start

- `SensorHub.start()` creates [`new SecurityManagerImpl(this)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L139), exposed by [`ISensorHub.getSecurityManager()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/ISensorHub.java#L61).
- It then calls [`ClientAuth.createInstance("keystore")`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L145), which sets the JVM-wide default `java.net.Authenticator`.
- Access control is "enabled" only when both a user registry and an authorizer are registered: [`isAccessControlEnabled()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/SecurityManagerImpl.java#L71). In this repo only `BasicSecurityRealm` [registers them](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/BasicSecurityRealm.java#L174-L178) (in `doStart`).
- Each register method uses `compareAndSet(null, x)`: a second registration throws `IllegalStateException`, and only the registered instance may unregister itself.

### Permission trees per module

Every `AbstractModule` gets a default [`new ModuleSecurity(this, "all", false)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L122) (disabled). Modules that enforce permissions replace it with a subclass that builds a tree under `rootPerm` and registers it, plus a `<alias>[*]` template clone, with `registerModulePermissions`.

| Subclass | Alias | Enabled by | Tree (children of `<alias>[<id>]`) |
|---|---|---|---|
| [`SOSSecurity`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSSecurity.java#L23) | `sos` | `config.security.enableAccessControl` | `get/{caps,sensor,foi,obs}`, `insert/{sensor,obs}`, `update/{sensor,obs}`, `delete/{sensor,obs}` |
| [`SPSSecurity`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSSecurity.java#L23) | `sps` | `config.security.enableAccessControl` | `get/{caps,sensor,params,task}`, `tasking/{submit,feasibility,update,cancel,reserve,direct}`, `insert sensor`, `update sensor`, `delete sensor`, `connect tasking` |
| [`ConSysApiSecurity`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L43) | `csapi` | `config.security.enableAccessControl` | `{get,list,stream,create,update,delete,*}/{procedures,properties,systems,deployments,fois,datastreams,obs,controls,commands,status}` |
| [`AdminUISecurity`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUISecurity.java#L22) | `webadmin` | always `true` ([`new AdminUISecurity`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIModule.java#L80)) | `view`, `shutdown`, `restart`, `save_config`, `add`, `remove`, `init`, `start`, `stop`, `update_config` |

`AdminUISecurity` also requires the HTTP server to have authentication on: [`isAccessControlEnabled()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUISecurity.java#L63).

### Permission strings and matching

Config strings are parsed by [`PermissionFactory.newPermissionSetting`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/PermissionFactory.java#L26): split on `/`; the first part becomes a `ModulePermissions` (unless `*`), later parts become `ItemPermission` or `WildcardPermission`. Example form: `sos[<moduleLocalID>]/get/obs`, `csapi[*]/get`, `*`.

[`PermissionSetting.implies(request)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/PermissionSetting.java#L44) walks both paths element by element:
- each granted element must `implies` the requested element at the same depth;
- if the grant is **shorter** than the request, the result is `true` (a grant covers all sub-permissions);
- if the request is shorter, the result is `true` only when the remaining grant element is its last one and is a `WildcardPermission`.

Element rules:

| Node | `implies(other)` |
|---|---|
| `ModulePermissions` | [same name, or (`[*]` form) other name starts with `<alias>[`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ModulePermissions.java#L84-L93) |
| `ItemPermission` | Same name; if this name has no `[...]`, the other's `[...]` qualifier is [stripped first](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ItemPermission.java#L57-L62) |
| `WildcardPermission` | Always `true` |

### Authorization decision

[`DefaultAuthorizerImpl.isAuthorized`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/DefaultAuthorizerImpl.java#L36):
1. For each role name of the user, look it up (unknown roles skipped). If that role grants the request, return `true`.
2. Otherwise return whether the user's own lists grant it.

Within one role or user, [`hasPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/DefaultAuthorizerImpl.java#L57) sets match on the first implying allow entry, then clears it on any implying deny entry (deny wins inside one set).

### Where checks are enforced

[`ModuleSecurity.hasPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleSecurity.java#L61) returns `true` without checking when the handler is disabled or access control is off. Otherwise it reads the thread-local user set by [`setCurrentUser`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleSecurity.java#L94); with no user it throws `AccessControlException` ("No user specified"). [`checkPermission`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleSecurity.java#L82) throws `AccessControlException` on refusal.

| Caller | User source | Checks |
|---|---|---|
| `SOSServlet.service` | `req.getRemoteUser()` or `anonymous` ([setCurrentUser](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L245)) | [`rootPerm`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L248) on every request, then one leaf per operation (e.g. `sos_read_obs`, `sos_insert_sensor`) |
| `SPSServlet.service` | same ([setCurrentUser](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L140)) | [`rootPerm`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L143), then per-operation leaves |
| `RestApiServlet` (ConSys) | same ([setCurrentUser](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L128-L134)) | Per resource in `BaseResourceHandler`: [get](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L207), [list](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L244), [create](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L303), [update](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L375), [delete](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L437); `stream` in `ObsHandler`, `CommandHandler`, `CommandStatusHandler`, `ResourceEventsHandler` |
| `AdminUIServlet.service` | `getUserPrincipal()` | [`admin_access`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUIServlet.java#L50) |
| `AdminUI` / `DefaultModulePanel` | thread-local set by servlet | [`admin_access`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUI.java#L163) at init; `osh_shutdown`, `osh_saveconfig`, `module_*` before each action |
| `LandingServlet.hasAccess` | `getUserPrincipal()` | [hard-coded url prefixes](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/LandingServlet.java#L101-L125) mapped to the first registered permission whose name contains `webadmin`, `csapi`, `sos` or `discoveryService` |

ConSys specifics ([`ConSysApiSecurity`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L43)):
- [`checkResourcePermission`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L360) wraps the permission in `ItemWithIdPermission(perm, id)`; [`checkParentPermission`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L375) in `ItemWithParentPermission(perm, parentId)`. `IllegalArgumentException` (bad ID) becomes a 404.
- The [`hasPermission`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L333) override also accepts the request if a `<type>[parent=<ancestorId>]` permission is granted for any ancestor system, found by walking the database (`getParentIds`).
- After a successful create, handlers grant the creating user owner permissions at run time via [`addPermissionsToCurrentUser`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L531) → `IUserRegistry.addAllowPermissions` (e.g. [`SystemHandler.addOwnerPermissions`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemHandler.java#L218)).

### Authentication (inbound HTTP)

`HttpServer.doStart` ([security handler block](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L194-L219)) installs a Jetty `ConstraintSecurityHandler` on the servlet context when `authMethod` is not `NONE`:

| `AuthMethod` | Jetty authenticator |
|---|---|
| `BASIC` | `BasicAuthenticator` wrapped in `HttpLogoutWrapper` |
| `DIGEST` | `DigestAuthenticator` wrapped in `HttpLogoutWrapper` |
| `CERT` | `ClientCertAuthenticator` wrapped in `HttpLogoutWrapper`; HTTPS connector gets a trust store and `setWantClientAuth(true)` |
| `EXTERNAL` | `securityManager.getAuthenticator()` (not wrapped) |

- The login service is [`OshLoginService`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/OshLoginService.java#L31). [`login`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/OshLoginService.java#L98): if the request carries a verified X509 certificate, the user ID is the certificate subject CN and no password is checked; otherwise the stored password is checked with Jetty `Credential.getCredential(stored).check(credentials)`. Roles come from `IUserInfo.getRoles()`. Code comment records that the earlier `CN=` username inference was an "authentication bypass".
- [`addServletSecurity`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L402) adds a constraint mapping (default roles `Constraint.ANY_AUTH`) with `OPTIONS` excluded; it does nothing when no security handler exists (auth `NONE`).
- [`HttpLogoutWrapper.validateRequest`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpLogoutWrapper.java#L64): a servlet path ending in `/logout` invalidates the session, returns 401 and a script redirecting to the same URL with `logout` replaced by `admin`.

### Outgoing credentials (`ClientAuth`)

[`ClientAuth`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/ClientAuth.java#L34) keeps user and password in `InheritableThreadLocal`s. Callers set them before connecting: `SOSTClient`, `SWEVirtualSensor`, `ConSysApiClientModule`. The keystore code in the constructor and `registerCredentials` is commented out.

## Configuration

| Where | Field | Default | Effect in code |
|---|---|---|---|
| `SecurityConfig` (in `SWEServiceConfig.security`, `ConSysApiServiceConfig.security`) | `enableAccessControl` | `false` | Passed as `enable` to the module's `ModuleSecurity` subclass |
| same | `requireAuth` | `true` | Passed to `addServletSecurity(endpoint, requireAuth)` |
| `HttpServerConfig` | `authMethod` | `NONE` | See table above |
| `HttpServerConfig` | `keyStorePath`, `keyStorePassword`, `keyAlias`, `trustStorePath`, `trustStorePassword` | `keyAlias = "jetty"` | Fall back to `javax.net.ssl.*` system properties; values go through `ModuleUtils.expand` |
| `BasicSecurityRealmConfig` | `users[]`, `roles[]` with `allow`/`deny` strings | empty | If both lists are empty, [`setConfiguration`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/BasicSecurityRealm.java#L131) adds role `admin` (allow `*`) and user `admin` / password `test` |
| `BasicSecurityRealm` state files | `user_permissions.json`, `role_permissions.json` | — | Run-time permission additions, saved through the module state manager; entries already in config are not duplicated |

## Observed behaviours to be aware of

1. **`EXTERNAL` auth has no provider in this repo.** Nothing in `src/main` calls `registerAuthenticator`. [`getAuthenticator()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/security/SecurityManagerImpl.java#L169) waits up to `TIMEOUT` (10 s) and then throws, so the `authenticator == null` check in `HttpServer` (line 212) cannot be reached.
2. **The "auth needs a user registry" guard runs only on config update.** [`updateConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/service/HttpServer.java#L100) refuses an auth method when access control is off; `doStart` does not check. With no realm, `OshLoginService` → `getUserRegistry()` fails its `Asserts.checkState`.
3. **Anonymous requests need an `anonymous` user.** Servlets pass `"anonymous"` to `setCurrentUser`; if no such user exists, the thread-local stays empty and an enabled check throws `AccessControlException` ("No user specified").
4. **Run-time checks mutate the registered trees.** `ItemWithIdPermission` / `ItemWithParentPermission` call the `AbstractPermission` constructor, which puts the new node into its parent's `children` (a plain `LinkedHashMap`). Each ConSys check therefore adds entries to the registered `csapi` tree. **Inferred:** the tree grows with the number of distinct IDs checked.
5. **Role grants win over user denies.** `DefaultAuthorizerImpl` returns `true` as soon as any role grants, without reading the user's own deny list; a deny only applies inside the same role or user.
6. **Duplicate child name in `AdminUISecurity`.** `osh_restart` and `module_restart` are both `ItemPermission(rootPerm, "restart")` ([lines 47, 56](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/AdminUISecurity.java#L47-L56)); the second replaces the first in `children`, and a grant on either name matches both.
7. **Dead permission code.** `SOSSecurity.checkPermission(String, IPermission)` has its body commented out; `SPSSecurity.checkPermission(String, IPermission)`, `SOSSecurity.addProcedurePermissions` and `SPSSecurity.addOfferingPermissions` have no callers. `ConSysApiSecurity.DummyModule` and `dsParentsCache` are unused. `ModuleSecurity` has an `unregister()` but its own registration line is commented out.
8. **`SOSWebSocketOut.run` sets the current user and never clears it** ([setCurrentUser](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSWebSocketOut.java#L123)); `SOSServlet` and `SPSServlet` clear it in `finally`.
9. **`ClientAuth` keystore path is inert.** With a user set and no password, `getPasswordAuthentication` dereferences `keyStore`, which is never initialised; the exception is rethrown as `IllegalStateException`.
10. **`isAuthEnabled()`** returns `config.authMethod != AuthMethod.NONE`, so a `null` method counts as enabled.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Add permissions to a service | Subclass `ModuleSecurity`, build `ItemPermission` children of `rootPerm`, register `rootPerm.cloneAsTemplatePermission(...)` and `rootPerm` (as `SOSSecurity`, `ConSysApiSecurity`); assign it to `securityHandler` in `setConfiguration`/`init` |
| Enforce a check in a servlet | `setCurrentUser(remoteUser or ANONYMOUS_USER)` → `checkPermission(...)` → `clearCurrentUser()` in `finally`, as in `SOSServlet.service` |
| Provide users/roles from another source | Implement `IUserRegistry` (+ `IAuthorizer`) in a module and register them in `doStart`, as `BasicSecurityRealm` does |
| Add an HTTP auth method | Extend `HttpServerConfig.AuthMethod` and the `if/else` block in `HttpServer.doStart` |
| Grant permissions at run time | `IUserRegistry.addAllowPermissions(userId, paths)`, as in `BaseResourceHandler.addPermissionsToCurrentUser` |

## Tests

| Test | Covers |
|---|---|
| [`TestBasicSecurityRealm`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/security/TestBasicSecurityRealm.java) | Save/load of run-time permission files; skipping entries added by other modules; truncated/invalid files; failed save keeps file |
| [`TestOshLoginService`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/service/TestOshLoginService.java) | Password login, `CN=` usernames do not bypass passwords, certificate login uses subject CN, null cases |
| [`TestHttpServer`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/service/TestHttpServer.java) | Server start with `NONE`/`BASIC`/`DIGEST`. The `/test` servlet is registered with `requireAuth = false`, so these tests do not show that credentials are enforced |

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.security.TestBasicSecurityRealm'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.service.TestOshLoginService'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.service.TestHttpServer'
```

No tests exist for `DefaultAuthorizerImpl`, `PermissionSetting` matching or any `ModuleSecurity` subclass.

## Related

- [Code map index](../index.md)
- [Comms & network](comms-network.md) (embedded HTTP server, service module base class)
- [Module lifecycle](module-lifecycle.md), [Connected Systems API service](service-consys.md), [SWE services](service-swe.md), [Admin web UI](webui.md)
