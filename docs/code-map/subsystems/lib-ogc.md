# OGC libraries (overview)

> Status: overview page. Verified against source on 2026-11-25.
> Everything here is stated from the code. Items marked **Inferred:** are not directly
> visible in code; **Open question** items are unresolved observations.
> See [conventions](../index.md#conventions).

## Scope

The seven Gradle projects under [`lib-ogc/`](../../../lib-ogc) hold the OGC data models (SWE Common,
GML, O&M, SensorML, ISO 19115 metadata, FES) and the OWS/SOS/SPS request/response bindings used by the
`sensorhub-*` modules. All use Gradle group `org.vast.opengis`. They contain 902 main and 49 test `.java`
files, so this page covers each project at package level and names only the main entry points.

- Projects are registered in `settings.gradle` ([project mapping lines](../../../settings.gradle#L20-L26)). Each `projectDir` is mapped to `lib-ogc/<name>`.
- [`lib-ogc/sensorml-profile-gen`](../../../lib-ogc/sensorml-profile-gen/build.gradle) has only a `build.gradle` (description "SensorML Profile Generator"). It has no `src/` folder and is not included in `settings.gradle`.
- Package roots: `net.opengis.*` and `org.isotc211.*` hold schema-shaped interfaces, `*Impl` classes and StAX bindings. `org.vast.*` holds the helpers, utilities, encoders and service code.

## Project dependency graph (from `build.gradle`)

```
swe-common-core            (logback, woodstox, gson, guava, trove4j, cloning)
  └─ swe-common-om         (+ jts-core)
       ├─ sensorml-core
       │    └─ ogc-services-swe ─┐
       └─ ogc-services-common    │   (+ servlet-api 3.1.0, activation)
            ├─ ogc-services-swe ─┤
            ├─ ogc-services-sos ─┘ (needs common + swe)
            └─ ogc-services-sps    (needs common + swe)
```

| Project | `description` | `api` dependencies | main / test `.java` |
|---|---|---|---|
| [`swe-common-core`](../../../lib-ogc/swe-common-core/build.gradle) | SWE Common Core | third-party only | 291 / 19 |
| [`swe-common-om`](../../../lib-ogc/swe-common-om/build.gradle) | SWE O&M and GML Models | `swe-common-core`, `jts-core` | 100 / 7 |
| [`sensorml-core`](../../../lib-ogc/sensorml-core/build.gradle) | SensorML Models | `swe-common-om` | 167 / 9 |
| [`ogc-services-common`](../../../lib-ogc/ogc-services-common/build.gradle) | OGC Services Common | `swe-common-om`, servlet-api, activation | 184 / 1 |
| [`ogc-services-swe`](../../../lib-ogc/ogc-services-swe/build.gradle) | OGC SWE Services Common | `ogc-services-common`, `sensorml-core` | 32 / 0 |
| [`ogc-services-sos`](../../../lib-ogc/ogc-services-sos/build.gradle) | OGC Sensor Observation Service (SOS) | `ogc-services-common`, `ogc-services-swe` | 47 / 7 |
| [`ogc-services-sps`](../../../lib-ogc/ogc-services-sps/build.gradle) | OGC Sensor Planning Service (SPS) | `ogc-services-common`, `ogc-services-swe` | 81 / 6 |

`ogc-services-common` and `sensorml-core` also publish a `testArtifacts` jar. `ogc-services-sos` and
`ogc-services-sps` use the one from `ogc-services-common` (`testImplementation ... configuration: 'testArtifacts'`).

## Per-project summary

### swe-common-core

| Package | Role |
|---|---|
| `net.opengis` | Shared binding bases: [`AbstractXMLStreamBindings`](../../../lib-ogc/swe-common-core/src/main/java/net/opengis/AbstractXMLStreamBindings.java#L38), [`OgcProperty`](../../../lib-ogc/swe-common-core/src/main/java/net/opengis/OgcProperty.java#L22), [`OgcPropertyList`](../../../lib-ogc/swe-common-core/src/main/java/net/opengis/OgcPropertyList.java#L42), href resolvers |
| `net.opengis.swe.v20` (+ `.bind`) | SWE Common 2.0 interfaces (57 files) and the StAX `XMLStreamBindings` |
| `org.vast.data` | Implementations of the component interfaces (`*Impl`) and the `DataBlock*` storage classes (77 files) |
| `org.vast.cdm.common` | Stream parser/writer interfaces and handler callbacks |
| `org.vast.swe` | Helpers, XML/JSON bindings, the older text/binary/XML parsers and writers |
| `org.vast.swe.fast` | Javadoc: "New implementation of text data parser with better efficiency..." ([`TextDataParser`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/fast/TextDataParser.java#L52)). Text, binary, XML and JSON parsers and writers |
| `org.vast.swe.helper` | Domain helpers: [`GeoPosHelper`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/helper/GeoPosHelper.java#L36), [`VectorHelper`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/helper/VectorHelper.java#L33), [`RasterHelper`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/helper/RasterHelper.java#L38) |
| `org.vast.swe.json`, `org.vast.json` | JSON stream reader/writer for SWE components, and generic JSON stream utilities |
| `org.vast.ogc` (+ `def`, `gml`, `xlink`) | [`OGCRegistry`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/ogc/OGCRegistry.java) (reader/writer class and namespace maps), xlink references, definition refs, `GMLUnitReader` |
| `org.vast.unit` | Units of measure; [`UnitParserUCUM`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/unit/UnitParserUCUM.java) with resource `ucum-essence.xml` |
| `org.vast.xml` (+ `transform`) | [`DOMHelper`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/xml/DOMHelper.java), [`XMLBindingsUtils`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/xml/XMLBindingsUtils.java#L34), StAX/DOM reader/writer interfaces |
| `org.vast.util` | [`Asserts`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/util/Asserts.java#L25), [`BaseBuilder`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/util/BaseBuilder.java#L28), date/time and number utilities |

Key entry points:

| Type | Role (from code / javadoc) |
|---|---|
| [`DataComponent`](../../../lib-ogc/swe-common-core/src/main/java/net/opengis/swe/v20/DataComponent.java#L31) | Javadoc: "Base interface for all SWE Common data components. It provides an API auto-generated from XML schemas as well as a generic API..." |
| [`DataBlock`](../../../lib-ogc/swe-common-core/src/main/java/net/opengis/swe/v20/DataBlock.java#L38) | Holds the values of a component tree; typed `getXXXValue(int)` / `setXXXValue(int, ...)` accessors. Javadoc says no index check is required |
| [`DataEncoding`](../../../lib-ogc/swe-common-core/src/main/java/net/opengis/swe/v20/DataEncoding.java#L26) | Base of text, binary, XML and JSON encodings |
| [`SWEHelper`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEHelper.java#L106) | Javadoc: "Helper class for creating common data structures and encodings and browsing a data component tree." Also the parser/writer factory methods [`createDataParser`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEHelper.java#L454) and [`createDataWriter`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEHelper.java#L479) |
| [`SWEBuilders`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEBuilders.java#L73) | Javadoc: "Utility class to build SWE Common data components with a fluent API" |
| [`SWEUtils`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEUtils.java) | Javadoc: "version agnostic access to SWE component structure and encoding readers and writers" |
| [`SWEStaxBindings`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEStaxBindings.java#L25), [`SWEJsonBindings`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEJsonBindings.java#L91) | XML (StAX) and JSON serialization of component trees |
| [`DataStreamParser`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/cdm/common/DataStreamParser.java), [`DataStreamWriter`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/cdm/common/DataStreamWriter.java) | Interfaces implemented by all encoders and decoders |
| [`SWEFactory`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/data/SWEFactory.java#L20), [`DataBlockFactory`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/data/DataBlockFactory.java#L29) | Create component implementations and wrap Java arrays as `DataBlock`s |

### swe-common-om

| Package | Role |
|---|---|
| `net.opengis.gml.v32` (+ `.impl`, `.bind`) | GML 3.2 interfaces, implementations ([`GMLFactory`](../../../lib-ogc/swe-common-om/src/main/java/net/opengis/gml/v32/impl/GMLFactory.java#L37)) and StAX bindings |
| `org.vast.ogc.gml` (+ `.json`) | Feature model: [`IFeature`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/gml/IFeature.java#L28) ("Simple interface for feature objects"), [`GenericFeatureImpl`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/gml/GenericFeatureImpl.java), [`FeatureRef`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/gml/FeatureRef.java#L51), [`GMLUtils`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/gml/GMLUtils.java#L66), [`GMLStaxBindings`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/gml/GMLStaxBindings.java#L44), [`GeoJsonBindings`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/gml/GeoJsonBindings.java#L58) |
| `org.vast.ogc.om` | O&M: [`IObservation`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/om/IObservation.java#L44), [`ObservationImpl`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/om/ObservationImpl.java), [`SamplingFeature`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/om/SamplingFeature.java#L33), [`MovingFeature`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/om/MovingFeature.java#L21), [`OMUtils`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/ogc/om/OMUtils.java) |
| `org.vast.ogc.geopose` | `Pose`, `PoseImpl`, `GeoPoseJsonBindings` |
| `org.vast.util` | [`TimeExtent`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/util/TimeExtent.java#L41) (javadoc: "Immutable class for storing a time instant or time period"), [`Bbox`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/util/Bbox.java), [`IResource`](../../../lib-ogc/swe-common-om/src/main/java/org/vast/util/IResource.java#L26), `Contact`, `SpatialExtent` |

**Split packages.** `org.vast.util` is spread across `swe-common-core` and `swe-common-om`, and so is
`org.vast.ogc.gml` (core has only `GMLUnitReader`).

### sensorml-core

| Package | Role |
|---|---|
| `net.opengis.sensorml.v20` (+ `.impl`, `.bind`) | SensorML 2.0 interfaces and implementations; two StAX bindings, `XMLStreamBindingsV1` and `XMLStreamBindingsV2` |
| `org.isotc211.v2005.gco`, `.gmd` (+ `.impl`, `.bind`) | ISO 19115/19139 metadata types (`CICitation`, `CIContact`, ...) |
| `org.vast.sensorML` | Helpers, builders, process/system implementations, JSON and StAX bindings |
| `org.vast.sensorML.helper` | `CommonIdentifiers`, `CommonCharacteristics`, `CommonCapabilities`, ... (preset terms) |
| `org.vast.sensorML.sampling` | Parametric sampling features (`SamplingPointXYZ`, `ViewingSector`, ...) |
| `org.vast.process` | Process execution: `IProcessExec`, `ExecutableProcessImpl`, `ExecutableChainImpl`, `DataConnection`, `DataQueue` |

Key entry points:

| Type | Role |
|---|---|
| [`SMLHelper`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLHelper.java#L65) | Extends `SWEHelper`. Javadoc: "Helper class for creating SensorML process and system components..." |
| [`SMLUtils`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLUtils.java) | Javadoc: "version agnostic access to SensorML object readers and writers". Uses an [`IProcessFactory`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/IProcessFactory.java#L30) to make processes executable |
| [`SMLBuilders`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLBuilders.java#L75), [`SMLMetadataBuilders`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLMetadataBuilders.java#L44) | Fluent builders for systems and metadata |
| [`SMLStaxBindings`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLStaxBindings.java#L58), [`SMLJsonBindings`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLJsonBindings.java#L76) | XML and JSON serialization |
| [`AbstractProcessImpl`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/AbstractProcessImpl.java#L60) | Implements both `AbstractProcess` and `IProcessExec`, and delegates to a transient `executableProcess` |
| [`IProcessExec`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/process/IProcessExec.java#L21), [`ExecutableProcessImpl`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/process/ExecutableProcessImpl.java#L41), [`ExecutableChainImpl`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/process/ExecutableChainImpl.java#L47) | Execution API (`init`, `execute`, `start`, `connect`), base class for algorithms, process chains |
| [`ProcessLoader`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/ProcessLoader.java#L46) | Default `IProcessFactory`: maps a process URI to a class name from an XML map file |

`sensorhub-core` replaces the default factory with the processing manager: [`smlUtils.setProcessFactory`](../../../sensorhub-core/src/main/java/org/sensorhub/impl/processing/SMLProcessImpl.java#L77). `IProcessingManager` extends `IProcessFactory`.

### ogc-services-common

| Package | Role |
|---|---|
| `net.opengis.fes.v20` (+ `.impl`, `.bind`) | Filter Encoding 2.0 model (71 interfaces, 60 impls) and StAX bindings |
| `net.opengis.ows.v11` (+ `.impl`) | 5 OWS 1.1 types |
| `org.vast.ows` | [`OWSRequest`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSRequest.java), [`OWSResponse`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSResponse.java), [`OWSRequestReader`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSRequestReader.java) / [`OWSRequestWriter`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSRequestWriter.java) and their `Abstract*` bases, [`OWSException`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSException.java), [`OWSServiceCapabilities`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSServiceCapabilities.java), [`OWSUtils`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSUtils.java) |
| `org.vast.ows.fes` | [`FESUtils`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/fes/FESUtils.java#L40), [`FESStaxBindings`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/fes/FESStaxBindings.java#L31) |
| `org.vast.ows.server` | [`OWSServlet`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/server/OWSServlet.java): "Abstract Base Class for all OWS Style Servlets" |
| `org.vast.ows.util` | `PostRequestFilter` |

### ogc-services-swe, ogc-services-sos, ogc-services-sps

All three are flat packages of request/response POJOs. Each request type has its own `*ReaderV20` and
`*WriterV20` classes.

| Project | Package | Entry points | Request families |
|---|---|---|---|
| ogc-services-swe | `org.vast.ows.swe` | [`SWESUtils`](../../../lib-ogc/ogc-services-swe/src/main/java/org/vast/ows/swe/SWESUtils.java), [`SWERequestReader`](../../../lib-ogc/ogc-services-swe/src/main/java/org/vast/ows/swe/SWERequestReader.java), [`DescribeSensorRequest`](../../../lib-ogc/ogc-services-swe/src/main/java/org/vast/ows/swe/DescribeSensorRequest.java) | SWES: DescribeSensor, InsertSensor, UpdateSensor, DeleteSensor, capabilities |
| ogc-services-sos | `org.vast.ows.sos` | [`SOSUtils`](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/SOSUtils.java#L44), [`GetObservationRequest`](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/GetObservationRequest.java), [`GetResultRequest`](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/GetResultRequest.java), [`InsertResultRequest`](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/InsertResultRequest.java#L41), [`SOSException`](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/SOSException.java), [`SOSServlet`](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/SOSServlet.java) | GetObservation, GetResult(Template), GetFeatureOfInterest, InsertObservation, InsertResult(Template), InsertSensor |
| ogc-services-sps | `org.vast.ows.sps` | [`SPSUtils`](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/SPSUtils.java#L53), [`TaskingRequest`](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/TaskingRequest.java#L27), [`SubmitRequest`](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/SubmitRequest.java#L35), [`DirectTaskingRequest`](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/DirectTaskingRequest.java#L36), [`StatusReport`](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/StatusReport.java#L45), [`SPSServiceCapabilities`](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/SPSServiceCapabilities.java#L39) | Submit, Reserve, Confirm, Cancel, Update, GetStatus, GetFeasibility, DescribeTasking, DescribeResultAccess, ConnectTasking, DirectTasking, InsertTaskingTemplate, InsertSensor |

`InsertSensorRequest` exists three times: [`org.vast.ows.swe.InsertSensorRequest`](../../../lib-ogc/ogc-services-swe/src/main/java/org/vast/ows/swe/InsertSensorRequest.java) is the base, and the SOS and SPS classes of the same simple name extend it ([sps subclass](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/InsertSensorRequest.java#L26)).

## How it works: reader/writer registry

- [`OGCRegistry`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/ogc/OGCRegistry.java) keeps static maps from (type, subType, version) to reader/writer class names, loaded from XML map files. Its static block loads `OGCRegistry.xml`.
- Each layer adds its own map file: `OMRegistry.xml` (`OMUtils`), `SMLRegistry.xml` ([`SMLUtils.loadRegistry`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/SMLUtils.java)) and `OWSRegistry.xml` ([`OWSUtils.loadRegistry`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSUtils.java)).
- `OWSUtils.loadRegistry` also runs a `ServiceLoader` over [`OWSBindingProvider`](../../../lib-ogc/ogc-services-common/src/main/java/org/vast/ows/OWSBindingProvider.java#L18) and calls `loadBindings()` on each provider it finds. The SOS and SPS jars register [`SOSUtils.loadBindings`](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/SOSUtils.java#L48) and [`SPSUtils.loadBindings`](../../../lib-ogc/ogc-services-sps/src/main/java/org/vast/ows/sps/SPSUtils.java#L68) in `META-INF/services/org.vast.ows.OWSBindingProvider`. These methods load `SOSRegistry.xml` and `SPSRegistry.xml`.
- `SOSRegistry.xml` maps some SOS operations to `org.vast.ows.swe` classes, for example `DescribeSensor` → `org.vast.ows.swe.DescribeSensorReaderV20`.

## Generated code

- The `net.opengis.*` and `org.isotc211.*` packages contain schema-shaped classes. Their javadoc reads "POJO class for XML type ...": 56 files in swe-common-core, 46 in swe-common-om, 116 in sensorml-core and 50 in ogc-services-common. Each `.bind` package has one large `XMLStreamBindings*` class (24,309 lines in total).
- These files are checked in. No build file in the repo has a code-generation step (no xjc or JAXB task in `build.gradle` or `common.gradle`).
- Javadoc and comments refer to generation: `DataComponent` says "API auto-generated from XML schemas" ([line 24](../../../lib-ogc/swe-common-core/src/main/java/net/opengis/swe/v20/DataComponent.java#L24)), and `XMLStreamBindingsV2` has a section headed "Methods added manually for incorrectly generated simple types" ([comment](../../../lib-ogc/sensorml-core/src/main/java/net/opengis/sensorml/v20/bind/XMLStreamBindingsV2.java#L5248)).
- **Inferred:** the generator is outside this repository, and the generated sources have since been edited by hand.

## Which sensorhub modules use what

Counted as the number of `.java` files (main + test) in each module that import at least one class from the
project. Imports were resolved against the class list of each lib. The only wildcard imports are `org.vast.ows.sos.*` and `org.vast.ows.sps.*`.

| Module | swe-common-core | swe-common-om | sensorml-core | ogc-services-common | ogc-services-swe | ogc-services-sos | ogc-services-sps |
|---|---|---|---|---|---|---|---|
| sensorhub-core | 168 | 83 | 41 | 0 | 0 | 0 | 0 |
| sensorhub-datastore-h2 | 22 | 15 | 5 | 0 | 0 | 0 | 0 |
| sensorhub-service-consys | 83 | 53 | 35 | 0 | 0 | 0 | 0 |
| sensorhub-service-swe | 46 | 30 | 11 | 32 | 18 | 40 | 10 |
| sensorhub-utils-kryo | 1 | 3 | 2 | 0 | 0 | 0 | 0 |
| sensorhub-webui-core | 16 | 4 | 3 | 3 | 0 | 1 | 1 |
| sensorhub-core-osgi | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- Gradle wiring: [`sensorhub-core`](../../../sensorhub-core/build.gradle#L8-L10) declares `embeddedApi` on `swe-common-core`, `swe-common-om` and `sensorml-core`. [`sensorhub-service-swe`](../../../sensorhub-service-swe/build.gradle#L7-L18) declares `embeddedApi` on `ogc-services-sos` and `ogc-services-sps` and excludes `swe-common-om` and `sensorml-core`, with the comment "already provided by sensorhub-core". `sensorhub-webui-core` reaches the OWS classes through `sensorhub-service-swe`.
- Most-imported classes: `org.vast.util.Asserts` (114 files in sensorhub-core), `net.opengis.swe.v20.DataComponent`, `org.vast.ogc.gml.IFeature`, `org.vast.util.TimeExtent`, `org.vast.swe.SWEHelper`, `org.vast.sensorML.SMLHelper` (consys) and `org.vast.ows.OWSUtils` (service-swe).
- `sensorhub-service-swe` servlets extend `OWSServlet` through [`SWEServlet`](../../../sensorhub-service-swe/src/main/java/org/sensorhub/impl/service/swe/SWEServlet.java#L72).

## Observed behaviours to be aware of

1. **`SWEHelper` mixes legacy and "fast" codecs.**
   - [`createDataParser`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEHelper.java#L454) returns the legacy `org.vast.swe.AsciiDataParser` and `org.vast.swe.BinaryDataParser`, but the `fast` `XmlDataParser` and `JsonDataParserGson`.
   - [`createDataWriter`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/SWEHelper.java#L479) returns the `fast` text, XML and JSON writers, but the legacy `org.vast.swe.BinaryDataWriter`.
   - The imports at lines 86–90 select these classes; the others resolve to the same package.
2. **No codec factory implementations.** [`CodecLookup`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/swe/CodecLookup.java#L28) loads `ICodecFactory` through `ServiceLoader`. It is called only from the legacy `BinaryDataParser` (compression). No `ICodecFactory` implementation or service file exists in the repo.
3. **`org.vast.ows.sos.SOSServlet` has no subclass in this repo.** The [abstract class](../../../lib-ogc/ogc-services-sos/src/main/java/org/vast/ows/sos/SOSServlet.java) extends `OWSServlet`. `sensorhub-service-swe` has its own `org.sensorhub.impl.service.sos.SOSServlet`, which extends `SWEServlet`. That class imports `org.vast.ows.sos.*`, but its own simple name takes precedence.
4. **`ProcessLoader` throws for unknown URIs.** [`loadProcess`](../../../lib-ogc/sensorml-core/src/main/java/org/vast/sensorML/ProcessLoader.java#L52) carries the TODOs "download new process implementation when not available locally" and "should actually resolve the URN". Its map is loaded only by `TestSMLProcessing` in this repo.
5. **Split packages** (`org.vast.util`, `org.vast.ogc.gml`) across `swe-common-core` and `swe-common-om`. **Inferred:** relevant to the OSGi bundling done by `common.gradle`; not verified.
6. **Mixed line endings.** Many `lib-ogc` sources contain lone CR (`\r`) line terminators. For example, `file` reports "CR, LF line terminators" for `OWSUtils.java`. Python `splitlines()` (used by the reference checker) and `grep -n` then count lines differently. Links to such files on this page therefore carry no `#L` anchor.
7. **Open question:** [`DataStreamParser`](../../../lib-ogc/swe-common-core/src/main/java/org/vast/cdm/common/DataStreamParser.java) javadoc contains "TODO add parseNextBlock() method taking DataBlock as argument".

## Where to make changes (by precedent in the code)

| Task | Existing pattern |
|---|---|
| Build a SWE record or output structure | `SWEHelper` / `GeoPosHelper` builder methods (`createRecord()...build()`), as used across `sensorhub-core` drivers |
| Describe a system in SensorML | `SMLHelper` and `SMLMetadataBuilders`, `CommonIdentifiers` presets (heavily used in `sensorhub-service-consys`) |
| Add an encoding or decoder | Implement `DataStreamParser` / `DataStreamWriter` in `org.vast.swe.fast` and add a branch to `SWEHelper.createDataParser` / `createDataWriter` |
| Add an OWS operation binding | Request POJO + `*ReaderV20` / `*WriterV20`, then an entry in the service's `*Registry.xml` (e.g. `SOSRegistry.xml`) |
| Register bindings from a new jar | Implement `OWSBindingProvider` and list it in `META-INF/services/org.vast.ows.OWSBindingProvider`, as `SOSUtils` / `SPSUtils` do |
| Add an executable process algorithm | Extend `ExecutableProcessImpl` with a static `ProcessInfo`, as the test class `WindChill_Process` does |

## Tests

| Project | Test classes |
|---|---|
| swe-common-core | 19 classes in `org.vast.swe.test` and `org.vast.swe.fast`, e.g. [`TestSweHelper`](../../../lib-ogc/swe-common-core/src/test/java/org/vast/swe/test/TestSweHelper.java), [`TestSweJsonBindingsV20`](../../../lib-ogc/swe-common-core/src/test/java/org/vast/swe/test/TestSweJsonBindingsV20.java), [`TestTextDataParser`](../../../lib-ogc/swe-common-core/src/test/java/org/vast/swe/fast/TestTextDataParser.java), [`TestBinaryDataParser`](../../../lib-ogc/swe-common-core/src/test/java/org/vast/swe/fast/TestBinaryDataParser.java), [`TestUnitConversion`](../../../lib-ogc/swe-common-core/src/test/java/org/vast/swe/test/TestUnitConversion.java) |
| swe-common-om | [`TestOMBindingsV20`](../../../lib-ogc/swe-common-om/src/test/java/org/vast/ogc/om/TestOMBindingsV20.java), [`TestGMLBindingsV32`](../../../lib-ogc/swe-common-om/src/test/java/org/vast/ogc/gml/TestGMLBindingsV32.java), [`TestGeoJsonBindings`](../../../lib-ogc/swe-common-om/src/test/java/org/vast/ogc/gml/TestGeoJsonBindings.java), [`TestTimeExtent`](../../../lib-ogc/swe-common-om/src/test/java/org/vast/util/TestTimeExtent.java), [`TestBbox`](../../../lib-ogc/swe-common-om/src/test/java/org/vast/util/TestBbox.java) (+2) |
| sensorml-core | [`TestSMLProcessing`](../../../lib-ogc/sensorml-core/src/test/java/org/vast/sensorML/test/TestSMLProcessing.java), [`TestSMLStaxBindingsV20`](../../../lib-ogc/sensorml-core/src/test/java/org/vast/sensorML/test/TestSMLStaxBindingsV20.java), [`TestSMLJsonBindingsV20`](../../../lib-ogc/sensorml-core/src/test/java/org/vast/sensorML/test/TestSMLJsonBindingsV20.java), [`TestSMLJsonBindingsV30`](../../../lib-ogc/sensorml-core/src/test/java/org/vast/sensorML/test/TestSMLJsonBindingsV30.java), [`TestSMLHelper`](../../../lib-ogc/sensorml-core/src/test/java/org/vast/sensorML/TestSMLHelper.java); plus 4 test process classes |
| ogc-services-common | Only the abstract base [`OWSTestCase`](../../../lib-ogc/ogc-services-common/src/test/java/org/vast/ows/test/OWSTestCase.java) (shared via `testArtifacts`) |
| ogc-services-swe | None |
| ogc-services-sos | 7 `TestSos*BindingsV20` classes, e.g. [`TestSosGetObsBindingsV20`](../../../lib-ogc/ogc-services-sos/src/test/java/org/vast/ows/sos/test/TestSosGetObsBindingsV20.java) |
| ogc-services-sps | 5 `TestSps*BindingsV20` classes + abstract [`SPSTestCase`](../../../lib-ogc/ogc-services-sps/src/test/java/org/vast/ows/sps/test/SPSTestCase.java), e.g. [`TestSpsTaskingBindingsV20`](../../../lib-ogc/ogc-services-sps/src/test/java/org/vast/ows/sps/test/TestSpsTaskingBindingsV20.java) |

Test resources (XML/JSON samples) are under each project's `src/test/resources`.

```bash
./gradlew :swe-common-core:test --tests 'org.vast.swe.test.TestSweHelper'
./gradlew :sensorml-core:test --tests 'org.vast.sensorML.test.TestSMLProcessing'
./gradlew :ogc-services-sos:test --tests 'org.vast.ows.sos.test.TestSosGetObsBindingsV20'
```

## Related

- [Code map index](../index.md)
- [Processing](processing.md) (uses `IProcessExec` / `SMLUtils`)
- [SWE services (SOS / SPS)](service-swe.md)
- [Connected Systems API](service-consys.md)
- [Sensor drivers](sensor-drivers.md)
- [Kryo serialization](kryo-serialization.md)
