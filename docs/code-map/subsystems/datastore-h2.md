# H2 Datastore

> Status: first version. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Gradle project `sensorhub-datastore-h2` ([`build.gradle`](../../../sensorhub-datastore-h2/build.gradle)): persistent
implementations of the datastore interfaces described in [Databases & datastores](databases.md), on top of the
H2 **MVStore** key/value engine (`com.h2database:h2-mvstore:1.4.200`). Values are serialized with Kryo
(project `sensorhub-utils-kryo`). Lucene's `EnglishAnalyzer` (`lucene-analyzers-common:8.11.2`) is used for full-text tokens.

| Package | Content |
|---|---|
| `org.sensorhub.impl.datastore.h2` | Database modules, configs, one `MV*StoreImpl` per store type, key classes and H2 `DataType`s |
| `org.sensorhub.impl.datastore.h2.kryo` | `KryoDataType` (generic Kryo-backed `DataType`), persistent class-ID resolver |
| `org.sensorhub.impl.datastore.h2.index` | `FullTextIndex`, `SpatialIndex` |
| `org.h2.mvstore` (in this module) | Extensions placed in H2's own package: `MVBTreeMap`, `RangeCursor`, `RTreeEntryCursor`, etc. |

**Inferred:** the `org.h2.mvstore` package is reused so these classes can access package-private H2 members.

Source folder: [`sensorhub-datastore-h2/src/main/java/`](../../../sensorhub-datastore-h2/src/main/java)

## Key types

### Modules and configuration

| Type | Role |
|---|---|
| [`MVObsSystemDatabase`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsSystemDatabase.java#L48) | Module implementing `IObsSystemDatabase`, `IProcedureDatabase`, `IObsSystemDatabaseModule`. One MVStore file holds 7 stores (system, deployment, FOI, obs, command, procedure, property) |
| [`MVFeatureDatabase`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVFeatureDatabase.java#L35) | Module implementing `IFeatureDatabase` with one `MVFeatureStoreImpl` (`feature_store`) |
| [`MVDatabaseConfig`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVDatabaseConfig.java#L31) | Abstract config: `storagePath`, `memoryCacheSize` (KB), `autoCommitBufferSize` (KB), `autoCommitPeriod` (s), `autoCompactFillRate`, `idProviderType`, `useCompression`, `readOnly`, `compactOnClose`, `printDebugInfoOnClose` |
| [`MVObsSystemDatabaseConfig`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsSystemDatabaseConfig.java#L28) / `MVFeatureDatabaseConfig` | Concrete configs; obs config adds `indexObsLocation` |
| [`MVObsSystemDatabaseDescriptor`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsSystemDatabaseDescriptor.java#L30) | Module provider "H2 Historical Obs Database"; listed in [`META-INF/services/org.sensorhub.api.module.IModuleProvider`](../../../sensorhub-datastore-h2/src/main/resources/META-INF/services/org.sensorhub.api.module.IModuleProvider) |
| [`MVFeatureDatabaseDescriptor`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVFeatureDatabaseDescriptor.java#L30) | Module provider "H2 GeoFeature Database"; **not** listed in that services file |
| `Activator` | OSGi bundle activator (`OshBundleActivator`), set in `build.gradle` |

`IdProviderType` ([enum](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVDatabaseConfig.java#L33-L37)) is `SEQUENTIAL` (default: last key + 1) or `UID_HASH` (murmur3 hash from `DataStoreUtils`, different seed per store type).

### Store implementations

| Store | Implements | Base | Value `DataType` |
|---|---|---|---|
| [`MVSystemStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVSystemStoreImpl.java#L45) | `ISystemDescStore` | `MVBaseFeatureStoreImpl` | `SensorMLDataType` |
| [`MVDeploymentStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVDeploymentStoreImpl.java#L43) | `IDeploymentStore` | `MVBaseFeatureStoreImpl` | `SensorMLDataType` |
| [`MVProcedureStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVProcedureStoreImpl.java#L41) | `IProcedureStore` | `MVBaseFeatureStoreImpl` | `SensorMLDataType` |
| [`MVFoiStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVFoiStoreImpl.java#L44), [`MVFeatureStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVFeatureStoreImpl.java#L28) | `IFoiStore`, `IFeatureStore` | `MVBaseFeatureStoreImpl` | `FeatureDataType` |
| [`MVPropertyStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVPropertyStoreImpl.java#L37) | `IPropertyStore` | [`MVBaseResourceStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVBaseResourceStoreImpl.java#L57) | `PropertyDataType` |
| [`MVObsStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L64) | `IObsStore` | — | `ObsDataType` |
| [`MVDataStreamStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVDataStreamStoreImpl.java#L57) | `IDataStreamStore` | — (created by `MVObsStoreImpl`) | `DataStreamInfoDataType` |
| [`MVCommandStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVCommandStoreImpl.java#L58) | `ICommandStore` | — | `CommandDataType` |
| [`MVCommandStreamStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVCommandStreamStoreImpl.java#L58), [`MVCommandStatusStoreImpl`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVCommandStatusStoreImpl.java#L53) | `ICommandStreamStore`, `ICommandStatusStore` | — (created by `MVCommandStoreImpl`) | `CommandStreamInfoDataType`, `CommandStatusDataType` |

Each top-level store has a static `open(mvStore, idScope, idProviderType, MVDataStoreInfo)` factory, e.g.
[`MVObsStoreImpl.open`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L128).
It reads or creates the store's `MVDataStoreInfo` (just a `name`) in the `@datastores` map
([`H2Utils.getDataStoreInfo`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/H2Utils.java#L68)).

### Serialization

- [`KryoDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/kryo/KryoDataType.java#L39) implements H2's `DataType` with a pool of Kryo instances for reads and one Kryo instance per "record type key" for writes (e.g. per datastream ID in [`ObsDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/ObsDataType.java#L38)). Default object serializer: `VersionedSerializer` with a `FieldSerializer` at `H2Utils.CURRENT_VERSION` (= [5](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/H2Utils.java#L39)).
- Typed subclasses (`ObsDataType`, `FeatureDataType`, `DataStreamInfoDataType`, …) register `VersionedSerializer`s from `sensorhub-utils-kryo` with older-format readers (e.g. `ObsDataSerializerV1` for version 2) and `BigIdSerializers.factory(idScope)`. See [Kryo serialization](kryo-serialization.md).
- [`PersistentClassResolver`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/kryo/PersistentClassResolver.java#L49) stores Kryo class-name → ID mappings in the `kryo_class_map` MVMap of the same file. Javadoc: "the MVStore needs to be committed twice on close to make sure the mappings are also serialized". `doStop()` calls `commit()` then `close()`.
- Keys use hand-written `DataType`s (`MV*KeyDataType`, `MVTimeSeriesRecordKeyDataType`, …) with var-long IDs and `H2Utils.writeInstant` (var-long seconds + int nanos). The **scope is not written**: key data types are constructed with `idScope` and add it on read ([`decode`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVTimeSeriesRecordKeyDataType.java#L101)). **Inferred:** changing `databaseNum` on an existing file changes every public ID.

## How it works

### Lifecycle (`MVObsSystemDatabase`)

1. `beforeInit()` rejects unsafe `storagePath` values (`FileUtils.isSafeFilePath`).
2. [`doStart()`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsSystemDatabase.java#L81) builds the MVStore from config, then `setAutoCommitDelay(autoCommitPeriod*1000)` and `setVersionsToKeep(0)`.
3. `idScope = databaseNum` (0 if unset). Each store is opened by name (`sys_store`, `depl_store`, `foi_store`, `obs_store`, `cmd_store`, `proc_store`, `prop_store`) and linked with `linkTo(...)`.
4. `afterStart()` registers with the database registry if `databaseNum != null`; `beforeStop()` unregisters.
5. `doStop()` commits, closes, optionally logs `MVStoreTool.info` and runs `MVStoreTool.compact` if `compactOnClose`.
6. [`executeTransaction`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsSystemDatabase.java#L290) is `synchronized`: it commits, runs the callable, and calls `mvStore.rollbackTo(version)` on exception.

### MVMap layout

All map names are `<storeName>:<suffix>`.

| Store | Map suffix | Key → value | Purpose |
|---|---|---|---|
| Feature-based (`MVBaseFeatureStoreImpl`) | `feature_records` | `MVFeatureParentKey`(parentID, internalID, validStartTime) → feature | Main map; sorted by parent so children can be range-scanned |
| | `feature_ids` | `MVFeatureParentKey` → void | Lookup by internal ID (`MVFeatureParentKeyByIdDataType`) |
| | `feature_uids` | UID string → `MVFeatureParentKey` | Lookup by UID |
| | `feature_geom` | R-tree (`SpatialIndex`) | Spatial filter |
| | `feature_text` | `FullTextKey`(token, key) → void (`FullTextIndex`) | Full-text filter |
| Obs (`MVObsStoreImpl`) | `obs_records` | `MVTimeSeriesRecordKey`(seriesID, phenomenonTime) → `IObsData` | Observations |
| | `obs_series` | `MVTimeSeriesKey`(dsID, resultTime, foiID) → `MVTimeSeriesInfo`(id) | Series by datastream |
| | `obs_series_foi` | `MVTimeSeriesKey` ordered (foiID, dsID, resultTime) → void | Series by FOI |
| Datastreams | `datastreams_records`, `datastreams_sys`, `datastreams_text` | `DataStreamKey` → info; (sysID, outputName, validStart) → void; full-text | |
| Commands | `cmd_records`, `cmd_series`, `status_records` | same series/record pattern as obs; `MVCommandStatusKey` → status | |
| Command streams | `cmdstreams_records`, `cmdstreams_sys`, `cmdstreams_text` | as datastreams | |
| Properties (`MVBaseResourceStoreImpl`) | `resource_main`, `resource_text`, `property_uri`, `base_property_uri` | `PropertyKey` → property; URI → key | |
| Whole file | `@datastores`, `kryo_class_map` | store name → `MVDataStoreInfo`; class name → Kryo ID | |

### Time series handling (observations)

- An obs series is the tuple (datastream ID, FOI ID, result time). Result time is stored as `Instant.MIN` when it equals phenomenon time ([`add`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L891)), so all such obs share one series.
- The obs ID is `MVTimeSeriesRecordKey` = scope + series ID + phenomenon time; it implements `BigId` directly.
- [`selectObsSeries`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L356) chooses the index: all series; series by datastream; series by FOI; or FOI series filtered by a set of datastream IDs (capped at `100*maxOrderedSeries`).
- [`selectEntries`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L413) range-scans `obs_records` per series and merges with `MergeSortSpliterator`, ordered by result time, then phenomenon time, FOI ID, datastream ID (reversed if the phenomenon-time filter is descending). With more than `maxOrderedSeries` (20000) series, it logs "time sorting disabled" and interleaves series instead.
- A filter with internal IDs bypasses series selection and does direct `getEntry` lookups.
- `getStatistics` uses `ceilingKey`/`floorKey` on `obs_records` to compute per-series time ranges, counts and histograms without reading values.
- `MVDataStreamStoreImpl.DataStreamInfoWithTimeRanges` ([wrapper](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVDataStreamStoreImpl.java#L91)) computes phenomenon/result time ranges lazily from the obs store, and closes an open-ended valid time at the next version's start.

### Feature versioning and indexes

- Feature versions share an internal ID and differ by valid start time ([`generateKey`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVBaseFeatureStoreImpl.java#L257)); features with no valid time use `FeatureKey.TIMELESS`.
- "Current version" = `floorKey(parentID, internalID, now)` in `feature_records`. [`FeatureValidTimeAdapter`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/FeatureValidTimeAdapter.java#L23) ends an open valid time at the next version's start.
- [`getIndexedStream`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVBaseFeatureStoreImpl.java#L415) picks the primary index in order: internal IDs → UIDs → spatial → full-text → parent scan / full scan; other criteria are applied as post-filters.
- [`FullTextIndex`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/index/FullTextIndex.java#L48) is a B-tree of (token, key) pairs; javadoc still says "based on a radix tree" (the radix-tree code is commented out). [`SpatialIndex`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/index/SpatialIndex.java#L44) wraps H2's `MVRTreeMap`.
- Updates to existing datastreams, command streams, features and resources go through `MVMap.operate` with a [`DecisionMakerWithError`](../../../sensorhub-datastore-h2/src/main/java/org/h2/mvstore/DecisionMakerWithError.java#L25) so validation errors can be reported from inside the atomic operation.

## Observed behaviours to be aware of

1. **Large-query fallback repeats the first record.** The unsorted path uses `Stream.iterate(0, i -> i++)` ([line 436](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L436)). `i++` returns the old value, so `i` stays 0 and each pass emits `skip(0).limit(1)` of every series again. **Open question:** intended `i -> i + 1`; not covered by tests (needs more than 20000 series).
2. **Result-time filtering differs by index.** `getObsSeriesByDataStream` and `getObsSeriesByFoi` always keep series whose result time is `Instant.MIN` ([line 231](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L231)). [`getAllObsSeries`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L193) (no datastream/FOI filter) applies `resultTimeRange.contains(...)` and drops them unless the range includes `Instant.MIN`.
3. **Series IDs come from the records map.** A new series gets `obs_records.lastKey().seriesID + 1` ([line 911](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L911)). [`remove(key)`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L934) leaves empty series in place (code comment: "in many cases they will be reused"). **Open question / Inferred:** if the highest-numbered series is emptied by `remove`, its ID can be handed to a new series while the old series entry still points to it. The `SEQUENTIAL` ID providers for features and datastreams also use last key + 1, so IDs of deleted last entries are reused.
4. **Same series and phenomenon time = overwrite.** `add` does `obs_records.put(key, obs)`, so a second obs with the same datastream, FOI, result-time class and phenomenon time replaces the first and returns the same ID.
5. **Ordering differs from the federated DB.** See [Databases, observed behaviour 1](databases.md#observed-behaviours-to-be-aware-of): `FederatedObsStore` merges member streams by phenomenon time only.
6. **Config fields not read:** `MVObsSystemDatabaseConfig.indexObsLocation` is never referenced outside its declaration ([line 32](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsSystemDatabaseConfig.java#L32)).
7. **Stubs and dead code:**
   - `MVObsStoreImpl.backup`/`restore` are empty `// TODO Auto-generated method stub` ([line 1031](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVObsStoreImpl.java#L1031)).
   - `MVCommandStreamStoreImpl.init` has an `if (idProvider == null)` branch that cannot run, because `idProvider` was null-checked a few lines earlier ([line 208](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVCommandStreamStoreImpl.java#L208)).
   - `H2Utils.readInstant` checks `nanos == 0` for `Instant.MAX`, whose nano field is 999,999,999, so that branch never matches ([line 170](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/H2Utils.java#L170)).
   - `MVBaseFeatureStoreImpl.add` tests `parentID != null`, then calls `parentID.getIdAsLong()` unconditionally on the next line ([line 243](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/MVBaseFeatureStoreImpl.java#L243)).
8. **Unreferenced classes** (searched all modules): `ObsClusterDataType`, `MVFeatureRef`, `MVFeatureRefDataType`, `MVFeatureKeyDataType`. `MVRadixTreeMap`, `RadixTreeCursor`, `RadixKeyDataType`, `RadixKeyBytesDataType`, `ResourceRadixKeyDataType` are referenced only by each other and by commented-out code. The `MVRadixTreeMap` javadoc says: "WARNING: This is NOT working since H2 MVStore version 1.4.198" ([line 35](../../../sensorhub-datastore-h2/src/main/java/org/h2/mvstore/MVRadixTreeMap.java#L35)); the build uses 1.4.200.
9. **`MVFeatureDatabase` has no service registration.** Only `MVObsSystemDatabaseDescriptor` is in the `IModuleProvider` services file, and nothing else in the repo references `MVFeatureDatabase`. **Inferred:** it is not offered by module discovery.

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Add a store to the obs DB | New `MV<X>StoreImpl` with a static `open(mvStore, idScope, idProviderType, MVDataStoreInfo)`; add a `*_STORE_NAME` constant, an `open` call and `linkTo` wiring in `MVObsSystemDatabase.doStart()`, and a getter (as `procStore`/`propStore`) |
| New feature-like store | Extend `MVBaseFeatureStoreImpl` and override `getFeatureDataType`, as `MVDeploymentStoreImpl` |
| New resource store (non-feature) | Extend `MVBaseResourceStoreImpl`, as `MVPropertyStoreImpl` (adds its own URI maps in `init`) |
| Add a field to a stored value | Value classes are serialized by Kryo field serializers. Precedent for format changes: bump `H2Utils.CURRENT_VERSION` and register the old reader under the old version in the `VersionedSerializer` factory, as `ObsDataType` does with `ObsDataSerializerV1` |
| Add a secondary index | Open another `MVBTreeMap` named `<storeName>:<suffix>` in `init`, with `MVVoidDataType` values for key-only indexes (as `obs_series_foi`), and keep it updated in `add`/`put`/`remove` |
| New config option | Field on `MVDatabaseConfig` with `@DisplayInfo`; read it in `doStart()` as for `memoryCacheSize` |

## Tests

Each test subclasses a shared suite from `sensorhub-core/src/testFixtures` (see [Databases, tests](databases.md#tests)), opening a real MVStore file in a temp directory:

| Test | Suite |
|---|---|
| [`TestMVObsStore`](../../../sensorhub-datastore-h2/src/test/java/org/sensorhub/impl/datastore/h2/TestMVObsStore.java) | `AbstractTestObsStore` (+ checks that 2 series are created) |
| [`TestMVDataStreamStore`](../../../sensorhub-datastore-h2/src/test/java/org/sensorhub/impl/datastore/h2/TestMVDataStreamStore.java) | `AbstractTestDataStreamStore` |
| [`TestMVCommandStore`](../../../sensorhub-datastore-h2/src/test/java/org/sensorhub/impl/datastore/h2/TestMVCommandStore.java) | `AbstractTestCommandStore` |
| [`TestMVCommandStreamStore`](../../../sensorhub-datastore-h2/src/test/java/org/sensorhub/impl/datastore/h2/TestMVCommandStreamStore.java) | `AbstractTestCommandStreamStore` |
| [`TestMVFeatureStore`](../../../sensorhub-datastore-h2/src/test/java/org/sensorhub/impl/datastore/h2/TestMVFeatureStore.java) | `AbstractTestFeatureStore` (throughput tests excluded in `build.gradle`) |
| [`TestMVObsDatabase`](../../../sensorhub-datastore-h2/src/test/java/org/sensorhub/impl/datastore/h2/TestMVObsDatabase.java) | `AbstractTestObsDatabase` |

`PrintDbInfo` in the test folder is a `main()` utility, not a test.
No dedicated tests exist for the system, FOI, deployment, procedure, property or command-status stores, `FullTextIndex` or `SpatialIndex`.

```bash
./gradlew :sensorhub-datastore-h2:test
./gradlew :sensorhub-datastore-h2:test --tests 'org.sensorhub.impl.datastore.h2.TestMVObsStore'
```

## Related

- [Code map index](../index.md)
- [Databases & datastores](databases.md) — interfaces, registry, federated DB
- [Kryo serialization](kryo-serialization.md) — `VersionedSerializer`, `BigIdSerializers`, compat serializers
- [Module lifecycle](module-lifecycle.md) — `AbstractModule` hooks used by the DB modules
