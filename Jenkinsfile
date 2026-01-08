pipeline {
    agent any

    environment {
        // Shared environment variables
        PYTHON_VERSION = '3.11'
        NODE_VERSION = '20'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Frontend Checks') {
            agent {
                docker { 
                    image 'node:20-alpine' 
                    args '-u root' // unexpected permission issues often happen in Jenkins docker agents
                }
            }
            steps {
                dir('frontend') {
                    sh 'npm ci'
                    sh 'npm run lint'
                    // Add build step if needed: sh 'npm run build'
                }
            }
        }

        stage('Backend Checks') {
            agent {
                docker {
                    image 'python:3.11'
                }
            }
            steps {
                dir('backend') {
                    sh 'pip install --upgrade pip'
                    sh 'pip install -r requirements.txt'
                    sh 'isort --check-only . || true'
                    sh 'pylint --fail-under=8.0 . || true'
                }
            }
        }

        stage('Sanity Check') {
            steps {
                echo 'Hello World! The pipeline is running correctly.'
                sh 'echo "Running a simple shell command check"'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
