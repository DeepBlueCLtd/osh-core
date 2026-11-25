# Kryo Serialization

> Status: draft page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

Gradle project `sensorhub-utils-kryo` ([`build.gradle`](../../../sensorhub-utils-kryo/build.gradle)):
description "Kryo Serialization", details "Utility classes for serialization/deserialization/cloning
of data model objects with Kryo". It contains Kryo `Serializer` classes and factories only. It does
not create or configure `Kryo` instances; its only consumer does that.

- Dependencies: `implementation project(':sensorhub-core')`, `embeddedApi 'com.esotericsoftware:kryo:5.5.0'`.
  In [`common.gradle`](../../../common.gradle), `embeddedApi` extends `api` and the jars are copied into the OSGi bundle.
- 21 main classes, all in `org.sensorhub.impl.serialization.kryo` and its `compat.*` sub-packages.
- What it serializes: version headers for any type, `BigId`, `QName`, GML geometries, `IFeature`, plus
  backward-compatible readers for `ObsData`, `CommandData`, `CommandStatus`, `FeatureId`,
  `CommandStreamInfo`, `DataStreamInfo`, SensorML capability/characteristic lists and JTS `PrecisionModel`.

Source folders:
- Main: [`sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo)
- Tests: [`sensorhub-utils-kryo/src/test/java/org/sensorhub/impl/serialization/kryo/`](../../../sensorhub-utils-kryo/src/test/java/org/sensorhub/impl/serialization/kryo)

## Who depends on it

Searched every `build.gradle` and every `.java` import across the repo:

| Consumer | How |
|---|---|
| `sensorhub-datastore-h2` | [`implementation project(':sensorhub-utils-kryo')`](../../../sensorhub-datastore-h2/build.gradle). Nine classes in `org.sensorhub.impl.datastore.h2` import it: `KryoDataType`, `ObsDataType`, `CommandDataType`, `CommandStatusDataType`, `CommandStreamInfoDataType`, `DataStreamInfoDataType`, `FeatureDataType`, `SensorMLDataType`, `PropertyDataType` |
| `sensorhub-core-osgi` (test only) | [`TestSensorHubOsgi`](../../../sensorhub-core-osgi/src/test/java/TestSensorHubOsgi.java) lists the `sensorhub-utils-kryo` bundle path |

No other module references `org.sensorhub.impl.serialization.kryo`. See [H2 datastore](datastore-h2.md) for how the H2 MVStore data types use these serializers.

## Key types

### Core (`org.sensorhub.impl.serialization.kryo`)

| Type | Role | Used by (outside this module) |
|---|---|---|
| [`VersionedSerializer`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L33) | Writes a var-int version, then delegates to the serializer for the current version. On read, picks a serializer by the stored version | All H2 `*DataType` classes |
| [`VersionedSerializer.factory(int)`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L154) → [`VersionedSerializerFactoryBuilder`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L160) | Builder: `put(version, serializer or factory)`, then `build()`. Adds a `FieldSerializerFactory` for the current version if none was given | H2 `*DataType` classes |
| [`VersionedSerializer.factory2()`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L127) | Factory from a `Map<Integer, SerializerFactory>` | H2 [`KryoDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/kryo/KryoDataType.java#L101) default serializer |
| [`VersionedSerializerFactory`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializerFactory.java#L25) | `SerializerFactory` wrapping a plain `FieldSerializer` at one version | Tests only (`TestVersionedSerializers`) |
| [`BigIdSerializers.factory()`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/BigIdSerializers.java#L110) | Chooses by runtime class: `BigIdLong` → var-long; `BigIdZero` → nothing written; otherwise → byte array. Reads rebuild IDs with the given `idScope` | H2 obs, command, command status, datastream, command stream types |
| [`QNameSerializer`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/QNameSerializer.java#L24) | Immutable; writes namespace URI, local part, prefix as nullable strings | Every H2 `*DataType` and `PropertyDataType` |
| [`GeomSerializer`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/GeomSerializer.java#L37) | GML `Point`, `LineString`, `Polygon` (with holes) as type byte + coordinates + SRS name + dimension | None (see Open questions) |

### Backward compatibility (`...kryo.compat`)

| Type | Handles (from javadoc / code) | Registered by H2 at version |
|---|---|---|
| [`BackwardCompatFieldSerializer`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/BackwardCompatFieldSerializer.java#L37) | Base class: `FieldSerializer` whose `read`/`write` iterate a customised `compatFields` array instead of the default cached fields | n/a |
| `compat.v1.BigIdAsLongCachedField`, `compat.v1.BigIdAsBigIntCachedField`, `compat.v2.BigIdAsBytesCachedField` | `CachedField`s converting a `BigId` field to/from a var-long, a `BigInteger`, or a byte array | n/a |
| [`ObsDataSerializerV1`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/ObsDataSerializerV1.java#L31) | `dataStreamID`, `foiID` as longs | 2 ([`ObsDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/ObsDataType.java#L49)) |
| [`CommandDataSerializerV1`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/CommandDataSerializerV1.java#L31) / [`CommandDataSerializerV2`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v2/CommandDataSerializerV2.java#L32) | v1: `id` as `BigInteger`; v2: `id` as bytes. Both: `commandStreamID`, `foiID` as longs | 1 and 2 ([`CommandDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/CommandDataType.java#L48-L50)) |
| [`CommandStatusSerializerV1`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/CommandStatusSerializerV1.java#L31) / [`CommandStatusSerializerV2`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v2/CommandStatusSerializerV2.java#L30) | command ID as `BigInteger` (v1) / bytes (v2) | 1 and 2 ([`CommandStatusDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/CommandStatusDataType.java#L48-L50)) |
| [`FeatureIdSerializerV1`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/FeatureIdSerializerV1.java#L31) | `internalID` as long | 2 (`DataStreamInfoDataType`, `CommandStreamInfoDataType`) |
| [`CommandStreamInfoSerializerV2`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v2/CommandStreamInfoSerializerV2.java#L32) | `FieldSerializer` with `resultStruct`, `resultEncoding` removed | 2 |
| [`DataStreamInfoSerializerV4`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v4/DataStreamInfoSerializerV4.java#L30) | Removes `phenomenonTimeInterval`, `resultTimeInterval`, `procedureID`, `deploymentID`, `featureOfInterestID`, `samplingFeatureID` | 4 ([`DataStreamInfoDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/DataStreamInfoDataType.java#L52-L53)) |
| [`CapabilityListSerializerV3`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v3/CapabilityListSerializerV3.java#L30) / [`CharacteristicListSerializerV3`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v3/CharacteristicListSerializerV3.java#L30) | Remove `relatedProperty`/`conditionList`, `conditionList` | 3 ([`SensorMLDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/SensorMLDataType.java#L53-L59)) |
| [`PrecisionModelSerializerV1`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/PrecisionModelSerializerV1.java#L31) | JTS `PrecisionModel` before 1.19 (no `gridSize`) | 1 ([`FeatureDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/FeatureDataType.java#L62-L63)) |
| [`FeatureSerializerV1`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/FeatureSerializerV1.java#L37) | Custom `IFeature` format: type, UID, name, description, geometry, valid time, property map | **current** version (`H2Utils.CURRENT_VERSION` = 5) ([`FeatureDataType`](../../../sensorhub-datastore-h2/src/main/java/org/sensorhub/impl/datastore/h2/FeatureDataType.java#L51-L52)) |

## How it works

### Versioned envelope

```
write: varInt(currentVersion) | payload written by serializers[currentVersion]
read:  v = varInt
       v > currentVersion          → IllegalStateException
       v == currentVersion         → serializers[currentVersion]
       v <  currentVersion         → serializer with the smallest version ≥ v
```

- [`write()`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L82) always uses the current-version serializer. Older serializers are used only for reading.
- [`read()`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L93) scans the sorted entries from the second-last downward. A serializer registered at version N therefore reads every stored version from the previous registered version + 1 up to N.
- The [constructor](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L49) rejects a map without the current version and any version greater than the current one.
- **Inferred:** the H2 `*DataType` classes pass `H2Utils.CURRENT_VERSION` (5) as the current version, so the stored version number tracks the H2 database format rather than each class.

### Compat field serializers

Subclasses of `BackwardCompatFieldSerializer` call `getFields()` in their constructor. They copy the
array into `compatFields`, replacing the entries for changed fields (matched by field name) with a
converting `CachedField`; for example, [`ObsDataSerializerV1.customizeCacheFields()`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/ObsDataSerializerV1.java#L44).
The `v3`/`v4` and `PrecisionModel`/`CommandStreamInfo` serializers instead extend `FieldSerializer` and
call `removeField(...)` for fields that did not exist in the older layout.

## Observed behaviours to be aware of

1. **`FeatureSerializerV1` is the current feature writer.** Despite the `V1` name and its unused `VERSION = 1` constant ([L39](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/FeatureSerializerV1.java#L39)), H2 registers it at the current version. Its `read` always builds a `GenericTemporalFeatureImpl` ([L82](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/FeatureSerializerV1.java#L82)), whatever the original `IFeature` class. Geometry and valid time are written as `null` when the feature has a custom geometry or time property.
2. **`ObsDataSerializerV1` is registered at version 2.** It reads stored versions 1 and 2. `CommandDataType` registers separate v1 and v2 readers.
3. **`BigIdLongSerializer` maps non-positive values to `BigId.NONE`** on read ([`read`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/BigIdSerializers.java#L85)). `BigIdBytesSerializer` maps bytes equal to `BigId.NONE` to `NONE`.
4. **Compat serializers can also write the old format.** `BackwardCompatFieldSerializer.write` uses `compatFields`. `VersionedSerializer` never calls an old serializer's `write`, so this path is not used by H2.

**Open questions** (all `.java` files and `build.gradle` files searched):
- [`GeomSerializer`](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/GeomSerializer.java#L37) is not registered anywhere. Its only reference is a commented-out line in `TestFeatureSerializer`.
- `VersionedSerializerFactory` is used only by `TestVersionedSerializers`.
- `GeomSerializer.read` bounds check uses `>` instead of `>=` ([L101](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/GeomSerializer.java#L101)). An index equal to `values().length` would raise `ArrayIndexOutOfBoundsException`, not the intended `IllegalStateException`.
- The `VersionedSerializer.read` error message is the literal text `"... > currentVersion"`, not the value ([L97](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/VersionedSerializer.java#L97)).
- `BigIdAsBigIntCachedField` javadoc says "serialize BigId fields as longs", but the code writes a `BigInteger` ([class](../../../sensorhub-utils-kryo/src/main/java/org/sensorhub/impl/serialization/kryo/compat/v1/BigIdAsBigIntCachedField.java#L35)). The javadoc is identical to `BigIdAsLongCachedField`'s.
- `copy()` in the `BigIdAs*CachedField` classes throws `UnsupportedOperationException`, so `Kryo.copy` on objects using these fields fails. The module description mentions "cloning".

## Where to make changes (by precedent in the code)

| Task | Existing pattern to follow |
|---|---|
| Change the stored layout of a persisted class | Bump `H2Utils.CURRENT_VERSION` in `sensorhub-datastore-h2`. Add a reader for the old layout here under `compat/vN`, and register it with `VersionedSerializer.factory(CURRENT_VERSION).put(N, ...)` in the matching H2 `*DataType` |
| A field was added to a class | `FieldSerializer` subclass calling `removeField("newField")`, as `DataStreamInfoSerializerV4` |
| A field changed type | `BackwardCompatFieldSerializer` subclass with a converting `CachedField`, as `ObsDataSerializerV1` + `BigIdAsLongCachedField` |
| Custom binary format for a type | Plain `Serializer<T>`, as `QNameSerializer`, `FeatureSerializerV1` |

## Tests

| Test class | Covers |
|---|---|
| [`TestVersionedSerializers`](../../../sensorhub-utils-kryo/src/test/java/org/sensorhub/impl/serialization/kryo/TestVersionedSerializers.java) | write with v1, read with v2 via `TestObjectV1CompatSerializer` (a `BackwardCompatFieldSerializer`); mixed v1/v2 records |
| [`TestFeatureSerializer`](../../../sensorhub-utils-kryo/src/test/java/org/sensorhub/impl/serialization/kryo/TestFeatureSerializer.java) | `FeatureSerializerV1` round trip for generic and moving features (sampling feature test commented out) |

Helpers: `TestObjectV1`, `TestObjectV2`, `TestObjectV1CompatSerializer`. The serializers are also exercised indirectly by the H2 store tests (`TestMVObsStore`, `TestMVFeatureStore`, etc.); see [H2 datastore](datastore-h2.md).

```bash
./gradlew :sensorhub-utils-kryo:test --tests 'org.sensorhub.impl.serialization.kryo.TestVersionedSerializers'
./gradlew :sensorhub-utils-kryo:test --tests 'org.sensorhub.impl.serialization.kryo.TestFeatureSerializer'
```

## Related

- [Code map index](../index.md)
- [H2 datastore](datastore-h2.md), the only consumer
- [Databases & datastores](databases.md), for the persisted types (`ObsData`, `CommandData`, `DataStreamInfo`, ...)
- [Module lifecycle](module-lifecycle.md)
