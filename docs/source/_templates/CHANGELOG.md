
# CHANGELOG



## v0.5.0 (2025-03-25)


### Bug fixes

* fix: resolve EML geographic coverage ID references ([`8642818`](https://github.com/EDIorg/spinneret/commit/8642818b6205fc1a704455b80552acfc72c76176)) 
* fix: include data package identifier in geoenvo resolve logs ([`e1fe2c6`](https://github.com/EDIorg/spinneret/commit/e1fe2c6f32feda3e48578d1e872d59ad828c57d7)) 

### Build system

* build: update dependencies to address security vulnerabilities ([`5a9e414`](https://github.com/EDIorg/spinneret/commit/5a9e414cbd371619bc00e26646552c96bd8ba81e)) 
* build: update geoenvo package to latest version ([`3876807`](https://github.com/EDIorg/spinneret/commit/387680788ba81ff61244916901eb16c3691301fa)) 

### Features

* feat: enable data source filtering in create_geoenv_data_files ([`1ba6ae7`](https://github.com/EDIorg/spinneret/commit/1ba6ae765ec7a92c7cf47b3d721840ceced540b6)) 
* feat: enhance geometry resolution logging with metadata ([`9e16bb0`](https://github.com/EDIorg/spinneret/commit/9e16bb0f799d014a64b8d6e8c9270529f200ed8d)) 

### Testing

* test: update geoenvo test configuration ([`5a6504e`](https://github.com/EDIorg/spinneret/commit/5a6504e1619296d078a2506a8d1a2c0fed630b7e)) 
* test: batch process EML with geoenvo ([`052345c`](https://github.com/EDIorg/spinneret/commit/052345c808ea13f196cf0366628e41195b822dab)) 

## v0.4.0 (2025-03-19)


### Build system

* build: update environment to use geoenvo package ([`425d0bf`](https://github.com/EDIorg/spinneret/commit/425d0bf3400d39b522206eea6bf0e23b8c3666ce)) 

### Features

* feat: iterate over EML files to obtain environments ([`74ff66a`](https://github.com/EDIorg/spinneret/commit/74ff66a81d935f2745cd93087ce130d0c0290a27)) 
* feat: add GeoJSON conversion to GeographicCoverage class ([`4cb2dc3`](https://github.com/EDIorg/spinneret/commit/4cb2dc333c7b01366a35a379e5a758be7f896f2f)) 
* feat: parse EML geographic coverage to spatial geometries ([`54a82cc`](https://github.com/EDIorg/spinneret/commit/54a82cc2fe5972698e980ed30bd0789bb4cf9345)) 

## v0.3.0 (2025-01-17)


### Bug fixes

* fix: correct return logic in `add_predicate_annotations_to_workbook` ([`5a49584`](https://github.com/EDIorg/spinneret/commit/5a495842e17f8dad5db95453ad2a540382b52ce3)) 
* fix: handle multiple semicolons in CURIE expansion ([`31d0e9c`](https://github.com/EDIorg/spinneret/commit/31d0e9cf12ae01017038b253c74b7093b0282593)) 
* fix: update OntoGPT templates to improve grounding ([`1c79260`](https://github.com/EDIorg/spinneret/commit/1c7926037e76f9137ba25548a030e26e55598f7c)) 
* fix: correct OntoGPT command construction ([`31a5ff4`](https://github.com/EDIorg/spinneret/commit/31a5ff4605c02fd1c8a49e7a98d8ff376233f5ce)) 
* fix: prevent OntoGPT cache-related errors by clearing cache ([`d342773`](https://github.com/EDIorg/spinneret/commit/d3427737114469e2be59cdf7289a724c08a8601b)) 
* fix: add missing parameters to `annotate_workbooks` ([`9e8570a`](https://github.com/EDIorg/spinneret/commit/9e8570a52f3448712af71738c74bb18d93f99a55)) 

### Build system

* build: configure Read the Docs for explicit path to config.py ([`ee47493`](https://github.com/EDIorg/spinneret/commit/ee474938e6c15baec225f1a303c842dfb731f78b)) 

### Features

* feat: make plot writing to file optional in `plot_grounding_rates` ([`18d01bb`](https://github.com/EDIorg/spinneret/commit/18d01bbf495bee37977bccf3b46f2114dce40a78)) 
* feat: visualize similarity metrics by configuration ([`b392629`](https://github.com/EDIorg/spinneret/commit/b39262910b05e2b0ea7de92e3759683c654c8920)) 
* feat: visualize similarity metrics by predicate ([`1bd1184`](https://github.com/EDIorg/spinneret/commit/1bd118495fb9a46c98336bdac6aded865b5de07f)) 
* feat: add logging to `benchmark_against_standard` for better insights ([`13b2eb6`](https://github.com/EDIorg/spinneret/commit/13b2eb64bcd5f3b01c9e41767f445897a803970e)) 
* feat: visualize grounding rates across OntoGPT configurations ([`8fd9962`](https://github.com/EDIorg/spinneret/commit/8fd9962ac308279f6c61fea0ea697d0d79e01145)) 
* feat: enhance CURIE expansion with expanded prefix map ([`5a09e7e`](https://github.com/EDIorg/spinneret/commit/5a09e7ed8c17e56083e960e08769f1ed08781b56)) 
* feat: introduce `temperature` parameter for OntoGPT calls ([`44ac7d6`](https://github.com/EDIorg/spinneret/commit/44ac7d61598c3f363ff71ee4b66622d1322dbe7b)) 
* feat: implement benchmark data collection and testing ([`f003b96`](https://github.com/EDIorg/spinneret/commit/f003b96237e7e97ea83b21b51612d2959f3f93fb)) 
* feat: implement performance metric logging ([`d667b31`](https://github.com/EDIorg/spinneret/commit/d667b3161d4cd533cb3ea8764dba26b56a85cd50)) 
* feat: implement logging for debugging ([`864889e`](https://github.com/EDIorg/spinneret/commit/864889eac7791a2cf91c03a176975d973f2e6caf)) 
* feat: initialize benchmark testing module ([`66843ba`](https://github.com/EDIorg/spinneret/commit/66843ba5fe8d2c41ce78875a214a43522c51b321)) 

### Performance improvements

* perf: optimize OntoGPT calls using `ollama_chat` ([`2a46e33`](https://github.com/EDIorg/spinneret/commit/2a46e3388bd2b4013848c83309ef773dc6e29fa0)) 
* perf: enhance OntoGPT grounding with sample size ([`57e6df7`](https://github.com/EDIorg/spinneret/commit/57e6df729b005224621d594a9ef169a7bc128f40)) 

### Refactoring

* refactor: consolidate OntoGPT workbook annotators into a single function ([`ed668b1`](https://github.com/EDIorg/spinneret/commit/ed668b1ecf46121045733d37f0dfdbc357d043ca)) 
* refactor: remove outdated `add_dataset_annotations_to_workbook` function ([`25f0a8b`](https://github.com/EDIorg/spinneret/commit/25f0a8bc89c406c70fc1259e68abc8c243c94384)) 
* refactor: replace print statements with logging ([`23907c6`](https://github.com/EDIorg/spinneret/commit/23907c66d9af541ac233782e0b24d97f5e96499e)) 

### Testing

* test: create test data for term-set similarity score analysis ([`513e5e5`](https://github.com/EDIorg/spinneret/commit/513e5e5789e84fe10d215c844c1d5098be6fb2f5)) 

## v0.2.0 (2024-11-13)


### Bug fixes

* fix: preserve case sensitivity in `local_model` arguments ([`2fd7fa3`](https://github.com/EDIorg/spinneret/commit/2fd7fa31c585857ec4d235df6938fa464a56d49e)) 
* fix: ensure correct file extension for OntoGPT output ([`677dd0a`](https://github.com/EDIorg/spinneret/commit/677dd0a4d92a94194336de471a16018d9c3b030e)) 
* fix: gracefully handle missing OntoGPT output files ([`3636672`](https://github.com/EDIorg/spinneret/commit/36366727a0128afab59befa63a0925ae9c77b7a3)) 
* fix: handle optional methods element gracefully ([`591ed67`](https://github.com/EDIorg/spinneret/commit/591ed675d017cc8f983539a4c4c3f18798ef5d99)) 
* fix: handle ungrounded IDs gracefully in CURIE expansion ([`b493340`](https://github.com/EDIorg/spinneret/commit/b493340341b4a410fcb7aa49a371bcbc6382d5ac)) 
* fix: remove empty XML tags during EML loading ([`4c42c93`](https://github.com/EDIorg/spinneret/commit/4c42c9362c82287b383f007eae8bc7537a7f3544)) 
* fix: enhance author attribution in `add_qudt_annotations_to_workbook` ([`3047953`](https://github.com/EDIorg/spinneret/commit/3047953cb6c4f9153e69b9c8e7be04159da7b07b)) 
* fix: ensure correct annotation placement in EML ([`346281c`](https://github.com/EDIorg/spinneret/commit/346281ca08204fda4d648b4c1af63c3a1614b1b1)) 
* fix: make `get_description` more resilient to missing elements ([`87a66d0`](https://github.com/EDIorg/spinneret/commit/87a66d08f5be7203237d0a34d1ab813495417ac8)) 
* fix: correct BioPortal annotator parameter format ([`b95961f`](https://github.com/EDIorg/spinneret/commit/b95961f772e7491956e70433e086d13be09a33d2)) 

### Build system

* build: integrate `ontogpt` for SPIRES-based annotation ([`235924e`](https://github.com/EDIorg/spinneret/commit/235924ec8180822892f85aa752e2defd992945d1)) 
* build: upgrade `soso` dependency to latest version ([`58b282a`](https://github.com/EDIorg/spinneret/commit/58b282aa27b5ec01e24808d23b700de767002250)) 
* build: integrate `soso` package for EML conversion ([`d368f92`](https://github.com/EDIorg/spinneret/commit/d368f92d3ecec307383ed9244932a0917a825f66)) 

### Documentation

* docs: provide QUDT annotation demonstration ([`f52a448`](https://github.com/EDIorg/spinneret/commit/f52a448c5fcb017eef3b3cd5e7a2b718cd8d5e13)) 
* docs: remove outdated parameter description ([`c745d2d`](https://github.com/EDIorg/spinneret/commit/c745d2dc323d5a23fe02d783deafbece2b975fd2)) 
* docs: clarify annotation refresh process ([`41176b3`](https://github.com/EDIorg/spinneret/commit/41176b3b8986efa5aaca79e1a4139760801f5b91)) 
* docs: clarify annotation reuse and skipping logic ([`5cfaa20`](https://github.com/EDIorg/spinneret/commit/5cfaa20484dcd91541e95a61e73a0bfbbfd4965d)) 
* docs: document main interface for clarity ([`4febaf6`](https://github.com/EDIorg/spinneret/commit/4febaf6a79110cac8664eee024dd23ada35c4014)) 
* docs: remove obsolete function reference ([`54589dc`](https://github.com/EDIorg/spinneret/commit/54589dcd31007d9763e1c932318d6704d430ffb5)) 
* docs: correct GitHub username references ([`0922168`](https://github.com/EDIorg/spinneret/commit/09221687093052f64a360759939eb0cc1097300d)) 

### Features

* feat: enhance `annotate_eml` flexibility with object/path input/output ([`e5a96a5`](https://github.com/EDIorg/spinneret/commit/e5a96a5ce9656ee45d6bfdfaa29a04fc78c700b0)) 
* feat: implement duplicate annotation removal in workbook annotators ([`7f388e3`](https://github.com/EDIorg/spinneret/commit/7f388e39b749f9271ba4a19b5a18ab667f822391)) 
* feat: remove empty workbook rows for clarity ([`89ae337`](https://github.com/EDIorg/spinneret/commit/89ae337b5393d7de6f961c1fcbca8016033acf69)) 
* feat: annotate `methods` with OntoGPT ([`d72647e`](https://github.com/EDIorg/spinneret/commit/d72647e80e3acbe163b7ae351c657cb123f67e72)) 
* feat: enhance get_description to include methods ([`adad111`](https://github.com/EDIorg/spinneret/commit/adad1116f758cd384df5e0eafd6a0459a60b398c)) 
* feat: annotate `research topic` with OntoGPT ([`42dbf77`](https://github.com/EDIorg/spinneret/commit/42dbf7727a242aa0c554b947e067bec71da8d180)) 
* feat: annotate `environmental medium` with OntoGPT ([`48b3246`](https://github.com/EDIorg/spinneret/commit/48b3246f2b3cd46f50718bf560c2af28c459c44f)) 
* feat: annotate `local environmental context` with OntoGPT ([`2335413`](https://github.com/EDIorg/spinneret/commit/233541304edb3ec5b98609367bc64ade468022ac)) 
* feat: annotate `broad environmental context` with OntoGPT ([`1c825bb`](https://github.com/EDIorg/spinneret/commit/1c825bb83657244f4eedf18fb5141f04aa8fb299)) 
* feat: annotate `processes` with OntoGPT ([`aaefbff`](https://github.com/EDIorg/spinneret/commit/aaefbffff05cacce818741d121fcd5358e36f832)) 
* feat: annotate `measurements` with OntoGPT ([`b91c65c`](https://github.com/EDIorg/spinneret/commit/b91c65c21a23b2d81251772e3009dfe5684bf519)) 
* feat: implement SPIRES-based annotation with `ontogpt` ([`62cc039`](https://github.com/EDIorg/spinneret/commit/62cc03988da37d29264799635335895d647fda90)) 
* feat: introduce `add_measurement_type_annotations_to_workbook` function ([`ad04013`](https://github.com/EDIorg/spinneret/commit/ad04013f92cdd5235159dda1fd04ab3ce14dcde4)) 
* feat: introduce `add_dataset_annotation_to_workbook` function ([`a0c1ccb`](https://github.com/EDIorg/spinneret/commit/a0c1ccb20f49ec26b3b3ee7d3e9e66114256760e)) 
* feat: implement `write_eml` for standardized output ([`eda07a5`](https://github.com/EDIorg/spinneret/commit/eda07a506ccb9b161ffe4ea1d99e3e9cb9681df9)) 
* feat: implement write_workbook for standardized output ([`3eeb606`](https://github.com/EDIorg/spinneret/commit/3eeb6066f9ab755a1814dff2e2dba9774b0be4a7)) 
* feat: add `delete_annotations` for workbook cleanup ([`410d666`](https://github.com/EDIorg/spinneret/commit/410d666ae5f3748be32f45a3585efe55b35e2037)) 
* feat: remove duplicate annotations from workbook ([`5b1e913`](https://github.com/EDIorg/spinneret/commit/5b1e9135dce8e7269211bd536e22265427ad216f)) 
* feat: add utility functions for workbook field population ([`9dac35e`](https://github.com/EDIorg/spinneret/commit/9dac35e8c17f346b32ca7fa17a180f5bc22b2cd1)) 
* feat: introduce workbook row initialization ([`4cd6858`](https://github.com/EDIorg/spinneret/commit/4cd68581d41bdcf0ddbd18dad1993d03233e9862)) 
* feat: implement QUDT annotation for workbooks ([`b06ae95`](https://github.com/EDIorg/spinneret/commit/b06ae95956454b2a39fecbcac1fe21ca0039554f)) 
* feat: integrate EML unit conversion to QUDT annotations ([`1afe98c`](https://github.com/EDIorg/spinneret/commit/1afe98c70b584269f8607c2f9ae7ac87e73a4f43)) 
* feat: convert string literals to URI refs ([`0be6551`](https://github.com/EDIorg/spinneret/commit/0be655117c91b6af6116645d06640d943d8b0286)) 
* feat: batch process for creating shadow metadata ([`30d28b6`](https://github.com/EDIorg/spinneret/commit/30d28b6c9f8d3c0ae12340ab4b00a80aaa869bc7)) 
* feat: introduce `create_shadow_eml` wrapper ([`31d1d01`](https://github.com/EDIorg/spinneret/commit/31d1d01d104327e40777ab9536c7501d14891afd)) 
* feat: ensure EML userId is a URL for linked data compatibility ([`8c2f8dc`](https://github.com/EDIorg/spinneret/commit/8c2f8dc27116967a69edd7c4eb88a174aca8420e)) 
* feat: introduce module for shadow metadata generation ([`49e81cf`](https://github.com/EDIorg/spinneret/commit/49e81cfd151bd7c8c16d29672bcb21b5d1233d8d)) 
* feat: add `@id` to Dataset type in SOSO files ([`9c19ec2`](https://github.com/EDIorg/spinneret/commit/9c19ec237f9b4cbe5b924548c759b7d119bb35ea)) 
* feat: implement heuristic URI validation utility ([`872ef5e`](https://github.com/EDIorg/spinneret/commit/872ef5ef35e7a9a2366f2b91788398689fcb2371)) 
* feat: introduce `create_kgraph` function ([`691d926`](https://github.com/EDIorg/spinneret/commit/691d9265ea01b815a08eedbde12abf2d9d65ac76)) 
* feat: integrate metadata and vocabulary loading into `load_graph` ([`6589ac0`](https://github.com/EDIorg/spinneret/commit/6589ac051167e0ad6c4a31f3c47a76240f9d2530)) 
* feat: load vocabularies into a graph ([`cca7cce`](https://github.com/EDIorg/spinneret/commit/cca7cce7ef2585b1ff4b852a66896cd9c468a1fa)) 
* feat: establish main module for codebase ([`9ee3a00`](https://github.com/EDIorg/spinneret/commit/9ee3a006c4bb9834e3960090e57769026999eb11)) 
* feat: integrate empty tag removal in workbook.create ([`6847f91`](https://github.com/EDIorg/spinneret/commit/6847f911d345f231a9aeb2f6e0ba4cac5ef007e0)) 
* feat: prevent processing errors from empty XML tags ([`574970e`](https://github.com/EDIorg/spinneret/commit/574970ef5dfc7d9d46ba2b3956706d4cd96038b9)) 
* feat: implement EML annotation from worksheet ([`281c098`](https://github.com/EDIorg/spinneret/commit/281c0987914f54a24941fde757533088b78237ca)) 
* feat: implement automatic workbook annotation ([`c384477`](https://github.com/EDIorg/spinneret/commit/c3844779f9b7833f5b5a503cf67854e628c91810)) 
* feat: integrate BioPortal annotator for term recommendation ([`9822406`](https://github.com/EDIorg/spinneret/commit/9822406efdf4fa80a217a4b61a9543684f626450)) 
* feat: introduce configuration file for spinneret ([`1231973`](https://github.com/EDIorg/spinneret/commit/1231973259b51bb6ec819a79020c190be5b3c176)) 
* feat: add element descriptions to workbook ([`9d6da08`](https://github.com/EDIorg/spinneret/commit/9d6da0854f59ab0a59802be8351e3c123d41b48b)) 

### Performance improvements

* perf: skip annotation if element is annotated ([`a508e9b`](https://github.com/EDIorg/spinneret/commit/a508e9b4c1ee779ad924973d28ecb99e047bff0f)) 
* perf: extend annotation with caching to all workbook annotators ([`7a9fa7c`](https://github.com/EDIorg/spinneret/commit/7a9fa7c42ecc5d75dadea81a1afe3bf5e84d2a6b)) 
* perf: optimize attribute annotation with caching ([`7287f31`](https://github.com/EDIorg/spinneret/commit/7287f3109e747a420ea62cadf4b70a567032bce8)) 

### Refactoring

* refactor: enhance duplicate annotation detection criteria ([`31067f8`](https://github.com/EDIorg/spinneret/commit/31067f8363206c7899c87c8e1359e55c5d99582c)) 
* refactor: remove extraneous commented code ([`83ed3d5`](https://github.com/EDIorg/spinneret/commit/83ed3d5650c9dadcf75088bdc344ed4447cb0612)) 
* refactor: prevent ungrounded annotations from being added to EML ([`e9af9cb`](https://github.com/EDIorg/spinneret/commit/e9af9cba2322732f5ee2b478cf3ff417aaf1a856)) 
* refactor: modularize workbook annotation for improved accuracy ([`05222c3`](https://github.com/EDIorg/spinneret/commit/05222c32d359a9df5ccdcffcfce9fe27c217fb9d)) 
* refactor: remove tentative annotation skipping logic ([`33e2731`](https://github.com/EDIorg/spinneret/commit/33e2731c7793813a339aad7c4bfa313fdb29d9b4)) 
* refactor: annotate workbook by predicate ([`cbae977`](https://github.com/EDIorg/spinneret/commit/cbae977e3f41dff17dccb235195ce61a10add0d5)) 
* refactor: pass EML to `annotate_workbook` subroutines for context ([`fc3dd16`](https://github.com/EDIorg/spinneret/commit/fc3dd16717949bd41b8f97e4d97761be479c2bbe)) 
* refactor: integrate `write_eml` ([`390da39`](https://github.com/EDIorg/spinneret/commit/390da394169552c94267b3f0f53694657e0c8a99)) 
* refactor: integrate `write_workbook` ([`3e90f64`](https://github.com/EDIorg/spinneret/commit/3e90f648794c0cd8f3ad6683f6025d53ad7e951d)) 
* refactor: integrate EML and workbook loading utilities ([`44468ea`](https://github.com/EDIorg/spinneret/commit/44468ea54b1fde860a0af64cafdf1cd600b5ba0a)) 
* refactor: centralize EML and workbook loading for code clarity ([`f0f2e5e`](https://github.com/EDIorg/spinneret/commit/f0f2e5e3f97bcb8eafd0983f4f84cc8a730ba177)) 
* refactor: streamline workbook row creation in annotators ([`962863c`](https://github.com/EDIorg/spinneret/commit/962863c0f01d810e5f77a2d33733ffe87a341895)) 
* refactor: integrate `delete_annotations` to workbook annotation ([`e74495a`](https://github.com/EDIorg/spinneret/commit/e74495a66fdabb5f9bb4a9df56e59cb18d9e8a56)) 
* refactor: standardize workbook annotator return types ([`400cc53`](https://github.com/EDIorg/spinneret/commit/400cc5322130e1d463ba30671982a83e983bf1a0)) 
* refactor: enable flexible I/O for workbook annotators ([`71f2a3e`](https://github.com/EDIorg/spinneret/commit/71f2a3e0072b74dda640c643f995261e88c59d05)) 
* refactor: utilize existing id attribute values in EML ([`92f10b4`](https://github.com/EDIorg/spinneret/commit/92f10b49342739e913f6eaece70140c867f8bfec)) 
* refactor: integrate workbook row creation ([`d7a7f7c`](https://github.com/EDIorg/spinneret/commit/d7a7f7c379b59c986a0ac23e79c3356c7b45bb48)) 
* refactor: create soso files from shadow EML files ([`e4c34c9`](https://github.com/EDIorg/spinneret/commit/e4c34c9e2eee4c2227489a940c522795c6a73521)) 
* refactor: rename `is_uri` function for accuracy ([`ded2748`](https://github.com/EDIorg/spinneret/commit/ded27484a57004c140cd34ee706b451f2a5ece27)) 
* refactor: rename `silhouette` module to `shadow` for clarity ([`badea82`](https://github.com/EDIorg/spinneret/commit/badea82afe591904141d535e2ccc38aca54153f5)) 
* refactor: rename `load_graph` to `create_graph` for clarity ([`f9b5f43`](https://github.com/EDIorg/spinneret/commit/f9b5f43c48c669585c351cc6feba0f9e1c35ecac)) 
* refactor: deprecate existing load functions in favor of `load_graph` ([`52ffe8e`](https://github.com/EDIorg/spinneret/commit/52ffe8ee5648960846372e9c72675e24c0bdaa1c)) 
* refactor: rename `combine_jsonld_files` to `load_metadata` ([`9eae7f5`](https://github.com/EDIorg/spinneret/commit/9eae7f5f8f99b4523fd18f774e8f6fbeb9069dc2)) 
* refactor: output one workbook per EML file ([`b6e7c92`](https://github.com/EDIorg/spinneret/commit/b6e7c924d5343acf2fe0438c26521bbfdbbfc2a2)) 

### Testing

* test: refine workbook annotator test clarity ([`cbe98ae`](https://github.com/EDIorg/spinneret/commit/cbe98ae5bf9fb7070acadf720ec0c3b069e95044)) 
* test: integrate `has_annotations` utility ([`987c5b0`](https://github.com/EDIorg/spinneret/commit/987c5b05dd94b13aaf998fc774b0b356884e12ef)) 
* test: implement `has_annotations` utility for testing ([`2831176`](https://github.com/EDIorg/spinneret/commit/2831176281820f767cc1a126e3b5cd26421eb4e4)) 
* test: address Pandas warnings in workbook annotation ([`8fc3263`](https://github.com/EDIorg/spinneret/commit/8fc326359f90962b35932dba35c8c7464abe1675)) 
* test: mock API calls to annotator with manual option ([`9eb93c7`](https://github.com/EDIorg/spinneret/commit/9eb93c71adde55e83c99e9abdd3510afbb6bb4b0)) 
* test: include missing annotated workbook for testing ([`b4d4374`](https://github.com/EDIorg/spinneret/commit/b4d437464c0026c0dc82dae30f799b839e24b139)) 

## v0.1.0 (2024-08-21)


### Build system

* build: establish package structure ([`8e71588`](https://github.com/EDIorg/spinneret/commit/8e71588ebd1f75d0a94846ab5fc84e6aa44c8d30)) 

### Continuous integration

* ci: align Black version in CI with local environment ([`35dec17`](https://github.com/EDIorg/spinneret/commit/35dec17ddd572d4ba1bcbeeaf8bf63362ab343bf)) 

### Features

* feat: migrate src/ modules from previous spinneret iteration ([`4a846ca`](https://github.com/EDIorg/spinneret/commit/4a846ca0541d20db2919ea344d5e896f99326822)) 

### Testing

* test: migrate tests/ module from previous spinneret iteration ([`a0f524b`](https://github.com/EDIorg/spinneret/commit/a0f524b10f3814cb424ec4c25b2604ae18d51d6b))
