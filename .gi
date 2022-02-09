# Initial template for CI/CD 

before_script:
  ## Install SSH agent
  - 'command -v ssh-agent >/dev/null || ( apt-get update -y && apt-get install openssh-client -y ) > /dev/null'
  ## Run ssh-agent (inside the build environment)
  - eval $(ssh-agent -s)
  ## Add the SSH key stored in SSH_PRIVATE_KEY variable to the agent store
  - echo "$SSH_PRIVATE_KEY" | base64 -d | ssh-add -
  ## Create the SSH directory and give it the right permissions
  - mkdir -p ~/.ssh
  - chmod 700 ~/.ssh
  ## Deploy hostkey
  - echo "$SSH_KNOWN_HOSTS" >> ~/.ssh/known_hosts
  - chmod 644 ~/.ssh/known_hosts

stages:
  - deployment

deploy-tsm:
  stage: deployment
  only:
    refs:
      - master
  image: ubuntu
  when: manual
  script:
    ## Fire it up! Deployment is triggered by SSH command directive in targets authorized_keys file.
    - ssh tsm-orchestration@tsm.intranet.ufz.de
