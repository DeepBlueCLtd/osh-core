# Connected Systems API Service

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Gradle project `sensorhub-service-consys` ("Connected Systems API"). It contains two hub modules:

| Module | Descriptor (via `META-INF/services`) | Role |
|---|---|---|
| `org.sensorhub.impl.service.consys.ConSysApiService` | `org.sensorhub.impl.service.consys.ConSysApiServiceDescriptor` | HTTP + WebSocket server for OGC API – Connected Systems. Reads from a hub database view, writes through the system transaction handlers |
| `org.sensorhub.impl.service.consys.client.ConSysApiClientModule` | `org.sensorhub.impl.service.consys.client.ConSysApiClientDescriptor` | Pushes local systems, datastreams and observations to a remote ConSys endpoint |

Source folders:
- Main: [`sensorhub-service-consys/src/main/java/.../consys/`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys)
- Tests: [`sensorhub-service-consys/src/test/java/.../consys/`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys)
- Static web assets for HTML output (Bootstrap CSS/JS): `src/main/resources/css`, `src/main/resources/js`

| Package (`...service.consys.`) | Contents |
|---|---|
| (root) | Module, config, servlet, `HandlerContext`, security, errors, `BaseHandler`, `RootHandler`, store wrapper base, `CurieResolver`, `SWECommonUtils` |
| `resource` | Handler/binding base classes, `RequestContext`, `ResourceFormat` |
| `system`, `procedure`, `deployment`, `feature`, `property` | Feature-like resources (GeoJSON / SensorML / HTML) |
| `obs`, `task` | Datastreams + observations; control streams + commands + status/result |
| `event`, `stream` | Resource event streaming base; WebSocket output |
| `home` | Landing page, `/conformance`, `/collections` |
| `sensorml`, `json` | SensorML JSON/XML/HTML helpers; JSON writer filters |
| `client` | Outbound client (`ConSysApiClient`) and client module |

## Key types

| Type | Role (from code / javadoc) |
|---|---|
| [`ConSysApiService`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L69) | Module. Extends `AbstractHttpServiceModule`, so [`doStart()`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L123) runs when the HTTP server module reaches STARTED. Builds the handler tree and deploys the servlet |
| [`ConSysApiServiceConfig`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiServiceConfig.java#L38) | Extends `OGCServiceConfig`. Default `endPoint = "/api"`. Fields: `databaseID`, `exposedResources`, `customFormats`, `security`, `uriPrefixMap`, `threadPoolSize`, and others (see Observed behaviours) |
| [`RestApiServlet`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L51) / [`ConSysApiServlet`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiServlet.java#L21) | Servlet. Each HTTP method runs asynchronously on the service thread pool; maps exceptions to status codes. `ConSysApiServlet` adds nothing |
| [`HandlerContext`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/HandlerContext.java#L50) | Shared by all handlers. Implements `IObsSystemDatabase`, `IdEncoders`; holds read DB, write DB, event bus, one `*StoreWrapper` per store, `CurieResolver` |
| [`AbstractDataStoreWrapper`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/AbstractDataStoreWrapper.java#L49) | Javadoc: "Wrapper to allow reading from federated data store or filtered view while writing to a dedicated store." Reads go to `readStore`, writes to `writeStore` |
| [`IResourceHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/IResourceHandler.java#L21) | `getNames()`, `doGet/doPost/doPut/doDelete(RequestContext)`, `addSubResource(...)` |
| [`BaseHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/BaseHandler.java#L41) | Sub-resource map keyed by name; query-parameter parsers (`f`/`format`, `select`, `id`, time, `bbox`, `geom`, `order`); paging links |
| [`RootHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RootHandler.java#L23) | Root of the tree. Empty path → `HomePageHandler`; POST/PUT/DELETE rejected when the service is read-only |
| [`BaseResourceHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L56) | Generic collection/item logic over one `IDataStore`: list, get, count, create, update, delete, nested routing, permission checks |
| [`ResourceHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/ResourceHandler.java#L46) | Adds filter building from the store's `filterBuilder()` (`id`, `q`) for `ResourceKey` stores |
| [`AbstractFeatureHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/feature/AbstractFeatureHandler.java#L44) | Adds `uid`, `validTime`, `bbox`, `geom`, `featureType`, `p:<prop>` filters; UID/name validation |
| [`RequestContext`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/RequestContext.java#L44) | Per-request state: remaining path (deque), query params, parent `ResourceRef`, chosen `ResourceFormat`, `PropertyFilter`, optional `StreamHandler`, created resource URIs |
| [`ResourceBinding`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/ResourceBinding.java#L35) | Javadoc: "Base class for all resource formatter / parser". `serialize`, `deserialize`, `startCollection`, `endCollection`. Subclassed by `ResourceBindingJson`, `ResourceBindingHtml`, `ResourceBindingXml` |
| [`ResourceFormat`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/ResourceFormat.java#L24) | MIME type + optional short name. Constants for HTML, JSON, GeoJSON, SML JSON/XML, O&M JSON, SWE JSON/XML/binary/CSV, `AUTO` |
| [`ConSysApiSecurity`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L43) | Extends `ModuleSecurity`, implements [`RestApiSecurity`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiSecurity.java#L22). One `ResourcePermissions` set per resource type |
| [`ResourceEventsHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/event/ResourceEventsHandler.java#L34) | Base for `/events` sub-resources; WebSocket-only |
| [`StreamHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/stream/StreamHandler.java#L21) / [`WebSocketOut`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/stream/WebSocketOut.java#L38) | Javadoc: "Output only websocket for sending real-time events and obs data" |
| [`FeatureIdEncoder`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/feature/FeatureIdEncoder.java#L31), [`DataStreamIdEncoder`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamIdEncoder.java#L31), [`CurieResolver`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/CurieResolver.java#L28) | ID decoding that also accepts UIDs and CURIEs (see [ID encoding](#id-encoding)) |
| [`CustomObsFormat`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/CustomObsFormat.java#L27) | Plug-in interface for extra observation formats, loaded by class name from `customFormats` config. No implementation in this repo |

## How it works

### Startup (`ConSysApiService.doStart`)

1. **Write DB** ([lines 129–137](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L129-L137)): the module named by `databaseID` (set to `null` if not open), else the system driver registry's state database.
2. **Read DB** ([lines 140–154](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L140-L154)): with `exposedResources` and a write DB, a `org.sensorhub.impl.database.registry.FilteredFederatedDatabase`; with `exposedResources` only, `exposedResources.getFilteredView(hub)`; otherwise the hub's federated database.
3. Creates `ConSysApiSecurity`, a `ScheduledThreadPool` named `CSApi-Pool` (size = `threadPoolSize`, or CPU count when ≤ 0), loads `customFormats`, fills a `CurieResolver` from `uriPrefixMap` (entries split on space or comma).
4. Creates [`new HandlerContext(...)`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L198) and sets `readOnly = writeDb == null || writeDb.isReadOnly()`.
5. Builds the handler tree ([lines 203–307](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L203-L307)), then [`deploy()`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L315) registers the servlet at `endPoint + "/*"` with `addServletSecurity(..., config.security.requireAuth)`.

### Request routing (handler tree)

`RequestContext` splits `req.getPathInfo()` on `/` into a deque ([`splitPath`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/RequestContext.java#L192)). Each handler pops one element:

- `BaseHandler.getSubResource(ctx)` ([line 111](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/BaseHandler.java#L111)) pops a name and looks it up in `subResources` (filled from each child's `getNames()`).
- `BaseResourceHandler.doGet` ([line 89](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L89)) then decides:

| Remaining path at this handler | GET action |
|---|---|
| empty | `subscribe()` if WebSocket request, else `list()` |
| `{id}` | `getById()` |
| `count` | `getElementCount()` → `{"count":N}` |
| `events` | `subscribeToEvents()` |
| `{id}/{child}/...` | `getSubResource(ctx, id)`: decode id, check `isValidID`, `ctx.setParent(this, id, internalID)`, recurse into child |

POST is allowed only on a collection ([`doPost`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L124)); PUT and DELETE only on `{id}`. Several handlers restrict POST further to a parent type, e.g. `DataStreamHandler` requires a `SystemHandler` parent ([`doPost`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamHandler.java#L83)).

Tree built in `doStart` (`→` = registered sub-resource; the same handler instance is reused under several parents):

| Handler (names) | Mounted under | Children |
|---|---|---|
| `ConformanceHandler` (`conformance`), `CollectionHandler` (`collections`), `JarStaticResourceHandler` (`static`) | root | – |
| `FeatureHandler` (`features`) | root, only if read DB is an `IFeatureDatabase` | – |
| `ProcedureHandler` (`procedures`), `PropertyHandler` (`properties`) | root, only if read DB is an `IProcedureDatabase` | `events` (procedures) |
| `SystemHandler` (`systems`) | root | `subsystems`, `history`, `samplingFeatures`, `datastreams`, `controlstreams`, `events` |
| `SystemMembersHandler` (`subsystems`, `members`) | systems, itself | same as systems |
| `DeploymentHandler` (`deployments`) / `DeploymentMembersHandler` (`subdeployments`, `members`) | root (if store exists) / deployments, itself | `subdeployments`, `events` |
| `FoiHandler` (`samplingFeatures`, `fois`) | root, systems, subsystems | `history`, `observations` |
| `DataStreamHandler` (`datastreams`) | root, systems, subsystems | `schema`, `observations`, `stats`, `events` |
| `ObsHandler` (`observations`) | root, datastreams, fois | – |
| `CommandStreamHandler` (`controlstreams`) | root, systems, subsystems | `schema`, `commands`, `status`, `events` |
| `CommandHandler` (`commands`) | controlstreams | `status`, `result` |

### Traced request: `GET /api/systems/{id}/datastreams`

1. [`RestApiServlet.service`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L144) logs the request; [`doGet`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L152) sets content type `application/json` and calls [`createContext`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L381). Not a WebSocket upgrade, so the [HTTP `RequestContext` constructor](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/RequestContext.java#L121) is used; path deque = `[systems, {id}, datastreams]`.
2. `req.startAsync`, then [`CompletableFuture.runAsync`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L161) on the `CSApi-Pool`: `setCurrentUser(req)` (remote user or anonymous) → `rootHandler.doGet(ctx)`.
3. [`RootHandler.doGet`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RootHandler.java#L39) pops `systems` → `SystemHandler`.
4. `SystemHandler` (inherited `BaseResourceHandler.doGet`) pops `{id}`; path not empty, so [`getSubResource(ctx, id)`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L486) pops `datastreams`, decodes `{id}` with the system `FeatureIdEncoder`, checks [`isValidID`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemHandler.java#L97) and stores the parent ref.
5. `DataStreamHandler.doGet` (inherited): path empty, not streaming → [`list()`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L240):
   - `checkParentPermission(permissions.list, parentId)` ([`ConSysApiSecurity.checkParentPermission`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L375));
   - `offset` (default 0), `limit` (default 100, capped at [10000](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L255));
   - [`ResourceHandler.getFilter`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/ResourceHandler.java#L88) → [`DataStreamHandler.buildFilter`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamHandler.java#L108): `id`, `q`, `validTime`, parent system (with `includeMembers(true)`), `foi`, `observedProperty`, `system`;
   - `parseFormat` (`f`, then `format`, default `AUTO`) → [`DataStreamHandler.getBinding`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamHandler.java#L66): `DataStreamBindingHtml` for HTML or AUTO with `Accept: text/html`, else `DataStreamBindingJson`;
   - `startCollection()`, `dataStore.selectEntries(filter)` (the read DB's datastream store), `skip(offset).limit(limit+1)`, `serialize` each, `endCollection(getPagingLinks(...))` ([`getPagingLinks`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/BaseHandler.java#L427) adds `prev`/`next` links).
6. `finally`: `clearCurrentUser()`, `aCtx.complete()`. Exceptions: `InvalidRequestException` → [`handleInvalidRequestException`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L498) (405/400/404/403/202/500); `SecurityException` → [`handleAuthException`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L532) (auth challenge if anonymous, else 403).

### Formats (bindings)

Each handler's `getBinding(ctx, forReading)` picks the binding from `ctx.getFormat()`. The format comes from `f`/`format` query params on GET ([`parseFormat`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/BaseHandler.java#L165)), or from the request `Content-Type` on POST/PUT. Short names accepted by [`fromShortName`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/ResourceFormat.java#L69): `json`, `geojson`, `sml3`, `sml2`, `html`; anything else is taken as a MIME type.

| Handler | Formats in `getBinding` | Default (`AUTO`) |
|---|---|---|
| systems, procedures | HTML, GeoJSON/JSON, `application/sml+json`, `application/sml+xml` | HTML if `Accept` has `text/html`, else GeoJSON |
| deployments | HTML, GeoJSON/JSON, SML JSON | same |
| samplingFeatures | HTML, GeoJSON/JSON (`DynamicFoiBindingGeoJson` when `snapshot` param present) | same |
| features | GeoJSON/JSON only | GeoJSON |
| properties | HTML, JSON, `text/turtle` | HTML or JSON |
| datastreams, controlstreams | HTML, JSON | HTML or JSON |
| `.../schema` | `obsFormat`/`cmdFormat` param: JSON/O&M JSON, `logical` (datastreams), any `application/swe+*` | O&M JSON schema |
| observations | custom format → JSON/O&M JSON (`ObsBindingOmJson`) → else `ObsBindingSweCommon` | SWE binary if datastream encoding is binary, else JSON ([`getBinding`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L96)) |
| commands | JSON, else `CommandBindingSweCommon` | JSON |

SWE Common sub-format → encoding mapping: [`SWECommonUtils.getEncoding`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/SWECommonUtils.java#L86). `swe+csv`, `text/plain`, `text/csv` → text; `swe+json`, `json` → JSON; `swe+xml`, `text/xml` → XML; `swe+binary` → native or default binary. Non-binary output is refused when the binary encoding has a `BinaryBlock` member.

Custom observation formats: [`getCustomFormatBinding`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L159) is tried first when a single datastream is targeted. With `AUTO` and a browser `User-Agent` (Firefox/Chrome/Safari, not streaming) the first compatible custom format is chosen; otherwise the one registered for the requested MIME type.

### ID encoding

- Public IDs are produced by the hub's `IdEncoders` (`ISensorHub.getIdEncoders()`): `org.sensorhub.impl.common.IdEncodersBase32` (one encoder for all types) or `org.sensorhub.impl.common.IdEncodersDES` when secure IDs are enabled ([hub start-up code](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L142)).
- `HandlerContext` wraps them for systems, procedures, deployments, FOIs ([`getFoiIdEncoder`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/HandlerContext.java#L286)) in `FeatureIdEncoder`, and for datastreams/control streams in `DataStreamIdEncoder`/`CommandStreamIdEncoder`.
- [`FeatureIdEncoder.decodeID`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/feature/FeatureIdEncoder.java#L54): if the string contains `:` or `[`, expand it as a CURIE and look up the current version by UID; else delegate.
- [`DataStreamIdEncoder.decodeID`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamIdEncoder.java#L54): same, but splits the URI at the last `:` into system UID + output name (comment: "datastream CURIEs must be of the form [prefix:sysName:outputName]").
- [`CurieResolver.expand`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/CurieResolver.java#L46): matches `[prefix:ref]`, maps the whole CURIE first, then the prefix.
- List filters accept either local IDs or URIs but not both ([`parseResourceIdsOrUids`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/BaseHandler.java#L218), 400 "cannot mix").

### Real-time streaming

See [Event bus](event-bus.md) for topics and subscription semantics.

- A WebSocket upgrade is detected in [`createContext`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/RestApiServlet.java#L384); a `WebSocketOut` becomes the context's `StreamHandler`, and `ctx.isStreamRequest()` is true.
- Handlers register a start callback; `WebSocketOut.onWebSocketConnect` ([line 55](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/stream/WebSocketOut.java#L55)) runs it. Incoming text/binary frames close the session ([`onWebSocketText`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/stream/WebSocketOut.java#L96)).
- **Observations** ([`ObsHandler.subscribe`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L222)): requires `permissions.stream` and a parent datastream. Real-time when no time filter, or a time filter that begins `now`; then [`startRealTimeStream`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L268) subscribes to `getDataStreamDataTopicID(dsInfo)` with `newSubscription(ObsEvent.class)` and `request(Long.MAX_VALUE)`. If the phenomenon or result time filter is a "latest" filter, the latest stored obs is sent first (with a one-shot dedup). Otherwise [`startReplayStream`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L369) reads from the store in batches of 100 on a 10 ms fixed-delay task, paced by `replaySpeed`.
- **Commands** ([`CommandHandler.startRealTimeStream`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/task/CommandHandler.java#L204)): if the user has `command_status_permissions.create`, connects as the command receiver via `connectCommandReceiver` ([line 276](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/task/CommandHandler.java#L276)); else subscribes to the command data topic. Details: [Commands](commands.md).
- **Resource events** (`/events`): [`ResourceEventsHandler.doGet`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/event/ResourceEventsHandler.java#L126) checks `permissions.stream`, requires a WebSocket, and calls the subclass `subscribe`. `SystemEventsHandler` ([`subscribe`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemEventsHandler.java#L42)) uses `systems/{uid}/status` or `systems/`; `DataStreamEventsHandler` and `CommandStreamEventsHandler` do the same for their event types.
- **MQTT:** `RequestContext` has two constructors taking a `URI` for "other protocols ... (e.g. MQTT publish/subscribe)" ([line 159](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/RequestContext.java#L159), [line 177](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/RequestContext.java#L177)). No caller exists in this repository. **Inferred:** an MQTT front end lives in another repository.

### Transactional writes

- Generic paths in `BaseResourceHandler`: [`create`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L296) (loop `deserialize` → `validate` → `addEntry` → `addOwnerPermissions`, then `commit()`), [`update`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L369), [`delete`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L431). `DataStoreException` → 400 "request rejected".
- The servlet returns 201 with `Location` for one created resource, or a JSON array of URIs for several; 204 for PUT/DELETE.
- Systems, subsystems, datastreams, observations and commands go through `org.sensorhub.impl.system.SystemDatabaseTransactionHandler` built on the **write DB** and the event bus, so changes also publish events (see [System registry](system-registry.md)):
  - [`SystemHandler.addEntry`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemHandler.java#L159): wraps SensorML in `SmlFeatureWrapper` (hide outputs/taskable params), `addSystemOrReturnExisting`, then `SystemUtils.addDatastreamsFromOutputs`. DELETE honours `cascade=true` ([line 210](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemHandler.java#L210)).
  - [`DataStreamHandler.addEntry`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamHandler.java#L166): `getSystemHandler(parent).addOrUpdateDataStream(res)`.
  - [`ObsHandler.addEntry`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L559): `DataStreamTransactionHandler.addObs(IObsData)`.
  - [`CommandHandler.addEntry`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/task/CommandHandler.java#L375): `submitCommand(...)` waits up to the request timeout for a status and writes it in the response. It uses a handler on the **read** DB; code comment: "I know the doc says otherwise but we need to use the federated DB for command transactions here".
- Other feature types (procedures, deployments, features, properties) write directly to the store wrappers ([`AbstractFeatureHandler.addEntry`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/feature/AbstractFeatureHandler.java#L240)).

### Security

See [Security](security.md) for `ModuleSecurity` and permission classes.

- [`ConSysApiSecurity` constructor](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L111) registers a tree `csapi/{get,list,stream,create,update,delete}/{procedures,properties,systems,deployments,fois,datastreams,obs,controls,commands,status}` plus an "All Ops" wildcard, and a template copy named "ConSys API Services".
- Handlers call `checkResourcePermission(perm, id)` (wrapped in `ItemWithIdPermission`) for get/update/delete and `checkParentPermission(perm, parentId)` (`ItemWithParentPermission`) for list/create.
- [`hasPermission`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L333) also grants a permission if it is held on any ancestor system ([`getParentIds`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L264) walks system parents of datastreams, control streams, FOIs).
- On create, `addOwnerPermissions` gives the creating user all-ops on the new resource and its children ([`SystemHandler.addOwnerPermissions`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemHandler.java#L218)), only if access control is enabled.

### Client module

- [`ConSysApiClientModule`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/client/ConSysApiClientModule.java#L38): [`doStart`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/client/ConSysApiClientModule.java#L109) checks the endpoint returns 200, registers top-level systems from `dataSourceSelector`, their subsystems, datastreams and FOIs, then subscribes to `systems/` events and, per datastream, to its data topic ([`startStream`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/client/ConSysApiClientModule.java#L385), via `consume(...)`), pushing each obs with `client.pushObs`.
- [`ConSysApiClient`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/client/ConSysApiClient.java#L108): async (`CompletableFuture`) methods for properties, procedures, systems, sampling features, datastreams, control streams, obs and commands. Uses `java.net.http.HttpClient` when available, else a fallback (comment: "Will not be available on Android"). It reuses the server-side bindings via client-side `RequestContext` constructors ([line 85](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/RequestContext.java#L85)).

## Observed behaviours to be aware of

1. **`HandlerContext` rejects a null write DB.** Its constructor calls [`Asserts.checkNotNull(writeDb)`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/HandlerContext.java#L74), but `doStart` sets `writeDb = null` when the configured database is not open and then computes `readOnly = writeDb == null || ...`. **Open question:** the `writeDb != null ? ... : null` branches in `HandlerContext` and the read-only-without-DB case look unreachable.
2. **Unused config fields.** `enableTransactional`, `maxResponseLimit`, `defaultLiveTimeout` (desc mentions "SOS-T") and `virtualSystemGroup` in the [config class](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiServiceConfig.java#L42-L75) are not read anywhere in the repo. Page size is capped by the hard-coded 10000 in `list()`. Write access is controlled only by DB writability.
3. **Write methods on some handlers do not throw.** `ResourceEventsHandler.doPost/doPut/doDelete` ([line 146](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/event/ResourceEventsHandler.java#L144-L147)) and `JarStaticResourceHandler` call `ServiceErrors.unsupportedOperation("")` without `throw`, so the request completes with no error. **Open question.**
4. **Procedure and deployment events are empty stubs.** [`ProcedureEventsHandler.subscribe`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/procedure/ProcedureEventsHandler.java#L36) and `DeploymentEventsHandler.subscribe` have empty bodies; `ProcedureEventBindingJson` and `DeploymentEventBindingJson` are unused.
5. **Some ID parameters are decoded with the handler's own encoder.** [`BaseHandler.parseResourceIds`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/BaseHandler.java#L193) ignores its `idEncoder` argument and calls `this.decodeID`. Affected: `foi` on datastreams ([line 130](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/DataStreamHandler.java#L130)), `stream` on commands, and the `foi` param when POSTing obs ([line 121](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L121)). `getFoiIdEncoder` delegates to `getSystemIdEncoder()`. With `IdEncodersBase32` all encoders are the same, so this only matters with `IdEncodersDES`. **Open question.**
6. **`count` has no permission check.** [`getElementCount`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/BaseResourceHandler.java#L470) does not call the security handler, unlike `list()`.
7. **`JarStaticResourceHandler` serves any classpath resource** under `/static/...`: the path minus `/static` goes straight to [`getResourceAsStream`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/resource/JarStaticResourceHandler.java#L42), without a directory restriction or permission check.
8. **Dead branch in `FeatureHandler.getBinding`.** `AUTO` is replaced by GeoJSON before the `AUTO && isBrowserHtmlRequest()` test ([lines 58–61](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/feature/FeatureHandler.java#L58-L61)), so `FeatureBindingHtml` is never returned.
9. **`p:` predicate dedup is a no-op.** `processedParams` is created inside the loop ([line 105](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/feature/AbstractFeatureHandler.java#L105)).
10. **Obs PUT/DELETE bypass the transaction handler.** [`ObsHandler.updateEntry`/`deleteEntry`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/obs/ObsHandler.java#L573-L593) write to the observation store directly, so no event is published (POST does publish).
11. **Dead / unused code** (grep of all `.java` files): `FeatureMembersHandler`, `FeatureHistoryHandler`, `FeatureCollectionBindingGeoJson`, `ObjectPatchJsonWriter`, `IResourceEventListener`, `UnauthorizedAccessException`; `ConSysApiSecurity.DummyModule`, field `authorizer`, and `dsParentsCache` (only used in commented-out code, [line 329](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiSecurity.java#L329)); `CustomObsFormat.getSchemaBinding` is never called; the `ObsStatsHandler` root/FOI mounts are commented out. `ConSysApiClientModule.isConnected()` always returns `false` ([line 427](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/client/ConSysApiClientModule.java#L427)).
12. **Conformance list vs code.** `CONF_CLASSES` ([line 74](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L74)) declares `.../conf/mqtt`, but this module has no MQTT code (see Streaming).

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Add a resource type | Subclass `ResourceHandler` (or `AbstractFeatureHandler` for features) with `NAMES`, `getBinding`, `buildFilter`, `getKey`, `isValidID`, `validate`, optional `addEntry/updateEntry/deleteEntry`, as in `PropertyHandler` / `DataStreamHandler`. Add a `ResourcePermissions` set in `ConSysApiSecurity`, a store wrapper + getter in `HandlerContext`, and mount it with `addSubResource` in `ConSysApiService.doStart` |
| Add a format | Add a `ResourceFormat` constant (and short name in `fromShortName` if needed), a `ResourceBindingJson`/`ResourceBindingHtml`/`ResourceBinding` subclass, and a branch in the handler's `getBinding`, e.g. `SystemBindingSmlXml` in `SystemHandler.getBinding`. For obs-only formats: implement `CustomObsFormat` and list it in `customFormats` |
| Add a query parameter | Parse it in the handler's `buildFilter` (or `getFilter` for `ObsHandler`/`CommandHandler`) with a `BaseHandler.parseXxxArg` helper and set it on the filter builder, e.g. `observedProperty` in `DataStreamHandler.buildFilter` |
| Add an `/events` stream | Subclass `ResourceEventsHandler`, implement `subscribe` as in `SystemEventsHandler`, register it in the parent handler's constructor and override `subscribeToEvents` |
| Add a nested resource | `parent.addSubResource(child)` in `doStart`; read the parent with `ctx.getParentRef()` / `ctx.getParentID()` in the child's filter |

## Tests

JUnit tests start a hub with an H2 database and the service at `/api` ([`AbstractTestApiBase`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/AbstractTestApiBase.java#L51)) and call it over HTTP.

| Test class | Covers |
|---|---|
| [`TestSystems`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestSystems.java), [`TestProcedures`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestProcedures.java), [`TestDeployments`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestDeployments.java) | Shared feature CRUD/search tests from [`AbstractTestAllFeatures`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/AbstractTestAllFeatures.java) / `AbstractTestAllSmlFeatures` |
| [`TestFois`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestFois.java), [`TestDataStreams`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestDataStreams.java), [`TestControlStreams`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestControlStreams.java), [`TestObservations`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestObservations.java) | Per-resource CRUD and filters |
| [`TestObservationsWs`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestObservationsWs.java), [`TestApiObsWs`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestApiObsWs.java) | WebSocket historical replay. The two files differ only in class name |
| [`TestApiAccessControl`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestApiAccessControl.java) | Its only test method is empty |
| `client/TestClient*` | Client tests. Excluded from the Gradle `test` task ([build file](../../../sensorhub-service-consys/build.gradle#L16)) |

`demodata/*` (e.g. `IngestDemoData` with a `main`) are data-loading programs, not tests.

```bash
./gradlew :sensorhub-service-consys:test
./gradlew :sensorhub-service-consys:test --tests 'org.sensorhub.impl.service.consys.TestDataStreams'
```

## Related

- [Code map index](../index.md)
- [Event bus](event-bus.md) – topics used for streaming
- [Security](security.md), [System registry](system-registry.md), [Commands](commands.md), [Databases](databases.md), [Module lifecycle](module-lifecycle.md), [SWE services](service-swe.md)
