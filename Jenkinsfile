pipeline {
    agent any

    environment {
        APP_NAME = 'iso-compliance-api'
        ECR_REPO_URI = '738094828254.dkr.ecr.ap-northeast-2.amazonaws.com/build/iso-compliance-api'
        AWS_REGION = 'ap-northeast-2'
        IMAGE_TAG = "${env.BUILD_ID}"
        SLACK_CHANNEL = '#build-iso'
        SLACK_CREDENTIALS_ID = 'slack'
    }

    stages {
        stage('prepare') {
            steps {
                script {
                    env.VERSION = readFile('version').trim()
                    env.BRANCH_NAME_FOR_TAG = sh(
                        returnStdout: true,
                        script: 'echo ${BRANCH_NAME}'
                        ).trim().replace("/", "-").replace("%2F", "-")

                    // Create docker image name
                    env.IMAGE_NAME = ""
                    if (env.BRANCH_NAME == 'main') {
                        env.IMAGE_NAME = "${ECR_REPO_URI}:v${VERSION}"
                    } else if (env.BRANCH_NAME == 'dev') {
                        env.IMAGE_NAME = "${ECR_REPO_URI}:${BRANCH_NAME_FOR_TAG}-${IMAGE_TAG}"
                    }
                }
                slackSend(
                    message: "start to build [${APP_NAME} v${VERSION}] \n <${BUILD_URL}|${currentBuild.fullDisplayName}> \n build_id: <${BUILD_URL}|${BUILD_ID}> \n build_tag: ${BUILD_TAG}\n job: <${JOB_URL}|${JOB_NAME}>",
                    color: 'good',
                    channel: env.SLACK_CHANNEL
                )
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t $IMAGE_NAME .
                '''
            }
        }

        stage('Login to AWS ECR') {
            steps {
                script {
                    sh '''
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO_URI}
                    '''
                }
            }
        }

        stage('Push Docker Image to ECR') {
            steps {
                script {
                    docker.image(env.IMAGE_NAME).push()
                }
            }
        }
    }

    post {
        always {
            script {
                sh "docker rmi ${IMAGE_NAME} || true"
            }
        }
        success {
            slackSend(
                channel: env.SLACK_CHANNEL,
                color: 'good',
                message: "The pipeline <${BUILD_URL}|${currentBuild.fullDisplayName}> completed successfully ."
            )
        }
        aborted {
            slackSend(
                channel: env.SLACK_CHANNEL,
                color: 'warning',
                message: "The pipeline <${BUILD_URL}|${currentBuild.fullDisplayName}> was aborted."
            )
        }
        failure {
            slackSend(
                channel: env.SLACK_CHANNEL,
                color: 'danger',
                message: "The pipeline <${BUILD_URL}|${currentBuild.fullDisplayName}> failed."
            )
        }
    }
}
