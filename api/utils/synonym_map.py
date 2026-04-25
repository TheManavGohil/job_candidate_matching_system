"""
Skill synonym dictionary and normalization utilities.
"""

# Map common variations to canonical skill names
SYNONYM_MAP = {
    # Programming Languages
    "python3": "python",
    "python 3": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "ecmascript": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "golang": "go",
    "go lang": "go",
    "c++": "cpp",
    "c plus plus": "cpp",
    "c#": "csharp",
    "c sharp": "csharp",
    "objective-c": "objective-c",
    "obj-c": "objective-c",
    "r lang": "r",
    "r language": "r",
    "java": "java",
    "kotlin": "kotlin",
    "swift": "swift",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "perl": "perl",
    "scala": "scala",
    "elixir": "elixir",
    "haskell": "haskell",
    "lua": "lua",
    "dart": "dart",
    "matlab": "matlab",
    "julia": "julia",

    # Web Frameworks
    "react.js": "react",
    "reactjs": "react",
    "react js": "react",
    "angular.js": "angular",
    "angularjs": "angular",
    "vue.js": "vue",
    "vuejs": "vue",
    "next.js": "nextjs",
    "next js": "nextjs",
    "nuxt.js": "nuxtjs",
    "node.js": "nodejs",
    "node js": "nodejs",
    "express.js": "express",
    "expressjs": "express",
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    "rails": "ruby on rails",
    "ruby on rails": "ruby on rails",
    "asp.net": "asp.net",
    "dotnet": ".net",
    ".net core": ".net",
    "svelte": "svelte",
    "sveltekit": "sveltekit",

    # Databases
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "psql": "postgresql",
    "mysql": "mysql",
    "my sql": "mysql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "mongo db": "mongodb",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "elastic search": "elasticsearch",
    "cassandra": "cassandra",
    "dynamodb": "dynamodb",
    "dynamo db": "dynamodb",
    "sqlite": "sqlite",
    "mariadb": "mariadb",
    "neo4j": "neo4j",
    "couchdb": "couchdb",
    "firestore": "firestore",
    "supabase": "supabase",

    # Cloud & DevOps
    "amazon web services": "aws",
    "aws": "aws",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "gcp": "gcp",
    "microsoft azure": "azure",
    "azure": "azure",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "terraform": "terraform",
    "ansible": "ansible",
    "jenkins": "jenkins",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "github actions": "github actions",
    "gitlab ci": "gitlab ci",
    "circleci": "circleci",
    "travis ci": "travis ci",
    "heroku": "heroku",
    "vercel": "vercel",
    "netlify": "netlify",
    "nginx": "nginx",
    "apache": "apache",
    "linux": "linux",

    # AI / ML
    "machine learning": "machine learning",
    "ml": "machine learning",
    "deep learning": "deep learning",
    "dl": "deep learning",
    "artificial intelligence": "ai",
    "ai": "ai",
    "natural language processing": "nlp",
    "nlp": "nlp",
    "computer vision": "computer vision",
    "cv": "computer vision",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "keras": "keras",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "sci-kit learn": "scikit-learn",
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "hugging face": "huggingface",
    "huggingface": "huggingface",
    "transformers": "transformers",
    "langchain": "langchain",
    "llm": "llm",
    "large language model": "llm",
    "large language models": "llm",
    "rag": "rag",
    "retrieval augmented generation": "rag",
    "generative ai": "generative ai",
    "gen ai": "generative ai",
    "openai": "openai",
    "chatgpt": "chatgpt",
    "gpt": "gpt",
    "bert": "bert",
    "spacy": "spacy",
    "nltk": "nltk",
    "opencv": "opencv",
    "yolo": "yolo",
    "stable diffusion": "stable diffusion",
    "mlops": "mlops",
    "data science": "data science",
    "data engineering": "data engineering",
    "feature engineering": "feature engineering",
    "model deployment": "model deployment",

    # Data & Analytics
    "apache spark": "spark",
    "spark": "spark",
    "pyspark": "pyspark",
    "hadoop": "hadoop",
    "apache kafka": "kafka",
    "kafka": "kafka",
    "airflow": "airflow",
    "apache airflow": "airflow",
    "dbt": "dbt",
    "snowflake": "snowflake",
    "bigquery": "bigquery",
    "big query": "bigquery",
    "redshift": "redshift",
    "tableau": "tableau",
    "power bi": "power bi",
    "powerbi": "power bi",
    "looker": "looker",
    "etl": "etl",
    "data warehousing": "data warehousing",

    # Mobile
    "react native": "react native",
    "react-native": "react native",
    "flutter": "flutter",
    "ios": "ios",
    "android": "android",
    "swiftui": "swiftui",
    "jetpack compose": "jetpack compose",

    # Tools & Practices
    "git": "git",
    "github": "github",
    "gitlab": "gitlab",
    "bitbucket": "bitbucket",
    "jira": "jira",
    "confluence": "confluence",
    "agile": "agile",
    "scrum": "scrum",
    "kanban": "kanban",
    "tdd": "tdd",
    "test driven development": "tdd",
    "bdd": "bdd",
    "rest": "rest api",
    "restful": "rest api",
    "rest api": "rest api",
    "graphql": "graphql",
    "grpc": "grpc",
    "websocket": "websocket",
    "websockets": "websocket",
    "microservices": "microservices",
    "micro services": "microservices",
    "api design": "api design",
    "system design": "system design",
    "design patterns": "design patterns",
    "solid principles": "solid",
    "oop": "oop",
    "object oriented": "oop",
    "functional programming": "functional programming",

    # Frontend
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",
    "sass": "sass",
    "scss": "sass",
    "less": "less",
    "tailwind": "tailwindcss",
    "tailwind css": "tailwindcss",
    "tailwindcss": "tailwindcss",
    "bootstrap": "bootstrap",
    "material ui": "material ui",
    "mui": "material ui",
    "chakra ui": "chakra ui",
    "styled components": "styled-components",
    "webpack": "webpack",
    "vite": "vite",
    "babel": "babel",
    "eslint": "eslint",
    "prettier": "prettier",
    "storybook": "storybook",
    "jest": "jest",
    "cypress": "cypress",
    "playwright": "playwright",
    "selenium": "selenium",
    "puppeteer": "puppeteer",

    # Security
    "oauth": "oauth",
    "oauth2": "oauth",
    "jwt": "jwt",
    "json web token": "jwt",
    "ssl": "ssl/tls",
    "tls": "ssl/tls",
    "encryption": "encryption",
    "cybersecurity": "cybersecurity",
    "penetration testing": "penetration testing",
    "pen testing": "penetration testing",

    # Other
    "sql": "sql",
    "nosql": "nosql",
    "orm": "orm",
    "rabbitmq": "rabbitmq",
    "celery": "celery",
    "socketio": "socket.io",
    "socket.io": "socket.io",
    "prometheus": "prometheus",
    "grafana": "grafana",
    "elk stack": "elk stack",
    "logstash": "logstash",
    "kibana": "kibana",
    "sentry": "sentry",
    "new relic": "new relic",
    "datadog": "datadog",
}

# Known tech skills set (for extraction from free text)
KNOWN_SKILLS = set(SYNONYM_MAP.values()) | set(SYNONYM_MAP.keys())


def normalize_skill(skill: str) -> str:
    """Normalize a skill name using the synonym map."""
    cleaned = skill.strip().lower()
    return SYNONYM_MAP.get(cleaned, cleaned)


def normalize_skills(skills: list) -> list:
    """Normalize a list of skills, deduplicate, and return sorted."""
    seen = set()
    result = []
    for s in skills:
        normalized = normalize_skill(s)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return sorted(result)


def extract_skills_from_text(text: str) -> list:
    """
    Extract known skills from free-form text.
    Uses exact substring matching against the known skills vocabulary.
    """
    text_lower = text.lower()
    found = set()

    # Sort by length descending to match longer phrases first
    sorted_skills = sorted(KNOWN_SKILLS, key=len, reverse=True)

    for skill in sorted_skills:
        skill_lower = skill.lower()
        if len(skill_lower) < 2:
            continue

        # Check for word-boundary matches to avoid false positives
        import re
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, text_lower):
            canonical = normalize_skill(skill_lower)
            found.add(canonical)

    return sorted(found)
