# include .env

.PHONY: scroll
scroll:
	poetry run python scheduled_post.py --scrollonly