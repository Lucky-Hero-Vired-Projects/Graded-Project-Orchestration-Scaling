# Provider configuration 
provider "aws" {
  region = "us-west-2" # Replace with your desired AWS region
}

# Security Group definition
resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Allow HTTP, HTTPS, SSH, and Jenkins access"

  ingress {
    description = "Allow HTTP traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTPS traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH traffic"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow Jenkins traffic"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "web-sg"
  }
}

# EC2 Instance definition
resource "aws_instance" "my_instance" {
  ami           = "ami-04dd23e62ed049936" # Replace with a valid AMI ID for your region
  instance_type = "t3.medium"
  key_name      = "studentpk-key" # Replace with your key pair name
  security_groups = [aws_security_group.web_sg.name]

  user_data = <<-EOF
    #!/bin/bash

    # Initial setup: Install system dependencies and tools
    sudo apt update -y && sudo apt upgrade -y
    sudo apt install -y curl unzip tar git apache2 openjdk-21-jdk python3 python3-pip docker.io ufw

    # Configure UFW
    sudo ufw allow OpenSSH
    sudo ufw allow 80/tcp
    sudo ufw allow 8080/tcp
    sudo ufw --force enable

    # Install Boto3 (AWS SDK for Python)
    pip3 install boto3

    # Install AWS CLI
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install

    # Install eksctl
    curl -L "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" -o eksctl.tar.gz
    tar -xzf eksctl.tar.gz
    sudo mv eksctl /usr/local/bin

    # Install kubectl
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    # Add user to Docker group
    sudo usermod -aG docker ubuntu

    # Application setup: Clone repository and configure
    sudo rm -rf /home/ubuntu/SampleMERNwithMicroservices
    git clone https://github.com/Prashanth6782/SampleMERNwithMicroservices.git /home/ubuntu/SampleMERNwithMicroservices

    # Add docker-compose.yml
    cat <<-DOCKERCOMPOSE > /home/ubuntu/SampleMERNwithMicroservices/docker-compose.yml
    version: '3.8'

    services:
      frontend:
        build:
          context: ./frontend
          dockerfile: Dockerfile
        ports:
          - "3000:3000"
        networks:
          - app-network

      hello-service:
        build:
          context: ./backend/helloService
          dockerfile: Dockerfile
        ports:
          - "3001:3001"
        networks:
          - app-network

      profile-service:
        build:
          context: ./backend/profileService
          dockerfile: Dockerfile
        ports:
          - "3002:3002"
        networks:
          - app-network

    networks:
      app-network:
        driver: bridge
    DOCKERCOMPOSE

    # Add Frontend Dockerfile
    cat <<-FRONTENDFILE > /home/ubuntu/SampleMERNwithMicroservices/frontend/Dockerfile
    FROM node:16-alpine

    # Working directory
    WORKDIR /usr/src/app

    COPY package*.json ./

    # Installing dependencies
    RUN npm install --silent

    # Copy local files
    COPY . . 
    EXPOSE 3000

    CMD ["npm","start"]
    FRONTENDFILE

    # Add Profile Service Dockerfile
    cat <<-PROFILEFILE > /home/ubuntu/SampleMERNwithMicroservices/backend/profileService/Dockerfile
    FROM node:16-alpine

    # Create app directory
    WORKDIR /usr/src/app

    # Install app dependencies
    COPY package*.json ./ 
    RUN npm install

    # Bundle app source
    COPY . . 
    EXPOSE 3002

    # Define the command
    CMD ["node", "index.js"]
    PROFILEFILE

    # Add Hello Service Dockerfile
    cat <<-HELLOFILE > /home/ubuntu/SampleMERNwithMicroservices/backend/helloService/Dockerfile
    FROM node:16-alpine

    # Create app directory
    WORKDIR /usr/src/app

    # Install app dependencies
    COPY package*.json ./ 
    RUN npm install

    # Bundle app source
    COPY . . 
    EXPOSE 3001

    # Define the command
    CMD ["node", "index.js"]
    HELLOFILE

    # Start Docker Compose
    cd /home/ubuntu/SampleMERNwithMicroservices
    docker-compose up -d --build

    # Install Jenkins
    sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
    echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
    sudo apt update -y
    sudo apt install jenkins -y
    sudo systemctl start jenkins
    sudo systemctl enable jenkins

    # Configure Apache as reverse proxy for Jenkins
    sudo bash -c 'echo "<VirtualHost *:80>
    ServerName localhost
    ProxyRequests Off
    ProxyPreserveHost On
    AllowEncodedSlashes NoDecode
    ProxyPass / http://localhost:8080/ nocanon
    ProxyPassReverse / http://localhost:8080/
    </VirtualHost>" > /etc/apache2/sites-available/jenkins.conf'
    sudo a2ensite jenkins
    sudo a2enmod headers
    sudo a2enmod rewrite
    sudo a2enmod proxy
    sudo a2enmod proxy_http
    sudo systemctl restart apache2

    echo "Setup complete. Access Jenkins at http://<your-server-ip>."
  EOF

  tags = {
    Name = "terraform-studentpk-bootstrap"
  }
}
