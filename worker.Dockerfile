FROM manavregistrycoderound.azurecr.io/api:v2
CMD ["celery", "-A", "api.tasks", "worker", "--loglevel=info"]
