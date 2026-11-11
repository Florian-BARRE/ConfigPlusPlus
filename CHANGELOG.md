# Changelog

## [0.4.1](https://github.com/Florian-BARRE/ConfigPlusPlus/compare/configplusplus-v0.4.0...configplusplus-v0.4.1) (2026-11-11)


### Bug Fixes

* **security:** drop the chained cause from cast errors so the value leaves the traceback ([#42](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/42)) ([bffe1c1](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/bffe1c10268e3065b12441c51a3733850b6b2aef))
* **security:** stop leaking the env_list item value in the cast-error message ([#41](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/41)) ([15b73ab](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/15b73ab339d9b537210754936af6a9e2360d4c9e))
* stop leaking env value in cast-error (BUG-01) ([#40](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/40)) ([1eac9d2](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/1eac9d237810cd42e553b5d281e3716f513033dc))


### Documentation

* add refactoring campaign target architecture and audit ([#36](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/36)) ([f0880ed](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/f0880ed8ad203ce3367ede53035ca074642ab4d0))
* add refactoring campaign wave/ticket plan ([#39](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/39)) ([817f65b](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/817f65be83c286bcef29fe13f34ee5cec0c4c32c))
* **agents:** rewrite the agent texts from the project's facts ([#21](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/21)) ([a34a2d2](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/a34a2d271964b6e32d1e53f8d1723f98b15de56a))
* close the refactoring campaign (reconcile prose, archive docs) ([#48](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/48)) ([5cc9e82](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/5cc9e82af2c37c87b420b88e962f834e7087ede0))
* correct the release and CI descriptions ([#31](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/31)) ([2e39604](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/2e3960469099dd1e1dc24be1b31bd5eff5ef3753))

## [0.4.0](https://github.com/Florian-BARRE/ConfigPlusPlus/compare/configplusplus-v0.3.0...configplusplus-v0.4.0) (2026-09-18)


### Features

* configurable display formats (table/json/dotenv/flat) via render() ([#14](https://github.com/Florian-BARRE/ConfigPlusPlus/issues/14)) ([cb983eb](https://github.com/Florian-BARRE/ConfigPlusPlus/commit/cb983eb746b1d8b8e1b56fafb2d45c350981d065))

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
