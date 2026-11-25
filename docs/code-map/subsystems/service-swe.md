# SWE Services (SOS / SPS)

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Gradle project `sensorhub-service-swe` ([`build.gradle`](../../../sensorhub-service-swe/build.gradle): "Implementation of OGC SWE standard interfaces as OSH services and virtual sensors"). It contains:

| Area | Package | What it is |
|---|---|---|
| SOS service | `org.sensorhub.impl.service.sos` | OGC Sensor Observation Service 2.0 module + servlet, data providers, async serializers |
| SPS service | `org.sensorhub.impl.service.sps` | OGC Sensor Planning Service 2.0 module + servlet, tasking connectors |
| Shared base | `org.sensorhub.impl.service.swe` | `SWEService`, `SWEServlet`, configs, OSGi `Activator` |
| SOS-T client | `org.sensorhub.impl.client.sost` | Module that pushes local systems/observations to a remote SOS (InsertSensor / InsertResult) |
| SOS / SPS clients | `org.sensorhub.impl.client.sos`, `.client.sps` | Plain client classes used by the virtual sensor |
| Virtual sensor | `org.sensorhub.impl.sensor.swe` | `SWEVirtualSensor`: a sensor driver that reads from a remote SOS and tasks a remote SPS |

OGC request/response classes (`GetResultRequest`, `SOSServiceCapabilities`, `OWSServlet`, ...) come from `lib-ogc` (`ogc-services-sos`, `ogc-services-sps`, `ogc-services-common`); see [OGC libraries](lib-ogc.md).

Modules are registered through [`META-INF/services/org.sensorhub.api.module.IModuleProvider`](../../../sensorhub-service-swe/src/main/resources/META-INF/services/org.sensorhub.api.module.IModuleProvider): `SOSServiceDescriptor`, `SPSServiceDescriptor`, `SOSTClientDescriptor`, `SWEVirtualSensorDescriptor`.

## Key types

### Shared base (`org.sensorhub.impl.service.swe`)

| Type | Role (from code / javadoc) |
|---|---|
| [`SWEService`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEService.java#L41) | Javadoc: "Base abstract class for both SOS and SPS service modules". Extends `AbstractHttpServiceModule`. Holds `readDatabase`, `writeDatabase`, a `ScheduledThreadPoolExecutor` |
| [`SWEServlet`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L72) | Extends `org.vast.ows.server.OWSServlet` (lib-ogc). Implements GetCapabilities, InsertSensor, UpdateSensor, DeleteSensor shared by SOS and SPS; owns a Jetty `WebSocketServletFactory` |
| [`SWEServiceConfig`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServiceConfig.java#L32) | `databaseID`, `exposedResources` (`ObsSystemDatabaseViewConfig`), `security`, `enableTransactional`, `virtualSensorGroup` |
| [`OfferingConfig`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/OfferingConfig.java#L28) | Base of per-system provider/connector configs: `name`, `description`, `enabled` |
| [`Activator`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/Activator.java#L23) | OSGi activator; calls `SOSUtils.loadRegistry()` with the bundle classloader |

### SOS (`org.sensorhub.impl.service.sos`)

| Type | Role |
|---|---|
| [`SOSService`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSService.java#L35) | Module. `doStart()` creates a `TimeOutMonitor` and a `SOSServlet`, then deploys it |
| [`SOSServlet`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L101) | Request dispatch, capabilities generation, provider/serializer selection, transactional ops |
| [`SOSServiceConfig`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServiceConfig.java#L32) | `customDataProviders`, `customFormats`, `maxObsCount` (100), `maxRecordCount` (100000), `maxFois`, `defaultLiveTimeout` (10 s), `templateTimeout` |
| [`ISOSAsyncDataProvider`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/ISOSAsyncDataProvider.java#L43) | Provider API: `getResultTemplate`, `getResults`, `getObservations`, `getProcedureDescriptions`, `getFeaturesOfInterest` — all push to a `Flow.Subscriber` |
| [`SOSProviderConfig`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSProviderConfig.java#L25) | Abstract per-system config; `systemUID`, abstract `createProvider(service, request)` |
| [`SystemDataProviderConfig`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SystemDataProviderConfig.java#L35) | Only concrete `SOSProviderConfig`. Chooses Streaming vs Historical provider per request |
| [`SystemDataProvider`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SystemDataProvider.java#L64) | Abstract base. Builds `ObsFilter` from request; DB-backed `StreamSubscription` (batched pull from a `Stream`) |
| [`HistoricalDataProvider`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/HistoricalDataProvider.java#L46) | Javadoc: fetches from an `IObsSystemDatabase`. Supports replay |
| [`StreamingDataProvider`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/StreamingDataProvider.java#L53) | Javadoc: "stream real-time observations from a system using the event-bus" |
| [`GetObsMultiProviderSubscriber`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/GetObsMultiProviderSubscriber.java#L31) | Chains several providers for one GetObservation response |
| [`TimeOutMonitor`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/TimeOutMonitor.java#L33) | Periodic task on the service thread pool that runs registered timeout checks |
| [`CapabilitiesUpdater`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/CapabilitiesUpdater.java#L36) | `updateOfferings()`: one offering per system in `readDatabase` |
| [`SOSProviderUtils`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSProviderUtils.java#L43) | `isFutureTimePeriod`, `isReplayRequest`, `getReplaySpeed`, `buildObservation`, output URI helpers |
| [`SOSSecurity`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSSecurity.java#L23) | Permission tree `get/{caps,sensor,foi,obs}`, `insert/...`, `update/...`, `delete/...` |
| [`SOSWebSocketOut`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSWebSocketOut.java#L37), [`SOSWebSocketIn`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSWebSocketIn.java#L36) | WebSocket endpoints for GetResult (out) and InsertResult (in) |
| [`IAsyncResponseSerializer`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/IAsyncResponseSerializer.java#L35), [`AbstractAsyncSerializer`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/AbstractAsyncSerializer.java#L43) | Serializers are `Flow.Subscriber`s + servlet `WriteListener`s. Concrete: `ObsSerializerXml/Json`, `ProcedureSerializerXml/Json`, `ResultSerializerXml/Text/Json/Binary`, `ResultTemplateSerializerXml/Json`, `FeatureSerializerGml/GeoJson` |

### SPS (`org.sensorhub.impl.service.sps`)

| Type | Role |
|---|---|
| [`SPSService`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSService.java#L36) | Module; `doStart()` creates and deploys `SPSServlet` |
| [`SPSServlet`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L79) | Dispatch, Submit, DirectTasking/ConnectTasking sessions, InsertTaskingTemplate |
| [`ISPSConnector`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/ISPSConnector.java#L36) | `getTaskingParams`, `sendCommand`, `startDirectTasking`, `subscribeToCommands` |
| [`SystemTaskingConnector`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SystemTaskingConnector.java#L48) | Only `ISPSConnector` implementation; sends commands via `CommandStreamTransactionHandler` |
| [`SPSSecurity`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSSecurity.java#L23) | Permissions `get/...`, `tasking/{submit,feasibility,update,cancel,reserve,direct}`, `insert sensor`, ... |

### Clients

| Type | Role |
|---|---|
| [`SOSTClient`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L91) | `IClientModule`; mirrors a filtered DB view to a remote SOS-T |
| [`SOSTClientConfig`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClientConfig.java#L33) | `dataSourceSelector`, `sos` (HTTP), `connection.usePersistentConnection`, `maxQueueSize` (10), `maxConnectErrors` (10) |
| [`SOSClient`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sos/SOSClient.java#L75), [`SPSClient`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sps/SPSClient.java#L39) | Used only by `SWEVirtualSensor` (and `TestSOSClient`) |
| [`SWEVirtualSensor`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/sensor/swe/SWEVirtualSensor.java#L51) | `AbstractSensorModule`; one `SWEVirtualSensorOutput` per remote observed property, `SWEVirtualSensorControl` per SPS tasking param |

## How it works

### Module start and database selection

[`SWEService.doStart()`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEService.java#L53):
1. `writeDatabase` = module `config.databaseID`, else the system-state DB from `getSystemDriverRegistry().getSystemStateDatabase()`.
2. `readDatabase`:
   - if `getResourceFilter()` returns a filter and a write DB exists → `FilteredFederatedDatabase(filter, writeDatabase.getDatabaseNum())` (code comment: "make sure we always expose its content ... by flagging it as unfiltered");
   - if a filter exists but no write DB → `config.exposedResources.getFilteredView(hub)`;
   - otherwise the hub's federated database.
3. Thread pool: `ScheduledThreadPoolExecutor(availableProcessors)` named [`SOSPool`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEService.java#L103) (same name for SPS).
4. Subclass deploys its servlet via [`deploy()`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEService.java#L127) (`httpServer.deployServlet` + `addServletSecurity(endPoint, requireAuth)`).

`SOSService.getResourceFilter()` ([source](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSService.java#L62)): `exposedResources.getObsFilter()`, else a system-UID filter built from `customDataProviders`, else `null`. SPS does the same with `CommandFilter` and `customConnectors`.

The servlet creates a `SystemDatabaseTransactionHandler` on `writeDatabase` ([constructor](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L99-L101)) used by all transactional operations.

### SOS request dispatch

[`SOSServlet.service()`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L235) sets the current user, checks `rootPerm`, then either accepts a WebSocket upgrade (GetResult → `SOSWebSocketOut`; InsertResult → handled inline; others rejected) or delegates to `OWSServlet.service()`, which parses and calls [`handleRequest(OWSRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L299).

| Operation | Handler | Permission | Behaviour |
|---|---|---|---|
| GetCapabilities | [`SWEServlet.handleRequest`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L109) | `sos_read_caps` | Async on thread pool; refreshes offerings at most every [`GET_CAPS_MIN_REFRESH_PERIOD`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L75) = 200 ms; rewrites endpoint URLs if server base URL contains `://localhost` |
| DescribeSensor | [`handleRequest(DescribeSensorRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L351) | `sos_read_sensor` | SensorML XML or JSON serializer; `getProcedureDescriptions` on provider |
| GetObservation | [`handleRequest(GetObservationRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L390) | `sos_read_obs` | procedures ∩ offerings; O&M XML/JSON; providers chained by `GetObsMultiProviderSubscriber` |
| GetResultTemplate | [`handleRequest(GetResultTemplateRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L437) | `sos_read_obs` | XML or JSON template serializer |
| GetResult | [`handleRequest(GetResultRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L512) | `sos_read_obs` | Template first, then serializer by format (XML/text/JSON/binary/custom/default by encoding); async timeout set to 0 for streaming or replay |
| GetFeatureOfInterest | [`handleRequest(GetFeatureOfInterestRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L586) | `sos_read_foi` | Always uses the default provider; GML or GeoJSON |
| InsertSensor / UpdateSensor / DeleteSensor | [`handleRequest(InsertSensorRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L169) and following | `sos_insert_sensor` etc. | `SystemWrapper(...).hideOutputs().hideTaskableParams().defaultToValidFromNow()` → `transactionHandler.addOrUpdateSystem`; datastreams/command streams created from SensorML outputs / taskable params |
| InsertObservation | [`handleRequest(InsertObservationRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L646) | `sos_insert_obs` | Always throws "InsertObservation not supported yet. Please use InsertResult." (`// TODO`) |
| InsertResultTemplate | [`handleRequest(InsertResultTemplateRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L663) | `sos_insert_sensor` | Reuses a datastream whose struct compatibility hash matches ([`findCompatibleDatastream`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L823)), else new output name from id/label or `outputNN`. Template ID = `procUID#outputName` |
| InsertResult | [`handleRequest(InsertResultRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L737) | `sos_insert_obs` | Parses records with `SWEHelper.createDataParser` and calls `DataStreamTransactionHandler.addObs` per block; WebSocket variant uses `SOSWebSocketIn` |

Transactional operations require `enableTransactional` **and** a non-null `writeDatabase` ([`checkTransactionalSupport`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L989)).

### Data provider selection

```
SOSServlet.getDataProvider(procUID, req)
  ├─ providerConfigs.get(procUID) != null → config.createProvider(service, req)
  └─ else getDefaultDataProvider(req) → new SystemDataProviderConfig{liveDataTimeout = defaultLiveTimeout}
SystemDataProviderConfig.createProvider(service, req)
  ├─ GetResult/GetObservation with isFutureTimePeriod(time) → StreamingDataProvider
  └─ otherwise                                              → HistoricalDataProvider
```

- [`createProvider`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SystemDataProviderConfig.java#L55); [`isFutureTimePeriod`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSProviderUtils.java#L85) = `time.beginsNow() && !time.isNow()`.
- [`getObsFilter`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SystemDataProvider.java#L344) maps the request time: `null` → all times; `isNow()` → `withCurrentTime()` (latest record); else `withRange(begin, end)`.
- The request time comes from `FESRequestUtils.filterToTimeExtent` ([source](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/fes/FESRequestUtils.java#L47)), which reads only the operand's time primitive; the operator and property name are not inspected.

### Historical provider (DB query)

- [`getObservations`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/HistoricalDataProvider.java#L151) / [`getResults`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/HistoricalDataProvider.java#L190): count matching obs first; if `>= maxObsCount` (GetObservation) or `>= maxRecordCount` (GetResult) throw `response_too_big_code`.
- Results are pulled from `database.getObservationStore().select(obsFilter)` through a `StreamSubscription` (batch size 100).
- **Replay**: if `replayspeed` extension is present and the time has a begin, a [`StreamReplaySubscription`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/HistoricalDataProvider.java#L54) is used. A fixed-delay task (every 10 ms on the service pool) sends the next obs only when `(phenomenonTime − requestStart) ≤ (wallclock elapsed × replaySpeed)`. Code comment: "instead of letting replay threads wait ... use a pool of timers running at fixed frequency".

### Streaming provider (event bus)

[`subscribeAndProcessDataEvents`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/StreamingDataProvider.java#L175):
1. Topics = `EventUtils.getDataStreamDataTopicID(sysUID, outputName)` for each selected datastream (see [Event bus](event-bus.md#topic-naming)).
2. If the time filter is `null` or `isNow()` → [`sendLatestRecordsOnly`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/StreamingDataProvider.java#L320) (DB query with `TimeExtent.now()`, then `onComplete`).
3. Otherwise `eventBus.newSubscription(ObsEvent.class).withTopicIDs(topics).subscribe(...)` with a wrapping subscription:
   - on the first `request(n)`, [`sendLatestRecords`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/StreamingDataProvider.java#L348) sends the latest DB record of each datastream (code comment: "TODO send only n records, not all of them"), then registers a timeout check with `TimeOutMonitor`;
   - [`onNext`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/StreamingDataProvider.java#L282) completes the stream when the first obs time stamp exceeds the request end time (GetResult only: "this only works for GetResult for now"), filters by FOI internal IDs, and requests 1 more for rejected events;
   - the timeout check cancels and completes when no event arrived for `liveDataTimeout` seconds.

### SPS

- [`SPSServlet.handleRequest(OWSRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L260) dispatches GetCapabilities, DescribeSensor, DescribeTasking, GetStatus, Submit, DirectTasking, ConnectTasking, InsertSensor, InsertTaskingTemplate. GetFeasibility, Update, Cancel, Reserve, Confirm, DescribeResultAccess throw `unsupported_op_code`.
- Commands are submitted through a second transaction handler on `readDatabase` ([`commandTxnHandler`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L122)). Code comment: "I know the doc says otherwise but we need to use the federated DB for command transactions here".
- Submit ([`handleRequest(SubmitRequest)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L488)) → `getConnector(procUID)` → [`SystemTaskingConnector.sendCommand`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SystemTaskingConnector.java#L145) → `CommandStreamTransactionHandler.submitCommand(...)`; the response is sent when the returned `ICommandStatus` future completes.
- DirectTasking creates a receive session; ConnectTasking (WebSocket only) streams commands in (`SPSWebSocketIn`) or, for sessions created by InsertTaskingTemplate, out (`SPSWebSocketOut`) via [`subscribeToCommands`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SystemTaskingConnector.java#L185), which always acks `CommandStatus.completed` (comment: "for now, we cannot get feedback from the remote system").

### SOS-T client

[`SOSTClient`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L91):
1. `doInit`: DB view from `config.dataSourceSelector.getFilteredView(hub)`; a `RobustIPConnection` whose `tryConnect` checks TCP then fetches capabilities.
2. [`doStart`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L244): once connected, [`subscribeToRegistryEvents`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L318) (`systems/` topic) and registers every selected system: InsertSensor, then InsertResultTemplate per datastream.
3. [`startStream`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L585) subscribes to the datastream data topic with `request(Long.MAX_VALUE)` and first sends the latest DB record.
4. [`handleEvent(ObsEvent)`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L704): stops the stream after `maxConnectErrors`; purges the queue when it reaches `maxQueueSize`; otherwise sends either a new InsertResult POST per ≥10 buffered records ([`sendAsNewRequest`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L844)) or into one persistent HTTP connection ([`sendInPersistentRequest`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/client/sost/SOSTClient.java#L898)).

## Temporal filtering vs legacy doc

Compared with [`sos-temporal-filtering.md`](../../../sensorhub-service-swe/src/site/markdown/sos-temporal-filtering.md) (legacy Maven-site page):

| Legacy doc says | Code | Status |
|---|---|---|
| `phenomenonTime,now` → latest observation | `isNow()` → `withCurrentTime()` in `getObsFilter` | Matches |
| `start/now` → historical up to latest | Not `beginsNow` → `HistoricalDataProvider` | Matches |
| `now/end` → real-time stream closed when an obs later than end arrives | `StreamingDataProvider`; stop check only when `selectedDataStream != null` (GetResult) | **Open question:** for GetObservation the end time is not checked; stream ends only by timeout |
| Real-time available only if sampling period below a threshold | Live stream ends after `liveDataTimeout` (default 10 s) without events | **Open question:** doc describes a period threshold, code uses an inactivity timeout |
| Only TEquals and During, only on `phenomenonTime` | `filterToTimeExtent` ignores operator and property; capabilities advertise only `During` ([capabilities code](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L212-L214)) | **Open question:** other operators/properties are not rejected |
| Past-to-future period "not supported for now"; closed after latest obs | Goes to `HistoricalDataProvider` (range query), no switch to live | Consistent with note (3) only in the "no streaming" case |
| Replay pauses "the SOS data provider thread" | Fixed-rate 10 ms timer, no sleeping thread | **Open question:** mechanism differs from doc |
| `replaySpeed` has no effect for live requests | Replay only in `HistoricalDataProvider`; but `SOSServlet` still sets async timeout 0 when `replayspeed` present | Matches for data; timeout side-effect not in doc |
| SOS subscription service: "TODO" | No subscription operation in `SOSServlet` | Matches (not implemented) |

## Observed behaviours to be aware of

1. **SPS advertises DeleteSensor but does not dispatch it.** `generateCapabilities` adds `DeleteSensor` when transactional ([lines 241–243](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L241-L243)); the dispatch chain has no `DeleteSensorRequest`/`UpdateSensorRequest` branch and ends in `unsupported_op_code` ([dispatch](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L290-L296)). The `handleRequest(DeleteSensorRequest)` overrides at lines 803–815 are unreachable from it.
2. **SPS Submit sends only the first command block.** Comment says "send all commands", but the code uses `if (it.hasNext())` once ([lines 507–517](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L507-L517)); with no block, `lastFuture` stays `null`.
3. **DirectTasking sessions are never removed.** `receiveSessionsMap.put` exists but no `remove` anywhere, so a second DirectTasking for the same procedure fails with "A direct tasking session is already started" ([check](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sps/SPSServlet.java#L582-L586)).
4. **GetResult over WebSocket error path.** `asyncCtx` is `null` for WebSocket requests, but the `exceptionally` handler calls `asyncCtx.getRequest()` ([lines 576–581](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L576-L581)).
5. **SOS/SPS-shared code throws `SPSException` for SOS.** Version negotiation in GetCapabilities and `SWEServlet.checkTransactionalSupport` build `SPSException` ([line 115](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L115)).
6. **InsertSensor maps any `DataStoreException` to "already registered"** ([lines 206–210](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L206-L210)).
7. **Wildcard system UIDs are documented, not implemented.** `SOSProviderConfig.systemUID` and `SPSConnectorConfig.systemUID` `@DisplayInfo` say a trailing `*` is allowed; lookups use `TreeMap.get`/`containsKey` with the exact UID ([`getDataProvider`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L922)).
8. **Unused config fields / per-procedure security.** No reader found for `SystemDataProviderConfig.excludedOutputs`, `SOSProviderConfig.maxFois`, `SOSServiceConfig.maxFois`, `SOSServiceConfig.templateTimeout`, `SWEServiceConfig.virtualSensorGroup`, `OfferingConfig.enabled`. `SOSSecurity.checkPermission(String, IPermission)` has its body commented out ([source](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSSecurity.java#L94)); `addProcedurePermissions` has no callers.
9. **Unused types / methods** (searched all `.java`): `ISOSDataProvider` and `ISOSCustomSerializer` (reference only each other); `SOSServlet.findIdenticalDatastream`; `SOSServlet.addProducerID` (body commented out); `ISOSAsyncDataProvider.getTimeout()` and `hasMultipleProducers()` have no callers. Custom formats instantiate `ISOSAsyncResultSerializer`, not `ISOSCustomSerializer` ([`getCustomFormatSerializer`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/SOSServlet.java#L1064)).
10. **`TimeOutMonitor` comment vs value.** Comment "every 10 seconds by default"; the value passed is 1000 ms ([constructor](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/sos/TimeOutMonitor.java#L39-L43)).
11. **UpdateSensor is handled but not advertised** in SOS capabilities (only InsertSensor/DeleteSensor are added).

## Where to make changes (by precedent in the code)

| Task | Existing pattern |
|---|---|
| Add an SOS operation | New `handleRequest(XxxRequest)` overload in `SOSServlet` + a branch in `handleRequest(OWSRequest)`; permission field in `SOSSecurity`; advertise in `generateCapabilities` |
| Add a per-system data source | Subclass `SOSProviderConfig` and return an `ISOSAsyncDataProvider` from `createProvider`, as `SystemDataProviderConfig` does |
| Add a response format | Implement `ISOSAsyncResultSerializer` (extend `AbstractResultSerializerSwe` / `AbstractAsyncSerializer`) and either add a branch in `handleRequest(GetResultRequest)` or register it via `SOSServiceConfig.customFormats` (class loaded with `ModuleRegistry.findClass`) |
| Change live/historical selection | `SystemDataProviderConfig.createProvider` and `SOSProviderUtils.isFutureTimePeriod` |
| Add an SPS tasking backend | Subclass `SPSConnectorConfig`, implement `ISPSConnector` like `SystemTaskingConnector` |

## Tests

All in `sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/`:

| Test | Covers |
|---|---|
| [`TestSOSService`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestSOSService.java) | Capabilities (incl. live/historical time range and timeout), DescribeSensor, GetResult (now / real-time / WebSocket), GetObservation, GetFOI. Contains "TODO test getresult replay" — replay is not tested |
| [`TestSOSTService`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestSOSTService.java) | Transactional SOS (InsertSensor, InsertResultTemplate, InsertResult over WebSocket). `testInsertObservation` is commented out |
| [`TestSOSTClient`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestSOSTClient.java), [`TestSOSClient`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestSOSClient.java) | Clients against a local SOS, retry limits |
| [`TestConcurrentGetCaps`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestConcurrentGetCaps.java) | Concurrent GetCapabilities |
| [`TestObsSerializers`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestObsSerializers.java), [`TestResultSerializers`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestResultSerializers.java), [`TestProcedureSerializers`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sos/TestProcedureSerializers.java) | Serializers, with helpers `TestAsyncContext`, `TestSubscriber`, `TestSubscription` |
| [`TestSPSService`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sps/TestSPSService.java), [`TestSPSTService`](../../../sensorhub-service-swe/src/test/java/org/sensorhub/impl/service/sps/TestSPSTService.java) | GetCapabilities, DescribeSensor/Tasking, Submit, DirectTasking; InsertSensor, InsertTaskingTemplate, ConnectTasking |

```bash
./gradlew :sensorhub-service-swe:test --tests 'org.sensorhub.impl.service.sos.TestSOSService'
./gradlew :sensorhub-service-swe:test --tests 'org.sensorhub.impl.service.sps.TestSPSService'
```

Tests depend on `sensorhub-core` test fixtures and `sensorhub-datastore-h2` ([`build.gradle`](../../../sensorhub-service-swe/build.gradle)).

## Related

- [Code map index](../index.md)
- [Event bus](event-bus.md) — topics used by `StreamingDataProvider` and `SOSTClient`
- [OGC libraries](lib-ogc.md) — request/response classes, `OWSServlet`
- [Databases & datastores](databases.md) — `IObsSystemDatabase`, `FilteredFederatedDatabase`
- [Commands / tasking](commands.md) — command stream transaction handlers used by SPS
- [Security](security.md) — `ModuleSecurity`, permissions
- [Connected Systems API](service-consys.md) — the other HTTP data service
- Legacy: [`sos-temporal-filtering.md`](../../../sensorhub-service-swe/src/site/markdown/sos-temporal-filtering.md)
