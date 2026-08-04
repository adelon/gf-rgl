# German Wikidata prototype baseline

Phase 1 starts from the completed source-independent German RGL extraction:

| Ref | Frozen commit | Role |
|---|---|---|
| `upstream/master` | `bd0506760e94daac8a9bc3bf5eb7b71fd5a4bd47` | Phase 0 reconstruction base |
| `ger-fixes` | `7899249e8c1e15888617d353df74c00f100da5a2` | Read-only design and curation reference |
| `ger` | `63542611429bb2103e5be39e056a944ece4cbf57` | Completed source-independent RGL changes only |
| `ger-wikidata-prototype` | `63542611429bb2103e5be39e056a944ece4cbf57` | Phase 1 implementation base |

Importer work is committed only on `ger-wikidata-prototype`. The historical
German dictionaries are not inventory inputs, and neither `ger` nor
`ger-fixes` is modified by this experiment.
