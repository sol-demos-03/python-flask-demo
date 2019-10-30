.DEFAULT_GOAL := deploy

DOCKER_AUTH_KIND ?= unknown

deploy:
	cp ../../pipelines/$(DOCKER_AUTH_KIND)/Jenkinsfile ../../../Jenkinsfile
	cp ../../templates/$(DOCKER_AUTH_KIND)/kubernetes.yaml.template ../../../kubernetes.yaml.template
.PHONY: deploy

undeploy:
