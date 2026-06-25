Inventory Management System
.
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── organization.py
│   │       │   └── user.py
│   │       └── router.py
│   ├── constants/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── error_handlers.py
│   │   ├── exceptions.py
│   │   └── security.py
│   ├── db/
│   │   ├── migrations/
│   │   └── models/
│   │       ├── base.py
│   │       ├── organization.py
│   │       └── user.py
│   ├── middlewares/
│   ├── repositories/
│   │   ├── auth_repository.py
│   │   ├── organization_repository.py
│   │   └── user_repository.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── response.py
│   │   └── user.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── organization_service.py
│   │   └── user_service.py
│   └── main.py
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── uv.lock
