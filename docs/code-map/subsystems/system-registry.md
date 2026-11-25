# System Registry & Data Model

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

How system drivers (sensors, actuators, processes) are registered with the hub, and how their
descriptions, outputs, command inputs and features of interest (FOIs) become records in a
database and events on the bus.

| Area | Interfaces / types | Implementation |
|---|---|---|
| Driver-side model | `org.sensorhub.api.system.ISystemDriver`, `org.sensorhub.api.data.IDataProducer`, `org.sensorhub.api.data.IStreamingDataInterface`, `org.sensorhub.api.command.ICommandReceiver` | Driver base classes (see [Sensor drivers](sensor-drivers.md)) |
| Stored resources | `org.sensorhub.api.system.ISystemWithDesc`, `org.sensorhub.api.data.IDataStreamInfo`, `org.sensorhub.api.data.IObsData`, FOIs as `IFeature` | `DataStreamInfo`, `ObsData`, `SystemWrapper` |
| Registry | `org.sensorhub.api.system.ISystemDriverRegistry` | `org.sensorhub.impl.system.DefaultSystemRegistry` |
| Transaction handlers | (none, concrete classes) | `org.sensorhub.impl.system.SystemDatabaseTransactionHandler` and siblings in `impl/system` |

Commands and command streams use the same handlers; they are covered in [Commands / tasking](commands.md).
The observation path from driver output to bus subscriber is traced in
[Event bus › Data path](event-bus.md#data-path-driver-output-to-bus-subscriber) and is not repeated here.

Source folders: [`api/system`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system),
[`api/data`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data),
[`api/feature`](../../../sensorhub-core/src/main/java/org/sensorhub/api/feature),
[`api/procedure`](../../../sensorhub-core/src/main/java/org/sensorhub/api/procedure),
[`impl/system`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system),
[`impl/data`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/data).

## Key types

### Data model (API)

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`ISystemDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/ISystemDriver.java#L35) | interface | Live driver. `getUniqueIdentifier()`, `getParentSystemUID()`, `getParentSystem()`, `getCurrentDescription()` (SensorML `AbstractProcess`), `getLatestDescriptionUpdate()`, `isEnabled()`. Extends `IEventProducer` |
| [`ISystemGroupDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/ISystemGroupDriver.java#L30) | interface | Adds `getMembers()`; members are registered as subsystems |
| [`IDataProducer`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/IDataProducer.java#L30) | interface | `getOutputs()` and `getCurrentFeaturesOfInterest()` |
| [`IStreamingDataInterface`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/IStreamingDataInterface.java#L33) | interface | One output: `getName()`, `getRecordDescription()`, `getRecommendedEncoding()`, `getValidStartTime()` (default `null`). Base implementation: [`AbstractDataInterface`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/data/AbstractDataInterface.java#L38) |
| [`IDataProducerModule`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/IDataProducerModule.java#L32) | interface | Javadoc: "Kept for backward compatibility; Will be removed later" |
| [`ISystemWithDesc`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/ISystemWithDesc.java#L44) | interface | Stored system resource (`ISmlFeature<AbstractProcess>`). Implemented for drivers by `SystemWrapper` |
| [`IProcedureWithDesc`](../../../sensorhub-core/src/main/java/org/sensorhub/api/procedure/IProcedureWithDesc.java#L39), [`IDeploymentWithDesc`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/IDeploymentWithDesc.java#L34) | interfaces | Procedure (datasheet / method) and deployment resources; no methods of their own |
| [`IDataStreamInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/IDataStreamInfo.java#L35) | interface | Datastream descriptor: `getSystemID()` (`FeatureId`), `getOutputName()`, record structure/encoding, `getValidTime()`, phenomenon/result time ranges. [`getFullName()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/IDataStreamInfo.java#L145) = `{sysUID}#{outputName}` |
| [`DataStreamInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/DataStreamInfo.java#L44) | class + Builder | Javadoc: "mainly useful for creating new datastreams as it does not provide dynamic timing information" |
| [`IObsData`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/IObsData.java#L32) | interface | One observation: datastream ID, FOI ID ([`NO_FOI`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/IObsData.java#L34) = `BigId.NONE`), phenomenon/result time, parameters, location, `DataBlock` result |
| [`ObsData`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/ObsData.java#L38) | class + Builder | Javadoc: "Immutable object representing observation data" |
| [`DataEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/DataEvent.java#L32), [`ObsEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/ObsEvent.java#L29) | events | `DataEvent`: raw `DataBlock`s from a driver output (+ optional FOI UID, result time). `ObsEvent`: `IObsData[]` as published on the bus |
| [`SystemEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/SystemEvent.java#L33) → [`DataStreamEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/data/DataStreamEvent.java#L31) | abstract events | Lifecycle subclasses: `System{Added,Changed,Enabled,Disabled,Removed}Event`, `DataStream{Added,Changed,Enabled,Disabled,Removed}Event`, [`FoiAddedEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/feature/FoiAddedEvent.java#L34) |
| [`FeatureId`](../../../sensorhub-core/src/main/java/org/sensorhub/api/feature/FeatureId.java#L31) | class | Javadoc: "Immutable data class containing both internal ID and globally unique ID" |

### Registry and state database

| Type | Role |
|---|---|
| [`ISystemDriverRegistry`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/ISystemDriverRegistry.java#L49) | `register(...)` overloads for drivers, procedures, outputs, control inputs and FOIs; `unregister`, `isRegistered`, `getSystemStateDatabase`, `registerDatabase` / `unregisterDatabase` / `hasDatabase` / `getDatabase`, `waitForDataStream`. Obtained via [`ISensorHub.getSystemDriverRegistry()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/ISensorHub.java#L52) |
| [`DefaultSystemRegistry`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L68) | Only implementation. Holds `driverHandlers` (top-level system UID → `SystemDriverTransactionHandler`), `obsSystemDatabases` (UID pattern → database, a `MapWithWildcards`) and `systemStateDb` |
| [`SystemDriverDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/system/SystemDriverDatabase.java#L45) | Module wrapping an `IObsSystemDatabase`; implements [`ISystemDriverDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/ISystemDriverDatabase.java#L33) (`getHandledSystems()`) |
| [`InMemorySystemStateDbConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/mem/InMemorySystemStateDbConfig.java#L20) | Config whose `moduleClass` is `InMemorySystemStateDatabase` |
| [`InMemorySystemStateDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/mem/InMemorySystemStateDatabase.java#L38) | Implements [`ISystemStateDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/ISystemStateDatabase.java#L31). In-memory stores; javadoc of `InMemoryObsStore` says it "only stores the latest observation of each data stream and FOI combination" |

### Transaction handlers (`org.sensorhub.impl.system`)

| Type | Visibility | Role |
|---|---|---|
| [`SystemDatabaseTransactionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDatabaseTransactionHandler.java#L49) | public | Root handler bound to one `IEventBus` and one `IObsSystemDatabase`. `addSystem`, `addOrUpdateSystem`, `addSystemOrReturnExisting`, FOI add/update, and factories `getSystemHandler`, `getDataStreamHandler`, `getCommandStreamHandler` |
| [`SystemTransactionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L74) | public | One system: `update`, `delete(cascade)`, `enable` / `disable`, `addMember`, `addOrUpdateDataStream`, `addOrUpdateCommandStream`, `addFoi`, `addOrUpdateFoi`; publishes `SystemEvent`s |
| [`DataStreamTransactionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DataStreamTransactionHandler.java#L55) | public | One datastream: `update`, `delete`, `enable` / `disable`, `addObs(...)`. Is an `IEventListener` on a driver output |
| [`CommandStreamTransactionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/CommandStreamTransactionHandler.java#L63) | public | One command stream; see [Commands / tasking](commands.md) |
| [`SystemRegistryTransactionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemRegistryTransactionHandler.java#L28) | package | Root handler used by the registry; its `createSystemHandler` returns `SystemDriverTransactionHandler` |
| [`SystemDriverTransactionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L52) | package | `SystemTransactionHandler` bound to a live driver: keeps maps of datastream, command stream and member handlers and command subscriptions; uses a `SerialExecutor` over the registry's executor |
| [`SystemSubscriptionHandler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemSubscriptionHandler.java#L49) | public | Builds bus subscriptions from a datastore filter (system, datastream, command stream, obs). Javadoc: "The filter is evaluated at the time of subscription and not re-evaluated afterwards" |
| [`SystemUtils`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemUtils.java#L41) | public | Converts between SensorML outputs / taskable params and datastreams / command streams |

The public handlers are also built directly, outside the registry, by ConSys handlers (e.g. `SystemHandler`:
[`new SystemDatabaseTransactionHandler`](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/system/SystemHandler.java#L64)),
SWE servlets, the admin UI and `CommandStreamSink`, each with `new SystemDatabaseTransactionHandler(eventBus, db)`.

## How it works

### Registry creation

- `SensorHub.start()` builds [`new DefaultSystemRegistry(this, new InMemorySystemStateDbConfig())`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L136).
- [`initDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L88) wraps that config in a `SystemDriverDatabase` (`databaseNum = 0`) and starts it. `SystemDriverDatabase.doStart` loads the `InMemorySystemStateDatabase` as a sub-module.
- [`getSystemStateDatabase()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L361) returns the wrapped in-memory database.

### Driver registration

Callers: `AbstractSensorModule.beforeStart` [`register(this).get()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L233) (only when the driver has no parent system), `AbstractProcessModule`, `AbstractProcessWrapperModule`, and `SensorSystem` for late members ([`register(memberProc)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L197)).

```
DefaultSystemRegistry.register(driver)
  parentUID != null → getDriverHandler(parentUID).registerMember(driver)          (group member)
  else supplyAsync on ForkJoinPool.commonPool():
    remove old handler; if a different driver object owns the UID → IllegalArgumentException
    old handler → doUnregister(false)
    db = getDatabaseForDriver(driver)          (mapped DB, else systemStateDb)
    new SystemRegistryTransactionHandler(hub, db, executor)
      .addOrUpdateSystem(new SystemWrapper(desc).hideOutputs().hideTaskableParams().defaultToValidFromNow())
    SystemDriverTransactionHandler.doFinishRegister(driver):
      enable()                                  → SystemEnabledEvent
      driver.registerListener(this)
      IDataProducer   → doRegister(foi) for each current FOI; doRegister(output) for each output
      ICommandReceiver→ doRegister(controlInput) for each command input   (see commands.md)
      ISystemGroupDriver → doRegisterMember(member, parent validTime) for each member
```

- [`register(ISystemDriver)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L119); [`doFinishRegister`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L69).
- [`addOrUpdateSystem`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDatabaseTransactionHandler.java#L129) calls `update` on an existing entry, else [`addSystem`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDatabaseTransactionHandler.java#L74), which publishes `SystemAddedEvent`.
- [`SystemTransactionHandler.update`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L111): same valid start time → overwrite; later valid start time → new version + `SystemChangedEvent`; earlier → `DataStoreException`.
- Outputs, command inputs and FOIs added after start are registered one at a time through the `register(IStreamingDataInterface)`, `register(IStreamingControlInterface)` and `register(ISystemDriver, IFeature)` overloads (e.g. `AbstractSensorModule` [`register(dataInterface)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L300), [`register(this, foi)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L427)). These run on the system handler's `SerialExecutor`.

### Output → datastream

[`doRegister(IStreamingDataInterface)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L260) calls `addOrUpdateDataStream(name, recordDescription, recommendedEncoding, validStartTime)`, replaces the previous handler (unregistering it as listener), calls `enable()` (`DataStreamEnabledEvent`) and registers the new `DataStreamTransactionHandler` as listener on the output.

[`addOrUpdateDataStream(IDataStreamInfo)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L332) rules. Datastream name is `"{system name} - {label or output name}"`; output name must equal the record structure name, else `IllegalStateException`.

| Existing latest version for (sysUID, outputName) | Result |
|---|---|
| none | `add` → new key, `DataStreamAddedEvent` |
| explicit `validTime` with a different begin | `add` new version, `DataStreamAddedEvent` |
| has obs (`getResultTimeRange() != null`) and structure incompatible or encoding differs | `add` new version with `validTime = [now, now…)`, `DataStreamAddedEvent` |
| struct, encoding, name or description differs | `DataStreamTransactionHandler.update` → `replace`, `DataStreamChangedEvent` |
| no difference | existing info reused, no event |

Observation ingestion (`handleEvent` → `addObs`) is described in the [event-bus data path](event-bus.md#data-path-driver-output-to-bus-subscriber). FOI UIDs carried by a `DataEvent` are resolved through a Guava `LoadingCache` built by [`createFoiIdCache`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDatabaseTransactionHandler.java#L344) (max 10 000 entries, 1 h after access).

### FOIs and members

- [`SystemTransactionHandler.addFoi`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L579) stores the FOI with the system as parent and publishes `FoiAddedEvent`. [`addOrUpdateFoi`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L600) overwrites when UID and valid start time match (no event).
- [`doRegisterMember`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L186) → `addOrUpdateMember` → [`addMember`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L260) (stored with the group's internal ID as parent, publishes `SystemAddedEvent(memberUID, parentUID)`), then `doFinishRegister` on the member handler.

### Unregistration

- [`unregister`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L204) removes the handler and calls [`doUnregister(true)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L120): unregisters listeners, recursively unregisters members, sends `DataStreamDisabledEvent` / `CommandStreamDisabledEvent` / `SystemDisabledEvent`, cancels command subscriptions. Records stay in the database (interface javadoc: "doesn't remove it from the data store").
- Called from `AbstractSensorModule.afterStop` and from `ModuleRegistry` [on module delete](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L928).
- Deleting records is done by [`SystemTransactionHandler.delete(cascade)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L156), called by e.g. ConSys, not by the registry.

### Mapping systems to a persistent database

- [`registerDatabase(uidPattern, db)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L281) rejects read-only DBs and patterns already mapped. It then re-registers matching top-level drivers (so their new handler writes to `db`) and removes matching systems, datastreams and command streams from the state DB.
- `SystemDriverDatabase.afterStart` calls it with `getHandledSystems()` ([call](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/system/SystemDriverDatabase.java#L122)); `beforeStop` calls `unregisterDatabase`.
- [`getDatabaseForDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L263) picks the mapped DB, falling back to the state DB.

### Events and `waitForDataStream`

- System events: [`publishSystemEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L647) publishes on `systems/{uid}/status`, each ancestor's status topic, then `systems/`. Datastream events follow the same pattern (see [event bus](event-bus.md#data-path-driver-output-to-bus-subscriber)).
- [`waitForDataStream`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L368) subscribes to the system status topic and completes when the federated DB returns a current datastream for the output (checked on subscribe and on each matching `DataStreamEvent`).

## Observed behaviours to be aware of

1. **Open question:** [`register(IProcedureWithDesc)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L112) is an auto-generated stub returning `null`. No caller found in the repo.
2. **Open question:** `ISystemDriverRegistry.register` javadoc says "No event is generated for members of a system group", but `addMember` publishes `SystemAddedEvent` for each member ([line 272](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L272)).
3. **Open question:** the same javadoc says the implementation "must take care of forwarding all events produced by the driver to the event bus". [`SystemDriverTransactionHandler.handleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L475) only reacts to a `SystemChangedEvent` from the driver itself (by re-reading its description); other driver events are not published.
4. **Open question:** [`unregisterDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L331) removes the mapping only; comment: "TODO update DB used by transaction handlers on the fly!". Registered handlers keep writing to the removed DB.
5. `registerDatabase` calls `getDriverHandler(uid)` for every matching top-level system in the state DB. Unregistered drivers stay in the state DB, so a match with no live handler throws `IllegalStateException` from inside the `forEach` ([lines 303–304](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L303-L304)). The futures returned by those `register` calls are discarded.
6. **Open question:** `SystemTransactionHandler.newlyCreated` is never assigned, so [`isNew()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemTransactionHandler.java#L708) always returns `false`.
7. **Open question:** [`unregisterMember`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L225) null-checks the `driver` field instead of its `proc` argument. No caller found.
8. **Open question:** `DataEventToObsConverter` and `SystemSubscriptionHandler` have no references outside their own files. `VirtualSystemGroupConfig` is declared as a field type in `SWEServiceConfig` and `ConSysApiServiceConfig`, but those fields are never read.
9. When an output emits `ObsEvent` instead of `DataEvent`, [`handleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DataStreamTransactionHandler.java#L258) republishes each observation as its own `ObsEvent` and stores it unchanged (its datastream ID is not set or checked).
10. In `addObs(DataEvent)` the null check on the FOI ID ([line 193](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DataStreamTransactionHandler.java#L193)) cannot trigger. **Inferred:** the cache loader throws for an unknown UID, and Guava `getUnchecked` wraps that in an unchecked exception thrown to the output's publisher.
11. `isRegistered(uid)` checks top-level handlers and their direct members only, not deeper nesting ([source](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L176)).

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Register a new kind of driver | Implement `ISystemDriver` (+ `IDataProducer` / `ICommandReceiver` / `ISystemGroupDriver`) and call `getSystemDriverRegistry().register(this)` on start, as in `AbstractSensorModule.beforeStart` |
| Add an output after start | `AbstractSensorModule.addOutput` → `registry.register(dataInterface)` |
| Create systems / datastreams without a driver | `new SystemDatabaseTransactionHandler(eventBus, db)` → `addOrUpdateSystem` → `addOrUpdateDataStream`, as in ConSys `SystemHandler` / `DataStreamHandler` |
| Change datastream versioning rules | `SystemTransactionHandler.addOrUpdateDataStream(IDataStreamInfo)` and `DataStreamTransactionHandler.update` |
| Change where a driver's data is persisted | `DefaultSystemRegistry.getDatabaseForDriver` / `registerDatabase`; `SystemDriverDatabase` config `systemUIDs` |
| Add a new system lifecycle event | Subclass `SystemEvent` (or `DataStreamEvent`) and publish through `publishSystemEvent` / `publishDataStreamEvent` |

## Tests

[`TestSystemDriverRegistry`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/system/TestSystemDriverRegistry.java) covers:
- registering a simple sensor (explicitly and via module start), checking datastreams and obs in the state DB;
- sensor groups and sensor arrays, including FOIs added after start;
- system/datastream events published on register and unregister (simple sensor only).

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.system.TestSystemDriverRegistry'
```

Registry callers are also exercised by `TestOnDemandProcess`, `TestCommandSinkProcess` and the ConSys tests
[`TestSystems`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestSystems.java) and
[`TestDataStreams`](../../../sensorhub-service-consys/src/test/java/org/sensorhub/impl/service/consys/TestDataStreams.java).
No test source calls `registerDatabase`, `waitForDataStream` or `delete(boolean)` by name (searched all `src/test` folders).

## Related

- [Code map index](../index.md)
- [Event bus](event-bus.md) (topics, obs data path)
- [Commands / tasking](commands.md)
- [Databases & datastores](databases.md)
- [Sensor drivers](sensor-drivers.md)
- [Module lifecycle](module-lifecycle.md)
- [Connected Systems API service](service-consys.md)
