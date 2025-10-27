multiagent-research-assistant/
├─ backend/
│  ├─ manage.py
│  ├─ requirements.txt
│  ├─ research_assistant/         # Django project
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  └─ wsgi.py
│  ├─ core/                       # Django app
│  │  ├─ models.py
│  │  ├─ serializers.py
│  │  ├─ views.py
│  │  ├─ urls.py
│  │  ├─ agents/                  # agent implementations
│  │  │  ├─ __init__.py
│  │  │  ├─ research_gathering.py
│  │  │  ├─ summarization.py
│  │  │  └─ knowledge_manager.py
│  │  └─ migrations/
│  └─ db.sqlite3
├─ frontend/
│  ├─ package.json
│  ├─ public/
│  └─ src/
│     ├─ App.js
│     ├─ index.js
│     ├─ components/
│     │  ├─ QueryForm.js
│     │  └─ Results.js
│     └─ api.js
└─ README.md
