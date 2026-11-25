# Module Lifecycle & Registry

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

How hub components ("modules") are described by configuration, instantiated, moved through
their lifecycle states, persisted, and how the hub itself boots them.

| Concern | Interfaces / base classes | Implementation |
|---|---|---|
| Module contract | `org.sensorhub.api.module.IModule`, `org.sensorhub.api.module.IModuleBase` | `org.sensorhub.impl.module.AbstractModule` |
| Configuration | `org.sensorhub.api.module.ModuleConfig` (extends `org.sensorhub.api.module.ModuleConfigBase`) | Subclassed per module |
| States & events | `org.sensorhub.api.module.ModuleEvent` (nested enums `Type`, `ModuleState`) | Emitted by `AbstractModule`, forwarded by `ModuleRegistry` |
| Registry | `org.sensorhub.api.module.IModuleManager` | `org.sensorhub.impl.module.ModuleRegistry` |
| Config persistence | `org.sensorhub.api.module.IModuleConfigRepository` | `org.sensorhub.impl.module.ModuleConfigJsonFile`, `org.sensorhub.impl.module.InMemoryConfigDb` |
| Class / type discovery | `org.sensorhub.api.module.IModuleProvider` | `org.sensorhub.impl.module.ModuleClassFinder`, `org.sensorhub.impl.module.JarModuleProvider` |
| Per-module state files | `org.sensorhub.api.module.IModuleStateManager` | `org.sensorhub.impl.module.DefaultModuleStateManager` |
| Sub-modules | `org.sensorhub.api.module.ISubModule`, `org.sensorhub.api.module.SubModuleConfig` | `org.sensorhub.impl.module.AbstractSubModule` |
| Hub bootstrap | `org.sensorhub.api.ISensorHub`, `org.sensorhub.api.ISensorHubConfig` | `org.sensorhub.impl.SensorHub`, `org.sensorhub.impl.SensorHubConfig`, `org.sensorhub.impl.Activator` (OSGi) |

Source folders:
- API: [`sensorhub-core/.../api/module/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module), config annotations in [`api/config/DisplayInfo.java`](../../../sensorhub-core/src/main/java/org/sensorhub/api/config/DisplayInfo.java)
- Implementation: [`sensorhub-core/.../impl/module/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module), [`SensorHub.java`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java)

## Key types

### API (`org.sensorhub.api.module`)

| Type | Kind | Role (from code / javadoc) |
|---|---|---|
| [`IModuleBase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/IModuleBase.java#L29) | interface | Common to modules and sub-modules: `init(config)`, `start()`, `stop()`, `getConfiguration()`, `getName()` |
| [`IModule`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/IModule.java#L34) | interface | Extends `IModuleBase` and `IEventProducer`. Adds `setParentHub`, `init()`, `updateConfig`, `getCurrentState`, `waitForState`, `saveState`/`loadState`, `cleanup`, error/status getters. Javadoc on `init`/`start`/`stop`: "can be synchronous or asynchronous, but when this method returns without error, the module state is guaranteed to be either ..." the transitional or final state |
| [`ModuleConfigBase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/ModuleConfigBase.java#L29) | abstract class | Fields `moduleClass`, `name`. `clone()` is a deep clone via `ConfigCloner` |
| [`ModuleConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/ModuleConfig.java#L29) | class | Adds `id`, `description`, [`autoStart`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/ModuleConfig.java#L46) (JSON alias `enabled`, default `false`) |
| [`ModuleEvent`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/ModuleEvent.java#L28) | event | `Type`: `STATE_CHANGED`, `CONFIG_CHANGED`, `CONNECTED`, `DISCONNECTED`, `STATUS`, `ERROR`, `LOADED`, `UNLOADED`, `DELETED`. [`getSourceID()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/ModuleEvent.java#L162) returns the module's local ID |
| [`ModuleEvent.ModuleState`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/ModuleEvent.java#L81) | enum | `LOADED`, `INITIALIZING`, `INITIALIZED`, `STARTING`, `STARTED`, `STOPPING`, `STOPPED` (ordinal order is used in comparisons) |
| [`IModuleConfigRepository`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/IModuleConfigRepository.java#L29) | interface | `getAllModulesConfigurations`, `contains`, `get`, `add`, `update`, `remove`, `commit`, `close`, [`getModuleClassFinder()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/IModuleConfigRepository.java#L36) |
| [`IModuleProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/IModuleProvider.java#L26) | interface | Module type descriptor: name, description, version, provider, module class, config class. Javadoc: "enable automatic module discovery" |
| [`IModuleStateManager`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/IModuleStateManager.java#L22) | interface | Key/value getters and `put`s, `flush`, data files and streams |
| [`IModuleManager`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/IModuleManager.java#L31) | interface | `getLoadedModules`, `isModuleLoaded`, `getModuleById`. Implemented by `ModuleRegistry`; extended by `org.sensorhub.api.comm.INetworkManager` |
| [`ISubModule`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/ISubModule.java#L29) / [`SubModuleConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/module/SubModuleConfig.java#L26) | interface / class | Javadoc: "reusable components such as comm providers, message queues, data loggers, etc. that are managed by a parent module" |

`ISensorHub` [`getModuleRegistry()`](../../../sensorhub-core/src/main/java/org/sensorhub/api/ISensorHub.java#L49) returns the concrete `ModuleRegistry` class, not an interface.

### Implementation (`org.sensorhub.impl.module`)

| Type | Role |
|---|---|
| [`AbstractModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L44) | Default `IModule`: state machine, template methods (`beforeX`/`doX`/`afterX`), error/status reporting, a `BasicEventHandler` for listeners ([field](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L48)), default `ModuleSecurity` |
| [`ModuleRegistry`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L77) | Loads modules from the config repository, runs init/start/stop on a thread pool, forwards module events to the event bus, saves config and state |
| [`ModuleConfigJsonFile`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L64) | JSON file repository (Gson). Each object carries its class in an [`objClass`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L67) field |
| [`InMemoryConfigDb`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/InMemoryConfigDb.java#L34) | Map-backed repository. Javadoc: "In memory config database used by JUnit tests"; also used by `SensorHub` when no config path is set |
| [`ModuleClassFinder`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleClassFinder.java#L38) | Javadoc: "can find classes using the ServiceLoader API or OSGI service discovery" |
| [`JarModuleProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/JarModuleProvider.java#L31) | Base `IModuleProvider` reading name/description/version/vendor from the jar MANIFEST via `ModuleUtils.getModuleInfo` |
| [`DefaultModuleStateManager`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/DefaultModuleStateManager.java#L43) | `Properties` file [`state.txt`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/DefaultModuleStateManager.java#L46) plus `.dat` files in `{moduleDataPath}/{safe(moduleID)}/` |
| [`AbstractSubModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractSubModule.java#L36) | Base `ISubModule`; routes errors/status to the parent `AbstractModule`. Only subclass in repo: `org.sensorhub.impl.comm.LocalMessageQueue` |
| [`ModuleSecurity`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleSecurity.java#L26) | Per-module permission checks (see [Security](security.md)) |
| [`RobustConnection`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/RobustConnection.java#L35) | Reconnect helper for modules; subclassed by `org.sensorhub.impl.comm.RobustIPConnection` |

## How it works

### State machine (`AbstractModule`)

```
            init()                     (sync)                start()                (sync)
 LOADED ───────────► INITIALIZING ───────────► INITIALIZED ─────────► STARTING ───────────► STARTED
   ▲                     │ error                    ▲  (also from STOPPED)  │ error → stop()
   └─────────────────────┘                          │                       ▼
                                         stop() from any state except LOADED/STOPPING/STOPPED
                                                  STOPPING ──(sync)──► STOPPED
                                       (back to LOADED if stop() was called while INITIALIZING)
```

- [`canInit()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L394): requires a config; clears error and status; sets `INITIALIZING`. No check on the current state.
- [`init()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L412): `beforeInit()` (asserts config, runs `ConfigValidator`) → `doInit()` → `afterInit()`; sets `INITIALIZED` unless `initAsync`. On any `Throwable`: `reportError` then [`setState(LOADED)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L432). The exception is not rethrown.
- [`canStart()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L483): returns `false` (WARN "already started") if `STARTED`/`STARTING`; throws if state ordinal < `INITIALIZED`; else sets `STARTING`.
- [`start()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L507): `beforeStart` → `doStart` → `afterStart`; sets `STARTED` unless `startAsync`. On error: `reportError` then `stop()`.
- [`canStop()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L565) / [`stop()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L582): no-op from `LOADED`, `STOPPING`, `STOPPED`. Sets `STOPPED` unless `stopAsync`.
- Async modules set the [`initAsync, startAsync, stopAsync`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L53) flags and call `setState(...)` themselves later. Precedents: `SMLProcessImpl` and `SWEVirtualSensor` (`initAsync`), `SOSTClient` (`startAsync`).
- [`waitForState()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L215) waits on `stateLock` until the state ordinal reaches the target (special case for waiting on a restart). It throws if `getCurrentError()` is non-null; `timeout` 0 means forever.
- [`updateConfig()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L131): comment: "Default implementation is to re-init and restart the module when config was changed". Stops if started, sets config, publishes `CONFIG_CHANGED`, calls `init()`, then `start()` if it was started.
- `isInitialized()` is `state.ordinal() >= INITIALIZED`, so it is also true in `STOPPING`/`STOPPED`.

### How module events are emitted

| Event | Emitted by |
|---|---|
| `STATE_CHANGED` | [`AbstractModule.setState()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L194), only when the state actually changes; also `notifyAll` on `stateLock` |
| `ERROR` | [`reportError()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L288) (wraps the cause in `SensorHubException` when a message is given) |
| `STATUS` | [`reportStatus()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L347) |
| `CONNECTED` / `DISCONNECTED` | [`notifyConnectionStatus()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L379) |
| `CONFIG_CHANGED` | `AbstractModule.updateConfig` |
| `LOADED`, `DELETED` | `ModuleRegistry.loadModuleAsync` / `destroyModule`, by calling its own `handleEvent` |
| `UNLOADED` | [`ModuleRegistry.unloadModule()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L521), published directly on [`getPublisher(moduleID)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L526) |

Path to the event bus:
1. At load, the registry calls `module.registerListener(this)`. Module events are dispatched synchronously by the module's `BasicEventHandler` (see [Event bus](event-bus.md#per-object-listeners-basiceventhandler)).
2. [`ModuleRegistry.handleEvent()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1257) logs state changes, calls [`postInit()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1386) on `INITIALIZED` (loads saved state via `loadState`), completes matching [`waitForModule`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1362) futures, then publishes on [`getPublisher(EVENT_GROUP_ID, ...)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1312) (group `urn:osh:modules`, member topic = module local ID).
3. `AbstractModule.registerListener` sends the current state to a new listener unless it is `LOADED`.

### `ModuleRegistry` operations

- Constructor ([line 108](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L108)): `loadedModules` is a synchronized `LinkedHashMap`; `asyncExec` is `ThreadPoolExecutor(0, Integer.MAX_VALUE, 10s, SynchronousQueue)` with threads named `ModuleRegistry`.
- [`loadModuleAsync(config, listener, doAutoStart)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L272): returns the existing instance if the ID is loaded; assigns a random UUID if `id` is null; instantiates `moduleClass` via `loadModuleClass`; `setParentHub`, `setConfiguration`, registers listeners; emits `LOADED`; if `autoStart`, calls `startModuleAsync`.
- `initModuleAsync` / [`startModuleAsync(module)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L684) / `stopModuleAsync` / `restartModuleAsync` / `updateModuleConfigAsync` submit a task to `asyncExec`. Exceptions are logged, not propagated. `startModuleAsync` inits first if needed (waiting up to `DEFAULT_TIMEOUT_MS` = 5 s) and sets the thread context classloader to the module's classloader ([line 694](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L694)).
- Sync variants (`loadModule`, `initModule`, `startModule`, `stopModule`) call the async version, then `waitForState(..., timeOut)`. The no-timeout overloads pass `Long.MAX_VALUE`.
- [`getModuleById()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1041) loads the module from the config repository if it is not loaded yet.
- [`destroyModule()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L907): removes the config from the repository (no `commit`), removes the instance, `stop()`, state-manager `cleanup()`, `module.cleanup()`, unregisters it from the system driver registry if it is an `ISystemDriver`, emits `DELETED`.
- [`saveModulesConfiguration()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L947): updates every loaded module's config, removes configs of unloaded modules, then `commit()`. Called from `AdminUI`.
- [`loadSubModule(config, init)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L451) instantiates a module that the registry does not track. Javadoc: "the caller (i.e. usually the parent module) is responsible for managing the submodule life cycle". Callers: `SensorSystem`, `SystemDriverDatabase`. The `ISubModule` overload ([line 419](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L419)) has no caller in this repo.
- [`createModuleConfig(provider)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L480) builds a new config from an `IModuleProvider` (random UUID, name `"New " + moduleName`, `autoStart=false`). Used by `ModuleTypeSelectionPopup` in the admin UI.
- [`getStateManager()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1215) returns `null` when the hub has no module data path, which disables state save/load.

### Class finding and module types

- [`ModuleClassFinder.findClass()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleClassFinder.java#L55): with OSGi, tries `loadClass` on every non-uninstalled bundle; without OSGi, `Class.forName`.
- [`findModuleClass()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleClassFinder.java#L85): with OSGi, matches the name against each `IModuleProvider` service's module or config class, then falls back to `Class.forName`.
- [`getInstalledModuleTypes()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleClassFinder.java#L147): OSGi service references, or `ServiceLoader.load(IModuleProvider.class)`.
- Providers are registered in `META-INF/services/org.sensorhub.api.module.IModuleProvider` files in `sensorhub-core` (7 entries, e.g. `SensorSystemDescriptor`, `SMLProcessDescriptor`), `sensorhub-service-swe` (4), `sensorhub-service-consys` (2), `sensorhub-datastore-h2` (1), `sensorhub-webui-core` (1). Descriptor classes typically extend `JarModuleProvider` (e.g. `org.sensorhub.impl.comm.LocalMessageQueueDescriptor`).
- `ModuleConfigJsonFile` resolves `objClass` values through `classFinder.findClass` ([RuntimeTypeAdapterFactory](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L79)).

### Config persistence (`ModuleConfigJsonFile`)

- The constructor requires the file to exist, then parses it with lenient Gson. String values go through [`JsonReaderWithVarExpansion`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L340) (`ModuleUtils.expand`). Duplicate IDs throw.
- [`commit()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L268): if `keepBackup`, moves the old file to `<file>.bak.<yyyyMMddHHmmss>`, then rewrites the whole file.
- `close()` does nothing: `commit()` is [commented out](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L293) with comment "it overrides changes made to config file everytime!".
- `getAllModulesConfigurations()` re-reads the file if the in-memory map is empty.

### Hub boot (`SensorHub.start()`)

[`start()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L105) (synchronized, runs once):
1. Logs version, JDK, OS and CPU info.
2. If no repository was passed in, creates a `ModuleClassFinder(osgiContext)` plus a `ModuleConfigJsonFile(path, keepBackup=true)`, or an `InMemoryConfigDb` when `getModuleConfigPath()` is null ([lines 124-130](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L124-L130)).
3. Creates `ModuleRegistry`, `EventBus`, `DefaultDatabaseRegistry`, `DefaultSystemRegistry` (with `InMemorySystemStateDbConfig`), `SecurityManagerImpl`, `NetworkManagerImpl`, `ProcessingManagerImpl`, and `IdEncodersDES` or `IdEncodersBase32` ([lines 133-142](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L133-L142)).
4. `ClientAuth.createInstance("keystore")`.
5. [`moduleRegistry.loadAllModules()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L148), then `started = true`.

[`loadAllModules()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L125):
1. For each config in repository order: rejects a duplicate `DatabaseConfig.databaseNum` ([line 137](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L137)); loads a clone with auto-start deferred. Load errors are logged and skipped.
2. Splits loaded modules into `IDatabase`/`IDataStore` and the rest.
3. Starts auto-start datastores and waits up to `DB_STARTUP_TIMEOUT_MS` (60 s) for all to reach `STARTED`. Any failure or timeout throws [`"Error starting datastores"`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L193).
4. Calls `startModuleAsync` on every other auto-start module, without waiting.

Stop: [`stop(saveConfig, saveState)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L169) → [`ModuleRegistry.shutdown()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L1092) → `eventBus.shutdown()`. Shutdown stops non-datastores first, then datastores (each batch waits up to `SHUTDOWN_TIMEOUT_MS` = 10 s). It optionally updates config and calls `saveState`, shuts down the executor, warns about modules not stopped, and calls `configRepo.close()`. `stop()` uses `(false, true)` and `saveAndStop()` uses `(true, true)`.

Entry points: [`SensorHub.main()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L263) (args `<module_config_path> [module_data_path] [options]`, plus a shutdown hook calling `stop()`) and the OSGi [`Activator.start()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/Activator.java#L30). The Activator reads property `org.sensorhub.config` and starts the hub on `FrameworkEvent.STARTED`. `SensorHubConfig` defaults the module data path to `.moduledata` ([line 42](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHubConfig.java#L42)) only in its 2-arg constructor.

## Observed behaviours to be aware of

None of these is covered by a test in `TestModuleRegistry` or `TestAsyncModule`.

1. **One failed datastore stops the whole boot.** In `loadAllModules`, wait futures complete only on `STARTED`. A datastore whose `start()` fails ends in `STOPPED`, so the 60 s timeout fires and `SensorHubException` is thrown. Non-datastore modules are then never started, and `SensorHub.started` stays `false`, so a later `stop()` does nothing.
2. **Boot order is datastores-first only.** The comment at [`SensorHub` L147](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L147) says "in the order implied by dependency constraints". `loadAllModules` has no other ordering logic; modules that depend on each other use `waitForModule`/`waitForState` themselves (e.g. `AsyncModule` in test fixtures).
3. **`unloadModule` can block forever.** It calls `stopModule(id)` (timeout `Long.MAX_VALUE`). For a module in `LOADED` state, `canStop()` returns false, so `STOPPED` is never reached. `unloadModule` has no callers in this repo.
4. **`init()` errors are swallowed.** `AbstractModule.init` catches all errors, resets to `LOADED` and does not rethrow. Callers detect failure through `getCurrentError()` or `waitForState`, which throws when an error is recorded.
5. **`start()` is accepted while `STOPPING`.** `canStart` only rejects ordinals below `INITIALIZED` and `STARTED`/`STARTING`.
6. **Javadoc vs code, `registerListener`.** `IModule` javadoc: "the current state of the module is also notified synchronously to guarantee that the listener always receives it". [`AbstractModule.registerListener`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/AbstractModule.java#L666) skips this when the state is `LOADED`.
7. **`destroyModule` does not commit.** The removal from `ModuleConfigJsonFile` only reaches disk on a later `commit()` (e.g. `saveModulesConfiguration`).
8. **Saved config contains expanded variables.** `JsonReaderWithVarExpansion` has a [TODO](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L353): "save original string w/ variable so we can save it back". `commit()` therefore writes the expanded values.
9. **Repository implementations differ.** `InMemoryConfigDb.get` returns `null` for an unknown ID and `add` overwrites duplicates. `ModuleConfigJsonFile.get` and `add` throw `IllegalArgumentException`, as the `add` javadoc in `IModuleConfigRepository` requires.
10. **Bypassed topic helpers.** Module events use the raw local ID as topic. `EventUtils.getModuleTopicID` and `getModuleRegistryTopicID` (`modules/...`) have no callers in this repo.
11. **`-useSecureIds` option.** `main()` prints `-useSecureIds`, but tests [`argMap.containsKey("useSecureIds")`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L302) without the dash. Options are read only from the third argument onwards.

**Open questions** (dead or suspicious code; all `.java` files searched):
- `ModuleRegistry.isDataStoreModule` ([line 206](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L206)) is never called. Field `allModulesLoaded` is never read, and `shutdownCalled` is written but never read ([lines 93-94](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleRegistry.java#L93-L94)).
- `IModuleManagerFactory` has no implementations or references.
- `ModuleRegistry.saveConfiguration`, `getModuleRef`, `waitForModuleType`, `getModuleDataFolder` and `unloadModule` have no callers in this repo. **Inferred:** they may be used by external module repositories.
- [`ModuleClassFinder.findServiceClass()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleClassFinder.java#L115) casts a service *instance* to `Class<T>` ([line 126](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleClassFinder.java#L126)) and has no callers.
- `org.sensorhub.api.module.IModuleConfigRepository` (API package) imports `org.sensorhub.impl.module.ModuleClassFinder`. `ISensorHub` likewise returns `ModuleRegistry`.
- `ModuleSecurity` constructor has the module permission registrations commented out.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Write a new module | Extend `AbstractModule<MyConfig>`, override `doInit`/`doStart`/`doStop`. `MyConfig` extends `ModuleConfig` (or a subtype). Test fixture example: `org.sensorhub.impl.module.AsyncModule` |
| Make a module discoverable | Add a descriptor extending `JarModuleProvider` and list it in `META-INF/services/org.sensorhub.api.module.IModuleProvider`, as `LocalMessageQueueDescriptor` does |
| Async init/start | Set `initAsync`/`startAsync` and call `setState(...)` when done (`SMLProcessImpl`, `SOSTClient`) |
| Wait for another module | `ModuleRegistry.waitForModule(id, ModuleState.STARTED)` (as `loadAllModules` does) or `module.waitForState(...)` (`SystemDriverDatabase`) |
| Module owning child modules | `getModuleRegistry().loadSubModule(config, init)` as in `SensorSystem`; or `ISubModule` + `AbstractSubModule` as in `LocalMessageQueue` |
| Persist module state | Override `saveState`/`loadState` with the given `IModuleStateManager` (needs a module data path) |
| Change boot order or startup timeouts | `ModuleRegistry.loadAllModules`, constants `DEFAULT_TIMEOUT_MS`, `DB_STARTUP_TIMEOUT_MS`, `SHUTDOWN_TIMEOUT_MS` |
| Add a hub-wide component | Construct it in `SensorHub.start()` and expose it via a getter on `ISensorHub` |

## Tests

| Test class | Covers |
|---|---|
| [`TestModuleRegistry`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/module/TestModuleRegistry.java) | config cloning, installed module types, load / async init / start / restart, start with dependency, group events on `EVENT_GROUP_ID` |
| [`TestAsyncModule`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/module/TestAsyncModule.java) | async init/start/stop/restart, timeouts, start called twice, start while initializing |
| [`TestModuleConfigJsonFile`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/module/TestModuleConfigJsonFile.java) | add, remove, read back |

Fixtures in `sensorhub-core/src/testFixtures/.../impl/module`: [`AsyncModule`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/module/AsyncModule.java) / [`AsyncModuleConfig`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/module/AsyncModuleConfig.java) (configurable delays and dependencies), [`DummyModule`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/module/DummyModule.java) (direct `IModule` implementation), `MyConfig1`, `MyConfig2`.

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.module.TestModuleRegistry'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.module.TestAsyncModule'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.module.TestModuleConfigJsonFile'
```

## Related

- [Code map index](../index.md)
- [Event bus](event-bus.md), for how forwarded module events are delivered
- [System registry](system-registry.md), [Databases](databases.md), [Sensor drivers](sensor-drivers.md), [Admin web UI](webui.md), [Security](security.md)
- Legacy Maven-site pages under `sensorhub-core/src/site/markdown/` (partly outdated; see `AGENTS.md`)
