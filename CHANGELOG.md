# Changelog

## [0.3.0](https://github.com/Florian-BARRE/ConfigPlusPlus/compare/configplusplus-v0.2.0...configplusplus-v0.3.0) (2026-09-02)


### Features

* env_list() plus safer env() casting and sink hygiene ([6f4a225](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/6f4a225e3a504f013194c2e4fcfae73c1bc1a0ec))
* ship PEP 561 py.typed marker so downstream type-checkers see the hints ([39457e3](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/39457e39997eeab1fdc31c6891d49fbd21a0c356))
* to_dict(mask), inherited-field aggregation, per-class sensitive keywords ([2703390](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/2703390f7ea0d0b9c1e94ba444be014d318e3535))


### Bug Fixes

* **ci:** make publish robust to release-please component tags and fix dispatch ([c595a74](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/c595a74dfb1dcb194cf474d516f842782f371b5c))
* **ci:** pin gh-action-pypi-publish by version tag, not commit SHA ([f95cf69](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/f95cf6993babbb33a3b990f7493af1a953bb3551))


### Documentation

* document env_list, to_dict(mask), custom keywords and py.typed ([f5dbb2e](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/f5dbb2e9a9e929986ced5112d3bd9aecc222f35b))

## [0.2.0](https://github.com/Florian-BARRE/ConfigPlusPlus/compare/configplusplus-v0.1.1...configplusplus-v0.2.0) (2026-09-02)


### Features

* export env_optional in the public API ([208d2cf](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/208d2cfc72100b5e794423df20b868bb9ecdc683))


### Bug Fixes

* **examples:** make comprehensive example runnable ([1da255b](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/1da255b636ad4914f2643067ca109af4191521ad))
* restore safe_load_envs default path and .env file matching ([54fd02a](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/54fd02af844fc2e78626bc308a5c79990ca68e54))


### Documentation

* rewrite README with hero, runnable examples and API reference ([4d4ba1b](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/4d4ba1bd8990f443fe8cf7b462e6c1df089d7656))
