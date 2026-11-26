# Sensor Drivers

> Status: Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Base interfaces and classes used to write sensor and actuator drivers: driver identity
(unique ID, XML ID), outputs, control inputs, features of interest (FOIs), and the SensorML
description generated for the driver. Also covers `SensorSystem`, a module that groups
other drivers and processes under one parent system.

How registered outputs reach the event bus and the databases is covered in
[System registry](system-registry.md) and [Event bus](event-bus.md#data-path-driver-output-to-bus-subscriber).
Module states (`init`/`start`/`stop`, `beforeXxx`/`afterXxx` hooks) are covered in
[Module lifecycle](module-lifecycle.md).

Source folders:
- API: [`sensorhub-core/.../api/sensor/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor)
- Implementation: [`sensorhub-core/.../impl/sensor/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor)
- Test fixtures (fake drivers): [`sensorhub-core/src/testFixtures/.../impl/sensor/`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor)

## Key types

### Interface hierarchy

```
ISystemDriver (api/system)                 name, UID, parent, SensorML description, isEnabled
 ├─ IDataProducer (api/data)               getOutputs(), getCurrentFeaturesOfInterest()
 ├─ ICommandReceiver (api/command)         getCommandInputs()
 └─ ISensorDriver  = ISystemDriver + IDataProducer + ICommandReceiver
     │                                     + getStatusOutputs(), getObservationOutputs(), isConnected()
     ├─ IActuatorDriver                    (empty marker interface)
     └─ ISensorModule<C extends SensorConfig> = IDataProducerModule<C> + ISensorDriver
```

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`ISensorDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/ISensorDriver.java#L32) | interface | Adds status/observation output maps and [`isConnected()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/ISensorDriver.java#L55). Javadoc on `isConnected`: "this method can block for long periods of time" |
| [`ISensorModule`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/ISensorModule.java#L30) | interface | A sensor driver that is also a hub module. Javadoc: "Inputs/Output should always be created in the init() method even if they are further modified during or after startup." |
| [`IActuatorDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/IActuatorDriver.java#L31) | interface | Javadoc: "just a semantic interface". No implementations or references in this repo |
| [`SensorConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/SensorConfig.java#L33) | config | Fields `sensorML` (URL or classpath-relative path of a base SensorML doc) and `lastUpdated`. [`getLocation()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/SensorConfig.java#L69) / [`getOrientation()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/SensorConfig.java#L80) return `null`; subclasses override them to supply a static position |
| [`PositionConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/PositionConfig.java#L28) | config | Nested `LLALocation`, `CartesianLocation`, `EulerOrientation` value classes |
| [`SensorException`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/SensorException.java#L28) | exception | Extends `SensorHubException` |
| [`SensorDriverConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/sensor/SensorDriverConfig.java#L28) | config | Empty `ModuleConfig` subclass. No references in this repo |

### Implementation (`org.sensorhub.impl.sensor`)

| Type | Role |
|---|---|
| [`AbstractSensorModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L91) | Base class for module-based drivers. Extends `AbstractModule`, implements `ISensorModule`. Holds output/control/FOI maps, IDs, the SensorML description and default position outputs |
| [`AbstractSensorDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorDriver.java#L60) | Non-module `ISensorDriver` base (UID and short ID passed to the constructor, own `BasicEventHandler`). **No subclasses or references in this repo** |
| [`AbstractSensorOutput`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorOutput.java#L32) | Base for outputs. Thin subclass of `org.sensorhub.impl.data.AbstractDataInterface`; adds a `parentSensor` field ("for backward compatibility") |
| [`AbstractSensorControl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorControl.java#L38) | Base for control inputs. Subclass of `org.sensorhub.impl.command.AbstractControlInterface` (see [Commands](commands.md)) |
| [`VarRateSensorOutput`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/VarRateSensorOutput.java#L30) | Output that averages the sampling period over the first 100 records ([`updateSamplingPeriod`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/VarRateSensorOutput.java#L53)). Only subclass in repo: `SWEVirtualSensorOutput` (sensorhub-service-swe) |
| [`DefaultLocationOutput`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/DefaultLocationOutput.java#L30) / [`DefaultLocationOutputLLA`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/DefaultLocationOutputLLA.java#L33) | Status output named `sensorLocation`, record ID `SENSOR_LOCATION`, fields time + lat/lon/alt vector (EPSG:4979) |
| [`DefaultOrientationOutput`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/DefaultOrientationOutput.java#L21) / [`DefaultOrientationOutputEuler`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/DefaultOrientationOutputEuler.java#L23) | Status output named `sensorOrientation`, record ID `SENSOR_ORIENTATION`, fields time + heading/pitch/roll (NED) |
| [`SensorSystem`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L54) | `AbstractSensorModule<SensorSystemConfig>` that also implements `ISystemGroupDriver`. Loads and owns member modules |
| [`SensorSystemConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystemConfig.java#L36) | `uniqueID` (`@Required`; URN, suffix, or `auto`), fixed `location` / `orientation`, and a list of [`SystemMember`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystemConfig.java#L39) (member `ModuleConfig` + relative location/orientation) |
| [`SensorSystemDescriptor`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystemDescriptor.java#L24) | `IModuleProvider` for `SensorSystem`; listed in [`META-INF/services/org.sensorhub.api.module.IModuleProvider`](../../../sensorhub-core/src/main/resources/META-INF/services/org.sensorhub.api.module.IModuleProvider) |
| [`SensorArrayConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorArrayConfig.java#L31) | Config with `commonConfig` and `sensors` list. Javadoc names "SensorArray modules"; no such module class and no references in this repo |

## How it works

### Driver identity (`AbstractSensorModule`)

- [`beforeInit()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L121) resets `uniqueID`, `xmlID`, position outputs and the description, and clears all outputs and control inputs.
- The subclass `doInit()` is expected to set `uniqueID` / `xmlID`, directly (as in `FakeSensor`) or via [`generateUniqueID(prefix, suffix)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L841) and [`generateXmlID(prefix, suffix)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L859). With a `null` suffix both use the first 8 characters of the module local ID.
- [`afterInit()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L152), if `uniqueID` is still `null`: sets it to `urn:uuid:{random UUID}`, derives `xmlID` as `SENSOR_{first 8 chars of UUID}` and sets `randomUniqueID = true`.
- [`saveState`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L805) stores the random UID under `UniqueID`; [`loadState`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L786) restores it, so a random UID survives restarts (see Observed behaviours #2).

### Outputs, control inputs and FOIs

| Method | Effect |
|---|---|
| [`addOutput(iface, isStatus)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L285) | Puts the output into `statusOutputs` or `obsOutputs` (keyed by `getName()`). If the module is already started and has a hub, also calls `getSystemDriverRegistry().register(output).get()` |
| [`addControlInput(iface)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L369) | Same pattern for `controlInputs`, registering via `register(IStreamingControlInterface)` if started |
| [`addFoi(foi)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L412) | Validates the FOI UID, puts it in `foiMap`; if started calls `register(this, foi).get()` |
| [`addLocationOutput(period)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L320) / [`addOrientationOutput(period)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L339) | Create the default position output once and add it as a **status** output |
| `getOutputs()` | Observation outputs followed by status outputs, as a new unmodifiable map |

- Outputs extend `AbstractDataInterface`, which creates its **own** `BasicEventHandler` per output ([`new BasicEventHandler()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/data/AbstractDataInterface.java#L72)). An output publishes `DataEvent`s on it, as `FakeSensorData` does ([`eventHandler.publish`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorData.java#L134)).
- [`AbstractSensorControl.submitCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorControl.java#L58) runs `execCommand(params)` in `CompletableFuture.supplyAsync`, returning `completed` on `true`, `failed` on `false` or `CommandException`. The default [`execCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorControl.java#L51) throws `UnsupportedOperationException`, which is not caught (the future completes exceptionally).

### Static position from config

When `config.getLocation()` is non-null, `afterInit()`:
1. adds a location output with `updatePeriod = NaN`;
2. if `foiMap` is empty, adds a `SamplingPoint` FOI with UID `{uniqueID}:foi` at that location (EPSG:4979).

When `config.getOrientation()` is non-null, it adds an orientation output.
[`beforeStart()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L222) then pushes one record into each of them via
[`updateLocation`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/DefaultLocationOutputLLA.java#L58) and
[`updateOrientation`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/DefaultOrientationOutputEuler.java#L43).
Both publish a `DataEvent` only when the values differ from the previous record or `forceUpdate` is `true`.

### SensorML description generation

- [`getCurrentDescription()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L480) calls `updateSensorDescription()` lazily, when the description has no identifier (e.g. after `beforeInit` reset it to an empty `PhysicalSystemImpl`).
- [`updateSensorDescription()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L507), under `sensorDescLock`:
  1. Parses `config.getSensorDescriptionURL()` with `SMLUtils` (SensorML 2.0) if set, otherwise starts from a new `PhysicalSystemImpl`.
  2. Fills only what the document does not already define: gml:id (`xmlID`), unique ID, `definition = SWEConstants.DEF_SENSOR`, name/description from config, a validity period `[lastUpdatedSensorDescription, now)`.
  3. If the doc has no outputs, adds a copy of each output's `getRecordDescription()`. If it has no parameters, adds a copy of each control input's `getCommandDescription()` marked updatable.
  4. For `AbstractPhysicalProcess` descriptions: config location updates an existing GML `Point` template, else is added as a SWE location vector; config orientation is added as an Euler vector; both together become one `DataRecord` position. With no config position but a location output whose `getAverageSamplingPeriod()` < 3600 s, a link `#SENSOR_LOCATION` is added as the position.
- Subclasses override `updateSensorDescription()`, call `super`, and append to `sensorDescription` (precedent: [`FakeSensor.updateSensorDescription`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensor.java#L84), [`SensorSystem.updateSensorDescription`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L203) which sets `DEF_SYSTEM`).
- [`notifyNewDescription(time)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L686) sets `lastUpdatedSensorDescription` and publishes a `SystemChangedEvent` on the module's event handler. The registry handles it in [`SystemDriverTransactionHandler.handleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L475) by calling `update(driver)`.
- [`updateConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L760) regenerates the description and calls `notifyNewDescription` when `config.sensorML != null`.

### Registration with the hub

| Step | Code |
|---|---|
| Start of a top-level driver | `beforeStart()` calls `getSystemDriverRegistry().register(this).get()` when the module has a hub and `getParentSystem() == null` ([line 233](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L233)). It throws `SensorException("Parent system must be started")` if the parent exists and is not enabled |
| Registry side | [`doFinishRegister`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/SystemDriverTransactionHandler.java#L69) registers as a listener on the driver, then registers each FOI, each output, each command input and, for an `ISystemGroupDriver`, each member. See [System registry](system-registry.md) |
| Enable/disable events | [`setState`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L773) publishes `SystemEnabledEvent` on `STARTED` and `SystemDisabledEvent` on `STOPPED` |
| Stop | [`afterStop()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L258) calls `unregister(this).get()` |

### `SensorSystem` (groups of drivers and processes)

- [`setConfiguration`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L273) loads one module per `SystemMember` through [`loadModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L141): `ModuleRegistry.loadSubModule(config, false)`, then `attachToParent(this)` for `AbstractSensorModule` and `AbstractProcessModule` members, then `registerListener(this::handleEvent)`. A missing member `id` is set to a random UUID.
- [`doInit`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L64): a `uniqueID` starting with `urn:` is used as-is; any other value except `auto` becomes `urn:osh:system:{value}`. `auto` falls back to the random `urn:uuid:` path; the XML ID prefix is `SYSTEM_`. It then calls `init()` on each member, logging errors.
- [`setState(STARTED)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L215) starts each member whose config has `autoStart`, after waiting up to 10 s for `INITIALIZED`. Members refuse to start before the parent is enabled (`beforeStart` check above).
- [`handleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L170) re-publishes member `ModuleEvent`s, copies changed member configs into `config.subsystems`, and registers a member with the system registry when it reaches `INITIALIZED` while the parent is enabled.
- [`addSubsystem`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L102) / [`removeSubSystem`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L114) change the member list at runtime (callers: `AdminUI`).
- [`getMembers()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/SensorSystem.java#L326) keys members by module local ID. Load/save state, stop and cleanup are forwarded to each member.

## Observed behaviours to be aware of

1. **`updateSensorDescription()` does not send an event.** Its javadoc says it will "send a SENSOR_CHANGED event"; the method body never calls `notifyNewDescription` ([lines 499–507](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L499-L507)). Only `updateConfig` does both.
2. **Restored random UIDs produce a different XML ID.** `afterInit` derives `xmlID` from the bare UUID. `loadState` passes the full saved `urn:uuid:...` string to `generateXmlIDFromUUID` ([line 795](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L795)), whose first 8 characters are `urn:uuid`, giving `SENSOR_URN:UUID` for every such driver. **Open question:** not covered by a test.
3. **`LastUpdatedSensorDescription` is saved but not restored.** `saveState` writes it; the restore code in `loadState` is commented out ([lines 798–800](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L798-L800)).
4. **Register/unregister are asymmetric for group members.** `beforeStart` registers only when `getParentSystem() == null`; `afterStop` unregisters unconditionally ([line 264](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L264)). `AbstractProcessModule.afterStop` checks `parentSystem == null` (see [Processing](processing.md)).
5. **`addFoi` after start does not check for a hub.** It calls `getParentHub().getSystemDriverRegistry()` without the `hasParentHub()` guard used by `addOutput` / `addControlInput` ([line 427](../../../sensorhub-core/src/main/java/org/sensorhub/impl/sensor/AbstractSensorModule.java#L427)).
6. **Lock mismatch on output maps.** `addOutput` writes `statusOutputs` while holding the `obsOutputs` lock; `getStatusOutputs` and `getOutputs` read it under the `statusOutputs` lock. The getters return unmodifiable *views* of the live maps, not copies. The same code is duplicated in `AbstractSensorDriver`.
7. **Javadoc says outputs publish through the parent's handler.** `AbstractSensorOutput` and `AbstractDataInterface` constructor javadoc say events are "published using the parent sensor's event handler"; the code creates a separate handler per output (see above).
8. **`ProcessingException` in sensor code.** `beforeStart`/`afterStop` throw `ProcessingException` on interrupt, `SensorException` otherwise.
9. **Unused types/fields:** `AbstractSensorDriver`, `IActuatorDriver`, `SensorDriverConfig`, `SensorArrayConfig`, `AbstractTestSensorDriver` (test fixture) have no users. `SystemMember.location` / `orientation` are not read by any Java code. `SensorSystem` has no unit test.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Write a new module-based driver | Extend `AbstractSensorModule<YourConfig>`; set `uniqueID`/`xmlID` and create outputs and controls in `doInit()`; implement `doStart`, `doStop`, `isConnected`. Precedent: [`FakeSensor`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensor.java#L29) ([`doInit`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensor.java#L61)) |
| Add an output | Extend `AbstractSensorOutput`, implement `getRecordDescription`, `getRecommendedEncoding`, `getAverageSamplingPeriod`, publish `DataEvent` on `eventHandler`. Precedent: [`FakeSensorData`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorData.java#L39), multi-producer variant [`FakeSensorData2`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorData2.java#L46) |
| Add a control input | Extend `AbstractSensorControl`; override `execCommand` or `submitCommand`. Precedents: [`FakeSensorControl1`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorControl1.java#L39), [`FakeSensorControl2`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorControl2.java#L38) |
| Static location/orientation from config | Override `getLocation()` / `getOrientation()` in the config class. Precedent: [`SensorConfigWithPos`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/SensorConfigWithPos.java#L23) with [`FakeSensorWithPos`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorWithPos.java#L27) |
| Driver with members or many FOIs | [`FakeSensorNetWithMembers`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorNetWithMembers.java#L44) (implements `ISystemGroupDriver`), [`FakeSensorNetOnlyFois`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/sensor/FakeSensorNetOnlyFois.java#L29) |
| Customise the SensorML description | Override `updateSensorDescription()`, call `super` inside `synchronized (sensorDescLock)`, then edit `sensorDescription` (as in `FakeSensor`, `FakeSensorWithPos`) |
| Make a driver available to the hub | Add an `IModuleProvider` and list it in `META-INF/services/org.sensorhub.api.module.IModuleProvider`, as `SensorSystemDescriptor` does (discovery: [Module lifecycle](module-lifecycle.md)) |

## Tests

| Test | Covers |
|---|---|
| [`TestSensorPosition`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/sensor/TestSensorPosition.java) | Static location, orientation, and both: FOI geometry, default output records, SensorML position type (`Vector` vs `DataRecord`) |
| [`TestSystemDriverRegistry`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/system/TestSystemDriverRegistry.java) | Registering `FakeSensor`, sensor groups (`FakeSensorNetWithMembers`), FOI-only networks, and published system events |
| [`TestStreamProcess`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestStreamProcess.java), [`TestCommandSinkProcess`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestCommandSinkProcess.java) | Use `FakeSensor` as a data source / command target |

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.sensor.TestSensorPosition'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.system.TestSystemDriverRegistry'
```

`FakeSensor` is also used by SOS/SPS tests in `sensorhub-service-swe` (`TestSOSService`, `TestSPSService`, ...).

## Related

- [Code map index](../index.md)
- [Module lifecycle](module-lifecycle.md), [System registry](system-registry.md), [Event bus](event-bus.md), [Commands](commands.md), [Processing](processing.md), [OGC libraries](lib-ogc.md)
