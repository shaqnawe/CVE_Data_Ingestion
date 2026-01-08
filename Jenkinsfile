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
                    sh 'isort --check-only .'
                    sh 'pylint --fail-under=8.0 .'
                }
            }
        }

        stage('Backend Tests (Integration)') {
            // This stage requires docker-compose on the host setup
            steps {
                script {
                    // Check if docker-compose is available
                    def dockerComposeExists = sh(script: "command -v docker-compose", returnStatus: true) == 0
                    if (dockerComposeExists) {
                        try {
                            sh 'docker-compose -f docker-compose.yml up -d db redis elasticsearch'
                            // Wait for services to be ready (simplistic sleep, better to use wait-for scripts)
                            sh 'sleep 20' 
                            
                            // run tests inside a container or locally if python is on host?
                            // Better run inside a separate container that attaches to the network
                            // Or simpler: use docker-compose run
                            sh 'docker-compose run backend pytest'
                        } finally {
                            sh 'docker-compose down -v'
                        }
                    } else {
                        echo "Docker Compose not found, skipping integration tests."
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
