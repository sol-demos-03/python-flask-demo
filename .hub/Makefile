.DEFAULT_GOAL := deploy

aws := aws
jq  := jq -r

PLATFORM_STATE_FILE   ?= should-come-from-env
PLATFORM_STATE_BUCKET ?= $(firstword $(subst /, ,$(PLATFORM_STATE_FILE:s3://%=%)))
PLATFORM_STATE_REGION ?= $(shell $(aws) s3api get-bucket-location --bucket $(PLATFORM_STATE_BUCKET) | $(jq) '.LocationConstraint//"us-east-1"')
NAMESPACE 	          ?= jenkins
DOMAIN_NAME           ?= should-be-set
APP_STATE_FILE_LOCAL  ?= hub.state
APP_STATE_FILE        ?= should-come-from-env
APP_STATE 			  ?= $(APP_STATE_FILE_LOCAL),$(APP_STATE_FILE)
APP_ELABORATE_FILE 	  ?= hub.elaborate
DOCKER_AUTH_KIND ?= unknown

hub := hub -d --aws_region=$(PLATFORM_STATE_REGION) --aws_use_iam_role_credentials=false
kubectl := kubectl --context="$(DOMAIN_NAME)" --namespace="$(NAMESPACE)"
kubectlapp := kubectl --context="$(DOMAIN_NAME)"

deploy:
	$(kubectl) apply -f templates/credentials.yaml
	$(kubectl) apply -f templates/$(DOCKER_AUTH_KIND)/pipeline.yaml
.PHONY: deploy

undeploy:
	- $(kubectl) delete -f templates/$(DOCKER_AUTH_KIND)/pipeline.yaml
	- $(kubectlapp) delete -f templates/$(DOCKER_AUTH_KIND)/kubernetes.yaml
.PHONY: undeploy

$(APP_ELABORATE_FILE):
	$(hub) elaborate hub.yaml managed.yaml -s $(PLATFORM_STATE_FILE) -e application.state=$(APP_ELABORATE_FILE) -o $@

hubdeploy: $(APP_ELABORATE_FILE)
	$(hub) deploy $(lastword $^) -s $(APP_STATE)
.PHONY: install

hubundeploy: $(APP_ELABORATE_FILE)
	$(hub) undeploy $(APP_ELABORATE_FILE) -s $(APP_STATE)
.PHONY: hubundeploy

params:
	$(eval APPLICATION_NAME=$(shell $(hub) explain $(APP_STATE) \
		--json | $(jq) '.stackOutputs | to_entries[] | select(.key == "application.name") | .value' ))
	$(eval JENKINS_NAMESPACE=$(shell $(hub) explain $(APP_STATE) \
		--json | $(jq) '.stackOutputs | to_entries[] | select(.key == "application.jenkins.namespace") | .value' ))
.PHONY: params

statemap:
	$(hub) kubeconfig $(APP_STATE) --switch-kube-context
	kubectl --namespace="$(JENKINS_NAMESPACE)" create configmap $(APPLICATION_NAME)-state \
		--from-file $(APP_STATE_FILE_LOCAL) || kubectl --namespace="$(JENKINS_NAMESPACE)" create configmap $(APPLICATION_NAME)-state  \
		--from-file $(APP_STATE_FILE_LOCAL) -o yaml --dry-run | kubectl --namespace="$(JENKINS_NAMESPACE)" replace -f -
.PHONY: statemap

rmstatemap:
	- $(hub) kubeconfig $(APP_STATE) --switch-kube-context
	- kubectl --namespace="$(JENKINS_NAMESPACE)" delete configmap $(APPLICATION_NAME)-state
.PHONY: rmstatemap

install: hubdeploy params statemap

uninstall: hubundeploy params rmstatemap

clean:
	rm -rf $(APP_ELABORATE_FILE) $(APP_STATE_FILE_LOCAL)
	rm -rf .git
