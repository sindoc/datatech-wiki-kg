PYTHON ?= python3

.PHONY: sync graph feeds refs media publish quality refresh install-hooks preview-mail kernel-sync test-case visualize

sync:
	$(PYTHON) scripts/sync_sources.py

graph:
	$(PYTHON) scripts/build_graph.py

feeds:
	$(PYTHON) scripts/generate_campaign_assets.py

refs:
	$(PYTHON) scripts/render_reference_exports.py

media:
	$(PYTHON) scripts/render_media_manifest.py

publish:
	$(PYTHON) scripts/render_publication_artifacts.py

quality:
	$(PYTHON) scripts/check_wikipedia_quality.py

refresh:
	$(PYTHON) scripts/refresh_repo.py

install-hooks:
	$(PYTHON) scripts/install_hooks.py

preview-mail:
	$(PYTHON) scripts/send_opt_in_update.py

kernel-sync:
	$(PYTHON) scripts/sync_kernel_views.py

test-case:
	$(PYTHON) scripts/test_case.py

visualize:
	$(PYTHON) scripts/render_process_visual.py
