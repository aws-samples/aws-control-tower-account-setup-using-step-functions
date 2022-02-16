.PHONY: setup build deploy format create-signing-profile clean

setup:
	python3 -m venv .venv
	.venv/bin/python3 -m pip install -U pip
	.venv/bin/python3 -m pip install -r requirements-dev.txt
	.venv/bin/python3 -m pip install -r dependencies/requirements.txt

create-signing-profile:
	aws signer put-signing-profile --platform-id "AWSLambda-SHA384-ECDSA" --profile-name AccountSetupProfile

build:
	sam build -u

deploy:
	sam deploy \
		--signing-profiles \
			SSOAssignmentFunction=AccountSetupProfile \
			ServiceCatalogPortfolioFunction=AccountSetupProfile \
			RegionalFunction=AccountSetupProfile \
			AccountFunction=AccountSetupProfile \
			DependencyLayer=AccountSetupProfile \
		--tags "GITHUB_ORG=aws-samples GITHUB_REPO=aws-control-tower-account-setup-using-step-functions"

clean:
	sam delete

format:
	.venv/bin/black -t py39 .
