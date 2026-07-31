.PHONY: help test lint serve

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-z-]+:.*##' Makefile | awk 'BEGIN{FS=":.*?## "}{printf "  %-10s %s\n", $$1, $$2}'

test: ## Run unit tests
	python3 -m unittest -v test_kali_share

lint: ## Syntax-check sources
	python3 -m py_compile kali_share.py test_kali_share.py
	@echo "syntax OK"

serve: ## Serve ./ on :8000 with a random token
	python3 kali_share.py serve --dir .
