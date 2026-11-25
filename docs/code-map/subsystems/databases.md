# Databases & Datastores (API, federated DB)

> Status: first version. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Storage abstractions in `sensorhub-core`, and the hub-level registry that combines several
databases into one read-only view:

| Layer | Package | Content |
|---|---|---|
| Database API | `org.sensorhub.api.database` | Database interfaces (a database = a set of datastores), registry interface, base config |
| Datastore API | `org.sensorhub.api.datastore.*` | `Map`-like store interfaces, keys, filter/query classes, `Empty*` placeholder stores |
| Registry + federated DB | `org.sensorhub.impl.database.registry` | `DefaultDatabaseRegistry`, `FederatedDatabase` and one `Federated*Store` per store type |
| System driver DB wrapper | `org.sensorhub.impl.database.system` | `SystemDriverDatabase` module, auto-purge policy |
| Helpers, in-memory stores, views | `org.sensorhub.impl.datastore`, `.mem`, `.view` | `DataStoreUtils`, `MergeSortSpliterator`, `InMemory*` stores, filtered `*View` stores |

The persistent implementation (H2 MVStore) is in a separate module: see [H2 datastore](datastore-h2.md).

Source folders:
- API: [`api/database/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database), [`api/datastore/`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore)
- Implementation: [`impl/database/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database), [`impl/datastore/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore)

## Key types

### Database interfaces (`org.sensorhub.api.database`)

| Type | Extends | Role (from code / javadoc) |
|---|---|---|
| [`IDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IDatabase.java#L29) | — | `getDatabaseNum()`, `executeTransaction(Callable)`, `commit()`, `isOpen()`, `isReadOnly()`. Javadoc: "A database contains one or more data stores." |
| [`IObsSystemDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IObsSystemDatabase.java#L46) | `IDatabase` | System, FOI, obs, command and deployment stores. `getDataStreamStore()`, `getCommandStreamStore()`, `getCommandStatusStore()` are defaults that delegate to the obs/command store |
| [`IProcedureDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IProcedureDatabase.java#L48) | `IDatabase` | `getProcedureStore()`, `getPropertyStore()` |
| [`IFeatureDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IFeatureDatabase.java#L28) | `IDatabase` | `getFeatureStore()` |
| [`IFederatedDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IFederatedDatabase.java#L28) | all three above | Marker for the hub's federated DB |
| [`ISystemStateDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/ISystemStateDatabase.java#L31) | `IObsSystemDatabase` | Marker. Javadoc: implementations "are not required to maintain full history" |
| [`ISystemDriverDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/system/ISystemDriverDatabase.java#L33) | `IObsSystemDatabase`, `IProcedureDatabase` | Adds `getHandledSystems()` (in `api.system`) |
| [`IObsSystemDatabaseModule`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IObsSystemDatabaseModule.java#L20) | `IObsSystemDatabase`, `IModule` | Type for DB implementations that are also modules |
| [`DatabaseConfig`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/DatabaseConfig.java#L30) | `ModuleConfig` | Single field `databaseNum` (`@Required`, but its description says it "can be omitted") |
| [`IDatabaseRegistry`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IDatabaseRegistry.java#L43) | — | `register`/`unregister`, lookups by number or module ID, typed collections, `getFederatedDatabase()` |
| [`IObsSystemDbAutoPurgePolicy`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IObsSystemDbAutoPurgePolicy.java#L31) | — | `trimStorage(db, log, systemUIDs)` |
| [`IDatabaseModuleDescriptor`](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IDatabaseModuleDescriptor.java#L27) | — | `isReadOnly()`. Only checked by the web UI (`SystemDriverDatabaseConfigForm`); no implementations in this repo |

### Datastore interfaces (`org.sensorhub.api.datastore.*`)

[`IDataStore<K, V, VF, Q>`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/IDataStore.java#L50) extends `java.util.Map<K, V>`.
It adds `selectEntries(query, fields)` (the one abstract query method), plus defaults `select`, `selectKeys`,
`removeEntries`, `countMatchingEntries` and `getNumRecords`, all built on `selectEntries`. It also declares `commit`, `backup`, `restore`
and `selectAllFilter`. [`IResourceStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/resource/IResourceStore.java#L34)
adds `add(V)` and a typed `filterBuilder()`.

| Store interface | Key | Value | Filter | Notes |
|---|---|---|---|---|
| [`ISystemDescStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/system/ISystemDescStore.java#L34) | `FeatureKey` | `ISystemWithDesc` | `SystemFilter` | Via [`IFeatureStoreBase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/feature/IFeatureStoreBase.java#L41): versioned by valid time, `add(parentID, f)`, `getCurrentVersion(uid)` |
| [`IFoiStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/feature/IFoiStore.java#L32) / [`IFeatureStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/feature/IFeatureStore.java#L29) | `FeatureKey` | `IFeature` | `FoiFilter` / `FeatureFilter` | `IFeatureStoreBase` |
| [`IDeploymentStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/deployment/IDeploymentStore.java#L32), [`IProcedureStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/procedure/IProcedureStore.java#L31) | `FeatureKey` | `IDeploymentWithDesc` / `IProcedureWithDesc` | `DeploymentFilter` / `ProcedureFilter` | `IFeatureStoreBase` |
| [`IDataStreamStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/obs/IDataStreamStore.java#L34) | `DataStreamKey` | `IDataStreamInfo` | `DataStreamFilter` | `getLatestVersion(sysUID, outputName)` |
| [`IObsStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/obs/IObsStore.java#L42) | `BigId` | `IObsData` | `ObsFilter` | `add(obs)`, `getDataStreams()`, `selectObservedFois`, `getStatistics(ObsStatsQuery)` |
| [`ICommandStreamStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/command/ICommandStreamStore.java#L34) | `CommandStreamKey` | `ICommandStreamInfo` | `CommandStreamFilter` | |
| [`ICommandStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/command/ICommandStore.java#L39) | `BigId` | `ICommandData` | `CommandFilter` | `getCommandStreams()`, `getStatusReports()` |
| [`ICommandStatusStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/command/ICommandStatusStore.java#L34) | `BigId` | `ICommandStatus` | `CommandStatusFilter` | |
| [`IPropertyStore`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/property/IPropertyStore.java#L31) | `PropertyKey` | `IDerivedProperty` | `PropertyFilter` | |

Stores are wired to each other with `linkTo(...)` methods (e.g. `IObsStore.linkTo(IFoiStore)`), so a
filter on one store can contain a nested filter on another.

### Filters and IDs

- All filters implement [`IQueryFilter`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/IQueryFilter.java#L18) (`getLimit()`) and `Predicate<V>`. They are immutable and built with nested `Builder` classes (`new ObsFilter.Builder()...build()`, `ObsFilter.Builder.from(f)` to copy).
- Resource filters derive from [`ResourceFilter`](../../../sensorhub-core/src/main/java/org/sensorhub/api/resource/ResourceFilter.java#L45) (internal IDs, full text, value predicate, limit); feature filters from [`FeatureFilterBase`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/feature/FeatureFilterBase.java#L51) (adds UIDs, valid time, location, `includeMembers`).
- [`ObsFilter`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/obs/ObsFilter.java#L45), `CommandFilter`, `CommandStatusFilter` implement `IQueryFilter` directly. `ObsFilter` holds internal IDs, phenomenon/result `TemporalFilter`s, a `SpatialFilter`, nested `DataStreamFilter` and `FoiFilter`, a value predicate and a limit.
- Building blocks: [`TemporalFilter`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/TemporalFilter.java#L34) (adds "now", "latest" and descending order), [`SpatialFilter`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/SpatialFilter.java#L35), [`VersionFilter`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/VersionFilter.java#L31), [`FullTextFilter`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/FullTextFilter.java#L37), [`RangeOrSet`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/RangeOrSet.java#L38).
- Filters have `intersect(other)`, which throws [`EmptyFilterIntersection`](../../../sensorhub-core/src/main/java/org/sensorhub/api/datastore/EmptyFilterIntersection.java#L19) when the result can match nothing (used by the `*View` stores).
- Filters are (de)serialized in module config JSON by [`DataStoreFiltersTypeAdapterFactory`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/DataStoreFiltersTypeAdapterFactory.java#L66), registered in `ModuleConfigJsonFile` ([gson builder](../../../sensorhub-core/src/main/java/org/sensorhub/impl/module/ModuleConfigJsonFile.java#L194)).
- IDs are [`BigId`](../../../sensorhub-core/src/main/java/org/sensorhub/api/common/BigId.java#L43): a `scope` (int) plus a variable-length byte ID. Javadoc: "The local ID part is typically used as the database local ID while the combination of scope and ID is used as a public ID (for example by the federated database)." `FeatureKey`, `DataStreamKey`, etc. wrap a `BigId` (plus a valid time for features).

### Implementation types

| Type | Role |
|---|---|
| [`DefaultDatabaseRegistry`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/DefaultDatabaseRegistry.java#L45) | Only `IDatabaseRegistry` implementation. `Map<Integer, IDatabase>` keyed by database number; typed collections are filtered live views of it |
| [`FederatedDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedDatabase.java#L41) | Read-only `IFederatedDatabase`. Holds one `Federated*Store` per store type; routes by `BigId.getScope()` |
| `Federated{SystemDesc,Foi,Deployment,Procedure,Feature}Store` | Extend [`FederatedBaseFeatureStore`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedBaseFeatureStore.java#L49) |
| `Federated{Obs,DataStream,Command,CommandStream,CommandStatus,Property}Store` | Extend `ReadOnlyDataStore` directly |
| [`FilteredFederatedDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FilteredFederatedDatabase.java#L42) | `FederatedDatabase` that wraps member DBs in `ObsSystemDatabaseView` / `ProcedureDatabaseView`. Used by `ConSysApiService` and `SWEService` |
| [`SystemDriverDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/system/SystemDriverDatabase.java#L45) | Module wrapping another DB module (`config.dbConfig`), mapping it to system UIDs and running auto-purge timers |
| [`MaxAgeAutoPurgePolicy`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/system/MaxAgeAutoPurgePolicy.java#L43) | Only purge policy; configured by `MaxAgeAutoPurgeConfig` (`maxRecordAge`, default 7 days) |
| [`InMemorySystemStateDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/mem/InMemorySystemStateDatabase.java#L38) | `ISystemStateDatabase` built from `InMemory*` stores; the hub's default state DB |
| [`ObsSystemDatabaseView`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/view/ObsSystemDatabaseView.java#L33), [`ProcedureDatabaseView`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/view/ProcedureDatabaseView.java#L27) | Read-only DB views that intersect every query with a fixed filter |
| [`ReadOnlyDataStore`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/ReadOnlyDataStore.java#L37) | Base class whose `put`/`remove`/`clear`/`commit` throw `UnsupportedOperationException` |
| [`MergeSortSpliterator`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/MergeSortSpliterator.java#L31) | Merges pre-sorted streams; javadoc: "The source streams must already be ordered according to the specified Comparator." |
| [`DataStoreUtils`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/DataStoreUtils.java#L60) | Key/value validation helpers, `selectXxxIDs(store, filter)` helpers, hash-based `IdProvider` factories |

In-memory stores in [`impl/datastore/mem/`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/mem):
`InMemorySystemStore`, `InMemoryFoiStore`, `InMemoryDeploymentStore`, `InMemoryProcedureStore`, `InMemoryFeatureStore`
(all on `InMemoryBaseFeatureStore`), `InMemoryDataStreamStore`, `InMemoryObsStore`, `InMemoryCommandStreamStore`,
`InMemoryCommandStore`, `InMemoryCommandStatusStore`, `InMemoryPropertyStore`, plus `InMemoryProcedureDatabase`.
Javadoc of the feature, obs and command stores says they are "only used to store the latest system state".

## How it works

### Startup and registration

1. `SensorHub.start()` creates [`new DefaultDatabaseRegistry(this)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L135), then `DefaultSystemRegistry` with an `InMemorySystemStateDbConfig` (line 136).
2. [`DefaultSystemRegistry.initDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L88) creates a `SystemDriverDatabase` with `databaseNum = 0` wrapping that in-memory config, and starts it.
3. `SystemDriverDatabase.doStart()` loads the wrapped DB as a sub-module, copying `databaseNum` into its config. [`afterStart()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/system/SystemDriverDatabase.java#L116) then:
   - maps its `systemUIDs` to itself via `ISystemDriverRegistry.registerDatabase(...)`;
   - registers itself in the database registry if `databaseNum != null`.
4. Other DB modules (e.g. `MVObsSystemDatabase`) call `getDatabaseRegistry().register(this)` in `afterStart()` when `databaseNum` is set, and `unregister` in `beforeStop()`.
5. [`DefaultDatabaseRegistry.register`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/DefaultDatabaseRegistry.java#L86) checks `dbNum != null && dbNum < 100` ([`checkDbNum`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/DefaultDatabaseRegistry.java#L116)) and throws `IllegalStateException` if the number is already taken.

The **system UID → database** mapping used when drivers write data lives in `DefaultSystemRegistry`
([`registerDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L281), a `MapWithWildcards`), not in the database registry.
A driver with no mapped DB is written to the state DB ([`getDatabaseForDriver`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L263)).
See [System registry](system-registry.md).

### ID scoping

- Each DB implementation creates IDs with `scope = databaseNum` (e.g. `InMemoryObsStore(idScope)`, `BigId.fromLong(idScope, ...)` in [`InMemoryBaseFeatureStore`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/mem/InMemoryBaseFeatureStore.java#L127)). There is no separate public/local ID translation in the federated DB.
- [`FederatedDatabase.getObsSystemDatabase(id)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedDatabase.java#L80) is `registry.getObsDatabaseByNum(id.getScope())`. Procedure and feature DBs are resolved the same way.
- `TestFederatedDatabaseRegistry.testPublicKeys` asserts that keys returned by the federated store equal the member DB's keys and that `getScope()` equals the DB number.
- String IDs exposed by services come from `IdEncoders` (`SensorHub` [start-up](../../../sensorhub-core/src/main/java/org/sensorhub/impl/SensorHub.java#L142): `IdEncodersDES` if `useSecureIds`, else `IdEncodersBase32`). Hash ID providers keep 42 bits; code comment: "so it can fit on a 8-bytes DES encrypted block, along with the ID scope" ([`getFeatureHashIdProvider`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/DataStoreUtils.java#L448)).

### Query routing in the federated DB

Each federated store builds a **dispatch map** `Map<dbNum, LocalFilterInfo{db, ids, filter}>`:

```
selectEntries(filter)
  → getFilterDispatchMap(filter)
      internal IDs set?      → group IDs by scope (getObsDbFilterDispatchMap), one filter per DB with only its IDs
      nested filter set?     → ask the other federated store for its dispatch map, re-wrap each per-DB filter
      neither                → null
  → map != null : query only the DBs in the map, with their per-DB filter
    map == null : query every registered DB with the original filter
  → obs / commands / status: MergeSortSpliterator over per-DB streams, then limit
    resources / features   : flatMap (concatenate) per-DB streams, then limit
```

- [`FederatedObsStore.getFilterDispatchMap`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedObsStore.java#L125) combines the datastream and FOI dispatch maps per DB.
- [`FederatedDataStreamStore.getFilterDispatchMap`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedDataStreamStore.java#L123) uses internal IDs, else the nested system filter, else the nested obs filter.
- [`FederatedSystemDescStore.getFilterDispatchMap`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedSystemDescStore.java#L69) skips routing on a parent filter whose first internal ID is 0 ("top level resource"; [lines 94–99](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedSystemDescStore.java#L94-L99)).
- `get(key)` / `containsKey(key)` go straight to the DB chosen by the key's scope. `getNumRecords()` sums over all DBs.
- Every write method, `commit()` and `executeTransaction()` throws `UnsupportedOperationException`; [`getDatabaseNum()`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedDatabase.java#L247) also throws.

### Filtered views

- [`FilteredFederatedDatabase`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FilteredFederatedDatabase.java#L86) takes obs/command/procedure filters plus a list of `unfilteredDatabases` numbers. `ConSysApiService` passes the write DB's number (`ConSysApiService`, [call site](../../../sensorhub-service-consys/src/main/java/org/sensorhub/impl/service/consys/ConSysApiService.java#L146)); `SWEService` does the same ([call site](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEService.java#L79)).
- [`ObsSystemDatabaseView`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/view/ObsSystemDatabaseView.java#L55) replaces a null obs or command filter with one matching `BigId.NONE` ("create filter that will never match anything") and derives a system filter from the nested datastream or command-stream filter.
- View stores call `viewFilter.intersect(filter)` and return an empty stream on `EmptyFilterIntersection` (e.g. [`ObsStoreView.selectEntries`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/view/ObsStoreView.java#L57)).
- [`ObsSystemDatabaseViewConfig.getFilteredView`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/view/ObsSystemDatabaseViewConfig.java#L52) builds a view from config, over the federated DB or a named DB module.

### Auto-purge

`SystemDriverDatabase.doStart()` creates one `java.util.Timer` and schedules each enabled `HistoricalObsAutoPurgeConfig`
every `purgePeriod` seconds ([lines 84–111](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/system/SystemDriverDatabase.java#L84-L111)).
[`MaxAgeAutoPurgePolicy.trimStorage`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/system/MaxAgeAutoPurgePolicy.java#L57) removes systems, FOIs,
datastreams and command streams whose valid time ended before `now - maxRecordAge`, then old obs per remaining datastream.

## Observed behaviours to be aware of

1. **Federated merge order may not match member order.** `FederatedObsStore` merges per-DB streams by phenomenon time only ([merge comparator](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FederatedObsStore.java#L230)). `MVObsStoreImpl` orders its output by result time first ([`comparator`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L465)). `MergeSortSpliterator` requires its inputs to be sorted by the same comparator. **Open question:** whether federated obs results are correctly ordered when result time ≠ phenomenon time.
2. **`unfilteredDatabases` only applies to scans.** [`FilteredFederatedDatabase.getObsSystemDatabase(id)`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/FilteredFederatedDatabase.java#L98) always wraps the DB in a view, whereas `getAllObsDatabases()` skips unfiltered DBs. So lookups by ID (`get`, dispatch by internal IDs) apply the filter even to an "unfiltered" DB.
3. **Some views do not filter `get(key)`.** `ObsStoreView`, `CommandStoreView` and `CommandStatusStoreView` delegate `get` without checking the view filter ([`ObsStoreView.get`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/view/ObsStoreView.java#L89)); the datastream, command-stream, feature and property views do check it.
4. **Database number validation.** [`DB_NUM_ERROR_MSG`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/database/registry/DefaultDatabaseRegistry.java#L52) says "> 0", but `checkDbNum` only checks `< 100`. Number 0 is used by the hub's own state DB. `DEFAULT_DB_ID`, `MAX_NUM_DB_BIGINT` and `END_PREFIX_CHAR` are unreferenced.
5. **Registry javadoc vs code.** `IDatabaseRegistry` javadoc says it "keeps track of which database contains data for each system" and that `register` maps the UIDs from `getHandledSystems()` ([javadoc](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IDatabaseRegistry.java#L47-L53)). `DefaultDatabaseRegistry.register` stores only number → DB; the UID mapping is done by `SystemDriverDatabase` through `ISystemDriverRegistry`.
6. **Unregistering does not re-route live drivers.** `DefaultSystemRegistry.unregisterDatabase` has `// TODO update DB used by transaction handlers on the fly!` ([line 341](../../../sensorhub-core/src/main/java/org/sensorhub/impl/system/DefaultSystemRegistry.java#L341)).
7. **`InMemoryProcedureDatabase.propStore` is never assigned**, so `getPropertyStore()` returns `null` ([field](../../../sensorhub-core/src/main/java/org/sensorhub/impl/datastore/mem/InMemoryProcedureDatabase.java#L38)). It is used only in `TestFederatedDatabaseRegistry`.
8. **Javadoc points to the wrong placeholder.** `IObsSystemDatabase.getObservationStore()` javadoc says to return `EmptyCommandStore` ([line 70](../../../sensorhub-core/src/main/java/org/sensorhub/api/database/IObsSystemDatabase.java#L70)). There are also two `EmptyCommandStore` classes: `org.sensorhub.api.datastore.command.EmptyCommandStore` (referenced only from that javadoc) and `org.sensorhub.impl.datastore.command.EmptyCommandStore` (used by `DataStoreUtils.EMPTY_COMMAND_STORE`).
9. **Unreferenced types / fields** (searched all modules): `AsyncStream`, `IteratorWrapper`, `EmptyObsStore`, `InMemoryPropertyStore`, `ObsDelegate`, `CommandDelegate`, `CommandStatusDelegate`. `EmptySystemStore`, `EmptyFoiStore` and `EmptyDeploymentStore` appear only in javadoc. `SystemDriverDatabaseConfig.minCommitPeriod` and `SystemDriverDatabase.lastCommitTime` are never read.
10. **`InMemorySystemStateDatabase.executeTransaction` throws `UnsupportedOperationException`**; `commit()` is a no-op.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| New database implementation | Module class extending `AbstractModule<C>` with `C extends DatabaseConfig`, implementing `IObsSystemDatabaseModule` (and optionally `IProcedureDatabase`), as `MVObsSystemDatabase`. Create IDs with scope = `databaseNum`. Call `getDatabaseRegistry().register(this)` in `afterStart()` and `unregister` in `beforeStop()`. Add a `JarModuleProvider` descriptor and list it in `META-INF/services/org.sensorhub.api.module.IModuleProvider` |
| Store type a DB does not support | Return an `Empty*Store` (`api.datastore.*`), as `SystemDriverDatabase.getProcedureStore()` does |
| New store type | Interface in `api.datastore.<x>` extending `IDataStore`/`IResourceStore`; getter on a DB interface; `Federated<X>Store` registered in the `FederatedDatabase` constructor; `<X>StoreView`; in-memory store if the state DB needs it |
| New filter criterion | Field + builder method + `test`/`intersect` on the filter class; then each store's `selectEntries`; and federated `getFilterDispatchMap` if it nests another store's filter |
| New purge policy | Subclass `HistoricalObsAutoPurgeConfig` (`getPolicy()`) and implement `IObsSystemDbAutoPurgePolicy`, as `MaxAgeAutoPurgeConfig` / `MaxAgeAutoPurgePolicy` |
| Expose a filtered subset to a service | `FilteredFederatedDatabase` or `ObsSystemDatabaseViewConfig.getFilteredView`, as in `ConSysApiService` |

## Tests

| Test | Covers |
|---|---|
| [`TestFederatedDatabaseRegistry`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/database/registry/TestFederatedDatabaseRegistry.java) | Register, duplicate DB numbers, empty DBs, key scope through the federated store |
| [`TestInMemObsStore`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/datastore/mem/TestInMemObsStore.java), `TestInMemDataStreamStore`, `TestInMemCommandStore`, `TestInMemCommandStreamStore`, `TestInMemFeatureStore` | In-memory stores, run against the shared abstract suites |
| [`TestDatastoreFilters`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/datastore/TestDatastoreFilters.java), [`TestTemporalFilter`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/datastore/TestTemporalFilter.java), [`TestSpatialFilter`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/datastore/TestSpatialFilter.java) | Filter building, `test`, `intersect` |
| [`TestGsonFilterTypeAdapters`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/datastore/TestGsonFilterTypeAdapters.java) | JSON (de)serialization of filters |
| [`TestMergeSortSpliterator`](../../../sensorhub-core/src/test/java/org/sensorhub/impl/datastore/TestMergeSortSpliterator.java) | Merge-sort of pre-ordered streams |

Shared abstract suites in [`src/testFixtures/.../impl/datastore/`](../../../sensorhub-core/src/testFixtures/java/org/sensorhub/impl/datastore):
`AbstractTestObsStore`, `AbstractTestDataStreamStore`, `AbstractTestCommandStore`, `AbstractTestCommandStreamStore`,
`AbstractTestFeatureStore`, `AbstractTestObsDatabase`. A subclass implements `initStore()` (or `initDatabase()`) and `forceReadBackFromStorage()`.

```bash
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.database.registry.TestFederatedDatabaseRegistry'
./gradlew :sensorhub-core:test --tests 'org.sensorhub.impl.datastore.*'
```

No test covers `FilteredFederatedDatabase`, the `*View` stores, `SystemDriverDatabase` or `MaxAgeAutoPurgePolicy` directly.

## Related

- [Code map index](../index.md)
- [H2 datastore](datastore-h2.md) — the persistent `IObsSystemDatabase` implementation
- [System registry](system-registry.md) — system UID → database mapping, transaction handlers that write to stores
- [Module lifecycle](module-lifecycle.md) — database modules are ordinary modules
- [Connected Systems API service](service-consys.md), [SWE services](service-swe.md) — main readers of the federated DB
- [Kryo serialization](kryo-serialization.md)
