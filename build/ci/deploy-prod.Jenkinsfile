pipeline {

  agent {
    node {
      label 'ci-base-v2'
    }
  }

  environment {
    // Slack
    SLACK_TOKEN                   = credentials("spdigital-slack-token")
    SLACK_CHANNEL                 = "#data-team-git"
    SLACK_TEAM_DOMAIN             = "sp-digital"

    // Kubernetes Docker
    DOCKER_REGISTRY               = "spdadocker.azurecr.io"
    KUBE_NAMESPACE                = "data-insight"
    KUBE_ENV                      = "prod"
    KUBE_SECRET                   = "getai-secret"
    INGRESS_HOST                  = "getai.di.spdigital.sg"

    VAULT_ADDR                    = "https://vault.in.spdigital.sg"
    VAULT_APP_TOKEN_PATH          = "jenkinsdontsupportv2/apptokens/prod/data-insight"
    VAULT_AIE_PATH                = "secret/data-aie"
    VAULT_SAS_PATH                = "secret/devops/sas-tokens/prod"
    VAULT_SAS_FILE                = "spdadiprod-rw"


    KAFKA_CA                      = "/pki-ca-az-int/issue/getai"
    KAFKA_CONSUMER_NAME           = "consumer.getai.kafka-chrono-prod.service.spda"
    //Devops
    VAULT_K8CONFIG_TOKEN_PATH     = "jenkinsdontsupportv2/apptokens/prod/kubeconfig"
    OVERWRITE_ROLEHASH            = "1"
  }

  stages {

    stage('Start') {
      steps {
        notifySlack('Deploy to Azure PROD', 'STARTED')
      }
    }

    stage('Get Kubeconfig') {
      steps {
        vaultProdWrapper {
          sh "make -f build/ci/Makefile k8config"
        }
      }
    }

    stage("Fetch SAS Key") {
        steps {
            vaultProdWrapper {
                sh "make -f build/ci/Makefile fetchkey"
            }
        }
        post {
          success { notifySlack("Fetch SAS Key", "SUCCESS") }
          failure { notifySlack("Fetch SAS Key", "FAILURE") }
        }
    }

    stage("Deploy") {
        when {
            expression {
                return params.MODE == 'Deploy';
            }
        }
        steps {
            vaultProdWrapper {
                sh '''
                sed -i.org "/image:/s|spdadocker.azurecr.io/spdigital-data/getai|${DOCKER_TAG}|" build/k8s/${KUBE_ENV}/get-ai-deploy.yml
                sed -i.org "/value:/s|{jenkins-build}|${KUBE_NAMESPACE}-${BUILD_ID}|" build/k8s/${KUBE_ENV}/get-ai-deploy.yml
                sed -i.org "/value:/s|{git-commit}|${GIT_COMMIT}|" build/k8s/${KUBE_ENV}/get-ai-deploy.yml
                sed -i.org "/host:/s|{ingress-host}|${INGRESS_HOST}|" build/k8s/${KUBE_ENV}/get-ai-ingress.yml
                sed -i.org "/value:/s|{kube-env}|${KUBE_ENV}|" build/k8s/${KUBE_ENV}/get-ai-deploy.yml
                sed -i.org "/image:/s|spdadocker.azurecr.io/spdigital-data/getai|${DOCKER_TAG}|" build/k8s/${KUBE_ENV}/get-ai-train-cronjob.yml
                sed -i.org "/value:/s|{jenkins-build}|${KUBE_NAMESPACE}-${BUILD_ID}|" build/k8s/${KUBE_ENV}/get-ai-train-cronjob.yml
                sed -i.org "/value:/s|{git-commit}|${GIT_COMMIT}|" build/k8s/${KUBE_ENV}/get-ai-train-cronjob.yml
                sed -i.org "/value:/s|{kube-env}|${KUBE_ENV}|" build/k8s/${KUBE_ENV}/get-ai-train-cronjob.yml
                sed -i.org "/image:/s|spdadocker.azurecr.io/spdigital-data/getai|${DOCKER_TAG}|" build/k8s/${KUBE_ENV}/get-ai-prediction-cronjob.yml
                sed -i.org "/value:/s|{jenkins-build}|${KUBE_NAMESPACE}-${BUILD_ID}|" build/k8s/${KUBE_ENV}/get-ai-prediction-cronjob.yml
                sed -i.org "/value:/s|{git-commit}|${GIT_COMMIT}|" build/k8s/${KUBE_ENV}/get-ai-prediction-cronjob.yml
                sed -i.org "/value:/s|{kube-env}|${KUBE_ENV}|" build/k8s/${KUBE_ENV}/get-ai-prediction-cronjob.yml
                '''
                sh "make -f build/ci/Makefile deploy"
            }
        }
        post {
          success { notifySlack("Deployment", "SUCCESS") }
          failure { notifySlack("Deployment", "FAILURE") }
        }
    }
    stage("Debug") {
        when {
            expression {
                return params.MODE == 'Debug';
            }
        }
        steps {
            vaultProdWrapper {
                sh '''
                sed -i.org "/value:/s|{kube-env}|${KUBE_ENV}|" build/k8s/${KUBE_ENV}/get-ai-train-init-job.yml
                sed -i.org "/image:/s|spdadocker.azurecr.io/spdigital-data/getai|${DOCKER_TAG}|" build/k8s/${KUBE_ENV}/get-ai-train-init-job.yml
                sed -i.org "/value:/s|{kube-env}|${KUBE_ENV}|" build/k8s/${KUBE_ENV}/get-ai-train-pod.yml
                sed -i.org "/image:/s|spdadocker.azurecr.io/spdigital-data/getai|${DOCKER_TAG}|" build/k8s/${KUBE_ENV}/get-ai-train-pod.yml
                '''
                sh """\
                    ${params.DEBUG_CMD}
                """
            }
        }
    }

  }

  post {
    success {
      notifySlack("GET AI Forecast Deployment", "SUCCESS")
    }
    failure {
      notifySlack("GET AI Forecast Deployment", "FAILURE")
    }
  }
}
