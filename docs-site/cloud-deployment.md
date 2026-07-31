# Cloud Deployment (AWS, GCP, Azure)

CommunityMetrics je plně "Cloud Ready". Zde jsou konfigurace pro profesionální nasazení v cloudu.

## 1. Terraform (Infrastruktura jako kód)

Použijte tento Terraform snippet pro vytvoření instance s předinstalovaným Dockerem na AWS.

```hcl
resource "aws_instance" "communitymetrics_prod" {
  ami           = "ami-0c55b159cbfafe1f0" # Ubuntu 24.04
  instance_type = "t3.medium"
  
  tags = {
    Name = "CommunityMetrics-Production"
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io docker-compose
              EOF
}
```

## 2. Ansible (Konfigurace OS)

Automatizujte instalaci závislostí a stažení bota na vašem serveru.

```yaml
- name: Setup CommunityMetrics Node
  hosts: all
  tasks:
    - name: Install Docker
      apt: name=docker.io state=present
    - name: Copy .env
      copy: src=.env dest=/opt/communitymetrics/.env
    - name: Launch CommunityMetrics
      docker_service:
        project_src: /opt/communitymetrics
        state: present
```

## 3. Kubernetes (Vysoká dostupnost)

Pro deployment v GKE nebo EKS využijte tento manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: communitymetrics-bot
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: bot
        image: communitymetrics/bot:latest
        envFrom:
        - dotEnv: .env
```

::: tip Monitoring v cloudu
Pro profesionální provoz doporučujeme přidat exportér pro Redis a sledovat metriky (např. `redis_memory_used_bytes`) v Grafaně.
:::

::: info Doporučení
Pro nejlevnější provoz doporučujeme *Hetzner Cloud* nebo *DigitalOcean*, kde získáte dedikovanou RAM pro Redis za zlomek ceny velkých cloudů.
:::
