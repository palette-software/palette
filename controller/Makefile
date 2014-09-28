include ../pylint.mk

all: pylint
	make -C DEBIAN all
.PHONY: all

pylint:
	$(PYLINT) controller/controller.py
	$(PYLINT) controller/agentinfo.py
	$(PYLINT) controller/agentmanager.py
	$(PYLINT) controller/agent.py
	$(PYLINT) controller/alert_email.py
	$(PYLINT) controller/auth.py
	$(PYLINT) controller/cache.py
	$(PYLINT) controller/clihandler.py
	$(PYLINT) controller/clierror.py
	$(PYLINT) controller/cloud.py
	$(PYLINT) controller/config.py
	$(PYLINT) controller/credential.py
	$(PYLINT) controller/croniter.py
	$(PYLINT) controller/data_connections.py
	$(PYLINT) controller/environment.py
	$(PYLINT) controller/event.py
	$(PYLINT) controller/event_control.py
	$(PYLINT) controller/extracts.py
	$(PYLINT) controller/exc.py
	$(PYLINT) controller/firewall.py
	$(PYLINT) controller/firewall_manager.py
	$(PYLINT) controller/http_requests.py
	$(PYLINT) controller/licensing.py
	$(PYLINT) controller/manager.py
	$(PYLINT) controller/mixin.py
	$(PYLINT) controller/odbc.py
	$(PYLINT) controller/palapi.py
	$(PYLINT) controller/ports.py
	$(PYLINT) controller/request.py
	$(PYLINT) controller/sched.py
	$(PYLINT) controller/sites.py
	$(PYLINT) controller/state_control.py
	$(PYLINT) controller/state.py
	$(PYLINT) controller/state_transitions.py
	$(PYLINT) controller/system.py
	$(PYLINT) controller/tableau.py
	$(PYLINT) controller/util.py
	$(PYLINT) controller/workbooks.py
	$(PYLINT) DEBIAN/bin/upgrade-agent
#	find . -name \*.py -exec pylint $(PYLINT_OPTS) '{}'  ';'
.PHONY: pylint

clean:
	rm -rf *.egg-info dist build
	find . -name \*.pyc -exec rm '{}' ';'
	make -C DEBIAN clean
.PHONY: pylint
