# Processing

> Status: Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Data processing components run by the hub. The code has three kinds:

| Kind | Base class | Runs | Example |
|---|---|---|---|
| **SensorML process chain module** | `org.sensorhub.impl.processing.SMLProcessImpl` | Continuously, on the SensorML execution engine, fed by hub data streams | `TestStreamProcess` chains |
| **On-demand process** | `org.sensorhub.impl.processing.OnDemandProcess` (an `AbstractProcessDriver`) | Once per command received on its input | `TestLinearEquationProcess` |
| **Hub-aware chain components** | `org.vast.process.ExecutableProcessImpl` + `org.sensorhub.impl.processing.ISensorHubProcess` | Inside a SensorML chain, as sources and sinks connected to the hub | `StreamDataSource`, `DataStreamSource`, `CommandStreamSink` |

Every process is an `IDataProcess`, i.e. a system driver with outputs and command inputs, so
it is registered with the [System registry](system-registry.md) like a sensor driver.
The SensorML model and execution engine classes (`AggregateProcessImpl`, `SMLUtils`,
`ExecutableProcessImpl`, `DataQueue`) live in `lib-ogc/sensorml-core`; see [OGC libraries](lib-ogc.md).

Source folders:
- API: [`sensorhub-core/.../api/processing/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing)
- Implementation: [`sensorhub-core/.../impl/processing/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing)
- Test fixtures: [`sensorhub-core/src/testFixtures/.../impl/processing/`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/processing)

## Key types

### API (`org.sensorhub.api.processing`)

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`IDataProcess`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IDataProcess.java#L40) | interface | `IDataProducer` + `ICommandReceiver`; adds `getInputDescriptors()`, `getOutputDescriptors()`, `getParameterDescriptors()`. Javadoc: for on-demand processes "output data is provided inline in the command result, and not evented into a datastream" |
| [`IProcessModule`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IProcessModule.java#L34) | interface | `IDataProducerModule<C extends ProcessConfig>` + `IDataProcess` |
| [`IOnDemandProcess`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IOnDemandProcess.java#L21) | interface | `execute()`, `execute(Collection<String> foiUIDs)`; constant [`ON_DEMAND_PROCESS_DEF`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IOnDemandProcess.java#L23) |
| [`IProcessProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IProcessProvider.java#L28) | interface | Extends `IModuleProvider`; [`getProcessMap()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IProcessProvider.java#L34) returns URI → `ProcessInfo`. Javadoc: "Provider interface used for executable process discovery" |
| [`IProcessingManager`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IProcessingManager.java#L29) | interface | Extends `org.vast.sensorML.IProcessFactory` (`loadProcess(uri)`); adds `getAllProcessingPackages()` |
| [`OSHProcessInfo`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/OSHProcessInfo.java#L21) | class | `ProcessInfo` whose URI is prefixed with `urn:osh:process:` |
| [`ProcessConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/ProcessConfig.java#L28) | config | Empty `ModuleConfig` subclass |
| [`ProcessingException`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/ProcessingException.java#L28) | exception | Extends `SensorHubException` |
| [`IStreamProcess`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IStreamProcess.java#L18), [`IParallelProcess`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IParallelProcess.java#L30), [`IProcessOutput`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IProcessOutput.java#L20), [`ProcessingEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/ProcessingEvent.java#L28) | interfaces / event | **No implementations or references elsewhere in this repo** (searched all `.java` files) |

### Implementation (`org.sensorhub.impl.processing`)

| Type | Role |
|---|---|
| [`ProcessingManagerImpl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/ProcessingManagerImpl.java#L38) | The only `IProcessingManager`. Created in `SensorHub.start()` ([`new ProcessingManagerImpl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L141)); exposed by [`ISensorHub.getProcessingManager()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/ISensorHub.java#L64) |
| [`AbstractProcessProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/AbstractProcessProvider.java#L25) | `JarModuleProvider` + `IProcessProvider`; subclasses call [`addImpl(info)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/AbstractProcessProvider.java#L30) |
| [`SMLProcessDescriptor`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessDescriptor.java#L22) | Provider for the `SMLProcessImpl` module (config `SMLProcessConfig`) and for the three hub chain components |
| [`AbstractProcessModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/AbstractProcessModule.java#L46) | `AbstractModule` + `IProcessModule`: descriptor maps, output/control maps, registration in start/stop |
| [`SMLProcessImpl`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessImpl.java#L52) | Module that loads a SensorML `AggregateProcess` (XML or JSON) and runs it |
| [`SMLProcessConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessConfig.java#L30) | `sensorML` file path; [`getSensorMLPath()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessConfig.java#L39) resolves it with `new File(...).getAbsolutePath()` |
| [`SMLOutputInterface`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLOutputInterface.java#L38) | Package-private `IStreamingDataInterface` that turns chain output into `DataEvent`s |
| [`SMLInputInterface`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLInputInterface.java#L35) | `IStreamingControlInterface` that queues command params into a chain input or parameter |
| [`AbstractProcessDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/AbstractProcessDriver.java#L42) | Non-module `IDataProcess` base with its own `BasicEventHandler`. Only subclass: `OnDemandProcess` |
| [`OnDemandProcess`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/OnDemandProcess.java#L46) | Synchronous on-demand process: one command input whose result carries the output inline |
| [`AbstractProcessWrapperModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/AbstractProcessWrapperModule.java#L47) | Wraps any `IDataProcess` as a module (javadoc: "so it can be instantiated directly in the SensorHub"); delegates all `IDataProcess` getters |
| [`ISensorHubProcess`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/ISensorHubProcess.java#L28) | `setParentHub(ISensorHub)`; javadoc: "processes that are attached to a given hub, such as data sources and sinks" |
| [`StreamDataSource`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/StreamDataSource.java#L45) | URI `urn:osh:process:datasource:stream`. Param `producerURI`; one chain output per datastream of that system |
| [`DataStreamSource`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/DataStreamSource.java#L49) | URI `urn:osh:process:datasource:datastream`. Params `systemUID`, `outputName`; one chain output |
| [`CommandStreamSink`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/CommandStreamSink.java#L40) | URI `urn:osh:process:datasink:commandstream`. Params `systemUID`, `inputName`; one chain input sent as a command |

## How it works

### Process discovery and loading

1. Providers are found with `java.util.ServiceLoader`. [`getAllProcessingPackages()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/ProcessingManagerImpl.java#L51) iterates `ServiceLoader.load(IProcessProvider.class)` on every call (no caching) and logs, then stops at, the first invalid entry.
2. Registration files:
   - main: [`META-INF/services/org.sensorhub.api.processing.IProcessProvider`](../../../sensorhub-core/src/main/resources/META-INF/services/org.sensorhub.api.processing.IProcessProvider) lists `SMLProcessDescriptor`;
   - tests: [`src/test/resources/...IProcessProvider`](../../../sensorhub-core/src/test/resources/META-INF/services/org.sensorhub.api.processing.IProcessProvider) adds `TestProcessDescriptors` (registers `AffineTransform1D_Process` from sensorml-core tests).
   - `SMLProcessDescriptor` is also listed as an `IModuleProvider` ([services file](../../../sensorhub-core/src/main/resources/META-INF/services/org.sensorhub.api.module.IModuleProvider)), which is how the `SMLProcessImpl` module type is offered (see [Module lifecycle](module-lifecycle.md)).
3. [`loadProcess(uri)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/ProcessingManagerImpl.java#L71) finds the first provider whose map contains `uri`, instantiates `getImplementationClass()` with its no-arg constructor, and calls `setParentHub(hub)` if it is an `ISensorHubProcess`. Unknown URIs throw `ProcessException("Unknown process ...")`.
4. Callers: `SMLProcessImpl.setParentHub` installs the manager as the `SMLUtils` process factory ([`setProcessFactory`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessImpl.java#L77)); the admin UI `ProcessAdminPanel` lists providers via [`getAllProcessingPackages()`](../../../sensorhub-webui-core/src/main/java/org/sensorhub/ui/ProcessAdminPanel.java#L440).
5. `SMLUtils` picks the URI for each `SimpleProcess` in a chain from the `method` href, else the `typeOf` title, else the `typeOf` href (the `SimpleProcess` branch of `makeProcessExecutable` in [`SMLUtils`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLUtils.java), which then calls `processFactory.loadProcess`). The test chains use `typeOf` hrefs such as `urn:osh:process:datasource:stream` ([`test-processchain.xml`](../../../sensorhub-core/src/test/resources/test-processchain.xml)).

### SensorML process chain module (`SMLProcessImpl`)

```
constructor           initAsync = true; empty AggregateProcessImpl wrapper
setParentHub(hub)     smlUtils = new SMLUtils(V2_0); smlUtils.setProcessFactory(hub.getProcessingManager())
doInit()              if config.sensorML != null:
                        parse file (.xml → smlUtils.readProcess, .json → SMLJsonBindings)
                        initChain():
                          wrapperProcess = smlUtils.getExecutableInstance(description, useThreads=true)
                          wrapperProcess.init()
                          refreshIOList(inputs | parameters | outputs)
                          setState(INITIALIZED)
afterInit()           (AbstractProcessModule) description + valid UID + ≥1 input or output required
beforeStart()         (AbstractProcessModule) register with system registry if no parent system
doStart()             wrapperProcess.start(onError → reportError)
doStop()              wrapperProcess.stop()
afterStop()           (AbstractProcessModule) unregister if no parent system
```

- [`initChain`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessImpl.java#L125) calls `setState(INITIALIZED)` itself because `initAsync` is `true`, so `AbstractModule.init()` does not set it.
- [`refreshIOList`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessImpl.java#L162) builds one `SMLInputInterface` per chain input **and** per parameter (both become command inputs) and one `SMLOutputInterface` per chain output.
- **Output path:** the [`SMLOutputInterface` constructor](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLOutputInterface.java#L81) connects the chain output to a `DataQueue` whose [`publishData()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLOutputInterface.java#L53) stores the record and publishes a `DataEvent` on the interface's own `BasicEventHandler`. From there the registry forwards it to the event bus as for any driver output ([Event bus data path](event-bus.md#data-path-driver-output-to-bus-subscriber)).
- **Input path:** [`SMLInputInterface.submitCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLInputInterface.java#L84) adds the command params to an `InputQueue` connected to the chain input and immediately returns a `COMPLETED` status. A synchronous-execution version is commented out.

### Hub sources and sinks inside a chain

| Component | On `notifyParamChange()` | On `start()` / `execute()` |
|---|---|---|
| `StreamDataSource` | Waits up to 10 s (polling every 500 ms) in [`checkForDataSource`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/StreamDataSource.java#L95) for the system and its current datastreams in the federated DB; adds one output per datastream | [`start`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/StreamDataSource.java#L134) subscribes to `ObsEvent`s on every `.../outputs/{name}/data` topic, `request(Long.MAX_VALUE)`, and calls `publishData(outputName)` for each obs |
| `DataStreamSource` | Same wait in [`checkForDataSource`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/DataStreamSource.java#L109), for one named output | [`start`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/DataStreamSource.java#L148) first publishes the latest stored obs (from the observation store), then streams new ones; the first streamed obs is dropped if its result time equals that latest obs |
| `CommandStreamSink` | Waits in [`checkForControlStream`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/CommandStreamSink.java#L98) for the control stream; adds one chain input with its schema and gets a `CommandStreamTransactionHandler` | [`execute`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/CommandStreamSink.java#L146) builds a `CommandData` from input 0 (sender `{process URI}#{instance name}`) and calls `submitCommand` |

Both sources have `pause()` / `resume()` methods that make `onNext` drop events. They do not implement `IStreamProcess`.

### On-demand processes

- [`OnDemandProcess` constructor](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/OnDemandProcess.java#L133) calls the subclass's `initProcess()`, which must set the `input` and `output` components (and optionally `params`) and return the SensorML description. It sets `definition = ON_DEMAND_PROCESS_DEF`, adds one `SyncInput` command input named after `input`, and puts `params` in the parameter descriptors.
- [`SyncInput.submitCommand`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/OnDemandProcess.java#L74) copies the command params into `input`, calls `execute()`, and returns `CommandStatus.completed(...)` with `CommandResult.withData(output data clone)`.
- Parameters are changed by writing into the `DataComponent` returned by `getParameterDescriptors()` (as `TestOnDemandProcess` and `TestLinearEquationProcessModule.doInit` do), not through a command.
- To run as a hub module, an `OnDemandProcess` is wrapped in an `AbstractProcessWrapperModule` subclass whose `initProcess()` returns it (precedent: `TestLinearEquationProcessModule`). The wrapper's `beforeStart`/`afterStop` register and unregister the module with the system registry, like `AbstractProcessModule`.
- [`execute(Collection)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/OnDemandProcess.java#L160) throws `UnsupportedOperationException`.

### Processes inside a `SensorSystem`

`SensorSystem` calls `AbstractProcessModule.attachToParent(this)` for process members (see [Sensor drivers](sensor-drivers.md#sensorsystem-groups-of-drivers-and-processes)). With a parent set, `beforeStart` skips registration and throws if the parent is not enabled.

## Observed behaviours to be aware of

1. **`lastUpdatedProcess` is never assigned.** It is declared in `AbstractProcessModule`, again (hiding it) in `SMLProcessImpl`, and in `AbstractProcessDriver`; no code assigns it, so `getLatestDescriptionUpdate()` always returns `Long.MIN_VALUE`. `SMLProcessImpl` also re-declares `paused` and `errorCount` ([lines 58–60](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessImpl.java#L58-L60)); `MAX_ERRORS` is unused.
2. **`SMLProcessImpl` with no `sensorML` fails init.** The comment in [`doInit`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessImpl.java#L82) says "otherwise we'll do it at the next update", but the class has no update hook, and `afterInit` throws "No process description created during init". A path ending neither in `.xml` nor `.json` leaves the description unset.
3. **Sampling period units in `SMLOutputInterface`.** `publishData` checks `!Double.isNaN(lastRecordTime)` on a `long` (always true) and subtracts `lastRecordTime` in milliseconds from `timeStamp` in seconds ([line 62](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLOutputInterface.java#L62)). **Open question:** `getAverageSamplingPeriod()` therefore does not return seconds between records.
4. **`SMLInputInterface` is partly stubbed.** `validateCommand`, [`registerListener`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLInputInterface.java#L147) and `unregisterListener` are empty `TODO Auto-generated` bodies; commands report `COMPLETED` before the chain processes them.
5. **`OnDemandProcess` leftovers.** `SyncInput.async` is never set to `true` (execution is always on the caller's thread); nested class [`SyncOutput`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/OnDemandProcess.java#L103) is never instantiated; `output` is not added to the output descriptors, so `getOutputDescriptors()` is empty.
6. **`IDataProcess.getOutputDescriptors` javadoc** is a copy of the inputs javadoc ("Gets the list of all input descriptors", [lines 53–60](../../../sensorhub-core/src/main/java/org/sensorhub/api/processing/IDataProcess.java#L53-L60)).
7. **`CommandStreamSink` naming and status.** The input-name param constant is [`OUTPUT_NAME_PARAM`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/CommandStreamSink.java#L44) = `"inputName"`, with definition `OutputName` and label "Output Name". The command status future is consumed by an empty lambda.
8. **Unused API and fixtures:** `IStreamProcess`, `IParallelProcess`, `IProcessOutput`, `ProcessingEvent` have no users. [`TestLinearEquationDescriptor`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/processing/TestLinearEquationDescriptor.java#L23) is not referenced or listed in a services file, and registers `StreamDataSource.INFO` rather than a linear-equation process.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Add a reusable chain component (process type) | Extend `ExecutableProcessImpl` with a static `OSHProcessInfo INFO`; implement `ISensorHubProcess` if it needs the hub. Add it with `addImpl(...)` in an `AbstractProcessProvider` subclass listed in `META-INF/services/org.sensorhub.api.processing.IProcessProvider`. Precedent: `StreamDataSource` + `SMLProcessDescriptor`; test precedent: [`TestProcessDescriptors`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestProcessDescriptors.java#L20) |
| Add an on-demand process | Extend `OnDemandProcess`, implement `initProcess()` and `execute()`; wrap it with an `AbstractProcessWrapperModule` subclass. Precedent: [`TestLinearEquationProcess`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/processing/TestLinearEquationProcess.java#L22) + [`TestLinearEquationProcessModule`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/processing/TestLinearEquationProcessModule.java#L21) |
| Add a new process module type | Extend `AbstractProcessModule`, create `processDescription` and I/O in `doInit()` using `addOutput` / `addInput` / `addParams`. Precedent: `SMLProcessImpl` |
| Change how process URIs resolve | `ProcessingManagerImpl.loadProcess`; URI selection per chain step is in `SMLUtils` (lib-ogc) |

## Tests

| Test | Covers |
|---|---|
| [`TestStreamProcess`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestStreamProcess.java) | `SMLProcessImpl` chains fed by a `FakeSensor` through `StreamDataSource` (`test-processchain*.xml`); output events counted |
| [`TestCommandSinkProcess`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestCommandSinkProcess.java) | Control loop: `DataStreamSource` → affine transform → `CommandStreamSink` to a `FakeSensorControl1` (`test-processchain-controlloop.xml`) |
| [`TestOnDemandProcess`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/processing/TestOnDemandProcess.java) | `TestLinearEquationProcessModule` invoked directly via `submitCommand`, and via the command stream handler of the system DB; checks the inline result |

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.processing.TestOnDemandProcess'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.processing.TestStreamProcess'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.processing.TestCommandSinkProcess'
```

`sensorhub-core-osgi` has its own copy of the `IProcessProvider` services file in its test resources.

## Related

- [Code map index](../index.md)
- [Sensor drivers](sensor-drivers.md), [System registry](system-registry.md), [Event bus](event-bus.md), [Commands](commands.md), [Module lifecycle](module-lifecycle.md), [OGC libraries](lib-ogc.md), [Admin web UI](webui.md)
