# Third-party notices and asset provenance

Repository source-code terms do not replace the terms of third-party packages or assets.

| Component | Use | Source / terms |
| --- | --- | --- |
| React, React DOM | Browser interface | [React](https://github.com/facebook/react), MIT |
| TypeScript, Vite | Type checking and bundling | [TypeScript](https://github.com/microsoft/TypeScript), Apache-2.0; [Vite](https://github.com/vitejs/vite), MIT |
| Lucide | Interface icons | [Lucide](https://github.com/lucide-icons/lucide), ISC |
| FastAPI, Starlette, Uvicorn | API and ASGI runtime | [FastAPI](https://github.com/fastapi/fastapi), MIT; [Starlette](https://github.com/Kludex/starlette) and [Uvicorn](https://github.com/Kludex/uvicorn), BSD-3-Clause |
| SQLAlchemy, Alembic | Database models and migrations | [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) and [Alembic](https://github.com/sqlalchemy/alembic), MIT |
| Psycopg | PostgreSQL driver | [Psycopg](https://www.psycopg.org/), LGPL-3.0; binary distribution includes separately licensed components |
| PostgreSQL | Local database; installed separately | [PostgreSQL licence](https://www.postgresql.org/about/licence/) |
| Pydantic, OpenPyXL, defusedxml | Validation and spreadsheet parsing | [Pydantic](https://github.com/pydantic/pydantic), MIT; [OpenPyXL](https://openpyxl.readthedocs.io/), MIT; [defusedxml](https://github.com/tiran/defusedxml), PSF |
| pwdlib, argon2-cffi | Password hashing | [pwdlib](https://github.com/frankie567/pwdlib) and [argon2-cffi](https://github.com/hynek/argon2-cffi), MIT |
| Yatra One | Self-hosted display lettering | Copyright 2014 The Yatra Project Authors; SIL OFL 1.1. [Bundled licence](frontend/public/fonts/yatra-one/OFL.txt); [upstream](https://github.com/google/fonts/tree/main/ofl/yatraone) |
| DM Sans | Interface text, requested from Google Fonts | [Upstream and SIL OFL 1.1](https://github.com/google/fonts/tree/main/ofl/dmsans); a system sans-serif fallback works without the font service |

This is a direct-component summary. Exact resolved packages are recorded in [Python requirements](backend/requirements-lock.txt) and [npm lockfile](frontend/package-lock.json); transitive packages retain their own notices.

## Original artwork

The Sampati bird emblem, folk-sky panorama and cloud-edge artwork were generated with OpenAI ImageGen for this project. A user-supplied drawing guided the style, rather than supplying the depicted subject. Exact prompts and generation provenance are recorded in [artwork provenance](frontend/public/artwork/provenance.json) and [cloud-edge provenance](frontend/public/artwork/cloud-edge-provenance.json). The source reference drawing is not distributed.

The supplied Shivaraja personal-use font is excluded from this repository and the public build. Its original local files are preserved privately under `.local/private-assets/`. Public display lettering uses the unmodified OFL-licensed Yatra One font.

## Fictional data and assistance

The CSV fixtures in `examples/` and the app's generated samples are fictional software examples. Screenshots show the local fictional demo, not live aircraft or an operational deployment.

OpenAI Codex assisted implementation, debugging, tests, documentation and repository preparation. ImageGen assisted the artwork. The application itself does not call an AI model or an external aviation feed. No independent model training or aviation-performance evaluation is claimed.

The README presentation was informed by Saishreek Singh's [REFLEX](https://github.com/Yoriichi-GOD/REFLEX) repository. Its source code, artwork, data and project claims were not copied into Sampati.
