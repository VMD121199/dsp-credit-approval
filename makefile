.DEFAULT_GOAL := help

.EXPORT_ALL_VARIABLES:
AIRFLOW_HOME = ${PWD}/airflow

AIRFLOW_GENERATED_FILES = logs ../output_data airflow.cfg airflow.db webserver_config.py

init: ## Initialize the database
	airflow db init

user: ## Creates a database use called admin
	airflow users create --username admin --firstname admin --lastname admin --role Admin --email admin@admin.com

webserver: ## Run the web server
	airflow webserver --port 8080 &

web: ## Open Airflow UI
	open http://localhost:8080

scheduler: ## Run the scheduler
	airflow scheduler &

up: webserver scheduler ## Run Airflow web server and scheduler

down: ## Stop Airflow web server and scheduler
	pkill airflow

clean: ## Remove files generated by Airflow setup
	@echo removing files generated by airflow or used by the practical work
	cd $(AIRFLOW_HOME) && rm -rf $(AIRFLOW_GENERATED_FILES)

help: ## Show the different possible targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'