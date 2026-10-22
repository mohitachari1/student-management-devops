cd C:\Users\Mohit\Downloads\student-management-devops\student-management-devops
$u = 'mohitachari225'
$j = @'
pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'mohitachari225'
        IMAGE_NAME     = "${DOCKERHUB_USER}/student-management"
        IMAGE_TAG      = "v${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Install Dependencies') {
            steps {
                sh 'python3 -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }
        stage('Build') {
            steps { sh '. venv/bin/activate && python -m py_compile app.py' }
        }
        stage('Test') {
            steps { sh '. venv/bin/activate && pytest -v' }
        }
        stage('Docker Build') {
            steps { sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .' }
        }
        stage('Docker Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                        usernameVariable: 'U', passwordVariable: 'P')]) {
                    sh 'echo $P | docker login -u $U --password-stdin'
                    sh 'docker push $IMAGE_NAME:$IMAGE_TAG'
                    sh 'docker push $IMAGE_NAME:latest'
                }
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker rm -f student-app || true'
                sh 'docker run -d --name student-app --network devops-net -p 5000:5000 $IMAGE_NAME:latest'
            }
        }
    }
    post {
        success { echo 'Pipeline succeeded - application deployed.' }
        failure { echo 'Pipeline failed - deployment skipped.' }
    }
}
'@
$j.Replace('USER_HERE', $u) | Set-Content Jenkinsfile -Encoding ascii
git add .
git commit -m "Set Docker Hub username"
git push